from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Funcionario
from .serializers import FuncionarioSerializer, FuncionarioSelectSerializer, FuncionarioListSerializer
from rest_framework import permissions
from multipla_teste.core.mixins import CompanyScopedMixin

class FuncionarioViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = Funcionario.objects.filter(is_active=True)
    serializer_class = FuncionarioSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['post'], url_path='soft-delete')
    def soft_delete(self, request):
        ids = request.data.get('ids', [])
        Funcionario.objects.filter(id__in=ids).update(is_active=False)
        return Response({"message": "Funcionários desativados com sucesso"}, status=status.HTTP_200_OK)

class FuncionarioSelectViewSet(CompanyScopedMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Funcionario.objects.filter(is_active=True)
    serializer_class = FuncionarioSelectSerializer

class FuncionarioListViewSet(CompanyScopedMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Funcionario.objects.filter(is_active=True)
    serializer_class = FuncionarioListSerializer
    permission_classes = [permissions.IsAuthenticated] 