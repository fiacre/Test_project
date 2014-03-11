"""
    Game and Vote Models
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User as Auth_User
import datetime 
import pytz
 
from django.conf import settings
from django.utils.timezone import activate
activate(settings.TIME_ZONE)
 
class Game(models.Model):
    '''
        Game class
        title: xbox game name
        owned: is title owned by nerdery
        gamer ; user the added game
        created: datetime of object

        class method
            _is_owned(Game, @title) : 
                return True if title is in db
    '''     
       
    title = models.CharField(max_length=255, unique=True)
    owned = models.BooleanField(default=False)
    user = models.ForeignKey(Auth_User)
    created = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.title

    class Meta:
        """ prefer simple db table name """
        db_table = 'games'
        ordering = ["-created"]


    @classmethod
    def is_added(cls, title):
        """ case insentive search for title """
        obj = cls.objects.filter(title__iexact=title)
        if obj:
            return True
        else:
            return False

class Vote(models.Model):
    '''
        Vote class
        game: reference to associated Game object 
        user: reference to associated django.models.User object
        count: votes per user per game
        created: datetime vote was created
        method vote: increment vote count
    '''
    game = models.ForeignKey(Game)
    user = models.ForeignKey(Auth_User)
    count = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now=True)

    class Meta:
        """ prefer simple table name in db """
        db_table = 'votes'

    def __unicode__(self):
        return "%s, %s, %s" % ( self.game, self.user, self.count )

class UserActivityLog(models.Model):
    user = models.ForeignKey(Auth_User)
    action_datetime = models.DateTimeField(auto_now=True)
    action = models.CharField(max_length=16)
    game = models.ForeignKey(Game)

    class Meta:
        db_table = 'user_activity'

    @classmethod
    def last_acted(cls, username):
        try:
            user_obj = Auth_User.objects.get(username=username)
        except ObjectDoesNotExist:
            raise("failed to create user from name %s" % username)
        try:
            ual = cls.objects.filter(user=user_obj).order_by('-action_datetime')[:1].get()
        except ObjectDoesNotExist:
            return None
        else:
            return ual.action_datetime
    
    @classmethod
    def log_user_action(cls, username, action, game):
        '''
            cls is UserActivityLog
            kwargs = 
                action
                username
                game
            if action is added or voted, 
            store user, action and game with
            datetime stamp
        '''
        try:
            user_obj = Auth_User.objects.get(username=username)
        except ObjectDoesNotExist:
            raise("failed to create user from name %s" % username)

        ual = cls.objects.create(user=user_obj, action=action, game=game)
        try:
            ual.full_clean()
        except ValidationError as e:
            raise e
        print ual
        ual.save()

