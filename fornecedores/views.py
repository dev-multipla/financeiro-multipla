from django.shortcuts import render
from rest_framework import viewsets
#fornecedores/views.py
from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status
from .models import Fornecedor
from .serializers import FornecedorSerializer, FornecedorSelectSerializer, FornecedorListSerializer

class FornecedorViewSet(viewsets.ModelViewSet):
    queryset = Fornecedor.objects.filter(is_active=True)
    serializer_class = FornecedorSerializer
    
    @action(detail=False, methods=['post'], url_path='soft-delete')
    def soft_delete(self, request):
        ids = request.data.get('ids', [])  # Recebe a lista de IDs
        Fornecedor.objects.filter(id__in=ids).update(is_active=False)  # Marca como inativo
        return Response({"message": "Clientes excluídos com sucesso."}, status=status.HTTP_200_OK)

class FornecedorSelectViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Fornecedor.objects.filter(is_active=True)
    serializer_class = FornecedorSelectSerializer

class FornecedorListViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Fornecedor.objects.filter(is_active=True)
    serializer_class = FornecedorListSerializer
from multipla_teste.core.mixins import CompanyScopedMixin

class FornecedorViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = Fornecedor.objects.filter(is_active=True) 
    serializer_class = FornecedorSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        qs = super().get_queryset() 
        return qs.filter(is_active=True).order_by('nome')
    
    @action(detail=False, methods=['post'], url_path='soft-delete')
    def soft_delete(self, request):
        empresa_id = self.get_company_id()
        ids = request.data.get('ids', [])
        Fornecedor.objects.filter(empresa_id=empresa_id, id__in=ids).update(is_active=False)
        return Response(
            {"message": "Fornecedores marcados como inativos com sucesso."},
            status=status.HTTP_200_OK
        )

class FornecedorSelectViewSet(CompanyScopedMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Fornecedor.objects.filter(is_active=True)
    serializer_class = FornecedorSelectSerializer
    
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True).order_by('nome')

class FornecedorListViewSet(CompanyScopedMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Fornecedor.objects.filter(is_active=True)
    serializer_class = FornecedorListSerializer
    
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True).order_by('nome')
