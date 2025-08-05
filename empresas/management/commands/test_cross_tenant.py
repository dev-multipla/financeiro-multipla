from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from empresas.models import Empresa
from usuarios.models import PerfilUsuario

class Command(BaseCommand):
    help = 'Testa funcionalidade cross-tenant'

    def add_arguments(self, parser):
        parser.add_argument('--user-id', type=int, required=True)
        parser.add_argument('--empresa-id', type=int, required=True)

    def handle(self, *args, **options):
        try:
            user = User.objects.get(id=options['user_id'])
            empresa = Empresa.objects.get(id=options['empresa_id'])
            perfil = user.perfilusuario
            
            self.stdout.write(f"=== TESTE CROSS-TENANT ===")
            self.stdout.write(f"Usuário: {user.username}")
            self.stdout.write(f"Empresa teste: {empresa.nome}")
            self.stdout.write(f"Empresa padrão: {perfil.empresa_padrao.nome}")
            
            # Lista empresas acessíveis
            empresas_acessiveis = perfil.empresas_acessiveis.all()
            self.stdout.write(f"\nEmpresas acessíveis:")
            for emp in empresas_acessiveis:
                self.stdout.write(f"  - {emp.nome} (ID: {emp.id})")
            
            # Verifica se tem acesso à empresa teste
            tem_acesso = (
                empresa.id == perfil.empresa_padrao.id or
                perfil.empresas_acessiveis.filter(id=empresa.id).exists()
            )
            
            self.stdout.write(f"\nTem acesso à empresa {empresa.nome}? {tem_acesso}")
            
            if not tem_acesso:
                self.stdout.write("Adicionando acesso...")
                perfil.empresas_acessiveis.add(empresa)
                self.stdout.write(self.style.SUCCESS("✓ Acesso adicionado!"))
            
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR("Usuário não encontrado"))
        except Empresa.DoesNotExist:
            self.stdout.write(self.style.ERROR("Empresa não encontrada"))
        except PerfilUsuario.DoesNotExist:
            self.stdout.write(self.style.ERROR("Usuário sem perfil"))
