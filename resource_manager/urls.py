from django.conf.urls import include, url
from django.contrib import admin
from rmapp import urls as rmapp_urls

urlpatterns = [
    url(r'^', include(rmapp_urls)),
    # url(r'^admin/', include(admin.site.urls)),
]
