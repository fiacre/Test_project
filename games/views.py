""" views for Game and Vote models """
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
from games.forms import GameAddForm 
from games.forms import GameVoteForm 
from games.forms import VoteCountForm 

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
    if ual and ual.day == datetime.now(pytz.UTC).day:
        return False
    elif datetime.now(pytz.UTC).isoweekday > 5:
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

    return render(request, 'games/games.html', {
        'games' : games,
        'added' : added
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


# methods below require a logged in user 
# This could be more DRY
@login_required
def my_votes(request):
    ''' see what I have added and voted for '''
    pass

@login_required
def game_vote(request, game_id = None):
    """ logged in user votes for a game here """
    print "game_vote : user : %s" % request.user.username
    if request.method == 'POST':
        form = GameVoteForm(request.POST)
        if form.is_valid():
            title = form.cleaned_data['games']
            #from title we get a Game 
            game = Game.objects.get(title=title)
            # see if this user has voted or added today
            if _can_act(request.user.username) == False:
                print "%s acted in the last 24 hours" % request.user
                return _raise_error(reason="You Can Only Vote/Add once a day")
             
            # remember to get out and vote! 
            # get the count (times this user has voted for this game )
            num_votes= Vote.objects.filter(user=request.user, game=game).count()
            # update Vote with that count+1
            vote = Vote.objects.create(user=request.user, game=game, count=num_votes+1)
            try:
                vote.full_clean()
            except ValidationError as e:
                return _raise_error(str(e))
            vote.save()
            # make entry in user activity log
            UserActivityLog.log_user_action(request.user, "voted", game)
            #say thanks!
            return _say_thanks(request, "your vote for %s has been counted!" % title)
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
            has voted or added in 24 hrs
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
                return _raise_error("%s is already owned" % title)
            
            # see if this game has been added
            game_obj = Game.objects.filter(title__iexact=title, owned=False)
            if game_obj:
                return _raise_error("already owned")
                
            else:
                # need a User
                user_obj = User.objects.get(username=request.user)
                # check this user's activity log
                if _can_act(request.user) == False:
                    print "%s acted today" % request.user
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
    
