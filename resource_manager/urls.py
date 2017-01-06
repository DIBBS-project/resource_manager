from django.conf.urls import include, url
from django.contrib import admin
from rmapp import views
from rest_framework.routers import DefaultRouter
import rest_framework.authtoken.views

router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'profiles', views.ProfileViewSet)
router.register(r'credentials', views.CredentialViewSet)
router.register(r'clusters', views.ClusterViewSet)
router.register(r'hosts', views.HostViewSet)

urlpatterns = [
    url(r'^', include(router.urls)),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^index/',  views.index, name='index'),
    url(r'^$',  views.index, name='index'),

    # RSA
    url(r'^rsa_public_key/(?P<user_id>[0-9]+)/$', views.rsa_public_key),

    # Credentials
    url(r'^credentials/user/(?P<user_id>[0-9]+)/$', views.credentials_for_user),

    # Demo
    # url(r'^demo/', include('demo.urls')),
    # url(r'^get_certificate/(?P<pk>[0-9]+)/$', views.get_certificate, name="get_certificate"),

    # Allows to get a token by sending credentials
    url(r'^api-token-auth/', rest_framework.authtoken.views.obtain_auth_token),
]
