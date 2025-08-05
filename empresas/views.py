#empresas/views.py
from rest_framework import viewsets, permissions
from .models import Empresa, Filial
from .serializers import EmpresaSerializer, FilialSerializer, EmpresaListSerializer, FilialListSerializer

class EmpresaViewSet(viewsets.ModelViewSet):
    queryset = Empresa.objects.all()
    serializer_class = EmpresaSerializer
    permission_classes = [permissions.IsAuthenticated]

class FilialViewSet(viewsets.ModelViewSet):
    queryset = Filial.objects.all()
    serializer_class = FilialSerializer
    permission_classes = [permissions.IsAuthenticated]

class EmpresaListViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para listar empresas."""

    queryset = Empresa.objects.all()
    serializer_class = EmpresaListSerializer
    permission_classes = [permissions.IsAuthenticated]


class FilialListViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para listar filiais."""

    queryset = Filial.objects.all()
    serializer_class = FilialListSerializer
    permission_classes = [permissions.IsAuthenticated]
class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permite que apenas usuários staff façam POST/PUT/DELETE;
    leituras são públicas para qualquer usuário autenticado.
    """
    def has_permission(self, request, view):
        # leitura permitida para qualquer autenticado
        if request.method in permissions.SAFE_METHODS:
             return request.user and request.user.is_authenticated
        # escrita restrita a staff
        return request.user and request.user.is_staff

class EmpresaViewSet(viewsets.ModelViewSet):
    queryset = Empresa.objects.all()
    serializer_class = EmpresaSerializer
    permission_classes = [IsAdminOrReadOnly]

class FilialViewSet(viewsets.ModelViewSet):
    # Se quiser manter “Filial” para casos internos, só não o exponha mais nos apps cliente/contrato.
    queryset = Filial.objects.all()
    serializer_class = FilialSerializer
    permission_classes = [IsAdminOrReadOnly]

class EmpresaListViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Empresa.objects.all()
    serializer_class = EmpresaListSerializer

class FilialListViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Filial.objects.all()
    serializer_class = FilialListSerializer
