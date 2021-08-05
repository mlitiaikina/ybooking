from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import serializers

from ybooking_app.helpers import generate_username
from ybooking_app.models import Profile, Timetable


class UserSerializer(serializers.ModelSerializer):
    patronymic = serializers.CharField(source='profile.patronymic')
    sex = serializers.IntegerField(source='profile.sex')
    birthday = serializers.DateField(source='profile.birthday')
    is_doctor = serializers.BooleanField(source='profile.is_doctor')

    _nested_fields = ['patronymic', 'sex', 'birthday', 'is_doctor']

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'patronymic', 'sex', 'birthday', 'is_doctor']

    @transaction.atomic()
    def create(self, validated_data):
        user_data = {
            'first_name': validated_data.pop('first_name'),
            'last_name': validated_data.pop('last_name')
        }
        user = User.objects.create_user(
            username=generate_username(**user_data),
            email=None,
            password=None,
            **user_data,
        )

        Profile.objects.create(user=user, **validated_data['profile'])
        return user

    def update(self, instance, validated_data):
        profile_data = {}
        for field in set(self._nested_fields) & set(validated_data.keys()):
            profile_data[field] = validated_data.pop(field)

        if profile_data:
            if hasattr(instance, 'profile'):
                instance.profile.update(**profile_data)
            else:
                Profile.objects.create(user=instance, **profile_data)

        return super().update(instance, validated_data)


class TimetableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Timetable
        fields = ('id', 'start', 'stop')


class StatisticsSerializer(serializers.ModelSerializer):
    day = serializers.DateField()
    count = serializers.IntegerField()

    class Meta:
        model = Timetable
        fields = ('day', 'count')
