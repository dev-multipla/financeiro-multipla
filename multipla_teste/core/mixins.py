# multipla_teste/core/mixins.py

from rest_framework.exceptions import PermissionDenied
from django.db import models
from ..tenant_router import get_current_tenant

class CompanyScopedMixin:
    """
    Mixin para ViewSets que precisam filtrar dados por empresa.
    Suporta acesso cross-tenant baseado em permissões do usuário.
    """

    def get_user_accessible_companies(self):
        if not self.request.user.is_authenticated:
            return set()

        try:
            perfil = self.request.user.perfilusuario
            # empresas_acessiveis contém as empresas com papel atribuído
            ids = set(
                perfil.empresas_acessiveis.values_list('id', flat=True)
            )
            ids.add(perfil.empresa_padrao.id)
            return ids
        except AttributeError:
            return set()

    def get_header_company_id(self):
        raw = (
            self.request.headers.get('X-Company-Id', '') or 
            self.request.headers.get('X-Company-ID', '')
        ).strip()
        
        #Sempre usamos X-Company-Id (minúsculo no CORS_ALLOW_HEADERS é o mesmo header)
        raw = self.request.headers.get('X-Company-Id', '').strip()

        if not raw or raw.lower() == 'all':
            return None

        try:
            company_id = int(raw)
        except ValueError:
            raise PermissionDenied("X-Company-ID deve ser um número inteiro")

        accessible_companies = self.get_user_accessible_companies()
        if company_id not in accessible_companies:
            raise PermissionDenied(f"Você não tem acesso à empresa ID {company_id}")

        return company_id

    def get_current_company_id(self):
        header_company = self.get_header_company_id()
        if header_company is not None:
            return header_company

        try:
            return self.request.user.perfilusuario.empresa_padrao.id
        except AttributeError:
            raise PermissionDenied("Usuário sem perfil configurado")

    def get_queryset(self):
        qs = super().get_queryset()
        # Se o header X-Company-Id for 'all' e o usuário for staff, retorna todos os registros
        raw = self.request.headers.get('X-Company-Id', '').strip().lower()
        if raw == 'all' and self.request.user.is_staff:
            return qs
        # Caso contrário, filtra pelo tenant atual
        company_id = self.get_current_company_id()
        return qs.filter(empresa_id=company_id)

    def perform_create(self, serializer):
        """No create, injetar empresa_id automaticamente."""
        company_id = self.get_current_company_id()
        if hasattr(serializer.Meta.model, 'empresa'):
            serializer.save(empresa_id=company_id)
        else:
            serializer.save()

    def perform_update(self, serializer):
        """No update, manter associação com empresa."""
        company_id = self.get_current_company_id()
        if hasattr(serializer.Meta.model, 'empresa'):
            serializer.save(empresa_id=company_id)
        else:
            serializer.save()

    def _fallback_queryset(self, qs):
        """
        Caso o tenant middleware não forneça registro, aplicar 
        filtro por empresa ou, se for staff com header 'all', sem filtro.
        """
        raw = self.request.headers.get('X-Company-ID', "").strip().lower()
        # Se quiser visualizar “all” e for staff, liberar todos
        if raw == 'all' and self.request.user.is_staff:
            return qs

        company_id = self.get_current_company_id()
        if hasattr(qs.model, 'empresa'):
            return qs.filter(empresa_id=company_id)
        # Se o modelo não tiver empresa, retorna sem filtro adicional
        return qs

# Mantém compatibilidade: views que costumavam chamar FilialScopedMixin
FilialScopedMixin = CompanyScopedMixin
