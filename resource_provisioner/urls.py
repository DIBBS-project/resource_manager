from django.conf.urls import patterns, include, url
from django.contrib import admin
from rpapp import views
# from rest_framework_jwt.views import obtain_jwt_token
import demo.views as demo_views

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'webservice.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^index/',  views.index, name='index'),
    url(r'^$',  views.index, name='index'),

    # Users
    url(r'^register_new_user/?$', views.register_new_user),
    url(r'^generate_new_token/?$', views.generate_new_token),

    # UserProfiles
    url(r'^users/?$', views.user_list),
    url(r'^users/(?P<pk>[0-9]+)/$', views.user_detail),

    # Clusters
    url(r'^clusters/?$', views.cluster_list),
    url(r'^clusters/(?P<pk>[0-9]+)/$', views.cluster_detail),

    # Hosts
    url(r'^hosts/?$', views.host_list),
    url(r'^hosts/(?P<pk>[0-9]+)/$', views.host_detail),

    # Token
    # url(r'^api-token-auth/', obtain_jwt_token),

    # Demo
    url(r'^demo/', include('demo.urls')),
    url(r'^get_certificate/(?P<pk>[0-9]+)/$', views.get_certificate, name="get_certificate"),

)
