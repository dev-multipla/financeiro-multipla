from django.db import models
#projetos/models.py
from django.db import models
from empresas.models import Empresa

class Projeto(models.Model):
    STATUS_CHOICES = (
        ('andamento', 'Em Andamento'),
        ('concluido', 'Concluído'),
        ('cancelado', 'Cancelado'),
    )

    nome = models.CharField(max_length=255)
    descricao = models.TextField()
    data_inicio = models.DateField()
    data_termino = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='andamento')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.nome
    data_termino = models.DateField(null=True, blank=True)  # Permite prazo indeterminado
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='andamento')
    is_active = models.BooleanField(default=True)
    empresa = models.ForeignKey(
           'empresas.Empresa',
           on_delete=models.CASCADE,
           db_constraint=False,
           db_index=True
     )

    
    def __str__(self):
        return self.nome

    @property
    def prazo_indeterminado(self):
        return self.data_termino is None
