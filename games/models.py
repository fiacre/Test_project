"""
    Game and Vote Models
"""
import logging
from django.db import models
from django.db.models.signals import post_save
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User as Auth_User
from datetime import datetime, timedelta
import pytz
from django.conf import settings
from django.utils.timezone import activate
activate(settings.TIME_ZONE)
TIMEZONE = pytz.timezone(settings.TIME_ZONE)
 
_log = logging.getLogger(__name__)

class Game(models.Model):
    '''
        Game class
        title: xbox game name
        owned: is title owned by nerdery
        user: user the added game
        created: datetime of object

        class method
            _is_owned(Game, @title) : 
                return True if title is in db
    '''     
       
    title = models.CharField(max_length=255, unique=True, blank=False)
    owned = models.BooleanField(default=False)
    user = models.ForeignKey(Auth_User)
    image = models.ImageField(upload_to='nat/media', height_field=450, width_field=600, null=True, blank=True)
    created = models.DateTimeField(default=datetime.now, blank=False)

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
    game = models.OneToOneField(Game)
    count = models.IntegerField(default=0)
    created = models.DateTimeField(default=datetime.now, blank=False)

    class Meta:
        """ prefer simple table name in db """
        db_table = 'votes'

    def __unicode__(self):
        return "%s, %s" % ( self.game, self.count )

    @classmethod
    def increment_count(cls, title):
        ''' orm classes with classmethods, blech '''
        # if object does not exist, let the chips fall where they may
        vote = cls.objects.get(game__title=title)
        vote.created = datetime.now()
        vote.count += 1
        vote.save()
        return vote

    
def create_new_vote(sender, instance, created, **kwargs):  
    ''' listen for signal to create vote ''' 
    if created:  
        vote, created = Vote.objects.get_or_create(game=instance)  
 
''' nab signal '''
post_save.connect(create_new_vote, sender=Game) 


class UserActivityLog(models.Model):
    '''
        User activities
        of add or vote
        are stored
    '''
    user = models.ForeignKey(Auth_User)
    created = models.DateTimeField(blank=False)
    action = models.CharField(max_length=16)
    game = models.ForeignKey(Game)

    class Meta:
        db_table = 'user_activity'

    def __unicode__(self):
        return "%s, %s, %s" % ( self.user, self.action, self.created ) 

    @classmethod
    def last_acted(cls, username):
        ''' when did this user last vote or add '''
        try:
            user_obj = Auth_User.objects.get(username=username)
        except ObjectDoesNotExist:
            raise("failed to create user from name %s" % username)
        try:
            ''' only need activity in
                the last few days
            '''
            d = datetime.now() - timedelta(days=2)
            ual = cls.objects.filter(user=user_obj, created__gt=d).order_by('-created')[:1].get()
        except ObjectDoesNotExist:
            return None
        else:
            _log.debug("last_acted: %s" % ual)
            _log.debug("last_acted in this timezone: %s" % ual.created.astimezone(tz=TIMEZONE))
            # that is utc time
            # we need localtime
            return ual.created.astimezone(tz=TIMEZONE)
    
    @classmethod
    def log_user_action(cls, username, action, game_title):
        '''
            cls is UserActivityLog
                action
                username
                game title
            if action is added or voted, 
            store user, action and game with
            datetime stamp set in current tz
        '''
        now = datetime.now(tz=TIMEZONE)
        _log.debug("what time is it? : %s " % now)
        _log.debug("in what time zone? : %s " % TIMEZONE)
        try:
            user_obj = Auth_User.objects.get(username=username)
        except ObjectDoesNotExist:
            raise("failed to create user from name %s" % username)

        ual = cls.objects.create(user=user_obj, created=now, action=action, game=Game.objects.get(title=game_title))
        _log.debug("log user action : %s" %  ual )
        ual.save()



class Rating(models.Model):
    RATING_STARS = (
        ('1', 'one star'),
        ('2', 'two stars'),
        ('3', 'three stars'),
        ('4', 'four stars'),
        ('5', 'five stars'),
    )
    game = models.ForeignKey(Game)
    rating = models.CharField(max_length=1, choices=RATING_STARS)

    class Meta:
        db_table = 'rating'
    
    def __unicode__(self):
        return "%s, %s" % (self.game, self.rating )

