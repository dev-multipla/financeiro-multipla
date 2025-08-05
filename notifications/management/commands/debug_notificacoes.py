# notifications/management/commands/debug_notificacoes.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from contratos.models import ProjecaoFaturamento
from multipla_teste.tenant_utils import default_db_context
from empresas.models import Empresa
import traceback

class Command(BaseCommand):
    help = 'Debug do sistema de notificações'

    def add_arguments(self, parser):
        parser.add_argument('--empresa-id', type=int, help='ID da empresa')

    def handle(self, *args, **options):
        empresa_id = options.get('empresa_id')
        
        try:
            self.stdout.write("=== DEBUG NOTIFICAÇÕES ===")
            
            # 1. Teste acesso ao banco default
            with default_db_context():
                empresas_count = Empresa.objects.count()
                self.stdout.write(f"✓ Empresas encontradas: {empresas_count}")
                
                if empresa_id:
                    empresa = Empresa.objects.get(id=empresa_id)
                    self.stdout.write(f"✓ Empresa selecionada: {empresa.nome}")
                else:
                    empresa = Empresa.objects.first()
                    self.stdout.write(f"✓ Usando primeira empresa: {empresa.nome if empresa else 'Nenhuma'}")
            
            if not empresa:
                self.stdout.write(self.style.ERROR("❌ Nenhuma empresa encontrada"))
                return
            
            # 2. Teste acesso aos usuários
            with default_db_context():
                users = User.objects.all()
                self.stdout.write(f"✓ Usuários totais: {users.count()}")
                
                # Verifica se tem perfilusuario
                users_with_profile = User.objects.filter(perfilusuario__isnull=False)
                self.stdout.write(f"✓ Usuários com perfil: {users_with_profile.count()}")
            
            # 3. Teste acesso ao tenant
            from multipla_teste.tenant_utils import tenant_context, ensure_tenant_db
            
            with tenant_context(empresa):
                self.stdout.write(f"✓ Contexto tenant configurado para empresa {empresa.id}")
                
                # Verifica projeções
                hoje = timezone.now().date()
                dois_dias = hoje + timedelta(days=2)
                
                projecoes = ProjecaoFaturamento.objects.filter(
                    data_vencimento=dois_dias,
                    pago=False
                )
                self.stdout.write(f"✓ Projeções que vencem em {dois_dias}: {projecoes.count()}")
                
                for proj in projecoes[:3]:  # Mostra até 3
                    self.stdout.write(f"  - Contrato: {proj.contrato.numero}, Valor: {proj.valor_parcela}")
            
            # 4. Teste criação de notificação
            try:
                from notifications.models import NotificacaoVencimento
                self.stdout.write("✓ Model NotificacaoVencimento importado com sucesso")
                
                # Conta notificações existentes
                with tenant_context(empresa):
                    notif_count = NotificacaoVencimento.objects.count()
                    self.stdout.write(f"✓ Notificações existentes: {notif_count}")
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Erro com model NotificacaoVencimento: {str(e)}"))
            
            self.stdout.write(self.style.SUCCESS("=== DEBUG CONCLUÍDO ==="))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erro geral: {str(e)}"))
            self.stdout.write(self.style.ERROR(traceback.format_exc()))