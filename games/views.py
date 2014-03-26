import logging
from datetime import datetime, timedelta, date
import pytz

from collections import OrderedDict
from django.http import Http404, HttpResponseServerError
from django.shortcuts import render_to_response, HttpResponse
from django.shortcuts import render
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from games.models import Game, Vote
from games.models import UserActivityLog
from django.views.generic import DetailView, ListView
from games.forms import GameAddForm 
from games.forms import GameVoteForm 
from games.forms import VoteCountForm 
from games.helpers import _can_act, _count_votes


from django.conf import settings
from django.utils.timezone import activate
activate(settings.TIME_ZONE)

_log = logging.getLogger(__name__)

# helper methods

def _raise_error(reason=''):
    ''' return status_code 500 '''
    response = HttpResponseServerError(reason)
    return response

def _say_thanks(request, msg):
    ''' be polite '''
    return render(request, "games/thanks.html", {
        "msg" : msg })

# views 
def login(request):
    ''' login view for adding or voting
        users Django standard user authentication
    '''
    username = request.POST['username']
    password = request.POST['password']
    user = authenticate(username=username, password=password)
    if user is not None:
        if user.is_active:
            login(request, user)
            return redirect('/games/main')
        else:
            raise Http404
            
def games(request):
    """
        games we own 
    """
    voted = Vote.objects.filter(count__gt=0).select_related('game')
    owned = Game.objects.filter(owned=True)
    no_votes = Game.objects.filter(owned=False).exclude(
        id__in=Vote.objects.filter(count__gt=0).values_list('game', flat=True)
        )

    return render(request, 'games/games.html', {
        'owned' : owned,
        'voted' : voted,
        'no_votes' : no_votes
        })

def main(request):
    ''' render main.html -- links to 
        other views
        not winning any awards for design!
    '''
    return render(request, 'games/main.html')
    
def vote_index(request):
    ''' votes view 
        show table of games and votes
    '''
    context = {}
    d = date.today().weekday()
    ''' only want games voted on since this Monday '''
    votes = Vote.objects.filter(
        created__gte=date.today()-timedelta(days=d), count__gt=0).select_related('game')
    _log.debug(votes)
    for vote in votes:
        #game = Game.objects.get(pk=vote.game.id)
        if vote.game.owned == False:
            context[vote.game.title] = vote.count
    context = OrderedDict(reversed(sorted(context.items(), key=lambda t: t[1])))
    return render(request, 'games/votes_list.html', {"context" : context })


def top_votes(request):
    """
        top votes this week
    """
    context = {}
    today = date.today()
    ''' figure out when the most recent Monday was '''
    monday = today - timedelta(days=today.weekday())
    votes = Vote.objects.filter(created__gte=monday)
    _log.debug(votes)
    for vote in votes:
        game = Game.objects.get(pk=vote.game.id)
        context[game.title] = vote.count
    ''' keep order by num votes '''
    ordered = OrderedDict(reversed(sorted(context.items(), key=lambda t: t[1])))

    return render(request, "games/vote_count.html", {
        'context' : ordered, 
        })


class AllVotes(ListView):
    ''' example of generic ListView 
        list all user actions and related objects
    '''
    model = Vote
    context_object_name = 'activity'

    queryset = UserActivityLog.objects.filter(
        action='voted').select_related(
        'game', 'user').order_by('created')


@login_required
def my_votes(request):
    ''' see what I have added and voted for '''
    actions = UserActivityLog.objects.filter(
        user=request.user, action='voted').select_related(
            'game', 'user').order_by('-created')
    return render(request, 'games/vote_list.html', {"actions" : actions })

# methods below require a logged in user 
# This definately could be more DRY ... just a first pass
@login_required
def game_vote(request, game_id=''):
    """ logged in user votes for a game here """
    _log.debug( "game_vote : user : %s" % request.user.username )

    if request.method == 'POST':
        form = GameVoteForm(request.POST)
        if form.is_valid():
            title = form.cleaned_data['title']
            _log.debug("game_vote ; title is : %s " % title)
            # see if this user has voted or added today
            if _can_act(request.user.username) == False:
                _log.debug("%s acted today" % request.user)
                response = _raise_error(reason="You Can Only Vote/Add once a day")
                return response
             
            # remember to get out and vote! 
            Vote.increment_count(title)
            # make entry in user activity log
            UserActivityLog.log_user_action(request.user, "voted", title)
            #say thanks!
            return _say_thanks(request, "your vote for %s has been counted!" % title)

    elif request.method == 'GET' and  game_id:
        # if object does not exist, punt to 500 handler
        game = Game.objects.get(pk=game_id)
        if _can_act(request.user.username) == False:
            _log.debug("%s acted in the last day" % request.user)
            response = _raise_error(reason="You Can't Vote till tomorrow, sorry")
            return response
        else:
            # user can vote
            Vote.increment_count(game.title)
            # log user action
            UserActivityLog.log_user_action(request.user, "voted", game.title)
            return _say_thanks(request, "your vote for %s has been counted!" % game.title)
    else:
        # if this is a GET, print form
        form = GameVoteForm()
    return render(request, 'games/vote.html', {
        'form': form,
    })


@login_required
def game_add(request):
    ''' 
        logged in user adds a game here 
        can't add a game if it is owned
        can't add a game if user
            has voted or added  today
        if user x adds, then user y adds
            count as a vote
        
        TODO: is owned, is_added in model?
    '''
    if request.method == 'POST':
        form = GameAddForm(request.POST)
        if form.is_valid():
            title = form.cleaned_data['title']
            # clean title
            tite= title.strip()
            if title == '':
                return _raise_error("No title")
            # see if this game is already owned 
            qs = Game.objects.filter(title__icontains=title, owned=True)
            if qs:
                _log.error("%s is already owned" % title)
                return _raise_error("%s is already owned" % title)
            
            # see if this game has been added 
            qs = Game.objects.filter(title__icontains=title, owned=False)
            if qs:
                # test if user has added or voted today
                if _can_act(request.user.username) == False:
                    _log.debug("%s acted in the last day" % request.user)
                    response = _raise_error(reason="You Can Only Vote/Add once a day")
                    return response
                # insert since this title exists
                # this is a vote
                Vote.increment_count(title)
                UserActivityLog.log_user_action( request.user, "voted", title )
                return _say_thanks(request, "You Voted for %s" % title)
                
            else:
                # need a User
                user_obj = User.objects.get(username=request.user)
                # check this user's activity log
                if _can_act(request.user) == False:
                    _log.debug("%s acted today" % request.user)
                    return _raise_error(reason="You Can Only Vote/Add once a day")
                    
                try:
                    obj = Game.objects.create(title=title, user=user_obj)
                except IntegrityError:
                    _raise_error("%s exists" % title)
                try:
                    obj.full_clean()
                except ValidationError as e:
                    return _raise_error(str(e))
                obj.save()
                UserActivityLog.log_user_action( request.user, "added", obj.title )
                return _say_thanks(request, "%s has been saved" % title)
    else:
        form = GameAddForm()
    return render(request, 'games/add_game.html', {
        'form': form,
    })
    

