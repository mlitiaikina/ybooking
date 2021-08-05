import datetime

import pytest
from django.urls import reverse
from rest_framework.status import HTTP_401_UNAUTHORIZED, HTTP_404_NOT_FOUND, HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_person_list_client(api_client):
    url = reverse('persons-list')
    resp = api_client.get(url)
    assert resp.status_code == HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_person_detail_client(api_client):
    url = reverse('persons-detail', args=(id,))
    resp = api_client.get(url)
    assert resp.status_code == HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_person_detail_user(api_user):
    url = reverse('persons-detail', args=(id,))
    resp = api_user.get(url)
    assert resp.status_code == HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_person_detail_admin(api_admin):
    url = reverse('persons-detail', args=(id,))
    resp = api_admin.get(url)
    assert resp.status_code == HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_create_person_admin(api_admin):
    url = reverse('persons-list')
    user_params = {
        'first_name': 'first_name',
        'last_name': 'last_name',
        'patrinymic': 'patrinymic',
        'sex': 1,
        'is_doctor': True,
        'birthday': datetime.datetime(2020, 12, 12),
    }
    resp = api_admin.post(url, user_params)
    assert resp.status_code == HTTP_400_BAD_REQUEST