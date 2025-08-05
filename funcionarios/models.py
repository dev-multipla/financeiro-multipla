from django.db import models
from django.core.validators import RegexValidator
from empresas.models import Empresa

# Validador de estado (como você já tinha antes)
def estado_validator(value):
    # Implemente aqui a lógica de validação para estados brasileiros
    pass

# Choices para diversos campos
SEXO_CHOICES = [
    ('M', 'Masculino'),
    ('F', 'Feminino'),
    ('O', 'Outro')
]

ESTADO_CIVIL_CHOICES = [
    ('S', 'Solteiro'),
    ('C', 'Casado'),
    ('D', 'Divorciado'),
    ('V', 'Viúvo'),
    ('U', 'União Estável')
]

GRAU_INSTRUCAO_CHOICES = [
    ('FI', 'Fundamental Incompleto'),
    ('FC', 'Fundamental Completo'),
    ('MI', 'Médio Incompleto'),
    ('MC', 'Médio Completo'),
    ('SI', 'Superior Incompleto'),
    ('SC', 'Superior Completo'),
    ('PG', 'Pós-Graduação'),
    ('ME', 'Mestrado'),
    ('DO', 'Doutorado')
]

TIPO_CONTRATO_CHOICES = [
    ('C', 'CLT'),
    ('P', 'Pessoa Jurídica'),
    ('T', 'Temporário'),
    ('E', 'Estágio')
]

CATEGORIA_CHOICES = [
    ('ADM', 'Administrativo'),
    ('TEC', 'Técnico'),
    ('GES', 'Gestão'),
    ('OPE', 'Operacional')
]

FORMA_PAGAMENTO_CHOICES = [
    ('D', 'Dinheiro'),
    ('T', 'Transferência Bancária'),
    ('P', 'Pix'),
    ('C', 'Cheque')
]

class Funcionario(models.Model):

    cpf = models.CharField(max_length=14, unique=True)
    nome_completo = models.CharField(max_length=255)
    data_nascimento = models.DateField()
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES)
    nacionalidade = models.CharField(max_length=50, default='Brasileira')
    endereco = models.CharField('Logradouro', max_length=255)
    numero = models.CharField('Número', max_length=10, default='S/N')
    bairro = models.CharField('Bairro', max_length=100, default='Bairro não informado')
    cidade = models.CharField('Cidade', max_length=100, default='Cidade não informada')
    estado = models.CharField('Estado', max_length=2, default='XX', validators=[estado_validator])
    cep = models.CharField('CEP', max_length=9, default='00000-000', null=True, blank=True)
    estado_civil = models.CharField(max_length=1, choices=ESTADO_CIVIL_CHOICES)
    grau_instrucao = models.CharField(max_length=2, choices=GRAU_INSTRUCAO_CHOICES)
    data_admissao = models.DateField()
    matricula = models.CharField(max_length=20, unique=True)
    cargo_funcao = models.CharField(max_length=100)
    tipo_contrato = models.CharField(max_length=1, choices=TIPO_CONTRATO_CHOICES)
    jornada_trabalho = models.CharField(max_length=50)  # Ex: "44 horas semanais"
    categoria = models.CharField(max_length=3, choices=CATEGORIA_CHOICES)
    salario = models.DecimalField(max_digits=10, decimal_places=2)
    forma_pagamento = models.CharField(max_length=1, choices=FORMA_PAGAMENTO_CHOICES)
    is_active = models.BooleanField(default=True)  # Para soft delete
    empresa = models.ForeignKey(
       Empresa,
       on_delete=models.PROTECT,
       db_constraint=False,
       db_index=True,
       null=True,        # permite nulos
       blank=True        # formulário DRF não exige
   )
    
    def __str__(self):
        return f"{self.nome_completo} ({self.matricula})"