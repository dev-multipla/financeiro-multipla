from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth.models import User
from empresas.models import Empresa, Filial
from usuarios.models import PerfilUsuario
from clientes.models import Cliente

class FilialScopingTests(APITestCase):
    def setUp(self):
        # 1) Criar uma empresa e duas filiais
        self.empresa = Empresa.objects.create(
            nome="Empresa X", cnpj="00.000.000/0001-00",
            endereco_matriz="Rua A, 100", cidade="Cidade", estado="ST",
            cep="00000-000", telefone="(00)0000-0000", email="e@x.co"
        )
        self.f1 = Filial.objects.create(
            empresa=self.empresa, nome="Filial 1",
            endereco="Rua B, 200", cidade="Cidade", estado="ST",
            cep="11111-111", telefone="(11)1111-1111", email="f1@x.co"
        )
        self.f2 = Filial.objects.create(
            empresa=self.empresa, nome="Filial 2",
            endereco="Rua C, 300", cidade="Cidade", estado="ST",
            cep="22222-222", telefone="(22)2222-2222", email="f2@x.co"
        )

        # 2) Criar um usuário e seu perfil atrelado à empresa (para passar pelo middleware)
        self.user = User.objects.create_user(username="testuser", password="pass")
        PerfilUsuario.objects.create(user=self.user, email="u@x.co", empresa=self.empresa)

        # 3) Criar 3 clientes: um Matriz (filial=None), um na f1, um na f2
        self.cli_matriz = Cliente.objects.create(
            nome="Cliente Matriz", cpf_cnpj="123", endereco="Matriz", cidade="C", estado="ST",
            telefone="(00)0000-0000", email="m@x.co", filial=None
        )
        self.cli_f1 = Cliente.objects.create(
            nome="Cliente F1", cpf_cnpj="456", endereco="F1", cidade="C", estado="ST",
            telefone="(11)1111-1111", email="f1cli@x.co", filial=self.f1
        )
        self.cli_f2 = Cliente.objects.create(
            nome="Cliente F2", cpf_cnpj="789", endereco="F2", cidade="C", estado="ST",
            telefone="(22)2222-2222", email="f2cli@x.co", filial=self.f2
        )

        # 4) Forçar autenticação (pula o JWT pra simplificar o teste)
        self.client = APIClient()
        self.client.force_authenticate(self.user)

        # 5) URL da listagem de clientes
        self.url = reverse('cliente-list')  # ajuste ao seu basename/rota

    def test_sem_header_ve_apenas_matriz(self):
        """
        Se não enviar X-Filial-ID ou enviar 'all', deve retornar somente os Clientes com filial=null.
        """
        # 1) sem header
        r1 = self.client.get(self.url)
        self.assertEqual(r1.status_code, status.HTTP_200_OK)
        ids1 = {c['id'] for c in r1.json()}
        self.assertSetEqual(ids1, {self.cli_matriz.id})

        # 2) explicitando 'all'
        r2 = self.client.get(self.url, HTTP_X_FILIAL_ID='all')
        self.assertEqual(r2.status_code, status.HTTP_200_OK)
        ids2 = {c['id'] for c in r2.json()}
        self.assertSetEqual(ids2, {self.cli_matriz.id})

    def test_header_filial1_retorna_somente_f1(self):
        """
        Se enviar X-Filial-ID igual ao ID da filial 1, retorna somente clientes daquela filial.
        """
        r = self.client.get(self.url, HTTP_X_FILIAL_ID=str(self.f1.id))
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        data = r.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['id'], self.cli_f1.id)

    def test_header_filial2_retorna_somente_f2(self):
        """
        Se enviar X-Filial-ID igual ao ID da filial 2, retorna somente clientes daquela filial.
        """
        r = self.client.get(self.url, HTTP_X_FILIAL_ID=str(self.f2.id))
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        data = r.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['id'], self.cli_f2.id)
