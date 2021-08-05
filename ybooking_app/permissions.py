from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsPatient(BasePermission):
    """
    The request is authenticated as a patient
    """

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'person') and
            request.user.person.is_patient
        )


class IsPatientOwner(IsPatient):

    def has_object_permission(self, request, view, obj):
        return bool(
            request.user and
            request.user.is_authenticated and
            obj.patient.user == request.user
        )