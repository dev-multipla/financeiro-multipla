# notifications/models.py
from django.db import models
from django.contrib.auth.models import User
from contratos.models import ProjecaoFaturamento

class NotificacaoVencimento(models.Model):
    TIPOS = (
        ('vencimento_2_dias', 'Vencimento em 2 dias'),
        ('vencimento_hoje', 'Vencimento hoje'),
        ('vencimento_atrasado', 'Vencimento em atraso'),
    )
    
    # Como usuários são globais, não precisamos de empresa_id aqui
    # A separação será feita via tenant routing
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    projecao = models.ForeignKey(ProjecaoFaturamento, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20, choices=TIPOS)
    titulo = models.CharField(max_length=200)
    mensagem = models.TextField()
    lida = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['usuario', 'projecao', 'tipo']
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.titulo} - {self.usuario.username}"