from django.test import TestCase
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
        self.user = User.objects.create_user('jim', 'jim@localhost.com', 'nat')
        self.user1 = User.objects.create_user('kim', 'kim@localhost.com', 'nat')
        self.user2 = User.objects.create_user('joe', 'joe@localhost.com', 'nat')
        self.user3 = User.objects.create_user('koe', 'koe@localhost.com', 'nat')
        self.user4 = User.objects.create_user('sam', 'sam@localhost.com', 'nat')
        self.user5 = User.objects.create_user('tam', 'tam@localhost.com', 'nat')
        self.user6 = User.objects.create_user('bob', 'bob@localhost.com', 'nat')


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
        game = Game(title='Game in UAL', user=self.user)
        game.save()
        action = 'added',
        user = self.user
        ual = UserActivityLog(game=game, user=user, action=action)
        ual.save()
        self.assertIsInstance(ual, UserActivityLog)

        UserActivityLog.log_user_action(user, action, game)
        last_acted = UserActivityLog.last_acted(self.user)
        print last_acted 

        self.assertIsInstance(last_acted, datetime)
        self.assertTrue(last_acted - datetime.now(pytz.UTC) < timedelta(seconds=1) )
        

    def test_game_add_form(self):
        form = GameAddForm(data={'title' : 'form game example', 
            'owned' : False,
            'user' : self.user1 })
        self.assertEqual(form.is_valid(), True)

    def test_add_game(self):
        ''' add a game with via POST '''
        request = self.factory.post('/games/add/', 
            { 'title' : 'a test title', })
        request.user = self.user3
        response = game_add(request)
        
        self.assertEqual(response.status_code, 200)


    def test_vote_twice_in_day(self):
        ''' POST two games within 30 minutes
            second POST should barf
        '''
        created_one = datetime.now(pytz.UTC)
        request = self.factory.post( '/games/vote/',
            { 'title' : 'A Test Title 123' })
        request.user = self.user4 
        response = game_vote(request)
        self.assertEqual(response.status_code, 200)


        request = self.factory.post( '/games/vote/',
            { 'title' : 'Another Test Title 123' } )
        request.user = self.user4 
        response = game_vote(request)
        
        self.assertNotEqual(response.status_code, 200) 

    def test_add_owned_title(self):
        request = self.factory.post( '/games/add/',
            { 'title' : 'a good test title', 'owned' : True } )
        request.user = self.user
        response=game_add(request)
        self.assertEqual(response.status_code, 200)

        request = self.factory.post( '/games/add/',
            { 'title' : 'a good test title' } )
        request.user = self.user1
        response=game_add(request)
        self.assertNotEqual(response.status_code, 200)
        
    def test_add_and_vote(self):
        request = self.factory.post( '/games/add/',
            { 'title' : "A Test Title 234" } )
        request.user = self.user5
        response=game_add(request)
        #self.assertEqual(response.status_code, 200)
        
        request = self.factory.post( '/games/vote/',
            { 'title' : 'another random test title' })
        request.user = self.user5
        response = game_vote(request)
        self.assertNotEqual(response.status_code, 200) 




