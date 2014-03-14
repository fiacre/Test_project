This *should* run as it

in a virtualenv run pip install -r requirements.txt

 THEN 
python manage.py syncdb
python manage.py createsuperuser


tests:
python manage.py test games 


Requirements:

DISPLAY GAMES
/games/games/ -- shows owned games in alpha order, voted games in voted order

VOTE FOR A GAME
/games/vote/ -- drop down list of games added (but not owned) in vote form

ADD NEW TITLE/GAME
games/add/ -- Form with text input for new titles -- checks against existing titles (case insensitive match)

VOTING AND ADD NEW TITLE RESTRICTIONS
either /games/add/ or games/vote/ runs a check :
    if weekend raise error
    if voted already today (midnight to midnight) raise error

MARKING A GAME AS OWNED

/admin/games/game/ 
superuser can check off owned for games add games, modify games, delete games etc
