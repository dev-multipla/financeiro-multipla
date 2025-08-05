# management/commands/setup_tenant_dbs.py
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
from django.db import connections
from empresas.models import Empresa
from multipla_teste.tenant_utils import ensure_tenant_db
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Configura bancos para todos os tenants existentes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--empresa-id',
            type=int,
            help='ID específico da empresa para configurar'
        )
        parser.add_argument(
            '--create-databases',
            action='store_true',
            help='Cria os bancos de dados fisicamente (requer privilégios)'
        )

    def handle(self, *args, **options):
        if options['empresa_id']:
            empresas = Empresa.objects.filter(id=options['empresa_id'])
        else:
            empresas = Empresa.objects.all()

        for empresa in empresas:
            self.stdout.write(f"Configurando tenant para empresa: {empresa.nome} (ID: {empresa.id})")
            
            try:
                # Configura o banco nas settings
                alias = ensure_tenant_db(empresa)
                
                if options['create_databases']:
                    # Aqui você poderia criar o banco fisicamente se necessário
                    self.stdout.write(f"  - Banco {alias} configurado")
                
                # Executa migrações
                self.stdout.write(f"  - Executando migrações para {alias}")
                call_command('migrate', database=alias, verbosity=0)
                
                self.stdout.write(
                    self.style.SUCCESS(f"  ✓ Tenant {empresa.nome} configurado com sucesso")
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  ✗ Erro configurando {empresa.nome}: {e}")
                )
                logger.exception(f"Erro configurando tenant {empresa.id}")

        self.stdout.write(self.style.SUCCESS("Configuração de tenants concluída"))