from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from pagamentos.models import FormaPagamento

class FormaPagamentoViewSetTestCase(TestCase):
    def setUp(self):
        # Crie um usuário para obter o token de autenticação
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        refresh = RefreshToken.for_user(self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

        # Crie algumas formas de pagamento para testar
        FormaPagamento.objects.create(descricao='Cartão de Crédito', tipo='cartao_credito')
        FormaPagamento.objects.create(descricao='Boleto Bancário', tipo='boleto')

    def test_list_formas_pagamento(self):
        url = reverse('formapagamento-list')  # Use o nome da URL configurada no seu urls.py
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Verifica se retornou as duas formas de pagamento criadas
