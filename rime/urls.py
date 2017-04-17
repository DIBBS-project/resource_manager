from django.conf.urls import include, url
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'clusters', views.ClusterViewSet)
# router.register(r'credentials', views.CredentialViewSet)
router.register(r'resources', views.ResourceViewSet, base_name='resources')

urlpatterns = [
    # url(r'^admin/', include(admin.site.urls)),
    url(r'^', include(router.urls)),
]
