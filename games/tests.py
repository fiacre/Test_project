#from django.test import TestCase
from django.test import TestCase

import unittest
from django.test import Client
from django.test.client import RequestFactory
from django.contrib.auth.models import User
from datetime import datetime, timedelta, date
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

class MockDateTime(datetime):
    @classmethod
    def monday_noon(cls):
        d = date.today().weekday()
        monday_date = date.today()-timedelta(days=d)
        return cls(monday_date.year, 
            monday_date.month, 
            monday_date.day, 
            12, 
            tzinfo= pytz.timezone("US/Central"))

class GamesTests(TestCase):
    fixtures = ['games/fixtures/users.json', 'games/fixtures/games.json']
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
        created_date = datetime.now(pytz.timezone(settings.TIME_ZONE)) - timedelta(days=3)
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
        #self.assertTrue(last_acted - datetime.now(pytz.UTC) < timedelta(seconds=1) )
        # don't care what UTC time is
        self.assertTrue(last_acted - datetime.now(pytz.timezone(settings.TIME_ZONE)) < timedelta(seconds=1) )
        

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

        game = Game(id=45698, title="xyz Test Count Votes", owned=False, user=joe)
        game.save()
        for user in ( rich, john, mary ):
            request = self.factory.post( '/games/vote/',
                { 'title' : 45698 })
            request.user = user
            response = game_vote(request, game_id=45698)
            self.assertEqual(response.status_code, 200) 
        v = Vote.objects.filter(game=game)[:1].get()
        print v
        self.assertEqual(v.count, 3)

    def add_existing_title(self):
        user1= User.objects.create_user('uuu', 'uuu@foo.com', 'foooo')
        user2 = User.objects.create_user('vvv', 'vvv@foo.com', 'boooo') 
        title = "  awesome magic game of foo   "
        
        request = self.factory.post('/games/add/', 
            { 'title' : title, })
        request.user = user1
        response = game_add(request)
        
        self.assertEqual(response.status_code, 200)

        request = self.factory.post('/games/add/', 
            { 'title' : title, })
        request.user = user2
        response = game_add(request)
        
        self.assertNotEqual(response.status_code, 200)

    @unittest.skip("not working yet")
    def test_vote_on_weekend(self):
        '''
            mock the datetime and vote
        '''
        monday_noon = MockDateTime.monday_noon()
        # add 5 days:
        vote_date = monday_noon + timedelta(days=5)
        # now vote
        tob = User.objects.get(username="tob") 
        game = Game.objects.get(title="AMF Bowling 2004")
        request = self.factory.post( '/games/vote/',
            { 'title' : game.id })
        request.user = tob 
        response = game_vote(request)
        self.assertNotEqual(response.status_code, 200)

    

