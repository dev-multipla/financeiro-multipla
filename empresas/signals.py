## empresas/signals.py
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.core.management import call_command
from django.db import connections
from .models import Empresa
import logging

@receiver(post_save, sender=Empresa)
def ensure_tenant_db(sender, instance, created, **kwargs):
    if not created:
        return

    alias = f"tenant_{instance.id}"
    dbname = f"multipla_financeiro_tenant_{instance.id}"
    default_cfg = settings.DATABASES['default']

    # Define banco de administração (padrão: 'postgres')
    admin_db = default_cfg.get('ADMIN_DB', 'postgres')

    # Cria o database se não existir
    try:
        conn = psycopg2.connect(
            dbname=admin_db,
            user=default_cfg['USER'],
            password=default_cfg['PASSWORD'],
            host=default_cfg['HOST'],
            port=default_cfg['PORT'],
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (dbname,)
            )
            if not cur.fetchone():
                cur.execute(
                    f"CREATE DATABASE \"{dbname}\""
                    " WITH OWNER %s"
                    " ENCODING 'UTF8'"
                    " LC_COLLATE='pt_BR.utf8'"
                    " LC_CTYPE='pt_BR.utf8'"
                    " TEMPLATE template0;",
                    (default_cfg['USER'],)
                )
    except Exception as e:
        logging.getLogger(__name__).error(f"Erro criando tenant DB {dbname}: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

    # Registra alias e executa migrações
    cfg = default_cfg.copy()
    cfg['NAME'] = dbname
    settings.DATABASES[alias] = cfg
    connections.close_all()
    try:
        call_command('migrate', database=alias, interactive=False, verbosity=0)
    except Exception as e:
        logging.getLogger(__name__).error(f"Erro migrando tenant {alias}: {e}")
