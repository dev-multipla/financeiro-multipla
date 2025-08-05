# multipla_teste/management/commands/migrate_tenants.py
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
from django.db import connections
from empresas.models import Empresa

class Command(BaseCommand):
    help = 'Roda migrate para default e depois para cada tenant_<id>.'

    def handle(self, *args, **options):
        # 1) Migrações no default
        self.stdout.write(self.style.MIGRATE_HEADING("Migrating default database…"))
        call_command('migrate', database='default', interactive=False)

        # 2) Para cada empresa, crie dinamicamente o alias e migre
        empresas = Empresa.objects.all()
        if not empresas:
            self.stdout.write(self.style.WARNING("Nenhum tenant (Empresa) encontrado."))
            return

        for emp in empresas:
            alias = f'tenant_{emp.id}'
            if alias not in settings.DATABASES:
                # 2a) registra o DB
                settings.DATABASES[alias] = {
                    'ENGINE':   'django.db.backends.postgresql',
                    'NAME':     f'multipla_financeiro_tenant_{emp.id}',
                    'USER':     'multipla',
                    'PASSWORD': 'multipla',
                    'HOST':     'localhost',
                    'PORT':     '5432',
                }
                # limpa cache de conexão (opcional)
                connections._connections.pop(alias, None)

            # 2b) roda migrate para o tenant
            self.stdout.write(self.style.MIGRATE_LABEL(f"Migrating {alias}…"))
            call_command('migrate', database=alias, interactive=False)

        self.stdout.write(self.style.SUCCESS("Todas migrações concluídas!"))
