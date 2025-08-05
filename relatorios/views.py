#relatorios/views.py

from decimal import Decimal
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action

from multipla_teste.core.mixins import CompanyScopedMixin

from .serializers import RelatorioResultadoContratoSerializer
from .services import montar_relatorio_resultado_por_contrato
from contratos.models import Contrato

from projetos.models import Projeto
from .services import montar_relatorio_resultado_por_projeto
from .serializers import RelatorioResultadoProjetoSerializer


class RelatorioResultadoPorContratoViewSet(CompanyScopedMixin, viewsets.ViewSet):
    """
    Endpoint para relatório analítico de Resultado por Contrato.

    Parâmetros de query string:
      - contrato_id (int, obrigatório)
      - data_inicio (YYYY-MM-DD, obrigatório)
      - data_fim (YYYY-MM-DD, obrigatório)
      - tipo (csv: ORÇADO,RECEITA,DESPESA)
      - include_orcado (bool)
      - projeto_id (int)
      - centro_custo (str)
      - conta_financeira (str)
      - valor_min (Decimal)
      - valor_max (Decimal)
      - order_by (str)
    """
    serializer_class = RelatorioResultadoContratoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        params        = request.query_params
        contrato_id   = params.get('contrato_id')
        data_inicio   = params.get('data_inicio')
        data_fim      = params.get('data_fim')

        if not all([contrato_id, data_inicio, data_fim]):
            return Response(
                {"error": "Os parâmetros 'contrato_id', 'data_inicio' e 'data_fim' são obrigatórios."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Garante que o contrato pertence ao tenant atual
        try:
            contrato = Contrato.objects.get(pk=contrato_id)
        except Contrato.DoesNotExist:
            return Response({"error": "Contrato não encontrado."},
                            status=status.HTTP_404_NOT_FOUND)

        # Prepara filtros opcionais
        tipos = params.get('tipo')
        if tipos:
            tipos = [t.strip().upper() for t in tipos.split(',')]
        include_orcado    = params.get('include_orcado', 'true').lower() != 'false'
        projeto_id        = params.get('projeto_id')
        centro_custo      = params.get('centro_custo')
        conta_financeira  = params.get('conta_financeira')
        valor_min         = params.get('valor_min')
        valor_max         = params.get('valor_max')
        order_by          = params.get('order_by')

        # Converte valores numéricos
        valor_min = Decimal(valor_min) if valor_min is not None else None
        valor_max = Decimal(valor_max) if valor_max is not None else None

        try:
            linhas = montar_relatorio_resultado_por_contrato(
                contrato_id=contrato_id,
                data_inicio=data_inicio,
                data_fim=data_fim,
                tipos=tipos,
                include_orcado=include_orcado,
                projeto_id=projeto_id,
                centro_custo=centro_custo,
                conta_financeira=conta_financeira,
                valor_min=valor_min,
                valor_max=valor_max,
                order_by=order_by,
            )
        except Exception as e:
            return Response({"error": str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        serializer = self.serializer_class(linhas, many=True)
        return Response(serializer.data)

class RelatorioResultadoPorProjetoViewSet(CompanyScopedMixin, viewsets.ViewSet):
    """
    Endpoint para relatório analítico de Resultado por Projeto.

    Parâmetros de query string:
      - projeto_id (int, obrigatório)
      - data_inicio (YYYY-MM-DD, obrigatório)
      - data_fim (YYYY-MM-DD, obrigatório)
      - tipo (csv: ORÇADO,RECEITA,DESPESA)
      - include_orcado (bool)
      - contrato_id (int)
      - centro_custo (str)
      - conta_financeira (str)
      - valor_min (Decimal)
      - valor_max (Decimal)
      - order_by (str)
    """
    serializer_class = RelatorioResultadoProjetoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        params = request.query_params
        projeto_id = params.get('projeto_id')
        data_inicio = params.get('data_inicio')
        data_fim = params.get('data_fim')

        if not all([projeto_id, data_inicio, data_fim]):
            return Response(
                {"error": "Os parâmetros 'projeto_id', 'data_inicio' e 'data_fim' são obrigatórios."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Garante que o projeto pertence à empresa atual
        try:
            company_id = self.get_current_company_id()
            projeto = Projeto.objects.filter(empresa_id=company_id).get(pk=projeto_id)
        except Projeto.DoesNotExist:
            return Response({"error": "Projeto não encontrado."},
                            status=status.HTTP_404_NOT_FOUND)

        # Prepara filtros opcionais
        tipos = params.get('tipo')
        if tipos:
            tipos = [t.strip().upper() for t in tipos.split(',')]
        include_orcado = params.get('include_orcado', 'true').lower() != 'false'
        contrato_id = params.get('contrato_id')
        centro_custo = params.get('centro_custo')
        conta_financeira = params.get('conta_financeira')
        valor_min = params.get('valor_min')
        valor_max = params.get('valor_max')
        order_by = params.get('order_by')

        # Converte valores numéricos
        valor_min = Decimal(valor_min) if valor_min is not None else None
        valor_max = Decimal(valor_max) if valor_max is not None else None

        try:
            linhas = montar_relatorio_resultado_por_projeto(
                projeto_id=projeto_id,
                data_inicio=data_inicio,
                data_fim=data_fim,
                tipos=tipos,
                include_orcado=include_orcado,
                contrato_id=contrato_id,
                centro_custo=centro_custo,
                conta_financeira=conta_financeira,
                valor_min=valor_min,
                valor_max=valor_max,
                order_by=order_by,
            )
        except Exception as e:
            return Response({"error": str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        serializer = self.serializer_class(linhas, many=True)
        return Response(serializer.data)