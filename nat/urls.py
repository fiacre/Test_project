from django.conf.urls import patterns, include, url

from games import urls
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

from nat.views import Login, Logout
from games.views import main
#from games import admin

urlpatterns = patterns('',
    url(r'^login/', Login.as_view(), name='login-view'),
    url(r'^logout/', Logout.as_view(), name='logout-view'),
    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'^games/', include('games.urls')),
    url(r'^$', main),
)
