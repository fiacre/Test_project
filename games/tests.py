from django.test import TestCase
import unittest
from django.test import Client
from django.test.client import RequestFactory
from django.contrib.auth.models import User
from datetime import datetime, timedelta
import pytz

from django.conf import settings
from django.utils.timezone import activate
activate(settings.TIME_ZONE)

# Create your tests here.
from games.models import Game, Vote, UserActivityLog
from games.views import login, games, main
from games.views import vote_index, top_votes, \
    game_vote, game_add

from games.forms import GameAddForm, GameVoteForm, VoteCountForm

class GamesTests(TestCase):
    fixtures = ['initial_data.json']
    ''' boilerplate test case '''
    def setUp(self):
        self.factory = RequestFactory()
        self.user= User.objects.get(username="alee")

    def test_login(self):
        request = self.factory.post('/login/', 
            {'username': 'alee', 
            'password': 'nat'})
        request.user = self.user
        response = game_vote(request)
        self.assertEqual(response.status_code, 200)
       
    def test_game_model(self):
        ''' test negative case too '''
        game = Game(title="A Game Title", user=self.user)
        self.assertIsInstance(game, Game)
        self.assertNotIsInstance(game, Vote)


    def test_game_model_2(self):
        ''' does model take created argument '''
        created_date = datetime.now(pytz.UTC) - timedelta(days=3)
        game = Game(title='Another Game Title', user=self.user, created=created_date)
        self.assertIsInstance(game, Game)

    def test_vote_model(self):
        ''' test negative case '''
        game = Game(title="Game Title 1234", user=self.user)
        game.save() # sends signal
        vote = Vote.objects.get(game=game)
        self.assertIsInstance(vote, Vote)
        self.assertNotIsInstance(vote, Game)

    def test_increment_vote(self):
        ''' make sure helper fuction works '''
        game = Game(title="My Special Test Game 1212", user=self.user)
        game.save()
        vote = Vote.objects.get(game=game)
        v = Vote.increment_count(game.title)
        self.assertEqual(v.count, 1)


    def test_ual(self):
        user=User.objects.get(username="jim")
        game = Game(title='Game in UAL', user=user)
        game.save()
        action = 'added',
        ual = UserActivityLog(game=game, user=user, action=action)
        ual.save()
        self.assertIsInstance(ual, UserActivityLog)

        UserActivityLog.log_user_action(user, action, game)
        last_acted = UserActivityLog.last_acted(user)

        self.assertIsInstance(last_acted, datetime)
        self.assertTrue(last_acted - datetime.now(pytz.UTC) < timedelta(seconds=1) )
        

    def test_game_add_form(self):
        user=User.objects.get(username="jim")
        form = GameAddForm(data={'title' : 'form game example', 
            'owned' : False,
            'user' : user })
        self.assertEqual(form.is_valid(), True)

    def test_add_game(self):
        ''' add a game with via POST '''
        user=User.objects.get(username="tim")
        request = self.factory.post('/games/add/', 
            { 'title' : 'a post test title', })
        request.user = user
        response = game_add(request)
        
        self.assertEqual(response.status_code, 200)


    def test_vote_twice_in_day(self):
        ''' POST two games within 30 minutes
            second POST should barf
        '''
        game_1 = Game.objects.get(title="AMF Bowling 2004")
        game_2 = Game.objects.get(title="Arctic Thunder")
        user=User.objects.get(username="tom")
        created_one = datetime.now(pytz.UTC)
        request = self.factory.post( '/games/vote/',
            { 'title' : game_1.id })
        request.user = user 
        response = game_vote(request)
        self.assertEqual(response.status_code, 200)


        request = self.factory.post( '/games/vote/',
            { 'title' : game_2.id } )
        request.user = user 
        response = game_vote(request)
        
        self.assertNotEqual(response.status_code, 200) 

    def test_add_added_title(self):
        user=User.objects.get(username="betty")
        request = self.factory.post( '/games/add/',
            { 'title' : 'a good test title' } )
        request.user = user
        response=game_add(request)
        self.assertEqual(response.status_code, 200)

        user=User.objects.get(username="sam")
        request = self.factory.post( '/games/add/',
            { 'title' : 'a good test title' } )
        request.user = user
        response=game_add(request)

        self.assertEqual(response.status_code, 200)

        vote = Vote.objects.get(game__title="a good test title")
        self.assertTrue(vote.count > 0 )
        
    def test_add_and_vote(self):
        user=User.objects.get(username="bob")
        request = self.factory.post( '/games/add/',
            { 'title' : "A Test Title 234" } )
        request.user = user
        response=game_add(request)
        #self.assertEqual(response.status_code, 200)
        
        request = self.factory.post( '/games/vote/',
            { 'title' : 1 })
        request.user = user
        response = game_vote(request)
        self.assertNotEqual(response.status_code, 200) 

    def test_vote_with_id(self):
        user=User.objects.get(username="jen")
        request = self.factory.get( '/games/vote/game_id/1/')
        request.user = user
        response = game_vote(request, game_id=1)
        self.assertEqual(response.status_code, 200) 

    def test_count_votes(self):
        ''' have joe, rich, john and mary
            vote on a game
        '''
        joe = User.objects.get(username="joe") 
        rich = User.objects.get(username="rich") 
        john = User.objects.get(username="john") 
        mary = User.objects.get(username="mary") 

        game = Game(id=20000, title="Test Count Votes", owned=False, user=joe)
        game.save()
        for user in ( rich, john, mary ):
            request = self.factory.post( '/games/vote/',
                { 'title' : 20000 })
            request.user = user
            response = game_vote(request, game_id=20000)
            self.assertEqual(response.status_code, 200) 
        v = Vote.objects.filter(game=game)[:1].get()
        self.assertEqual(v.count, 3)

