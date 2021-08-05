from django.urls import path, include
from rest_framework_nested import routers
from rest_framework.authtoken.views import obtain_auth_token

from ybooking_app import views

router = routers.DefaultRouter()
router.register(r'persons', views.UserViewSet,  basename='persons')
router.register(r'blocked-persons', views.BlockedUserViewSet, basename='blocked-persons')
router.register(r'statistics', views.StatisticsViewSet, basename='statistics')

domains_router = routers.NestedSimpleRouter(router, r'persons', lookup='person')
domains_router.register(r'schedule', views.TimetableViewSet, basename='schedule')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(domains_router.urls)),
    path('api-token-auth/', obtain_auth_token, name='api_token_auth')
]
