""" UrlConf file """
from django.conf import settings
from django.conf.urls import patterns, url

from games import views

urlpatterns = patterns('',
    url(r'^games/$', views.games, name="games"),
    url(r'^main/$', views.main, name="main"),
    url(r'^vote_index/$', views.vote_index, name="vote_index"),
    url(r'^vote/$', views.game_vote, name="vote"),
    url(r'^vote/game_id/(?P<game_id>\d+)/$', views.game_vote),
    url(r'^top_votes/$', views.top_votes, name="top_votes"),
    url(r'^all_votes/$', views.AllVotes.as_view()),
    url(r'^my_votes/$', views.my_votes, name="my_votes"),
    url(r'^add/$', views.game_add, name="game_add"),
)
handler500 = 'views.games._error_view'
