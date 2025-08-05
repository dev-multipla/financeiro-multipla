from django.apps import AppConfig

# empresas/apps.py
from django.apps import AppConfig
from django.conf import settings
from django.db import connections

class EmpresasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'empresas'

    def ready(self):
        # Importa o model
        from .models import Empresa

        # Configuração padrão de conexão
        default_cfg = settings.DATABASES.get('default', {})
        if not default_cfg:
            return

        # Para cada empresa, registra o alias tenant_{id}
    """  for empresa in Empresa.objects.all():
            alias = f"tenant_{empresa.id}"
            dbname = f"multipla_financeiro_tenant_{empresa.id}"
            if alias not in settings.DATABASES:
                cfg = default_cfg.copy()
                cfg['NAME'] = dbname
                settings.DATABASES[alias] = cfg"""

        # Fecha todas as conexões para o Django recarregar os novos aliases
       # connections.close_all()
