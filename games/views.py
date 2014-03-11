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
from django.db.models import Count
from django.contrib.auth.models import User
from games.models import Game, Vote
from games.models import UserActivityLog
from django.views.generic import DetailView, ListView
from games.forms import GameAddForm 
from games.forms import GameVoteForm 
from games.forms import VoteCountForm 


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

def _can_act(user):
    ''' has this user acted today
        check the activity log
    '''
    ual = UserActivityLog.last_acted(user)

    _log.debug("user %s activity log : %s " % (user, ual))

    if ual is None :
        return True
    if ual.day == datetime.now().day:
        return False
    elif datetime.now().isoweekday() > 5:
        ''' is it the weekend ? '''
        return False
    else:
        return True

def _count_votes():
    ''' aggregate votes
        based on a filter (if exists)
        return ordered dict
        of games and vote counts
    '''
    context = {}
    votes = Vote.objects.values('game').annotate(vcount=Count('game'))
    for vote in votes:
        game = Game.objects.get(pk=vote.get('game'))
        if game.owned == False:
            context[game.title] = vote.get('vcount')
    return OrderedDict(reversed(sorted(context.items(), key=lambda t: t[1])))
        

    
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
    added = _count_votes()
    games = Game.objects.filter(owned=True)
    no_votes = Game.objects.filter(owned=False).exclude(id__in=Vote.objects.all().values_list('game', flat=True))

    return render(request, 'games/games.html', {
        'games' : games,
        'added' : added,
        'no_votes' : no_votes
        })

def main(request):
    ''' render main.html -- links to 
        other views
        not winning any awards for design!
    '''
    return render(request, 'games/main.html')
    
def vote_index(request):
    """ votes view 
        show table of games and votes
    """
    ordered = _count_votes()
    return render(request, 'games/votes_list.html', {"context" : ordered })


def top_votes(request):
    """
        top votes this week
    """
    context = {}
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    votes = Vote.objects.filter(created__gte=monday).values('game').annotate(vcount=Count('game'))
    for vote in votes:
        game = Game.objects.get(pk=vote.get('game'))
        context[game.title] = vote.get('vcount')
    ordered = OrderedDict(reversed(sorted(context.items(), key=lambda t: t[1])))

    return render(request, "games/vote_count.html", {
        'context' : ordered, 
        })


class AllVotes(ListView):
    ''' example of geeric ListView 
        list al vote and related objects
    '''
    model = Vote
    context_object_name = 'votes'
    template = 'games/vote_list.html'
    queryset = Vote.objects.all().select_related('game', 'user').order_by('created')


@login_required
def my_votes(request):
    ''' see what I have added and voted for '''
    votes = Vote.objects.filter(user=request.user).select_related('game', 'user').order_by('-created')
    return render(request, 'games/vote_list.html', {"votes" : votes })

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
            #from title we get a Game 
            # if this raises an error, let it throw 500
            game = Game.objects.get(title=title)
            # see if this user has voted or added today
            if _can_act(request.user.username) == False:
                _log.debug("%s acted today" % request.user)
                response = _raise_error(reason="You Can Only Vote/Add once a day")
                return response
             
            # remember to get out and vote! 
            # get the count (times this user has voted for this game )
            num_votes= Vote.objects.filter(game=game).count()
            # update Vote with that count+1
            vote = Vote.objects.create(user=request.user, game=game, count=num_votes+1)
            vote.save()
            # make entry in user activity log
            UserActivityLog.log_user_action(request.user, "voted", game)
            #say thanks!
            return _say_thanks(request, "your vote for %s has been counted!" % title)
    elif game_id is not None:
        # if object does not exist, punt to 500 handler
        game = Game.objects.get(pk=game_id)
        if _can_act(request.user.username) == False:
            _log.debug("%s acted in the last day" % request.user)
            response = _raise_error(reason="You Can't Vote till tomorrow, sorry")
            return response
        else:
            vote = Vote.objects.create(user=request.user, game=game, count=1)
            vote.save()
            UserActivityLog.log_user_action(request.user, "voted", game)
            return _say_thanks(request, "your vote for %s has been counted!" % game.title)
    else:
        # if this is a GET, print form
        form = GameVoteForm()
    return render(request, 'games/vote.html', {
        'form': form,
    })


@login_required
def game_add(request):
    """ 
        logged in user adds a game here 
        can't add a game if it is owned
        can't add a game if user
            has voted or added  today
        if user x adds, then user y adds
            count as a vote
    """
    if request.method == 'POST':
        form = GameAddForm(request.POST)
        if form.is_valid():
            title = form.cleaned_data['title']
            # see if this game is already owned 
            # would like this to be fuzzy
            # case-insensitive for now
            game_obj = Game.objects.filter(title__iexact=title, owned=True)
            if game_obj:
                _log.error("%s is already owned" % title)
                return _raise_error("%s is already owned" % title)
            
            # see if this game has been added
            game_obj = Game.objects.filter(title__iexact=title, owned=False)
            if game_obj:
                #return _raise_error("already owned")
                # this counts as a vote
                if _can_act(request.user.username) == False:
                    _log.debug("%s acted in the last 24 hours" % request.user)
                    response = _raise_error(reason="You Can Only Vote/Add once a day")
                    return response
                game = Game.objects.filter(title__iexact=title)[:1].get()
                num_votes= Vote.objects.filter(user=request.user, game=game_obj).count()
                vote = Vote.objects.create(user=request.user, game=game, count=num_votes+1)
                vote.save()
                UserActivityLog.log_user_action( request.user, "voted", game )
                return _say_thanks(request, "You Voted for %s" % title)
                
            else:
                # need a User
                user_obj = User.objects.get(username=request.user)
                # check this user's activity log
                if _can_act(request.user) == False:
                    _log.debug("%s acted today" % request.user)
                    return _raise_error(reason="You Can Only Vote/Add once a day")
                    
                # if title wasn't matched above, we're safe
                # to create without throwing a db error
                obj = Game.objects.create(title=title, user=user_obj)
                try:
                    obj.full_clean()
                except ValidationError as e:
                    return _raise_error(str(e))
                obj.save()
                UserActivityLog.log_user_action( request.user, "added", obj )
                return _say_thanks(request, "%s has been saved" % title)
    else:
        form = GameAddForm()
    return render(request, 'games/add_game.html', {
        'form': form,
    })
    
