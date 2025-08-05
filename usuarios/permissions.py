# usuarios/permissions.py
from rest_framework import permissions
from .models import UsuarioEmpresaRole, PerfilUsuario

class IsEmpresaAdminOrFinanceiro(permissions.BasePermission):
    """
    Permite acesso apenas se o usuário tiver papel 'admin' ou 'financeiro' na empresa corrente.
    Supõe que o tenant (empresa) já foi definido no header 'X-Company-ID',
    e que existe um PerfilUsuario associado a request.user.
    """

    def has_permission(self, request, view):
        try:
            perfil = request.user.perfilusuario
        except PerfilUsuario.DoesNotExist:
            return False

        # Descobrimos a empresa atual (via mixin ou header)
        company_id = request.headers.get('X-Company-ID')
        if not company_id or company_id.lower() == 'all':
            # usa a empresa_padrao
            empresa = perfil.empresa_padrao
        else:
            try:
                empresa = perfil.empresas_acessiveis.get(id=int(company_id))
            except (ValueError, PerfilUsuario.empresas_acessiveis.through.DoesNotExist):
                return False

        # Busca a relação no through model:
        try:
            user_role = UsuarioEmpresaRole.objects.get(
                perfil_usuario=perfil,
                empresa=empresa
            ).role
        except UsuarioEmpresaRole.DoesNotExist:
            return False

        return user_role in ['admin', 'financeiro']


class IsEmpresaLeitura(permissions.BasePermission):
    """
    Permite apenas leitura de dados se o usuário tiver papel 'leitura' ou superior.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            try:
                perfil = request.user.perfilusuario
            except PerfilUsuario.DoesNotExist:
                return False

            company_id = request.headers.get('X-Company-ID')
            if not company_id or company_id.lower() == 'all':
                empresa = perfil.empresa_padrao
            else:
                try:
                    empresa = perfil.empresas_acessiveis.get(id=int(company_id))
                except (ValueError, PerfilUsuario.empresas_acessiveis.through.DoesNotExist):
                    return False

            try:
                user_role = UsuarioEmpresaRole.objects.get(
                    perfil_usuario=perfil,
                    empresa=empresa
                ).role
            except UsuarioEmpresaRole.DoesNotExist:
                return False

            # 'leitura' já é papel que permite SAFE_METHODS
            return user_role in ['leitura', 'financeiro', 'admin']
        return False
