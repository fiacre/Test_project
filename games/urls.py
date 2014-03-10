""" UrlConf file """
from django.conf import settings
from django.conf.urls import patterns, url

from games import views

urlpatterns = patterns('',
    url(r'^games/$', views.games),
    url(r'^main/$', views.main),
    url(r'^vote_index/$', views.vote_index),
    url(r'^vote/$', views.game_vote),
    url(r'^vote/game_id/(?P<game_id>\d+)/$', views.game_vote),
    url(r'^top_votes/$', views.top_votes),
    url(r'^add/$', views.game_add),
)
