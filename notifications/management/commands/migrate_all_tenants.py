# notifications/management/commands/migrate_all_tenants.py
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
from multipla_teste.tenant_utils import default_db_context
from empresas.models import Empresa

class Command(BaseCommand):
    help = 'Roda migrations em todos os tenants'

    def add_arguments(self, parser):
        parser.add_argument(
            '--app',
            type=str,
            help='App específico para migrar (opcional)',
            default=None
        )

    def handle(self, *args, **options):
        app = options.get('app')
        
        # Primeiro migra o default
        self.stdout.write("Migrando banco default...")
        if app:
            call_command('migrate', app, database='default')
        else:
            call_command('migrate', database='default')
        
        # Depois migra todos os tenants
        with default_db_context():
            empresas = Empresa.objects.all()
        
        for empresa in empresas:
            alias = f"tenant_{empresa.id}"
            if alias in settings.DATABASES:
                self.stdout.write(f"Migrando {alias} ({empresa.nome})...")
                try:
                    if app:
                        call_command('migrate', app, database=alias)
                    else:
                        call_command('migrate', database=alias)
                    self.stdout.write(
                        self.style.SUCCESS(f"✓ {alias} migrado com sucesso")
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"✗ Erro ao migrar {alias}: {str(e)}")
                    )
        
        self.stdout.write(
            self.style.SUCCESS("Migrations concluídas em todos os tenants!")
        )