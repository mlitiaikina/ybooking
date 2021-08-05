from django.contrib.auth.models import User
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework import viewsets
from rest_framework.response import Response

from ybooking_app.models import Profile, Timetable
from ybooking_app.permissions import IsPatient, IsPatientOwner
from ybooking_app.serializers import UserSerializer, TimetableSerializer, StatisticsSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserSerializer

    permission_classes_by_action = {
        'list': [permissions.IsAuthenticated],
        'retrieve': [permissions.IsAuthenticated],
        'create': [permissions.IsAdminUser],
        'destroy': [permissions.IsAdminUser],
        'update': [permissions.IsAdminUser],
        'partial_update': [permissions.IsAdminUser],
    }

    def get_permissions(self):
        try:
            return [permission() for permission in self.permission_classes_by_action[self.action]]
        except KeyError:
            return [permission() for permission in self.permission_classes]

    def perform_destroy(self, instance):
        """ Deactivate user """
        instance.is_active = False
        instance.save()


class BlockedUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(is_active=False)
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]

    def perform_destroy(self, instance):
        """ Activate user back """
        instance.is_active = True
        instance.save()


class TimetableViewSet(viewsets.ModelViewSet):
    queryset = Timetable.objects.all()
    serializer_class = TimetableSerializer
    permission_classes = [IsPatient]

    permission_classes_by_action = {
        'list': [permissions.IsAuthenticated],
        'retrieve': [permissions.IsAuthenticated],
        'create': [permissions.IsAdminUser],
        'destroy': [IsPatientOwner],
        'update': [permissions.IsAdminUser],
        'partial_update': [IsPatient],
    }

    def get_permissions(self):
        try:
            return [permission() for permission in self.permission_classes_by_action[self.action]]
        except KeyError:
            return [permission() for permission in self.permission_classes]

    def get_queryset(self):
        try:
            person = Profile.objects.get(
                user__is_active=True,
                pk=self.kwargs['person_pk'],
            )
        except Profile.DoesNotExist:
            raise ValueError(f'There is no person with id={self.kwargs["persons_pk"]}')

        return Timetable.objects.filter(**self._get_filter_by_person(person))

    def destroy(self, request, *args, **kwargs):
        """ Clear patient field in session """
        timetable = self.get_object()

        if self.request.user.id != timetable.patient_id and not self.request.user.is_superuser:
            return Response(
                status=status.HTTP_403_FORBIDDEN,
                data='Patient can see modify only his/her own schedule.',
            )

        timetable.patient_id = None
        timetable.save()
        return Response(data='Session canceled')

    def partial_update(self, request, *args, **kwargs):
        """ Fill patient field in session """
        instance = self.get_object()
        if instance.patient is not None:
            return Response(status=status.HTTP_423_LOCKED, data='Session already assigned.')

        return super().partial_update(request, args, kwargs)

    def perform_update(self, serializer):
        serializer.instance.patient_id = self.request.user.id
        super().perform_update(serializer)

    def _get_filter_by_person(self, person):
        filters = {'start__gt': timezone.now()}
        if person.is_doctor:
            filters.update({
                'doctor_id': person.id,
                'patient_id__isnull': True,
            })
        elif person.is_patient:

            if person.user_id != self.request.user.id and not self.request.user.is_superuser:
                raise PermissionError('Access denied! Patient can see only own schedule.')

            filters.update({'patient_id': person.id})
        else:
            raise NotImplementedError('Unknown person group')

        return filters


class StatisticsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Timetable.objects.annotate(
        day=TruncDate('start'),
    ).order_by('day').values('day').annotate(
        count=Count('day'),
    )
    serializer_class = StatisticsSerializer
    permission_classes = [permissions.IsAuthenticated]
