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
    ''' boilerplate test case '''
    def setUp(self):
        self.factory = RequestFactory()
        # create some users 
        self.user = User.objects.create_user('jim', 'jim@localhost.com', 'nat')
        self.user1 = User.objects.create_user('kim', 'kim@localhost.com', 'nat')
        self.user2 = User.objects.create_user('joe', 'joe@localhost.com', 'nat')
        self.user3 = User.objects.create_user('koe', 'koe@localhost.com', 'nat')
        self.user4 = User.objects.create_user('sam', 'sam@localhost.com', 'nat')
        self.user5 = User.objects.create_user('tam', 'tam@localhost.com', 'nat')
        self.user6 = User.objects.create_user('bob', 'bob@localhost.com', 'nat')
        self.user7 = User.objects.create_user('rob', 'rob@localhost.com', 'nat')
        self.user8 = User.objects.create_user('sob', 'sob@localhost.com', 'nat')
        self.user9 = User.objects.create_user('tob', 'tob@localhost.com', 'nat')
        #create some games
        request = self.factory.post( '/games/add/',
            { 'title' : 'a good test title 123' } )
        request.user = self.user
        response=game_add(request)
        self.assertEqual(response.status_code, 200)
        request = self.factory.post( '/games/add/',
            { 'title' : 'a good test title 234' } )
        request.user = self.user1
        response=game_add(request)
        self.assertEqual(response.status_code, 200)
        # now user and user1 CAN'T add or vote



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
        game = Game(title="A Third Game Title", user=self.user)
        vote = Vote(game=game, user=self.user)       
        self.assertIsInstance(vote, Vote)
        self.assertNotIsInstance(vote, Game)

    def test_ual(self):
        game = Game(title='Game in UAL', user=self.user3)
        game.save()
        action = 'added',
        user = self.user3
        ual = UserActivityLog(game=game, user=user, action=action)
        ual.save()
        self.assertIsInstance(ual, UserActivityLog)

        UserActivityLog.log_user_action(user, action, game)
        last_acted = UserActivityLog.last_acted(self.user3)
        print last_acted 

        self.assertIsInstance(last_acted, datetime)
        self.assertTrue(last_acted - datetime.now(pytz.UTC) < timedelta(seconds=1) )
        

    def test_game_add_form(self):
        form = GameAddForm(data={'title' : 'form game example', 
            'owned' : False,
            'user' : self.user4 })
        self.assertEqual(form.is_valid(), True)

    def test_add_game(self):
        ''' add a game with via POST '''
        request = self.factory.post('/games/add/', 
            { 'title' : 'a test title', })
        request.user = self.user5
        response = game_add(request)
        
        self.assertEqual(response.status_code, 200)


    def test_vote_twice_in_day(self):
        ''' POST two games within 30 minutes
            second POST should barf
        '''
        created_one = datetime.now(pytz.UTC)
        request = self.factory.post( '/games/vote/',
            { 'title' : 1 })
        request.user = self.user6 
        response = game_vote(request)
        self.assertEqual(response.status_code, 200)


        request = self.factory.post( '/games/vote/',
            { 'title' : 2 } )
        request.user = self.user6 
        response = game_vote(request)
        
        self.assertNotEqual(response.status_code, 200) 

    def test_add_added_title(self):
        request = self.factory.post( '/games/add/',
            { 'title' : 'a good test title' } )
        request.user = self.user7
        response=game_add(request)
        self.assertEqual(response.status_code, 200)

        request = self.factory.post( '/games/add/',
            { 'title' : 'a good test title' } )
        request.user = self.user7
        response=game_add(request)

        print response.status_code


        self.assertNotEqual(response.status_code, 200)
        
    def test_add_and_vote(self):
        request = self.factory.post( '/games/add/',
            { 'title' : "A Test Title 234" } )
        request.user = self.user8
        response=game_add(request)
        #self.assertEqual(response.status_code, 200)
        
        request = self.factory.post( '/games/vote/',
            { 'title' : 1 })
        request.user = self.user8
        response = game_vote(request)
        self.assertNotEqual(response.status_code, 200) 

    def test_vote_with_id(self):
        request = self.factory.get( '/games/vote/game_id/1/')
        request.user = self.user9
        response = game_vote(request, game_id=1)
        self.assertEqual(response.status_code, 200) 
        


