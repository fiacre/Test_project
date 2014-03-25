import pytz
import logging
from datetime import datetime, timedelta, date
from collections import OrderedDict

from django.conf import settings
from django.utils.timezone import activate

from games.models import UserActivityLog, Vote

activate(settings.TIME_ZONE)

_log = logging.getLogger(__name__)

def _can_act(user):
    ''' has this user acted today
        check the activity log
    '''
    tz = pytz.timezone(settings.TIME_ZONE)
    ual = UserActivityLog.last_acted(user)

    _log.debug("user %s activity log : %s " % (user, ual))

    if ual is None :
        return True
    if ual.day == datetime.now(tz=tz).day:
        return False
    elif datetime.now(tz=tz).weekday() >= 5:
        ''' is it the weekend  '''
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
     
    votes = Vote.objects.all().select_related('game')
    for vote in votes:
        game = Game.objects.get(pk=vote.game.id)
        if game.owned == False:
            context[game.title] = vote.count
    return OrderedDict(reversed(sorted(context.items(), key=lambda t: t[1])))
