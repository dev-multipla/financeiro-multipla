#relatorios/services.py
from datetime import date
from django.db.models import Q
from django.utils.dateparse import parse_date
from contratos.models import Contrato, ProjecaoFaturamento
from contas_pagar.models import (
    ContaAPagar, ContaPagarAvulso,
    ContaAReceber, ContaReceberAvulso
)


def montar_relatorio_resultado_por_contrato(
    contrato_id,
    data_inicio,
    data_fim,
    tipos=None,
    include_orcado=True,
    projeto_id=None,
    centro_custo=None,
    conta_financeira=None,
    valor_min=None,
    valor_max=None,
    order_by=None
):
    """
    Monta uma lista de movimentos (ORÇADO, RECEITA, DESPESA) para o contrato informado,
    aplicando filtros opcionais, ordenação e calculando saldo acumulado.
    """
    # Conversão de strings para date e limpeza de barras
    if isinstance(data_inicio, str):
        data_inicio = parse_date(data_inicio.rstrip('/'))
    if isinstance(data_fim, str):
        data_fim = parse_date(data_fim.rstrip('/'))

    contrato = Contrato.objects.get(pk=contrato_id)
    project_ids = list(contrato.contrato_projetos.values_list('projeto_id', flat=True))

    itens = []

    # 1) ORÇADO (projeções)
    if include_orcado:
        qs_orc = ProjecaoFaturamento.objects.filter(
            contrato=contrato,
            data_vencimento__range=(data_inicio, data_fim)
        )
        if projeto_id:
            qs_orc = qs_orc.filter(
                contrato__contrato_projetos__projeto_id=projeto_id
            )
        for proj in qs_orc:
            itens.append({
                'tipo': 'ORÇADO',
                'data_movimento': proj.data_vencimento,
                'contrato': f"{contrato.numero} – {contrato.descricao}",
                'centro_custo': '',
                'conta_financeira': contrato.numero,
                'valor': proj.valor_parcela,
            })

    # 2) RECEITA normal
    qs_rec = ContaAReceber.objects.filter(
        contrato=contrato,
        status='recebido',
        data_recebimento__range=(data_inicio, data_fim)
    )
    if projeto_id:
        qs_rec = qs_rec.filter(
            contrato__contrato_projetos__projeto_id=projeto_id
        )
    for r in qs_rec:
        itens.append({
            'tipo': 'RECEITA',
            'data_movimento': r.data_recebimento,
            'contrato': f"{contrato.numero} – {contrato.descricao}",
            'centro_custo': r.centro_custo.descricao if r.centro_custo else '',
            'conta_financeira': r.conta_financeira.descricao if r.conta_financeira else '',
            'valor': r.valor_total,
        })

    # 3) RECEITA avulsa vinculada aos mesmos projetos
    qs_rec_avulsa = ContaReceberAvulso.objects.filter(
        projetos__in=project_ids,
        status='recebido',  # corrigido para status de recebimento
        data_recebimento__range=(data_inicio, data_fim)
    )
    if projeto_id:
        qs_rec_avulsa = qs_rec_avulsa.filter(
            projetos__id=projeto_id
        )
    for r in qs_rec_avulsa:
        itens.append({
            'tipo': 'RECEITA',
            'data_movimento': r.data_recebimento,
            'contrato': f"{contrato.numero} – {contrato.descricao}",
            'centro_custo': r.centro_custo.descricao if r.centro_custo else '',
            'conta_financeira': r.conta_financeira.descricao if r.conta_financeira else '',
            'valor': r.valor,
        })

    # 4) DESPESA normal
    qs_desp = ContaAPagar.objects.filter(
        contrato__contrato_projetos__projeto_id__in=project_ids,
        status='pago',
        data_pagamento__range=(data_inicio, data_fim)
    )
    if projeto_id:
        qs_desp = qs_desp.filter(
            contrato__contrato_projetos__projeto_id=projeto_id
        )
    for d in qs_desp:
        itens.append({
            'tipo': 'DESPESA',
            'data_movimento': d.data_pagamento,
            'contrato': f"{contrato.numero} – {contrato.descricao}",
            'centro_custo': d.centro_custo.descricao if d.centro_custo else '',
            'conta_financeira': d.conta_financeira.descricao if d.conta_financeira else '',
            'valor': d.valor_total,
        })

    # 5) DESPESA avulsa vinculada aos mesmos projetos
    qs_desp_avulsa = ContaPagarAvulso.objects.filter(
        projetos__in=project_ids,
        status='pago',
        data_pagamento__range=(data_inicio, data_fim)
    )
    if projeto_id:
        qs_desp_avulsa = qs_desp_avulsa.filter(
            projetos__id=projeto_id
        )
    for d in qs_desp_avulsa:
        itens.append({
            'tipo': 'DESPESA',
            'data_movimento': d.data_pagamento,
            'contrato': f"{contrato.numero} – {contrato.descricao}",
            'centro_custo': d.centro_custo.descricao if d.centro_custo else '',
            'conta_financeira': d.conta_financeira.descricao if d.conta_financeira else '',
            'valor': d.valor,
        })

    # 6) Filtros adicionais em memória: tipos, centro_custo, conta_financeira, valor_min, valor_max
    def filtra(item):
        if tipos and item['tipo'] not in tipos:
            return False
        if projeto_id and item['tipo'] == 'ORÇADO':
            # ORÇADO já filtrado pelo projeto acima
            pass
        if centro_custo and centro_custo.lower() not in item['centro_custo'].lower():
            return False
        if conta_financeira and conta_financeira.lower() not in item['conta_financeira'].lower():
            return False
        if valor_min is not None and item['valor'] < valor_min:
            return False
        if valor_max is not None and item['valor'] > valor_max:
            return False
        return True

    itens = list(filter(filtra, itens))

    # 7) Ordenação
    if order_by:
        reverse = order_by.startswith('-')
        key = order_by.lstrip('-')
        itens.sort(key=lambda x: x.get(key), reverse=reverse)
    else:
        itens.sort(key=lambda x: x['data_movimento'])

    # 8) Saldo acumulado (ignora ORÇADO)
    saldo = 0
    for item in itens:
        if item['tipo'] == 'RECEITA':
            saldo += item['valor']
        elif item['tipo'] == 'DESPESA':
            saldo -= item['valor']
        item['saldo'] = saldo

    return itens

def montar_relatorio_resultado_por_projeto(
    projeto_id,
    data_inicio,
    data_fim,
    tipos=None,
    include_orcado=True,
    contrato_id=None,
    centro_custo=None,
    conta_financeira=None,
    valor_min=None,
    valor_max=None,
    order_by=None
):
    """
    Monta uma lista de movimentos (ORÇADO, RECEITA, DESPESA) para o projeto informado,
    aplicando filtros opcionais, ordenação e calculando saldo acumulado.
    """
    from projetos.models import Projeto
    
    # Conversão de strings para date e limpeza de barras
    if isinstance(data_inicio, str):
        data_inicio = parse_date(data_inicio.rstrip('/'))
    if isinstance(data_fim, str):
        data_fim = parse_date(data_fim.rstrip('/'))

    projeto = Projeto.objects.get(pk=projeto_id)
    
    # Buscar todos os contratos vinculados ao projeto
    contratos_projeto = projeto.contrato_projetos.all()
    contrato_ids = list(contratos_projeto.values_list('contrato_id', flat=True))

    itens = []

    # 1) ORÇADO (projeções de todos os contratos do projeto)
    if include_orcado:
        qs_orc = ProjecaoFaturamento.objects.filter(
            contrato_id__in=contrato_ids,
            data_vencimento__range=(data_inicio, data_fim)
        )
        if contrato_id:
            qs_orc = qs_orc.filter(contrato_id=contrato_id)
            
        for proj in qs_orc:
            # Pegar o valor proporcional do projeto no contrato
            contrato_projeto = contratos_projeto.filter(contrato=proj.contrato).first()
            valor_proporcional = proj.valor_parcela
            if contrato_projeto and proj.contrato.valor_total > 0:
                proporcao = contrato_projeto.valor_projeto / proj.contrato.valor_total
                valor_proporcional = proj.valor_parcela * proporcao
            
            itens.append({
                'tipo': 'ORÇADO',
                'data_movimento': proj.data_vencimento,
                'projeto': projeto.nome,
                'contrato': f"{proj.contrato.numero} – {proj.contrato.descricao}",
                'centro_custo': '',
                'conta_financeira': proj.contrato.numero,
                'valor': valor_proporcional,
            })

    # 2) RECEITA normal (contratos vinculados ao projeto)
    qs_rec = ContaAReceber.objects.filter(
        contrato_id__in=contrato_ids,
        status='recebido',
        data_recebimento__range=(data_inicio, data_fim)
    )
    if contrato_id:
        qs_rec = qs_rec.filter(contrato_id=contrato_id)
        
    for r in qs_rec:
        # Pegar o valor proporcional do projeto no contrato
        contrato_projeto = contratos_projeto.filter(contrato=r.contrato).first()
        valor_proporcional = r.valor_total
        if contrato_projeto and r.contrato.valor_total > 0:
            proporcao = contrato_projeto.valor_projeto / r.contrato.valor_total
            valor_proporcional = r.valor_total * proporcao
            
        itens.append({
            'tipo': 'RECEITA',
            'data_movimento': r.data_recebimento,
            'projeto': projeto.nome,
            'contrato': f"{r.contrato.numero} – {r.contrato.descricao}",
            'centro_custo': r.centro_custo.descricao if r.centro_custo else '',
            'conta_financeira': r.conta_financeira.descricao if r.conta_financeira else '',
            'valor': valor_proporcional,
        })

    # 3) RECEITA avulsa vinculada diretamente ao projeto
    qs_rec_avulsa = ContaReceberAvulso.objects.filter(
        projetos__id=projeto_id,
        status='recebido',
        data_recebimento__range=(data_inicio, data_fim)
    )
    
    for r in qs_rec_avulsa:
        # Para contas avulsas, verificar se há valor específico do projeto
        projeto_conta = r.projetoconta_set.filter(projeto_id=projeto_id).first()
        valor_projeto = projeto_conta.valor if projeto_conta else r.valor
        
        itens.append({
            'tipo': 'RECEITA',
            'data_movimento': r.data_recebimento,
            'projeto': projeto.nome,
            'contrato': 'Avulso',
            'centro_custo': r.centro_custo.descricao if r.centro_custo else '',
            'conta_financeira': r.conta_financeira.descricao if r.conta_financeira else '',
            'valor': valor_projeto,
        })

    # 4) DESPESA normal (contratos vinculados ao projeto)
    qs_desp = ContaAPagar.objects.filter(
        contrato_id__in=contrato_ids,
        status='pago',
        data_pagamento__range=(data_inicio, data_fim)
    )
    if contrato_id:
        qs_desp = qs_desp.filter(contrato_id=contrato_id)
        
    for d in qs_desp:
        # Pegar o valor proporcional do projeto no contrato
        contrato_projeto = contratos_projeto.filter(contrato=d.contrato).first()
        valor_proporcional = d.valor_total
        if contrato_projeto and d.contrato.valor_total > 0:
            proporcao = contrato_projeto.valor_projeto / d.contrato.valor_total
            valor_proporcional = d.valor_total * proporcao
            
        itens.append({
            'tipo': 'DESPESA',
            'data_movimento': d.data_pagamento,
            'projeto': projeto.nome,
            'contrato': f"{d.contrato.numero} – {d.contrato.descricao}",
            'centro_custo': d.centro_custo.descricao if d.centro_custo else '',
            'conta_financeira': d.conta_financeira.descricao if d.conta_financeira else '',
            'valor': valor_proporcional,
        })

    # 5) DESPESA avulsa vinculada diretamente ao projeto
    qs_desp_avulsa = ContaPagarAvulso.objects.filter(
        projetos__id=projeto_id,
        status='pago',
        data_pagamento__range=(data_inicio, data_fim)
    )
    
    for d in qs_desp_avulsa:
        # Para contas avulsas, verificar se há valor específico do projeto
        projeto_conta_pagar = d.projetocontapagar_set.filter(projeto_id=projeto_id).first()
        valor_projeto = projeto_conta_pagar.valor if projeto_conta_pagar else d.valor
        
        itens.append({
            'tipo': 'DESPESA',
            'data_movimento': d.data_pagamento,
            'projeto': projeto.nome,
            'contrato': 'Avulso',
            'centro_custo': d.centro_custo.descricao if d.centro_custo else '',
            'conta_financeira': d.conta_financeira.descricao if d.conta_financeira else '',
            'valor': valor_projeto,
        })

    # 6) Filtros adicionais em memória
    def filtra(item):
        if tipos and item['tipo'] not in tipos:
            return False
        if centro_custo and centro_custo.lower() not in item['centro_custo'].lower():
            return False
        if conta_financeira and conta_financeira.lower() not in item['conta_financeira'].lower():
            return False
        if valor_min is not None and item['valor'] < valor_min:
            return False
        if valor_max is not None and item['valor'] > valor_max:
            return False
        return True

    itens = list(filter(filtra, itens))

    # 7) Ordenação
    if order_by:
        reverse = order_by.startswith('-')
        key = order_by.lstrip('-')
        itens.sort(key=lambda x: x.get(key), reverse=reverse)
    else:
        itens.sort(key=lambda x: x['data_movimento'])

    # 8) Saldo acumulado (ignora ORÇADO)
    saldo = 0
    for item in itens:
        if item['tipo'] == 'RECEITA':
            saldo += item['valor']
        elif item['tipo'] == 'DESPESA':
            saldo -= item['valor']
        item['saldo'] = saldo

    return itens