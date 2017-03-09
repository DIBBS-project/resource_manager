from django.conf.urls import include, url
from django.contrib import admin
from rest_framework.routers import DefaultRouter

from . import views


router = DefaultRouter()
router.register(r'profiles', views.ProfileViewSet)
router.register(r'credentials', views.CredentialViewSet)
router.register(r'clusters', views.ClusterViewSet)
router.register(r'hosts', views.HostViewSet)

urlpatterns = [
    url(r'^', include(router.urls)),
]
