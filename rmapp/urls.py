from django.conf.urls import include, url
from django.contrib import admin
from rmapp import urls as rmapp_urls

urlpatterns = [
    url(r'^', include(rmapp_urls)),
    # url(r'^admin/', include(admin.site.urls)),
]

from rest_framework.routers import DefaultRouter

router = DefaultRouter()
# router.register(r'users', views.UserViewSet)
router.register(r'profiles', views.ProfileViewSet)
router.register(r'credentials', views.CredentialViewSet)
router.register(r'clusters', views.ClusterViewSet)
router.register(r'hosts', views.HostViewSet)
