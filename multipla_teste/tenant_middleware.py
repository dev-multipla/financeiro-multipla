
# multipla_teste/tenant_middleware.py
from django.utils.deprecation import MiddlewareMixin
from .tenant_utils import set_current_tenant
from django.http import JsonResponse

from .tenant_utils import set_current_tenant,ensure_tenant_db
from empresas.models import Empresa
import logging

logger = logging.getLogger(__name__)

class TenantMiddleware(MiddlewareMixin):
    def process_request(self, request):
        """
        Middleware para configurar o tenant baseado no header X-Company-Id.
        Se o header for inválido ou não corresponder a uma Empresa, retorna 400.
        """
        # Limpa o tenant atual no início de cada request
        set_current_tenant(None)

        company_id = request.headers.get('X-Company-Id')
        if not company_id:
            # Nenhum header → segue sem tenant (default)
            logger.debug("Header X-Company-Id não encontrado")
            return  # continua no banco default

        # Valida se é inteiro
        try:
            company_id_int = int(company_id)
        except ValueError:
            logger.error(f"ID de empresa inválido: {company_id}")
            return JsonResponse(
                {"detail": "X-Company-Id deve ser um número inteiro"},
                status=400
            )

        # Busca a empresa
        try:
            empresa = Empresa.objects.get(id=company_id_int)
        except Empresa.DoesNotExist:
            logger.error(f"Empresa não encontrada para ID: {company_id_int}")
            return JsonResponse(
                {"detail": f"Empresa não encontrada para ID: {company_id_int}"},
                status=400
            )

        # Configura o tenant
        ensure_tenant_db(empresa)
        set_current_tenant(empresa)
        logger.info(f"Tenant configurado para empresa: {empresa.nome} (ID: {empresa.id})")
        # segue para o view normalmente