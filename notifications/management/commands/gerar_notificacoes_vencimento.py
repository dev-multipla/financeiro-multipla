# notifications/management/commands/gerar_notificacoes_vencimento.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from contratos.models import ProjecaoFaturamento
from notifications.models import NotificacaoVencimento
from multipla_teste.tenant_utils import execute_on_all_tenants, default_db_context
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Gera notificações de vencimento para todas as empresas (tenants)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--empresa-id',
            type=int,
            help='ID da empresa específica (opcional)'
        )

    def handle(self, *args, **options):
        empresa_id = options.get('empresa_id')
        
        if empresa_id:
            # Processar apenas uma empresa específica
            with default_db_context():
                from empresas.models import Empresa
                empresa = Empresa.objects.get(id=empresa_id)
            
            self._processar_empresa(empresa)
        else:
            # Processar todas as empresas
            results = execute_on_all_tenants(self._processar_empresa)
            
            # Log dos resultados
            for tenant, result in results.items():
                if 'error' in result:
                    logger.error(f"Erro no {tenant}: {result['error']}")
                else:
                    logger.info(f"Sucesso no {tenant}: {result}")

    def _processar_empresa(self, empresa):
        """Processa notificações para uma empresa específica"""
        hoje = timezone.now().date()
        dois_dias = hoje + timedelta(days=2)
        
        try:
            # Busca usuários desta empresa (banco default)
            with default_db_context():
                usuarios_empresa = list(
                    User.objects.filter(
                        perfilusuario__empresa_padrao=empresa,
                        is_active=True
                    )
                )
            
            if not usuarios_empresa:
                return {'notificacoes': 0, 'usuarios': 0}
            
            # Busca projeções que vencem em 2 dias (banco tenant)
            projecoes_2_dias = ProjecaoFaturamento.objects.filter(
                data_vencimento=dois_dias,
                pago=False,
                contrato__is_deleted=False
            )
            
            notificacoes_criadas = 0
            
            for projecao in projecoes_2_dias:
                for usuario in usuarios_empresa:
                    # Verifica se já existe notificação
                    exists = NotificacaoVencimento.objects.filter(
                        usuario=usuario,
                        projecao=projecao,
                        tipo='vencimento_2_dias'
                    ).exists()
                    
                    if not exists:
                        NotificacaoVencimento.objects.create(
                            usuario=usuario,
                            projecao=projecao,
                            tipo='vencimento_2_dias',
                            titulo=f"Vencimento em 2 dias",
                            mensagem=f"Contrato {projecao.contrato.numero} vence em {projecao.data_vencimento.strftime('%d/%m/%Y')}"
                        )
                        notificacoes_criadas += 1
            
            return {
                'notificacoes': notificacoes_criadas,
                'usuarios': len(usuarios_empresa),
                'projecoes_encontradas': projecoes_2_dias.count()
            }
            
        except Exception as e:
            logger.error(f"Erro processando empresa {empresa.id}: {str(e)}")
            raise