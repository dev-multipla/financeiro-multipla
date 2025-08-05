
# multipla_teste/tenant_middleware.py
from django.utils.deprecation import MiddlewareMixin
from .tenant_utils import set_current_tenant
from .tenant_utils import ensure_tenant_db
from empresas.models import Empresa
import logging

logger = logging.getLogger(__name__)

class TenantMiddleware(MiddlewareMixin):
    def process_request(self, request):
        """
        Middleware para configurar o tenant baseado no header HTTP_X_COMPANY_ID
        """
        # Limpa o tenant atual no início de cada request
        set_current_tenant(None)
        
        company_id = request.headers.get('X-Company-Id')
        
        if not company_id:
            logger.debug("Header X-Company-Id não encontrado")
            return
        
        try:
            empresa = Empresa.objects.get(id=company_id)
            ensure_tenant_db(empresa)
            set_current_tenant(empresa)
            logger.info(f"Tenant configurado para empresa: {empresa.nome} (ID: {empresa.id})")
        except Empresa.DoesNotExist:
            logger.error(f"Empresa não encontrada para ID: {company_id}")
        except ValueError:
            logger.error(f"ID de empresa inválido: {company_id}")