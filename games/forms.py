""" game vote form """
from django import forms
from games.models import Game

class GameAddForm(forms.Form):
    """ view.game_add: 
        simple text widget form 
    """
    title = forms.CharField(max_length=100)

class GameVoteForm(forms.Form):
    """ views.game_vote:
        dropdown widget
        only show games not owned
    """
    games = forms.ModelChoiceField(
        queryset=Game.objects.filter(owned=False).order_by('title')
        )

class VoteCountForm(forms.Form):
    """
        Get top voted games
        in a time period
    """
    from_t = forms.DateTimeInput()
    to_t = forms.DateTimeInput()

