#contas_pagar/serializers.py
from rest_framework import serializers
from django.core.validators import DecimalValidator
from .models import ContaAPagar, ContaAReceber, ContaPagarAvulso, ContaReceberAvulso
from projetos.models import Projeto
from pagamentos.models import FormaPagamento
from contratos.models import Contrato
from financeiro.models import ContaFinanceira, CentroCusto
from .models import ContaAPagar, ContaAReceber, ContaPagarAvulso, ContaReceberAvulso, ProjetoConta, ProjetoContaPagar
from projetos.models import Projeto
from pagamentos.models import FormaPagamento
from contratos.models import Contrato, ProjecaoFaturamento
from financeiro.models import ContaFinanceira, CentroCusto
from clientes.models import Cliente 
from fornecedores.models import Fornecedor 

'''class ProjetoContaAPagarSerializer(serializers.ModelSerializer):
    projeto = serializers.PrimaryKeyRelatedField(queryset=Projeto.objects.all()) 

    class Meta:
        model = ProjetoContaAPagar
        fields = ['projeto', 'valor']'''

class ContaAPagarSerializer(serializers.ModelSerializer):
    # Campos calculados para front-end
    projetos = serializers.SerializerMethodField(read_only=True)
    cliente_fornecedor = serializers.SerializerMethodField(read_only=True)
    tipo_contrato = serializers.CharField(source='contrato.tipo', read_only=True)

    empresa = serializers.PrimaryKeyRelatedField(read_only=True)
    
    class Meta:
        model = ContaAPagar
        fields = [
            'id', 'contrato', 'forma_pagamento', 'data_pagamento', 'competencia',
            'valor_total', 'conta_financeira', 'centro_custo', 'projetos',
            'cliente_fornecedor', 'tipo_contrato', 'status',
            'diferenca', 'justificativa_diferenca', 'empresa',
        ]

        
    def get_projetos(self, obj):
        return [{
            'id': cp.projeto.id,
            'nome': cp.projeto.nome,
            'valor': cp.valor_projeto
        } for cp in obj.contrato.contrato_projetos.all()]

    def get_cliente_fornecedor(self, obj):
        if obj.contrato.tipo == 'cliente':
            return {'id': obj.contrato.cliente.id, 'nome': obj.contrato.cliente.nome}
        return {'id': obj.contrato.fornecedor.id, 'nome': obj.contrato.fornecedor.nome}

class ContaPagarAvulsoSerializer(serializers.ModelSerializer):
    
    def get_cliente_fornecedor(self, obj):
        # Para contas a pagar, o contrato deve estar vinculado a um fornecedor
        return {'id': obj.contrato.fornecedor.id, 'nome': obj.contrato.fornecedor.nome}
    
    def validate(self, data):
        """
        Valida duas regras:
        1. Não permitir lançamento duplicado para o mesmo contrato no mesmo mês.
        2. Caso o valor lançado (valor_total) difira do valor esperado na projeção,
           deve ser informada uma justificativa e calcular a diferença.
        """
        contrato = data.get('contrato')
        data_pagamento = data.get('data_pagamento')
        valor_total = data.get('valor_total')
        
        # Regra 1: Lançamento duplicado
        if contrato and data_pagamento:
            ano = data_pagamento.year
            mes = data_pagamento.month
            qs = ContaAPagar.objects.filter(
                contrato=contrato,
                data_pagamento__year=ano,
                data_pagamento__month=mes,
                is_active=True
            )
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError("Já existe um lançamento para este contrato no mesmo mês.")
        
        # Regra 2: Diferença entre valor lançado e valor esperado na projeção
        if contrato and data_pagamento and valor_total is not None:
            projecao = ProjecaoFaturamento.objects.filter(
                contrato=contrato,
                data_vencimento=data_pagamento
            ).first()
            if projecao:
                valor_esperado = projecao.valor_parcela
                if valor_total != valor_esperado:
                    diferenca = valor_total - valor_esperado
                    data['diferenca'] = diferenca
                    if not data.get('justificativa_diferenca'):
                        raise serializers.ValidationError(
                            "Justificativa da diferença é obrigatória quando o valor lançado difere do esperado."
                        )
        return data

# Serializer para entrada (write-only)
class ProjetoValorSerializer(serializers.Serializer):
    projeto = serializers.PrimaryKeyRelatedField(queryset=Projeto.objects.all())
    valor = serializers.DecimalField(max_digits=10, decimal_places=2)

# Serializer para saída (read-only)
class ProjetoContaPagarOutputSerializer(serializers.ModelSerializer):
    projeto_id = serializers.IntegerField(source='projeto.id')
    projeto_nome = serializers.CharField(source='projeto.nome')
    valor = serializers.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        model = ProjetoContaPagar
        fields = ['projeto_id', 'projeto_nome', 'valor']

class ContaPagarAvulsoSerializer(serializers.ModelSerializer):
    # Campo para receber dados dos projetos (escrita)
    projetos = ProjetoValorSerializer(many=True, write_only=True, required=False)
    # Campo para exibir os projetos vinculados (leitura)
    projetos_info = serializers.SerializerMethodField(read_only=True)
    empresa = serializers.PrimaryKeyRelatedField(read_only=True)
    
    class Meta:
        model = ContaPagarAvulso
        fields = '__all__'
        extra_kwargs = {
            'valor': {'validators': [DecimalValidator(max_digits=10, decimal_places=2)]},
        }

'''class ProjetoContaAReceberSerializer(serializers.ModelSerializer):
    projeto = serializers.PrimaryKeyRelatedField(queryset=Projeto.objects.all()) 

    class Meta:
        model = ProjetoContaAPagar
        fields = ['projeto', 'valor']'''

class ContaAReceberSerializer(serializers.ModelSerializer):
    projetos = serializers.SerializerMethodField()
    cliente = serializers.SerializerMethodField()
    tipo_contrato = serializers.CharField(source='contrato.tipo', read_only=True)

    class Meta:
        model = ContaAReceber
        fields = [
            'id', 'contrato', 'forma_pagamento', 'data_recebimento', 
            'competencia', 'valor_total', 'conta_financeira', 
            'centro_custo', 'projetos', 'cliente', 'tipo_contrato'
        ]

    def get_projetos(self, obj):
        try:
            return [{
                'id': cp.projeto.id,
                'nome': cp.projeto.nome,
                'valor': cp.valor_projeto
            } for cp in obj.contrato.contrato_projetos.all()]
        except Exception as e:
            print(f"Erro ao buscar projetos: {e}")
            return []

    def get_cliente(self, obj):
        try:
            if obj.contrato and obj.contrato.cliente:
                return {
                    'id': obj.contrato.cliente.id,
                    'nome': obj.contrato.cliente.nome
                }
            return None
        except Exception as e:
            print(f"Erro ao buscar cliente: {e}")
            return None

    
class ContaReceberAvulsoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContaReceberAvulso
        fields = '__all__'
        extra_kwargs = {
            'valor': {'validators': [DecimalValidator(max_digits=10, decimal_places=2)]},
        }
    
    def get_projetos_info(self, obj):
        projetos_conta = ProjetoContaPagar.objects.filter(conta=obj)
        return ProjetoContaPagarOutputSerializer(projetos_conta, many=True).data

    def create(self, validated_data):
        projetos_data = validated_data.pop('projetos', [])
        conta = ContaPagarAvulso.objects.create(**validated_data)
        
        # Vincula cada projeto e salva o valor específico no modelo intermediário
        for projeto_data in projetos_data:
            projeto = projeto_data['projeto']
            valor = projeto_data['valor']
            # Cria o registro intermediário
            ProjetoContaPagar.objects.create(conta=conta, projeto=projeto, valor=valor)
            # Associa o projeto à relação ManyToMany, se necessário
            conta.projetos.add(projeto)
        
        return conta
    
    def update(self, instance, validated_data):
        projetos_data = validated_data.pop('projetos', None)
        
        # Atualiza os campos da conta principal
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if projetos_data is not None:
            # Remove associações anteriores
            instance.projetos.clear()
            ProjetoContaPagar.objects.filter(conta=instance).delete()
            
            for projeto_data in projetos_data:
                projeto = projeto_data['projeto']
                valor = projeto_data['valor']
                ProjetoContaPagar.objects.create(conta=instance, projeto=projeto, valor=valor)
                instance.projetos.add(projeto)
        
        return instance
    
class ContaAReceberSerializer(serializers.ModelSerializer):
    # Campos calculados para front-end
    projetos = serializers.SerializerMethodField(read_only=True)
    cliente_fornecedor = serializers.SerializerMethodField(read_only=True)
    tipo_contrato = serializers.CharField(source='contrato.tipo', read_only=True)
    empresa = serializers.PrimaryKeyRelatedField(read_only=True)
    
    class Meta:
        model = ContaAReceber
        fields = [
            'id', 'contrato', 'forma_pagamento', 'data_recebimento', 'competencia',
            'valor_total', 'conta_financeira', 'centro_custo', 'projetos',
            'cliente_fornecedor', 'tipo_contrato', 'status',
            # Campos para controle de diferença
            'diferenca', 'justificativa_diferenca', 'empresa',
        ]
    
    def get_projetos(self, obj):
        return [{
            'id': cp.projeto.id,
            'nome': cp.projeto.nome,
            'valor': cp.valor_projeto
        } for cp in obj.contrato.contrato_projetos.all()]
    
    def get_cliente_fornecedor(self, obj):
        # Para contas a receber, o contrato está vinculado ao cliente
        return {'id': obj.contrato.cliente.id, 'nome': obj.contrato.cliente.nome}
    
    def validate(self, data):
        """
        Valida:
        1. Não permitir lançamento duplicado para o mesmo contrato no mesmo mês (usando data_recebimento).
        2. Se o valor lançado difere do esperado, exige justificativa e calcula a diferença.
        """
        contrato = data.get('contrato')
        data_recebimento = data.get('data_recebimento')
        valor_total = data.get('valor_total')
        
        # Regra 1: Lançamento duplicado
        if contrato and data_recebimento:
            ano = data_recebimento.year
            mes = data_recebimento.month
            qs = ContaAReceber.objects.filter(
                contrato=contrato,
                data_recebimento__year=ano,
                data_recebimento__month=mes,
                is_active=True
            )
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError("Já existe um lançamento para este contrato no mesmo mês.")
        
        # Regra 2: Diferença de valor
        if contrato and data_recebimento and valor_total is not None:
            projecao = ProjecaoFaturamento.objects.filter(
                contrato=contrato,
                data_vencimento=data_recebimento
            ).first()
            if projecao:
                valor_esperado = projecao.valor_parcela
                if valor_total != valor_esperado:
                    diferenca = valor_total - valor_esperado
                    data['diferenca'] = diferenca
                    if not data.get('justificativa_diferenca'):
                        raise serializers.ValidationError(
                            "Justificativa da diferença é obrigatória quando o valor lançado difere do esperado."
                        )
        return data

    
# Serializer para entrada de dados dos projetos (write-only)
class ProjetoContaInputSerializer(serializers.Serializer):
    projeto = serializers.PrimaryKeyRelatedField(queryset=Projeto.objects.all())
    valor = serializers.DecimalField(max_digits=10, decimal_places=2)

# Serializer para saída dos dados dos projetos (read-only)
class ProjetoContaOutputSerializer(serializers.ModelSerializer):
    projeto_id = serializers.IntegerField(source='projeto.id')
    projeto_nome = serializers.CharField(source='projeto.nome')
    valor = serializers.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        model = ProjetoConta
        fields = ['projeto_id', 'projeto_nome', 'valor']

class ContaReceberAvulsoSerializer(serializers.ModelSerializer):
    # Campo para receber os dados (input)
    projetos = ProjetoContaInputSerializer(many=True, write_only=True, required=False)
    # Campo para exibir os dados dos projetos associados (output)
    projetos_info = serializers.SerializerMethodField(read_only=True)
    # Permite escrever o cliente via ID
    cliente = serializers.PrimaryKeyRelatedField(queryset=Cliente.objects.all())
    empresa = serializers.PrimaryKeyRelatedField(read_only=True)
    
    class Meta:
        model = ContaReceberAvulso
        fields = [
            'id', 'descricao', 'valor', 'data_recebimento', 'competencia',
            'cliente', 'conta_financeira', 'centro_custo', 'projetos', 'projetos_info', 'status', 'is_active', 'empresa'
        ]

    def get_projetos_info(self, obj):
        projeto_contas = ProjetoConta.objects.filter(conta=obj)
        return ProjetoContaOutputSerializer(projeto_contas, many=True).data

    def create(self, validated_data):
        projetos_data = validated_data.pop('projetos', [])
        conta = ContaReceberAvulso.objects.create(**validated_data)
        for projeto_data in projetos_data:
            projeto = projeto_data.get('projeto')
            valor = projeto_data.get('valor')
            # Cria o registro intermediário com o valor do projeto
            ProjetoConta.objects.create(conta=conta, projeto=projeto, valor=valor)
            # Associa o projeto na relação ManyToMany se necessário
            conta.projetos.add(projeto)
        return conta

    def update(self, instance, validated_data):
        projetos_data = validated_data.pop('projetos', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if projetos_data is not None:
            # Limpa os relacionamentos anteriores
            instance.projetos.clear()
            ProjetoConta.objects.filter(conta=instance).delete()
            for projeto_data in projetos_data:
                projeto = projeto_data.get('projeto')
                valor = projeto_data.get('valor')
                ProjetoConta.objects.create(conta=instance, projeto=projeto, valor=valor)
                instance.projetos.add(projeto)
        return instance

class StatusContaAPagarSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=ContaAPagar.STATUS_CHOICES)

class StatusContaAReceberSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=ContaAReceber.STATUS_CHOICES)

class ConsolidatedContasSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    contrato = serializers.SerializerMethodField()
    tipo = serializers.SerializerMethodField()
    descricao = serializers.SerializerMethodField()
    data_vencimento = serializers.SerializerMethodField()
    valor_total = serializers.DecimalField(max_digits=10, decimal_places=2)
    status = serializers.CharField()
    detalhes = serializers.SerializerMethodField()

    def get_contrato(self, obj):
        # Serializa o objeto para extrair o campo "contrato" do serializer interno
        if isinstance(obj, ContaAPagar):
            data = ContaAPagarSerializer(obj, context=self.context).data
        else:
            data = ContaAReceberSerializer(obj, context=self.context).data
        return data.get('contrato')

    def get_tipo(self, obj):
        # Determina o tipo baseado na classe do objeto
        return 'pagar' if isinstance(obj, ContaAPagar) else 'receber'

    def get_descricao(self, obj):
        if isinstance(obj, ContaAPagar):
            return f"Conta a Pagar - {obj.contrato.fornecedor.nome}"
        return f"Conta a Receber - {obj.contrato.cliente.nome}"
    
    def get_data_vencimento(self, obj):
        if isinstance(obj, ContaAPagar):
            return obj.data_vencimento
        return obj.data_vencimento 

    valor_total = serializers.SerializerMethodField()  # Alterado para MethodField
    status = serializers.SerializerMethodField()         # Para tratar também os avulsos
    detalhes = serializers.SerializerMethodField()

    def get_valor_total(self, obj):
        # Se o objeto tiver o atributo 'valor_total' (contas normais), usa-o;
        # Caso contrário, utiliza 'valor' (contas avulsas)
        if hasattr(obj, 'valor_total'):
            return obj.valor_total
        elif hasattr(obj, 'valor'):
            return obj.valor
        return None

    def get_status(self, obj):
        # Contas normais possuem o atributo 'status', para avulsos você pode definir um valor padrão
        return obj.status if hasattr(obj, 'status') else "pendente"

    def get_contrato(self, obj):
        if hasattr(obj, 'contrato'):
            if isinstance(obj, ContaAPagar):
                data = ContaAPagarSerializer(obj, context=self.context).data
            elif isinstance(obj, ContaAReceber):
                data = ContaAReceberSerializer(obj, context=self.context).data
            else:
                data = {}
            return data.get('contrato', "Avulso")
        return "Avulso"

    def get_tipo(self, obj):
        if isinstance(obj, (ContaAPagar, ContaPagarAvulso)):
            return 'pagar'
        return 'receber'

    def get_descricao(self, obj):
        if isinstance(obj, ContaAReceber):
            return f"Conta a Receber - {obj.contrato.cliente.nome}" if (obj.contrato and hasattr(obj.contrato, 'cliente')) else "Conta a Receber"
        elif isinstance(obj, ContaReceberAvulso):
            return f"Conta a Receber Avulso - {obj.cliente.nome}" if hasattr(obj, 'cliente') else "Conta a Receber Avulso"
        elif isinstance(obj, ContaAPagar):
            return f"Conta a Pagar - {obj.contrato.fornecedor.nome}" if (obj.contrato and hasattr(obj.contrato, 'fornecedor')) else "Conta a Pagar"
        elif isinstance(obj, ContaPagarAvulso):
            return f"Conta a Pagar Avulso - {obj.fornecedor.nome}" if hasattr(obj, 'fornecedor') else "Conta a Pagar Avulso"
        return "Sem descrição"

    def get_data_vencimento(self, obj):
        # Utiliza data_pagamento para contas a pagar (normais e avulsas) e data_recebimento para contas a receber
        if isinstance(obj, (ContaAPagar, ContaPagarAvulso)):
            return obj.data_pagamento
        return obj.data_recebimento

    def get_detalhes(self, obj):
        from .serializers import ContaAPagarSerializer, ContaAReceberSerializer  # Import local para evitar circular
        serializer = (
            ContaAPagarSerializer(obj, context=self.context)
            if isinstance(obj, ContaAPagar)
            else ContaAReceberSerializer(obj, context=self.context)
        )
        return serializer.data
    
        # Seleciona o serializer correto para cada tipo de conta
        if isinstance(obj, ContaAPagar):
            serializer = ContaAPagarSerializer(obj, context=self.context)
        elif isinstance(obj, ContaPagarAvulso):
            serializer = ContaPagarAvulsoSerializer(obj, context=self.context)
        elif isinstance(obj, ContaAReceber):
            serializer = ContaAReceberSerializer(obj, context=self.context)
        elif isinstance(obj, ContaReceberAvulso):
            serializer = ContaReceberAvulsoSerializer(obj, context=self.context)
        else:
            serializer = None
        return serializer.data if serializer else {}

class RelatorioFinanceiroSerializer(serializers.Serializer):
    contrato_nome = serializers.CharField()
    projeto_nome = serializers.CharField()
    receita = serializers.DecimalField(max_digits=10, decimal_places=2)
    despesa = serializers.DecimalField(max_digits=10, decimal_places=2)
    resultado = serializers.DecimalField(max_digits=10, decimal_places=2)

class ProjecaoMensalSerializer(serializers.Serializer):
    mes = serializers.CharField()
    tipo = serializers.CharField()
    valor_total = serializers.DecimalField(max_digits=10, decimal_places=2)
    valor_pago = serializers.DecimalField(max_digits=10, decimal_places=2)
    valor_aberto = serializers.DecimalField(max_digits=10, decimal_places=2)

class TotaisSerializer(serializers.Serializer):
    total_receber = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_pagar = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_recebido = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_pago = serializers.DecimalField(max_digits=10, decimal_places=2)

class RelatorioProjecoesSerializer(serializers.Serializer):
    relatorio = ProjecaoMensalSerializer(many=True)
    totais = TotaisSerializer()

    def to_representation(self, instance):
        # Este método permite customizar a representação final dos dados
        data = super().to_representation(instance)
        
        # Aqui você pode adicionar lógica adicional se necessário
        # Por exemplo, adicionar campos calculados ou reformatar dados

        return data