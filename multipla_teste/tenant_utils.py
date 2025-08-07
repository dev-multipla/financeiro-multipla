from django.conf import settings
from django.db import connections, transaction
from .tenant_router import set_current_tenant, get_current_tenant
from contextlib import contextmanager
from empresas.models import Empresa
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

@contextmanager
def tenant_context(empresa):
    """
    Context manager para executar operações em um tenant específico
    Usage:
        with tenant_context(empresa):
            # Operações serão executadas no banco do tenant
            clientes = Cliente.objects.all()
    """
    old_tenant = get_current_tenant()
    try:
        set_current_tenant(empresa)
        ensure_tenant_db(empresa)
        yield
    finally:
        set_current_tenant(old_tenant)

@contextmanager
def default_db_context():
    """
    Context manager para forçar operações no banco default
    Usage:
        with default_db_context():
            # Operações serão executadas no banco default
            empresas = Empresa.objects.all()
    """
    old_tenant = get_current_tenant()
    try:
        set_current_tenant(None)
        yield
    finally:
        set_current_tenant(old_tenant)


def ensure_tenant_db(empresa):
    """
    Garante que o banco do tenant está configurado e acessível
    Args:
        empresa: Instância do modelo Empresa
    Returns:
        str: Alias do banco configurado
    """
    alias = f"tenant_{empresa.id}"

    if alias not in settings.DATABASES:
        base = settings.DATABASES["default"].copy()
        base["NAME"] = f"multipla_financeiro_tenant_{empresa.id}"
        settings.DATABASES[alias] = base
        logger.info(f"Banco {alias} configurado dinamicamente")

        # Fecha qualquer conexão antiga para este alias
        try:
            if alias in connections.databases:
                connections[alias].close()
        except Exception as e:
            logger.warning(f"Erro fechando conexão antiga {alias}: {e}")

    return alias


def aggregate_across_tenants(model_class, queryset_fn, include_empresa_info=True, max_workers=None):
    """
    Agrega dados de todos os tenants disponíveis.
    Se max_workers for None ou <=1, executa serialmente para evitar contenção.
    Caso contrário, usa ThreadPoolExecutor para paralelismo.
    """
    results = []

    # Carrega lista de empresas no DB default
    with default_db_context():
        empresas = list(Empresa.objects.all())

    def process_empresa(empresa):
        try:
            with tenant_context(empresa):
                alias = f"tenant_{empresa.id}"
                if alias not in connections.databases:
                    return None

                qs = model_class.objects.using(alias).all()
                return {
                    'empresa': empresa,
                    'result': queryset_fn(qs)
                }
        except Exception as e:
            logger.error(f"Erro no tenant {empresa.id}: {e}")
            return {
                'empresa': empresa,
                'error': str(e)
            }

    # Escolhe execução: paralela ou serial
    if max_workers and max_workers > 1:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(process_empresa, emp): emp for emp in empresas}
            for future in as_completed(futures):
                res = future.result()
                if res:
                    results.append(res)
    else:
        for empresa in empresas:
            res = process_empresa(empresa)
            if res:
                results.append(res)

    return results


def execute_on_all_tenants(operation_fn, include_default=False):
    """
    Executa uma operação em todos os tenants

    Args:
        operation_fn: Função a ser executada (recebe empresa como parâmetro)
        include_default: Se deve executar também no banco default

    Returns:
        dict: Resultados por tenant
    """
    results = {}

    if include_default:
        try:
            with default_db_context():
                results['default'] = operation_fn(None)
        except Exception as e:
            results['default'] = {'error': str(e)}

    # Obtém todas as empresas
    with default_db_context():
        empresas = Empresa.objects.all()

    for empresa in empresas:
        try:
            with tenant_context(empresa):
                results[f"tenant_{empresa.id}"] = operation_fn(empresa)
        except Exception as e:
            results[f"tenant_{empresa.id}"] = {'error': str(e)}
            logger.error(f"Erro executando operação no tenant {empresa.id}: {e}")

    return results


def get_tenant_stats():
    """
    Retorna estatísticas sobre os tenants configurados

    Returns:
        dict: Estatísticas dos tenants
    """
    stats = {
        'total_empresas': 0,
        'tenants_configurados': 0,
        'bancos_default': [],
        'bancos_tenant': [],
    }

    with default_db_context():
        stats['total_empresas'] = Empresa.objects.count()

    for alias, config in settings.DATABASES.items():
        if alias == 'default':
            stats['bancos_default'].append(config['NAME'])
        elif alias.startswith('tenant_'):
            stats['bancos_tenant'].append({
                'alias': alias,
                'database': config['NAME'],
                'tenant_id': int(alias.split('_')[1])
            })
            stats['tenants_configurados'] += 1

    return stats

@contextmanager
def tenant_transaction(empresa):
    """
    Context manager para transações no banco do tenant
    Usage:
        with tenant_transaction(empresa):
            # Operações transacionais no tenant
            cliente.save()
            fatura.save()
    """
    alias = ensure_tenant_db(empresa)
    old_tenant = get_current_tenant()

    try:
        set_current_tenant(empresa)
        with transaction.atomic(using=alias):
            yield
    finally:
        set_current_tenant(old_tenant)


def validate_cross_tenant_access(user, empresa_id):
    """
    Valida se um usuário tem acesso a uma empresa específica

    Args:
        user: Instância do User
        empresa_id: ID da empresa

    Returns:
        bool: True se tem acesso, False caso contrário
    """
    if not user.is_authenticated:
        return False

    try:
        perfil = user.perfilusuario
        empresas_acessiveis = set(perfil.empresas_acessiveis.values_list('id', flat=True))
        empresas_acessiveis.add(perfil.empresa_padrao.id)
        return empresa_id in empresas_acessiveis
    except AttributeError:
        return False