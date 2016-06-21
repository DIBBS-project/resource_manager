from django.conf.urls import url, include
from demo import views


urlpatterns = [
    url(r'^demo/',  views.index, name='demo'),
    url(r'^_users/',  views.users),
    url(r'^$',  views.index, name='demo'),
    # url(r'^details/(?P<pk>[0-9]+)/$', views.show_details,  name='execution_details'),
]
