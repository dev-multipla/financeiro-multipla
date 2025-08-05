# empresas/management/commands/migrate_tenants.py
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import logging

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
from django.db import connections

from empresas.models import Empresa

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Migra banco default e cria/migra bancos de cada tenant automaticamente.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant-id',
            type=int,
            help='Migrar apenas um tenant específico'
        )
        parser.add_argument(
            '--skip-default',
            action='store_true',
            help='Pular migração do banco default'
        )
        parser.add_argument(
            '--create-only',
            action='store_true',
            help='Apenas criar os bancos, sem migrar'
        )

    def handle(self, *args, **options):
        try:
            # 1) Migrar o database default (se não for pulado e não estivermos em modo create-only)
            if not options['skip_default'] and not options['create_only']:
                self._migrate_default()

            # 2) Processar os tenants (criar e/ou migrar)
            self._process_tenants(options)

            self.stdout.write(self.style.SUCCESS("\n=== TODAS AS OPERAÇÕES CONCLUÍDAS ==="))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erro fatal: {e}"))
            logger.exception("Erro durante migração de tenants")

    def _migrate_default(self):
        """Migra o banco default."""
        self.stdout.write(self.style.MIGRATE_HEADING("=== Migrando banco DEFAULT ==="))
        try:
            call_command('migrate', database='default', interactive=False, verbosity=1)
            self.stdout.write(self.style.SUCCESS("✓ Migração do default concluída"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Erro na migração do default: {e}"))
            raise

    def _process_tenants(self, options):
        """
        Processa todos os tenants (empresas) — cria Banco se necessário e/ou migra.
        """
        default_cfg = settings.DATABASES['default']

        # Determina quais empresas processar
        if options['tenant_id']:
            try:
                empresas = [Empresa.objects.get(id=options['tenant_id'])]
            except Empresa.DoesNotExist:
                raise Exception(f"Empresa ID {options['tenant_id']} não encontrada")
        else:
            empresas = Empresa.objects.all()

        if not empresas:
            self.stdout.write(self.style.WARNING("Nenhuma empresa encontrada"))
            return

        for empresa in empresas:
            self._process_single_tenant(empresa, default_cfg, options)

    def _process_single_tenant(self, empresa, default_cfg, options):
        """
        Cria e/ou migra o banco de um único tenant (empresa).
        """
        alias = f"tenant_{empresa.id}"
        dbname = f"multipla_financeiro_tenant_{empresa.id}"

        self.stdout.write(f"\n--- Processando {empresa.nome} (ID: {empresa.id}) ---")

        try:
            # 1) Criar o banco se não existir
            self._create_tenant_database(dbname, default_cfg)

            # 2) Registrar o alias em settings.DATABASES
            self._register_tenant_database(alias, dbname, default_cfg)

            # 3) Executar migrações (se não estivermos em modo apenas criação)
            if not options['create_only']:
                self._migrate_tenant_database(alias)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Erro processando tenant {alias}: {e}"))
            logger.exception(f"Erro processando tenant {empresa.nome}")

    def _create_tenant_database(self, dbname, default_cfg):
        """
        Cria o banco de dados do tenant no PostgreSQL se ainda não existir.
        Usa psycopg2 conectando ao banco administrativo (geralmente 'postgres' ou outro definido em ADMIN_DB).
        """
        # O nome do DB administrativo (padrão 'postgres' se não informado)
        admin_db = default_cfg.get('ADMIN_DB', 'postgres')

        conn = None
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
                # Verifica se o banco já existe
                cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
                if cur.fetchone():
                    self.stdout.write(f"✓ Banco {dbname} já existe")
                    return

                # Cria o banco
                self.stdout.write(self.style.WARNING(f"⚠ Criando banco {dbname}..."))
                cur.execute(f'''
                    CREATE DATABASE "{dbname}"
                    WITH OWNER = %s
                    ENCODING = 'UTF8'
                    LC_COLLATE = 'pt_BR.utf8'
                    LC_CTYPE = 'pt_BR.utf8'
                    TEMPLATE = template0
                ''', (default_cfg['USER'],))

                self.stdout.write(self.style.SUCCESS(f"✓ Banco {dbname} criado com sucesso"))
        except psycopg2.Error as e:
            raise Exception(f"Erro PostgreSQL criando {dbname}: {e}")
        except Exception as e:
            raise Exception(f"Erro criando banco {dbname}: {e}")
        finally:
            if conn:
                conn.close()

    def _register_tenant_database(self, alias, dbname, default_cfg):
        """
        Registra o alias do banco do tenant em settings.DATABASES,
        copiando a configuração do default e ajustando apenas o NAME.
        Em seguida, limpa todas as conexões ativas para forçar a reconfiguração.
        """
        if alias not in settings.DATABASES:
            cfg = default_cfg.copy()
            cfg['NAME'] = dbname
            settings.DATABASES[alias] = cfg
            self.stdout.write(f"✓ Alias {alias} registrado em settings.DATABASES")

        # Fecha todas as conexões ativas (incluindo as do tenant, se já existirem),
        # para garantir que novas conexões sejam criadas com as configurações atualizadas.
        connections.close_all()

    def _migrate_tenant_database(self, alias):
        """
        Executa as migrations no banco do tenant (alias).
        Como o TenantRouter já permite migrações em `db.startswith('tenant_')`,
        basta chamar call_command('migrate', database=alias).
        """
        try:
            self.stdout.write(f"Migrando {alias}...")
            call_command('migrate', database=alias, interactive=False, verbosity=1)
            self.stdout.write(self.style.SUCCESS(f"✓ {alias} migrado com sucesso"))
        except Exception as e:
            raise Exception(f"Erro migrando {alias}: {e}")
