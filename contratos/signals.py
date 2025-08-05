from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Contrato, ProjecaoFaturamento
from dateutil.relativedelta import relativedelta
import logging

# Configuração básica do logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
handler = logging.StreamHandler()
handler.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

@receiver(post_save, sender=Contrato)
def gerar_projecoes_faturamento(sender, instance, created, **kwargs):
    # Só executa quando o contrato for criado e estiver confirmado
    if created and instance.confirmado:
        try:
            # Se data_termino não estiver definido, usa 12 meses como horizonte padrão
            horizonte = 12 if instance.data_termino is None else None

            # Chama o método de geração de projeções,
            # passando o horizonte apenas quando necessário
            instance.gerar_projecoes(
                save=True,
                horizonte_projecao=horizonte
            )
        except Exception as e:
            logger.error(
                f"Erro ao gerar projeções para contrato {instance.id}: {e}"
            )
