import pytest
from rest_framework.authtoken.models import Token


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def api_user(django_user_model):
    from rest_framework.test import APIClient
    client = APIClient()

    username = 'user1'
    password = '123'
    user = django_user_model.objects.create_user(username=username, password=password, is_staff=False)

    user_token = Token.objects.create(user=user)
    client.force_login(user)
    client.credentials(HTTP_AUTHORIZATION=f'Token {user_token.key}')
    return client


@pytest.fixture
def api_admin(admin_user):
    from rest_framework.test import APIClient
    client = APIClient()

    token, _ = Token.objects.get_or_create(user=admin_user)
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    return client
