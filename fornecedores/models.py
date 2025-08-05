#fornecedores/models.py
from django.db import models
from empresas.models import Empresa

class Fornecedor(models.Model):
    nome = models.CharField(max_length=255)
    cpf_cnpj = models.CharField(max_length=18, unique=True, blank=True, null=True)  # CPF ou CNPJ opcional
    endereco = models.CharField(max_length=255)
    cidade = models.CharField(max_length=100)
    estado = models.CharField(max_length=2)
    cep = models.CharField(max_length=9, blank=True, null=True)  # CEP opcional
    telefone = models.CharField(max_length=15)
    email = models.EmailField(unique=True, blank=True, null=True) # Email opcional
    is_active = models.BooleanField(default=True)

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        db_constraint=False,  # desativa a FK no nível do banco
        db_index=True
    )
    
    def __str__(self):
        return self.nome
