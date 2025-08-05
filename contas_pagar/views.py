# contas_pagar/views.py
from rest_framework import viewsets, status, permissions
from .models import ContaAPagar, ContaAReceber, ContaPagarAvulso, ContaReceberAvulso
from .serializers import (
    ContaAPagarSerializer, ContaAReceberSerializer, StatusContaAPagarSerializer, 
    StatusContaAReceberSerializer, ContaPagarAvulsoSerializer, ContaReceberAvulsoSerializer, 
    ConsolidatedContasSerializer
)
from contratos.serializers import ProjecaoFaturamentoSerializer
from rest_framework.views import APIView
from django.db.models import Sum, F, Case, When, Value, DecimalField, CharField, Subquery, OuterRef
from django.db.models.functions import Coalesce, TruncMonth
from rest_framework.response import Response
from rest_framework.decorators import action
import pandas as pd
from dateutil.relativedelta import relativedelta
from datetime import date, timedelta, datetime
from contratos.models import Contrato, ProjecaoFaturamento
from itertools import chain
from django.http import Http404
from django.utils import timezone
from django.utils.dateparse import parse_date
from multipla_teste.core.mixins import CompanyScopedMixin
from django.db.models import Q


class ContaAPagarViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = ContaAPagar.objects.filter(is_active=True)
    serializer_class = ContaAPagarSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()   # já filtrado por empresa
        return (
            qs
            .select_related(
                'contrato', 'forma_pagamento',
                'conta_financeira', 'centro_custo', 'contrato__fornecedor'
            )
            .prefetch_related(
                'contrato__contrato_projetos',
                'contrato__contrato_projetos__projeto'
            )
            .order_by('-data_pagamento')
        )

    @action(detail=False, methods=['get'], url_path='ultima-conta')
    def get_last_conta_by_contrato(self, request):
        contrato_id = request.query_params.get('contrato_id')

        if not contrato_id:
            return Response({"error": "O ID do contrato é obrigatório"}, status=status.HTTP_400_BAD_REQUEST)

        ultima_conta = self.get_queryset().filter(contrato_id=contrato_id).order_by('-data_pagamento').first()

        if not ultima_conta:
            return Response({"error": "Nenhuma conta encontrada para este contrato"}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(ultima_conta)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def valor_total(self, request):
        total = self.get_queryset().aggregate(total=Sum('valor_total'))['total']
        return Response({'valor_total': total})

    @action(detail=False, methods=['get'])
    def proximo_vencimento(self, request):
        conta = ContaAPagar.objects.order_by('data_pagamento').first()
        serializer = self.get_serializer(conta)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def contas_pendentes(self, request):
        contas = ContaAPagar.objects.filter(data_pagamento__isnull=True)
        serializer = self.get_serializer(contas, many=True)
        return Response(serializer.data)
    
    def _marcar_projecao_mes_pago(self, conta):
        pag_date = conta.data_pagamento
        projecao = ProjecaoFaturamento.objects.filter(
            contrato=conta.contrato,
            pago=False,
            data_vencimento__year=pag_date.year,
            data_vencimento__month=pag_date.month
        ).first()
        if projecao:
            projecao.pago = True
            projecao.save()

    def perform_create(self, serializer):
        # chama o CompanyScopedMixin.perform_create → injeta empresa_id
        super().perform_create(serializer)
        # agora marca a projeção no objeto criado
        self._marcar_projecao_mes_pago(serializer.instance)

    def perform_update(self, serializer):
        # chama o CompanyScopedMixin.perform_update → mantém empresa_id
        super().perform_update(serializer)
        self._marcar_projecao_mes_pago(serializer.instance)

    @action(detail=False, methods=['get'], url_path='total-pagas-mes-vencimento')
    def total_pagas_mes_vencimento(self, request):
        hoje = date.today()
        mes_atual = hoje.month
        ano_atual = hoje.year

        total = ContaAPagar.objects.filter(
            # Filtra pela data de vencimento da projeção (não pela data de pagamento)
            contrato__projecoes_faturamento__data_vencimento__year=ano_atual,
            contrato__projecoes_faturamento__data_vencimento__month=mes_atual,
            
            # Garante que a projeção foi marcada como paga
            contrato__projecoes_faturamento__pago=True,
            
            # Considera apenas contas ativas
            is_active=True
        ).aggregate(
            total=Coalesce(Sum('valor_total'), Value(0), output_field=DecimalField())
        )

        return Response({'total_pagas_mes_vencimento': total['total']})

    @action(detail=False, methods=['get'], url_path='total-faturamento-pagar')
    def total_faturamento_pagar(self, request):
        hoje = date.today()
        mes_atual = hoje.month
        ano_atual = hoje.year

        # Filtra projeções NÃO PAGAS com vencimento no mês/ano atual
        parcelas_nao_pagas = ProjecaoFaturamento.objects.filter(
            data_vencimento__year=ano_atual,
            data_vencimento__month=mes_atual,
            contrato__tipo='fornecedor',
            pago=False  # <-- Filtro crucial para pegar apenas as pendentes
        )

        total_pendente = parcelas_nao_pagas.aggregate(
            total=Coalesce(Sum('valor_parcela'), Value(0), output_field=DecimalField())
        )['total']

        return Response({'total_faturamento_pagar': total_pendente})
    
    @action(detail=False, methods=['get'], url_path='proximo-vencimento-nao-pago')
    def proximo_vencimento_nao_pago(self, request):
        hoje = date.today()

        # Busca a próxima projeção não paga (vencimento futuro ou hoje)
        proxima_projecao = ProjecaoFaturamento.objects.filter(
            contrato__tipo='fornecedor',
            pago=False,
            data_vencimento__gte=hoje
        ).order_by('data_vencimento').first()

        if not proxima_projecao:
            return Response(
                {'detail': 'Nenhum vencimento pendente encontrado.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Serialização simplificada
        data = {
            'id': proxima_projecao.id,
            'data_vencimento': proxima_projecao.data_vencimento,
            'valor': float(proxima_projecao.valor_parcela),
            'contrato': {
                'id': proxima_projecao.contrato.id,
                'numero': proxima_projecao.contrato.numero,
                'descricao': proxima_projecao.contrato.descricao
            }
        }

        return Response(data)

    def perform_destroy(self, instance):
        # Soft delete: define is_active como False
        instance.is_active = False
        instance.save()


class ContaAReceberViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    serializer_class = ContaAReceberSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = ContaAReceber.objects.all()
    
    def get_queryset(self):
        qs = super().get_queryset()
        return (
            qs
            .select_related(
                'contrato', 'forma_pagamento',
                'conta_financeira', 'centro_custo', 'contrato__cliente'
            )
            .prefetch_related(
                'contrato__contrato_projetos',
                'contrato__contrato_projetos__projeto'
            )
            .order_by('-data_recebimento')
        )

    @action(detail=False, methods=['get'], url_path='ultima-conta')
    def get_last_conta_by_contrato(self, request):
        contrato_id = request.query_params.get('contrato_id')

        if not contrato_id:
            return Response({"error": "O ID do contrato é obrigatório"}, status=status.HTTP_400_BAD_REQUEST)

        # Busca a última conta a receber relacionada ao contrato, ordenada por data de recebimento
        ultima_conta = ContaAReceber.objects.filter(contrato_id=contrato_id).order_by('-data_recebimento').first()

        if not ultima_conta:
            return Response({"error": "Nenhuma conta encontrada para este contrato"}, status=status.HTTP_404_NOT_FOUND)

        # Serializa a conta encontrada
        serializer = self.get_serializer(ultima_conta)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def valor_total(self, request):
        total = ContaAReceber.objects.aggregate(total=Sum('valor_total'))['total']
        return Response({'valor_total': total})

    @action(detail=False, methods=['get'])
    def proximo_vencimento(self, request):
        conta = ContaAReceber.objects.order_by('data_recebimento').first()
        serializer = self.get_serializer(conta)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def contas_pendentes(self, request):
        contas = ContaAReceber.objects.filter(data_recebimento__isnull=True)
        serializer = self.get_serializer(contas, many=True)
        return Response(serializer.data)

    def _marcar_projecao_mes_recebido(self, conta):
        rec_date = conta.data_recebimento
        projecao = ProjecaoFaturamento.objects.filter(
            contrato=conta.contrato,
            pago=False,
            data_vencimento__year=rec_date.year,
            data_vencimento__month=rec_date.month
        ).first()
        if projecao:
            projecao.pago = True
            projecao.save()

    def perform_create(self, serializer):
        super().perform_create(serializer)
        # chama o método existente
        self._marcar_projecao_mes_recebido(serializer.instance)
        
    def perform_update(self, serializer):
        conta = serializer.save()
        self._marcar_projecao_mes_recebido(conta)

    @action(detail=False, methods=['get'], url_path='total-recebidas-ano')
    def total_recebidas_ano(self, request):
        ano_atual = date.today().year
        total_recebidas = ContaAReceber.objects.filter(data_recebimento__year=ano_atual).aggregate(total=Sum('valor_total'))['total']
        return Response({'total_recebidas_ano': total_recebidas})        
    
    @action(detail=False, methods=['get'], url_path='total-recebidas-mes-vencimento')
    def total_recebidas_mes_vencimento(self, request):
        hoje = date.today()
        mes_atual = hoje.month
        ano_atual = hoje.year

        total = ContaAReceber.objects.filter(
            # Filtra pela data de vencimento da projeção (não pela data de recebimento)
            contrato__projecoes_faturamento__data_vencimento__year=ano_atual,
            contrato__projecoes_faturamento__data_vencimento__month=mes_atual,
            
            # Marca a projeção como quitada (usando o campo 'pago')
            contrato__projecoes_faturamento__pago=True,
            
            # Considera apenas contas ativas
            is_active=True
        ).aggregate(
            total=Coalesce(Sum('valor_total'), Value(0), output_field=DecimalField())
        )

        return Response({'total_recebidas_mes_vencimento': total['total']})

    @action(detail=False, methods=['get'])
    def total_faturamento_receber(self, request):
        hoje = date.today()
        mes_atual = hoje.month
        ano_atual = hoje.year

        parcelas_nao_pagas = ProjecaoFaturamento.objects.filter(
            data_vencimento__year=ano_atual,
            data_vencimento__month=mes_atual,
            contrato__tipo='cliente',
            pago=False  # <-- Filtro crucial para pegar apenas as pendentes
        )

        total_pendente = parcelas_nao_pagas.aggregate(
            total=Coalesce(Sum('valor_parcela'), Value(0), output_field=DecimalField())
        )['total']

        return Response({'total_faturamento_receber': total_pendente})

    def perform_destroy(self, instance):
        # Soft delete: define is_active como False
        instance.is_active = False
        instance.save()
    
    @action(
        detail=False,
        methods=['get'],
        url_path='vencimentos-proximos',
        url_name='vencimentos_proximos'
    )
    def vencimentos_proximos(self, request):
        hoje = date.today()
        amanha = hoje + timedelta(days=1)
        final_mes = (hoje.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        qs = ProjecaoFaturamento.objects.filter(
            contrato__tipo='fornecedor',
            pago=False,
            data_vencimento__gte=amanha,
            data_vencimento__lte=final_mes
        )
        serializer = ProjecaoFaturamentoSerializer(qs, many=True)
        return Response(serializer.data)


class ContaPagarAvulsoViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = ContaPagarAvulso.objects.filter(is_active=True)
    serializer_class = ContaPagarAvulsoSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return super().get_queryset().order_by('-data_pagamento')
    
    def perform_create(self, serializer):
        # obtém o tenant correto
        company_id = self.get_current_company_id()
        # salva de uma vez com empresa e is_active
        serializer.save(
            empresa_id=company_id,
            is_active=True
        )
        
    @action(detail=True, methods=['post'], url_path='soft-delete')
    def soft_delete(self, request, pk=None):
        conta = self.get_object()
        conta.delete()  # utiliza o método delete() customizado
        return Response({"status": "Conta desativada"}, status=status.HTTP_200_OK)


class ContaReceberAvulsoViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = ContaReceberAvulso.objects.filter(is_active=True)
    serializer_class = ContaReceberAvulsoSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return super().get_queryset().order_by('-data_recebimento')
    
    def perform_create(self, serializer):
        # obtém o tenant correto
        company_id = self.get_current_company_id()
        # salva de uma vez com empresa e is_active
        serializer.save(
            empresa_id=company_id,
            is_active=True
        )
        
    @action(detail=True, methods=['delete'], url_path='soft-delete')
    def soft_delete(self, request, pk=None):
        conta = self.get_object()
        conta.delete()  # Aciona o soft-delete
        return Response(
            {"status": "Conta a Receber Avulso excluída com sucesso"},
            status=status.HTTP_204_NO_CONTENT
        )


class ConsolidatedViewSet(CompanyScopedMixin, viewsets.GenericViewSet):
    """
    Retorna todas as contas (a pagar / a receber, normais e avulsas)
    já filtradas pelo tenant e pela empresa do usuário.
    Suporta list e retrieve, além de patch para atualizar status.
    """
    queryset = ContaAPagar.objects.all()
    serializer_class = ConsolidatedContasSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def _get_model_classes_by_type(self, tipo):
        """Retorna as classes de modelo baseado no tipo"""
        if tipo == 'pagar':
            return ContaAPagar, ContaPagarAvulso
        else:  # receber
            return ContaAReceber, ContaReceberAvulso
    
    def _get_filtered_queryset(self, model_cls, data_field):
        """Aplica filtros comuns a um modelo específico"""
        # Filtro base por empresa e ativo
        queryset = model_cls.objects.filter(
            empresa_id=self.get_current_company_id(),
            is_active=True
        )
        
        # Filtros por parâmetros da requisição
        status_val = self.request.query_params.get('status')
        if status_val:
            queryset = queryset.filter(status=status_val)
            
        dt_inicio = self.request.query_params.get('data_inicio')
        dt_fim = self.request.query_params.get('data_fim')
        
        if dt_inicio:
            queryset = queryset.filter(**{f"{data_field}__gte": dt_inicio})
        if dt_fim:
            queryset = queryset.filter(**{f"{data_field}__lte": dt_fim})
            
        return queryset

    def get_queryset(self):
        """Retorna queryset combinado baseado no tipo"""
        tipo = self.request.query_params.get('tipo', 'receber').lower()
        
        if tipo == 'pagar':
            # Contas a pagar normais e avulsas
            qs_pagar = self._get_filtered_queryset(ContaAPagar, 'data_pagamento')
            qs_pagar_avulso = self._get_filtered_queryset(ContaPagarAvulso, 'data_pagamento')
            
            # Combina e ordena
            combined = list(qs_pagar) + list(qs_pagar_avulso)
            combined.sort(key=lambda o: o.data_pagamento, reverse=True)
            
        else:  # receber
            # Contas a receber normais e avulsas
            qs_receber = self._get_filtered_queryset(ContaAReceber, 'data_recebimento')
            qs_receber_avulso = self._get_filtered_queryset(ContaReceberAvulso, 'data_recebimento')
            
            # Combina e ordena
            combined = list(qs_receber) + list(qs_receber_avulso)
            combined.sort(key=lambda o: o.data_recebimento, reverse=True)
            
        return combined

    def _find_object_by_pk_and_type(self, pk, tipo):
        """Busca objeto específico por PK e tipo"""
        pk = int(pk)
        model_main, model_avulso = self._get_model_classes_by_type(tipo)
        
        # Busca na tabela principal
        try:
            obj = model_main.objects.get(
                pk=pk,
                empresa_id=self.get_current_company_id(),
                is_active=True
            )
            return obj
        except model_main.DoesNotExist:
            pass
        
        # Busca na tabela avulsa
        try:
            obj = model_avulso.objects.get(
                pk=pk,
                empresa_id=self.get_current_company_id(),
                is_active=True
            )
            return obj
        except model_avulso.DoesNotExist:
            pass
            
        return None

    def get_object(self):
        """Recupera uma única instância baseada no PK e tipo"""
        pk = self.kwargs.get('pk')
        tipo = self.request.query_params.get('tipo', 'receber').lower()
        
        obj = self._find_object_by_pk_and_type(pk, tipo)
        if obj is None:
            raise Http404(f"Conta não encontrada com ID {pk} e tipo {tipo}")
            
        return obj

    def list(self, request):
        """Lista todas as contas consolidadas"""
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """Recupera uma conta específica"""
        obj = self.get_object()
        serializer = self.serializer_class(obj)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'], url_path='atualizar-status')
    def atualizar_status(self, request, pk=None):
        """Atualiza o status de uma conta específica"""
        try:
            # Debug: log dos dados recebidos
            print(f"DEBUG - Dados recebidos: {request.data}")
            print(f"DEBUG - Content-Type: {request.content_type}")
            print(f"DEBUG - Method: {request.method}")
            
            conta = self.get_object()
            novo_status = request.data.get('status')
            data_conf = request.data.get('data_confirmacao')
            
            # Debug: log da conta encontrada
            print(f"DEBUG - Conta encontrada: {type(conta).__name__} ID: {conta.pk}")
            
            if not novo_status:
                return Response({
                    'error': 'Status é obrigatório',
                    'debug_info': {
                        'received_data': dict(request.data),
                        'content_type': request.content_type,
                        'body_raw': request.body.decode('utf-8') if request.body else 'Empty body'
                    }
                }, status=400)
            
            # Valida se o status é válido para o modelo
            if hasattr(conta, 'STATUS_CHOICES'):
                valid_statuses = [choice[0] for choice in conta.STATUS_CHOICES]
                if novo_status not in valid_statuses:
                    return Response(
                        {'error': f'Status inválido. Opções válidas: {valid_statuses}'}, 
                        status=400
                    )
            
            # Atualiza o status
            old_status = conta.status
            conta.status = novo_status
            
            # Atualiza data de confirmação se fornecida
            if data_conf:
                if hasattr(conta, 'data_pagamento'):
                    conta.data_pagamento = data_conf
                elif hasattr(conta, 'data_recebimento'):
                    conta.data_recebimento = data_conf
            
            conta.save()
            
            # Atualiza projeção se aplicável
            self._atualizar_projecao(conta)
            
            return Response({
                'message': f'Status atualizado de "{old_status}" para "{novo_status}"',
                'id': conta.pk,
                'status_anterior': old_status,
                'status_atual': novo_status,
                'tipo_conta': type(conta).__name__
            })
            
        except Exception as e:
            import traceback
            return Response({
                'error': f'Erro ao atualizar status: {str(e)}',
                'traceback': traceback.format_exc()
            }, status=500)
    
    def _atualizar_projecao(self, conta):
        """Atualiza projeção de faturamento se aplicável"""
        try:
            if hasattr(conta, 'contrato') and conta.contrato:
                from contratos.models import ProjecaoFaturamento
                
                data_vencimento = getattr(conta, 'data_pagamento', None) or getattr(conta, 'data_recebimento', None)
                
                if data_vencimento:
                    proj = ProjecaoFaturamento.objects.filter(
                        contrato=conta.contrato,
                        data_vencimento=data_vencimento
                    ).first()
                    
                    if proj:
                        proj.pago = True
                        proj.save()
        except Exception as e:
            # Log do erro mas não falha a operação principal
            print(f"Erro ao atualizar projeção: {str(e)}")
class RelatorioProjecoesViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['get'])
    def gerar_relatorio(self, request):
        # 1) parâmetros
        di = request.query_params.get('data_inicio')
        df = request.query_params.get('data_fim')
        cli = request.query_params.get('cliente')
        ctr = request.query_params.get('contrato')
        pj  = request.query_params.get('projeto')
        st  = request.query_params.get('status')

        # 2) defaults
        if not di:
            di = date.today().replace(day=1)
        if not df:
            df = (date.today() + relativedelta(months=12)).replace(day=1)

        qs = ProjecaoFaturamento.objects.filter(
            data_vencimento__range=[di, df]
        ).annotate(mes=TruncMonth('data_vencimento'))

        # 3) filtros
        if cli:
            qs = qs.filter(contrato__cliente__nome__icontains=cli)
        if ctr:
            qs = qs.filter(contrato_id=ctr)
        if pj:
            qs = qs.filter(contrato__contrato_projetos__projeto_id=pj)
        if st:
            qs = qs.filter(pago=(st.lower()=='pago'))

        # 4) agregação com contrato
        agrup = qs.values(
            'mes', 'contrato__tipo', 'contrato__numero', 'contrato__descricao'
        ).annotate(
            valor_total=Sum('valor_parcela'),
            valor_pago=Sum(Case(
                When(pago=True, then=F('valor_parcela')),
                default=0, output_field=DecimalField()
            )),
            valor_aberto=Sum(Case(
                When(pago=False, then=F('valor_parcela')),
                default=0, output_field=DecimalField()
            ))
        ).order_by('mes', 'contrato__numero')

        # 5) montar lista e totais
        rel, tot = [], {'total_receber':0,'total_pagar':0,'total_recebido':0,'total_pago':0}
        for a in agrup:
            tipo = 'Receber' if a['contrato__tipo']=='cliente' else 'Pagar'
            rec = a['valor_total'] if tipo=='Receber' else 0
            pag = a['valor_pago']  if tipo=='Pagar'   else 0
            if tipo=='Receber':
                tot['total_receber']  += a['valor_total']
                tot['total_recebido'] += a['valor_pago']
            else:
                tot['total_pagar'] += a['valor_total']
                tot['total_pago']  += a['valor_pago']

            rel.append({
                'mes':     a['mes'].strftime('%Y-%m'),
                'tipo':    tipo,
                'contrato': {
                    'numero':    a['contrato__numero'],
                    'descricao': a['contrato__descricao'],
                },
                'valor_total':  a['valor_total'],
                'valor_pago':   a['valor_pago'],
                'valor_aberto': a['valor_aberto'],
            })

        return Response({'relatorio': rel, 'totais': tot})

class RelatorioFinanceiroViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['get'])
    def gerar_relatorio(self, request):
        mes = request.query_params.get('mes')
        ano = request.query_params.get('ano')

        if not mes.isdigit() or not ano.isdigit():
            return Response({'error': 'Período inválido'}, status=status.HTTP_400_BAD_REQUEST)
        mes = int(mes)
        ano = int(ano)

        # Consultar receitas
        receitas = ContaAReceber.objects.filter(
            data_recebimento__month=mes,
            data_recebimento__year=ano
        ).values(
            contrato_nome=F('contrato__numero'),
            projeto_nome=F('projetos__projeto__nome')
        ).annotate(
            receita=Coalesce(Sum('projetos__valor'), Value(0), output_field=DecimalField()),
            despesa=Value(0, output_field=DecimalField())
        )

        # Consultar receitas avulsas
        receitas_avulsas = ContaReceberAvulso.objects.filter(
            data_recebimento__month=mes,
            data_recebimento__year=ano
        ).values(
            contrato_nome=Value('Avulso', output_field=CharField()),
            projeto_nome=Case(
                When(projetos__isnull=False, then=F('projetos__nome')),
                default=Value('-', output_field=CharField())
            )
        ).annotate(
            receita=F('valor'),
            despesa=Value(0, output_field=DecimalField())
        )

        # Consultar despesas
        despesas = ContaAPagar.objects.filter(
            data_pagamento__month=mes,
            data_pagamento__year=ano
        ).values(
            contrato_nome=F('contrato__numero'),
            projeto_nome=Case(
                When(projetos__isnull=False, then=F('projetos__nome')),
                default=Value('Custo Fixo'),
                output_field=CharField()
            )
        ).annotate(
            despesa=Coalesce(Sum('projeto_contas_a_pagar__valor'), F('valor_total'), output_field=DecimalField()),
            receita=Value(0, output_field=DecimalField())
        )

        # Consultar despesas avulsas
        despesas_avulsas = ContaPagarAvulso.objects.filter(
            data_pagamento__month=mes,
            data_pagamento__year=ano
        ).values(
            contrato_nome=Value('Avulso', output_field=CharField()),
            projeto_nome=Case(
                When(projetos__isnull=False, then=F('projetos__nome')),
                default=Value('-', output_field=CharField())
            )
        ).annotate(
            despesa=F('valor'),
            receita=Value(0, output_field=DecimalField())
        )

        # Converter para DataFrames
        df_receitas = pd.DataFrame(list(receitas))
        df_despesas = pd.DataFrame(list(despesas))
        df_receitas_avulsas = pd.DataFrame(list(receitas_avulsas))
        df_despesas_avulsas = pd.DataFrame(list(despesas_avulsas))

        # Combinar DataFrames
        df = pd.concat([df_receitas, df_despesas, df_receitas_avulsas, df_despesas_avulsas], ignore_index=True)

        # Calcular resultados
        df['resultado'] = df['receita'] - df['despesa']

        # Calcular totais
        total_receita = df['receita'].sum()
        total_despesa = df['despesa'].sum()
        total_geral = total_receita - total_despesa

        # Adicionar linha de total geral
        total_row = pd.DataFrame([{
            'contrato_nome': 'Total',
            'projeto_nome': '',
            'receita': total_receita,
            'despesa': total_despesa,
            'resultado': total_geral
        }])
        df = pd.concat([df, total_row], ignore_index=True)

        # Renomear colunas
        df = df.rename(columns={
            'contrato_nome': 'Contrato',
            'projeto_nome': 'Projeto',
            'receita': 'Receita',
            'despesa': 'Despesa',
            'resultado': 'Resultado'
        })

        # Serializar os dados para JSON
        data = df.to_dict('records')
        return Response(data)

class TotalContasAPagarView(APIView):
    def get(self, request, *args, **kwargs):
        total = ContaAPagar.objects.aggregate(total_sum=Sum('valor_total'))['total_sum'] or 0
        return Response({"total_contas_a_pagar": total}, status=status.HTTP_200_OK)

class ProximosVencimentosView(APIView):
    def get(self, request, *args, **kwargs):
        today = datetime.now().date()
        next_week = today + timedelta(days=7)
        proximos_vencimentos = ContaAPagar.objects.filter(data_primeiro_vencimento__range=[today, next_week])
        return Response({
            "proximos_vencimentos": proximos_vencimentos.values('id', 'descricao', 'data_primeiro_vencimento', 'valor_total')
        }, status=status.HTTP_200_OK)
    
class ProximosVencimentosViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Endpoint para retornar o vencimento mais próximo dentro do mês atual.
    Se o vencimento atual for pago, na próxima consulta será retornado o próximo a vencer.
    
    Permite a filtragem adicional via parâmetros de query:
      - ?conta=receber  : Filtra contratos do tipo 'cliente' (contas a receber)
      - ?conta=pagar    : Filtra contratos do tipo 'fornecedor' e 'funcionario' (contas a pagar)
    """
    serializer_class = ProjecaoFaturamentoSerializer
    queryset = ProjecaoFaturamento.objects.filter(pago=False)

    def get_queryset(self):
        qs = super().get_queryset()
        hoje = timezone.now().date()
        
        # Define o primeiro e o último dia do mês atual
        primeiro_dia = hoje.replace(day=1)
        ultimo_dia = (primeiro_dia + relativedelta(months=1)) - relativedelta(days=1)
        
        # Filtra as projeções do mês atual e que não foram pagas
        qs = qs.filter(data_vencimento__gte=primeiro_dia, data_vencimento__lte=ultimo_dia)

        # Filtragem adicional via parâmetro 'conta'
        tipo_conta = self.request.query_params.get('conta', '').strip('/').lower()
        if tipo_conta:
            if tipo_conta == 'receber':
                qs = qs.filter(contrato__tipo='cliente')
            elif tipo_conta == 'pagar':
                qs = qs.filter(contrato__tipo__in=['fornecedor', 'funcionario'])

        
        # Ordena pela data de vencimento em ordem ascendente
        qs = qs.order_by('data_vencimento')
        
        # Retorna somente o vencimento mais próximo
        return qs[:1]

    
class ContasPendentesViewSet(viewsets.ViewSet):
    """
    ViewSet para listar as contas a pagar pendentes (não pagas).
    """
    serializer_class = ContaAPagarSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Filtre as contas a pagar que ainda não foram pagas (data_pagamento é nula)
        queryset = ContaAPagar.objects.filter(data_pagamento__isnull=True)
        print("Queryset de contas pendentes:", queryset)
        return queryset

class ContasListView(APIView):
    def get(self, request, *args, **kwargs):
        contas_pagar = ContaAPagar.objects.all()
        contas_receber = ContaAReceber.objects.all()
        pagar_serializer = ContaAPagarSerializer(contas_pagar, many=True)
        receber_serializer = ContaAReceberSerializer(contas_receber, many=True)
        return Response({
            "contas_pagar": pagar_serializer.data,
            "contas_receber": receber_serializer.data
        })

class RelatorioOperacionalViewSet(CompanyScopedMixin, viewsets.ViewSet):
    """
    Endpoint único que retorna um relatório operacional financeiro com cinco listas:
      - receber_atrasadas: Projeções de contas a receber vencidas e não pagas
      - receber_pagas:     Projeções de contas a receber pagas
      - receber_nao_faturadas: Contratos de cliente sem projeções no período
      - pagar:             Projeções de contas a pagar no período
      - pagar_atrasadas:   Projeções de contas a pagar vencidas e não pagas
    Suporta filtros via query params: data_inicio, data_fim, contrato, cliente, fornecedor, projeto
    """
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def gerar_relatorio(self, request):
        # Leitura de filtros opcionais
        di = request.query_params.get('data_inicio')
        df = request.query_params.get('data_fim')
        contrato_id  = request.query_params.get('contrato')
        cliente_id   = request.query_params.get('cliente')
        fornecedor_id= request.query_params.get('fornecedor')
        projeto_id   = request.query_params.get('projeto')

        # Parse de datas
        try:
            di = parse_date(di) if di else None
            df = parse_date(df) if df else None
        except Exception:
            return Response({'error': 'Formato de data inválido'}, status=status.HTTP_400_BAD_REQUEST)

        # Função auxiliar para aplicar filtros period, contrato, cliente/fornecedor, projeto
        def filtrar_qs(qs, tipo):
            # filtrar por período
            if di and df:
                qs = qs.filter(data_vencimento__range=[di, df])
            elif di:
                qs = qs.filter(data_vencimento__gte=di)
            elif df:
                qs = qs.filter(data_vencimento__lte=df)
            # contrato, projeto
            if contrato_id:
                qs = qs.filter(contrato_id=contrato_id)
            if projeto_id:
                qs = qs.filter(contrato__contrato_projetos__projeto_id=projeto_id)
            # cliente ou fornecedor
            if tipo == 'receber' and cliente_id:
                qs = qs.filter(contrato__cliente_id=cliente_id)
            if tipo == 'pagar' and fornecedor_id:
                qs = qs.filter(contrato__fornecedor_id=fornecedor_id)
            return qs

        # --- Contas a receber faturadas (projeções) ---
        base_receber = ProjecaoFaturamento.objects.filter(contrato__tipo='cliente')
        base_receber = filtrar_qs(base_receber, 'receber')
        receber_atrasadas_qs = base_receber.filter(pago=False, data_vencimento__lt=date.today())
        receber_pagas_qs     = base_receber.filter(pago=True)

        # --- Contratos de receber não faturadas (nenhuma projeção no período) ---
        contratos = Contrato.objects.filter(tipo='cliente', is_deleted=False)
        if contrato_id:
            contratos = contratos.filter(id=contrato_id)
        if cliente_id:
            contratos = contratos.filter(cliente_id=cliente_id)
        if projeto_id:
            contratos = contratos.filter(contrato_projetos__projeto_id=projeto_id)
        if di and df:
            contratos = contratos.exclude(
                id__in=base_receber.values_list('contrato_id', flat=True)
            )

        # --- Contas a pagar (projeções) ---
        base_pagar = ProjecaoFaturamento.objects.filter(
            contrato__tipo__in=['fornecedor', 'funcionario']
        )
        base_pagar = filtrar_qs(base_pagar, 'pagar')
        pagar_qs         = base_pagar
        pagar_atrasadas_qs = base_pagar.filter(pago=False, data_vencimento__lt=date.today())

        # Função para serializar projeções
        def serialize_proj(qs):
            return [
                {
                    'id': p.id,
                    'contrato': {
                        'id': p.contrato.id,
                        'numero': p.contrato.numero
                    },
                    'cliente_fornecedor': (
                        p.contrato.cliente.nome if p.contrato.tipo=='cliente' else p.contrato.fornecedor.nome
                    ),
                    'projetos': [cp.projeto.nome for cp in p.contrato.contrato_projetos.all()],
                    'data_vencimento': p.data_vencimento,
                    'valor': p.valor_parcela,
                    'pago': p.pago
                }
                for p in qs.select_related('contrato').prefetch_related('contrato__contrato_projetos__projeto')
            ]

        # Montagem do JSON de resposta
        resultado = {
            'receber_atrasadas': serialize_proj(receber_atrasadas_qs),
            'receber_pagas':     serialize_proj(receber_pagas_qs),
            'receber_nao_faturadas': [
                {
                    'contrato_id': c.id,
                    'numero': c.numero,
                    'cliente': c.cliente.nome
                }
                for c in contratos
            ],
            'pagar':             serialize_proj(pagar_qs),
            'pagar_atrasadas':   serialize_proj(pagar_atrasadas_qs)
        }

        return Response(resultado)


class RelatorioFinanceiroViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['get'])
    def gerar_relatorio(self, request):
        mes = request.query_params.get('mes')
        ano = request.query_params.get('ano')

        if not mes.isdigit() or not ano.isdigit():
            return Response({'error': 'Período inválido'}, status=status.HTTP_400_BAD_REQUEST)
        mes = int(mes)
        ano = int(ano)

        # Consultar receitas
        receitas = ContaAReceber.objects.filter(
            data_recebimento__month=mes,
            data_recebimento__year=ano
        ).values(
            contrato_nome=F('contrato__numero'),
            projeto_nome=F('projetos__projeto__nome')
        ).annotate(
            receita=Coalesce(Sum('projetos__valor'), Value(0), output_field=DecimalField()),
            despesa=Value(0, output_field=DecimalField())
        )

        # Consultar receitas avulsas
        receitas_avulsas = ContaReceberAvulso.objects.filter(
            data_recebimento__month=mes,
            data_recebimento__year=ano
        ).values(
            contrato_nome=Value('Avulso', output_field=CharField()),
            projeto_nome=Case(
                When(projetos__isnull=False, then=F('projetos__nome')),
                default=Value('-', output_field=CharField())
            )
        ).annotate(
            receita=F('valor'),
            despesa=Value(0, output_field=DecimalField())
        )

        # Consultar despesas
        despesas = ContaAPagar.objects.filter(
            data_pagamento__month=mes,
            data_pagamento__year=ano
        ).values(
            contrato_nome=F('contrato__numero'),
            projeto_nome=Case(
                When(projetos__isnull=False, then=F('projetos__nome')),
                default=Value('Custo Fixo'),
                output_field=CharField()
            )
        ).annotate(
            despesa=Coalesce(Sum('projeto_contas_a_pagar__valor'), F('valor_total'), output_field=DecimalField()),
            receita=Value(0, output_field=DecimalField())
        )

        # Consultar despesas avulsas
        despesas_avulsas = ContaPagarAvulso.objects.filter(
            data_pagamento__month=mes,
            data_pagamento__year=ano
        ).values(
            contrato_nome=Value('Avulso', output_field=CharField()),
            projeto_nome=Case(
                When(projetos__isnull=False, then=F('projetos__nome')),
                default=Value('-', output_field=CharField())
            )
        ).annotate(
            despesa=F('valor'),
            receita=Value(0, output_field=DecimalField())
        )

        # Converter para DataFrames
        df_receitas = pd.DataFrame(list(receitas))
        df_despesas = pd.DataFrame(list(despesas))
        df_receitas_avulsas = pd.DataFrame(list(receitas_avulsas))
        df_despesas_avulsas = pd.DataFrame(list(despesas_avulsas))

        # Combinar DataFrames
        df = pd.concat([df_receitas, df_despesas, df_receitas_avulsas, df_despesas_avulsas], ignore_index=True)

        # Calcular resultados
        df['resultado'] = df['receita'] - df['despesa']

        # Calcular totais
        total_receita = df['receita'].sum()
        total_despesa = df['despesa'].sum()
        total_geral = total_receita - total_despesa

        # Adicionar linha de total geral
        total_row = pd.DataFrame([{
            'contrato_nome': 'Total',
            'projeto_nome': '',
            'receita': total_receita,
            'despesa': total_despesa,
            'resultado': total_geral
        }])
        df = pd.concat([df, total_row], ignore_index=True)

        # Renomear colunas
        df = df.rename(columns={
            'contrato_nome': 'Contrato',
            'projeto_nome': 'Projeto',
            'receita': 'Receita',
            'despesa': 'Despesa',
            'resultado': 'Resultado'
        })

        # Serializar os dados para JSON
        data = df.to_dict('records')
        return Response(data)


class TotalContasAPagarView(APIView):
    def get(self, request, *args, **kwargs):
        total = ContaAPagar.objects.aggregate(total_sum=Sum('valor_total'))['total_sum'] or 0
        return Response({"total_contas_a_pagar": total}, status=status.HTTP_200_OK)


class ProximosVencimentosView(APIView):
    def get(self, request, *args, **kwargs):
        today = datetime.now().date()
        next_week = today + timedelta(days=7)
        proximos_vencimentos = ContaAPagar.objects.filter(data_primeiro_vencimento__range=[today, next_week])
        return Response({
            "proximos_vencimentos": proximos_vencimentos.values('id', 'descricao', 'data_primeiro_vencimento', 'valor_total')
        }, status=status.HTTP_200_OK)


class ProximosVencimentosViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Endpoint para retornar o vencimento mais próximo dentro do mês atual.
    Se o vencimento atual for pago, na próxima consulta será retornado o próximo a vencer.
    
    Permite a filtragem adicional via parâmetros de query:
      - ?conta=receber  : Filtra contratos do tipo 'cliente' (contas a receber)
      - ?conta=pagar    : Filtra contratos do tipo 'fornecedor' e 'funcionario' (contas a pagar)
    """
    serializer_class = ProjecaoFaturamentoSerializer
    queryset = ProjecaoFaturamento.objects.filter(pago=False)

    def get_queryset(self):
        qs = super().get_queryset()
        hoje = timezone.now().date()
        
        # Define o primeiro e o último dia do mês atual
        primeiro_dia = hoje.replace(day=1)
        ultimo_dia = (primeiro_dia + relativedelta(months=1)) - relativedelta(days=1)
        
        # Filtra as projeções do mês atual e que não foram pagas
        qs = qs.filter(data_vencimento__gte=primeiro_dia, data_vencimento__lte=ultimo_dia)

        # Filtragem adicional via parâmetro 'conta'
        tipo_conta = self.request.query_params.get('conta', '').strip('/').lower()
        if tipo_conta:
            if tipo_conta == 'receber':
                qs = qs.filter(contrato__tipo='cliente')
            elif tipo_conta == 'pagar':
                qs = qs.filter(contrato__tipo__in=['fornecedor', 'funcionario'])

        # Ordena pela data de vencimento em ordem ascendente
        qs = qs.order_by('data_vencimento')
        
        # Retorna somente o vencimento mais próximo
        return qs[:1]


class ContasPendentesViewSet(viewsets.ViewSet):
    """
    ViewSet para listar as contas a pagar pendentes (não pagas).
    """
    serializer_class = ContaAPagarSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Filtre as contas a pagar que ainda não foram pagas (data_pagamento é nula)
        queryset = ContaAPagar.objects.filter(data_pagamento__isnull=True)
        print("Queryset de contas pendentes:", queryset)
        return queryset


class ContasListView(APIView):
    def get(self, request, *args, **kwargs):
        contas_pagar = ContaAPagar.objects.all()
        contas_receber = ContaAReceber.objects.all()
        pagar_serializer = ContaAPagarSerializer(contas_pagar, many=True)
        receber_serializer = ContaAReceberSerializer(contas_receber, many=True)
        return Response({
            "contas_pagar": pagar_serializer.data,
            "contas_receber": receber_serializer.data
        })