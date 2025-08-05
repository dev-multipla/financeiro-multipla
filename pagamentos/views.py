from rest_framework import viewsets, permissions, serializers
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status
from .models import FormaPagamento
from .serializers import FormaPagamentoSerializer

class FormaPagamentoViewSet(viewsets.ModelViewSet):
    queryset = FormaPagamento.objects.filter(is_active=True)
    serializer_class = FormaPagamentoSerializer
    
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['post'], url_path='soft-delete')
    def soft_delete(self, request):
        ids = request.data.get('ids', [])  # Recebe a lista de IDs
        FormaPagamento.objects.filter(id__in=ids).update(is_active=False)  # Marca como inativo
        return Response({"message": "Formas de pagamento excluídas com sucesso."}, status=status.HTTP_200_OK)


class FormaPagamentoSelectViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = FormaPagamento.objects.filter(is_active=True)
    serializer_class = FormaPagamentoSerializer
# pagamentos/views.py

from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status

from .models import FormaPagamento
from .serializers import (
    FormaPagamentoSerializer,
    FormaPagamentoListSerializer,
    FormaPagamentoSelectSerializer
)
from multipla_teste.core.mixins import CompanyScopedMixin


class FormaPagamentoViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet completo para criar/editar/excluir (soft-delete) Formas de Pagamento,
    todas filtradas pelo campo `empresa` do tenant corrente.
    """
    queryset = FormaPagamento.objects.all()
    serializer_class = FormaPagamentoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Aplica filtro: is_active=True e empresa=tenant
        qs = super().get_queryset()
        return qs.filter(is_active=True)

    @action(detail=False, methods=['post'], url_path='soft-delete')
    def soft_delete(self, request):
        """
        POST /api/formas-pagamento/soft-delete/
        Body: { "ids": [1, 2, 3] }
        Marca como is_active=False todas as formas cujos IDs vierem na lista.
        """
        ids = request.data.get('ids', [])
        if not isinstance(ids, list):
            return Response(
                {"detail": "Você deve enviar uma lista de IDs."},
                status=status.HTTP_400_BAD_REQUEST
            )
        # Garantimos que apenas registros dessa empresa são afetados:
        company_id = self.get_current_company_id()
        FormaPagamento.objects.filter(
            id__in=ids,
            empresa_id=company_id
        ).update(is_active=False)
        return Response(
            {"message": "Formas de pagamento marcadas como inativas."},
            status=status.HTTP_200_OK
        )


class FormaPagamentoSelectViewSet(CompanyScopedMixin, viewsets.ReadOnlyModelViewSet):
    """
    Listagem simples de Formas de Pagamento (id, descricao),
    filtradas pela empresa corrente.
    """
    queryset = FormaPagamento.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return FormaPagamentoSelectSerializer
        return FormaPagamentoSerializer


class FormaPagamentoSelectSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormaPagamento
        fields = ['id', 'descricao']
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(is_active=True)


class FormaPagamentoListViewSet(CompanyScopedMixin, viewsets.ReadOnlyModelViewSet):
    """
    Uma ViewSet somente-leitura que retorna todos os campos,
    mas ainda filtrados por empresa e is_active=True.
    """
    queryset = FormaPagamento.objects.all()
    serializer_class = FormaPagamentoListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(is_active=True)
