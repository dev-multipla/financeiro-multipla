#empresas/models.py
from django.db import models

class Empresa(models.Model):
    nome = models.CharField("Nome/Razão Social", max_length=255)
    cnpj = models.CharField("CNPJ", max_length=18, unique=True)
    endereco_matriz = models.CharField("Endereço da Matriz", max_length=255)
    cidade = models.CharField(max_length=100)
    estado = models.CharField(max_length=2)
    cep = models.CharField(max_length=9)
    telefone = models.CharField(max_length=15)
    email = models.EmailField()

    def __str__(self):
        return self.nome

class Filial(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='filiais')
    nome = models.CharField(max_length=255)
    endereco = models.CharField(max_length=255)
    cidade = models.CharField(max_length=100)
    estado = models.CharField(max_length=2)
    cep = models.CharField(max_length=9)
    telefone = models.CharField(max_length=15)
    email = models.EmailField()

    def __str__(self):
        return f"{self.nome} - {self.empresa.nome}"
