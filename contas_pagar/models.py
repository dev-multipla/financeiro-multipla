#contas_pagar/models.py
from django.db import models
from projetos.models import Projeto
from contratos.models import Contrato
from pagamentos.models import FormaPagamento
from financeiro.models import ContaFinanceira,CentroCusto
from empresas.models import Empresa
from pagamentos.models import FormaPagamento
from financeiro.models import ContaFinanceira,CentroCusto
from decimal import Decimal

class ContaAPagar(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('pago', 'Pago'),
        ('estornado', 'Estornado'),
    ]

    status = models.CharField(  
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pendente'
    )

    contrato = models.ForeignKey(Contrato, on_delete=models.PROTECT, related_name='contas_pagar')
    forma_pagamento = models.ForeignKey(FormaPagamento, on_delete=models.PROTECT)
    data_pagamento = models.DateField()
    competencia = models.DateField()
    valor_total = models.DecimalField(max_digits=10, decimal_places=2)
    conta_financeira = models.ForeignKey(ContaFinanceira, on_delete=models.SET_NULL, null=True)
    centro_custo = models.ForeignKey(CentroCusto, on_delete=models.SET_NULL, null=True)
    is_active = models.BooleanField(default=True)
    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.PROTECT,
        db_constraint=False,
        db_index=True
    )
    
    # Novos campos para controle da diferença
    diferenca = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    justificativa_diferenca = models.TextField(null=True, blank=True)

    @property
    def projetos(self):
        return self.contrato.contrato_projetos.all()


#contas a receber

class ContaAReceber(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('recebido', 'Recebido'),
        ('estornado', 'Estornado'),
    ]

  # <-- Adicione este campo
    status = models.CharField(  
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pendente'
    )


    contrato = models.ForeignKey('contratos.Contrato', on_delete=models.PROTECT, related_name='contas_receber')
    forma_pagamento = models.ForeignKey('pagamentos.FormaPagamento', on_delete=models.PROTECT)
    data_recebimento = models.DateField()
    competencia = models.DateField()
    valor_total = models.DecimalField(max_digits=10, decimal_places=2)
    conta_financeira = models.ForeignKey('financeiro.ContaFinanceira', on_delete=models.SET_NULL, null=True)
    centro_custo = models.ForeignKey('financeiro.CentroCusto', on_delete=models.SET_NULL, null=True)
    is_active = models.BooleanField(default=True)

    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.PROTECT,
        db_constraint=False,
        db_index=True
    )
    is_active = models.BooleanField(default=True)

    # Novos campos para controle da diferença
    diferenca = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    justificativa_diferenca = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['-data_recebimento']

    def __str__(self):
        return f"Conta a Receber #{self.id}"

class ContaPagarAvulso(models.Model):
    
    tipo_pagador = models.CharField(
        max_length=20,
        choices=[('fornecedor', 'Fornecedor'), ('funcionario', 'Funcionário')],
        default='fornecedor'
    )

    descricao = models.CharField(max_length=255)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    data_pagamento = models.DateField()
    competencia = models.CharField(max_length=7)  # Formato 'MM/AAAA'
    fornecedor = models.ForeignKey('fornecedores.Fornecedor', on_delete=models.PROTECT)
    conta_financeira = models.ForeignKey(ContaFinanceira, on_delete=models.SET_NULL, null=True)
    centro_custo = models.ForeignKey(CentroCusto, on_delete=models.SET_NULL, null=True)
    projetos = models.ManyToManyField(Projeto, blank=True)
    is_active = models.BooleanField(default=True)

    def delete(self, *args, **kwargs):
        self.is_active = False
        self.save()
    funcionario = models.ForeignKey('funcionarios.Funcionario', on_delete=models.PROTECT, null=True, blank=True)
    conta_financeira = models.ForeignKey(ContaFinanceira, on_delete=models.SET_NULL, null=True)
    centro_custo = models.ForeignKey(CentroCusto, on_delete=models.SET_NULL, null=True)
    projetos = models.ManyToManyField(Projeto, blank=True)
    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.PROTECT,
        db_constraint=False,
        db_index=True
    )
    is_active = models.BooleanField(default=True)

    status = models.CharField(
        max_length=20,
        choices=[('pendente', 'Pendente'), ('pago', 'Pago'), ('estornado', 'Estornado')],
        default='pendente'
    )

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.tipo_pagador == 'fornecedor' and not self.fornecedor:
            raise ValidationError({'fornecedor': 'Este campo é obrigatório quando o tipo de pagador é fornecedor.'})
        if self.tipo_pagador == 'funcionario' and not self.funcionario:
            raise ValidationError({'funcionario': 'Este campo é obrigatório quando o tipo de pagador é funcionário.'})

    def delete(self, *args, **kwargs):
        self.is_active = False
        self.save()

class ProjetoContaPagar(models.Model):
    conta = models.ForeignKey(ContaPagarAvulso, on_delete=models.CASCADE)
    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE)
    valor = models.DecimalField(max_digits=10, decimal_places=2)

class ContaReceberAvulso(models.Model):
    descricao = models.CharField(max_length=255)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    data_recebimento = models.DateField()
    competencia = models.CharField(max_length=7)  # Formato 'MM/AAAA'
    cliente = models.ForeignKey('clientes.Cliente', on_delete=models.PROTECT)
    conta_financeira = models.ForeignKey(ContaFinanceira, on_delete=models.SET_NULL, null=True)
    centro_custo = models.ForeignKey(CentroCusto, on_delete=models.SET_NULL, null=True)
    projetos = models.ManyToManyField(Projeto, blank=True)
    is_active = models.BooleanField(default=True)

    def delete(self, *args, **kwargs):
        self.is_active = False
        self.save()
    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.PROTECT,
        db_constraint=False,
        db_index=True
    )
    is_active = models.BooleanField(default=True)

    status = models.CharField(
        max_length=20,
        choices=[('pendente', 'Pendente'), ('recebido','Recebido'), ('estornado', 'Estornado')],
        default='pendente'
    )

    def delete(self, *args, **kwargs):
        self.is_active = False
        self.save()

# Modelo intermediário para armazenar o valor de cada projeto
class ProjetoConta(models.Model):
    conta = models.ForeignKey(ContaReceberAvulso, on_delete=models.CASCADE)
    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
