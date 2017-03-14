from django.conf.urls import include, url
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
# router.register(r'clusters', views.ClustersViewSet)
router.register(r'credentials', views.CredentialViewSet)
router.register(r'resources', views.ResourceViewSet)

urlpatterns = [
    # url(r'^admin/', include(admin.site.urls)),
    url(r'^', include(router.urls)),
]
