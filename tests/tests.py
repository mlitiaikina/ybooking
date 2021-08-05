import json

import pytest
from django.urls import reverse
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)


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
        'last_name': 'last_name-by-admin',
        'patronymic': 'patrinymic',
        'sex': 1,
        'is_doctor': True,
        'birthday': '2020-12-12',
    }
    resp = api_admin.post(url, user_params)
    assert resp.status_code == HTTP_201_CREATED


@pytest.mark.django_db
def test_create_person_user(api_user):
    url = reverse('persons-list')
    user_params = {
        'first_name': 'first_name',
        'last_name': 'last_name-by-user',
        'patronymic': 'patrinymic',
        'sex': 1,
        'is_doctor': True,
        'birthday': '2020-12-12',
    }
    resp = api_user.post(url, user_params)
    assert resp.status_code == HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_update_person(api_admin, api_user, doctor_obj):
    detail_url = reverse('persons-detail', args=(doctor_obj.id,))
    update_resp = api_admin.patch(
        detail_url,
        {'first_name': 'first_name-by-admin'},
    )
    assert update_resp.status_code == HTTP_200_OK
    assert update_resp.data['first_name'] == 'first_name-by-admin'

    update_resp = api_user.patch(
        detail_url,
        {'first_name': 'first_name-by-user'},
    )
    assert update_resp.status_code == HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_block_person(api_admin, api_user, doctor_obj):
    detail_url = reverse('persons-detail', args=(doctor_obj.id,))

    delete_resp = api_user.delete(detail_url)
    assert delete_resp.status_code == HTTP_403_FORBIDDEN

    # block person
    delete_resp = api_admin.delete(detail_url)
    assert delete_resp.status_code == HTTP_204_NO_CONTENT

    # revert blocking
    blocked_url = reverse('blocked-persons-detail', args=(doctor_obj.id,))
    blocked_resp = api_admin.delete(blocked_url)
    assert blocked_resp.status_code == HTTP_204_NO_CONTENT


@pytest.mark.django_db
def test_sessions_user(api_user, doctor_obj):
    list_url = reverse('schedule-list', kwargs={'person_pk': doctor_obj.profile.id})

    get_resp = api_user.get(list_url)
    assert get_resp.status_code == HTTP_200_OK
    assert get_resp.data['count'] == 2

    post_resp = api_user.post(list_url, {})
    assert post_resp.status_code == HTTP_403_FORBIDDEN

    data = json.loads(get_resp.content.decode())
    detail_url = reverse(
        'schedule-detail',
        kwargs={'person_pk': doctor_obj.profile.id, 'pk': data['results'][0]['id']}
    )

    get_resp = api_user.get(detail_url)
    assert get_resp.status_code == HTTP_200_OK

    resp = api_user.patch(detail_url, {})
    assert resp.status_code == HTTP_403_FORBIDDEN

    resp = api_user.delete(detail_url)
    assert resp.status_code == HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_sessions_patient(api_patient, doctor_obj):
    doctor_slots_list_url = reverse('schedule-list', kwargs={'person_pk': doctor_obj.profile.id})

    get_resp = api_patient.get(doctor_slots_list_url)
    assert get_resp.status_code == HTTP_200_OK
    assert get_resp.data['count'] == 2

    data = json.loads(get_resp.content.decode())
    doctor_free_slots = data['results']

    post_resp = api_patient.post(doctor_slots_list_url, {})
    assert post_resp.status_code == HTTP_403_FORBIDDEN

    doctor_slot_detail_url = reverse(
        'schedule-detail',
        kwargs={
            'person_pk': doctor_obj.profile.id,
            'pk': doctor_free_slots[0]['id'],
        }
    )

    get_resp = api_patient.get(doctor_slot_detail_url)
    assert get_resp.status_code == HTTP_200_OK

    # book timeslot by patient
    resp = api_patient.patch(doctor_slot_detail_url, {})
    assert resp.status_code == HTTP_200_OK

    # try to book it again
    resp = api_patient.patch(doctor_slot_detail_url, {})
    assert resp.status_code == HTTP_404_NOT_FOUND

    # slot was removed from free doctor slots, so now doctor has 1 free slot
    get_resp = api_patient.get(doctor_slots_list_url)
    assert get_resp.status_code == HTTP_200_OK
    assert get_resp.data['count'] == 1

    patient_slots_list_url = reverse(
        'schedule-list',
        kwargs={'person_pk': api_patient.session['_auth_user_id']},
    )

    # patient has 1 booked timeslot
    get_resp = api_patient.get(patient_slots_list_url)
    assert get_resp.status_code == HTTP_200_OK
    assert get_resp.data['count'] == 1

    data = json.loads(get_resp.content.decode())
    patient_slots = data['results']

    patient_slot_detail_url = reverse(
        'schedule-detail',
        kwargs={
            'person_pk': api_patient.session['_auth_user_id'],
            'pk': patient_slots[0]['id'],
        }
    )

    # cancel booking
    resp = api_patient.delete(patient_slot_detail_url)
    assert resp.status_code == HTTP_200_OK

    # now patient has no booked timeslot
    get_resp = api_patient.get(patient_slots_list_url)
    assert get_resp.status_code == HTTP_200_OK
    assert get_resp.data['count'] == 0

    # and doctor again has 2 slots
    get_resp = api_patient.get(doctor_slots_list_url)
    assert get_resp.status_code == HTTP_200_OK
    assert get_resp.data['count'] == 2
