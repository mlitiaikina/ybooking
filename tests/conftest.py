from datetime import timedelta, datetime

import pytest
from rest_framework.authtoken.models import Token

from ybooking_app.models import Profile, Timetable
from ybooking_app.serializers import UserSerializer


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
    user = django_user_model.objects.create_user(
        username=username,
        password=password,
        is_staff=False,
    )

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


@pytest.fixture
def doctor_obj():
    serializer = UserSerializer(data={
        'first_name': 'doctor_firts_name',
        'last_name': 'doctor_last_name',
        'patronymic': 'doctor_patrinymic',
        'sex': Profile.Sex.MAN,
        'is_doctor': True,
        'birthday': '1940-12-12',
    })
    serializer.is_valid(raise_exception=True)
    doctor = serializer.save()

    # create several timeslots for doctor
    session_duration = 30
    sessions_start_time = [
        datetime.now() - timedelta(days=1),
        datetime.now() + timedelta(hours=12),
        datetime.now() + timedelta(days=1),
    ]

    for start in sessions_start_time:
        Timetable.objects.create(
            doctor=doctor.profile,
            start=start,
            stop=start + timedelta(minutes=session_duration),
        )

    return doctor


@pytest.fixture
def api_patient(django_user_model):
    from rest_framework.test import APIClient
    client = APIClient()

    username = 'user1'
    password = '123'
    user = django_user_model.objects.create_user(
        username=username,
        password=password,
        is_staff=False,
    )

    Profile.objects.create(
        user=user,
        **{
            'patronymic': 'doctor_patrinymic',
            'sex': Profile.Sex.WOMAN,
            'is_doctor': False,
            'birthday': '1999-02-02',
        }
    )

    user_token = Token.objects.create(user=user)
    client.force_login(user)
    client.credentials(HTTP_AUTHORIZATION=f'Token {user_token.key}')

    return client