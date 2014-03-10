This *should* run as it

in a virtualenv run pip install -r requirements.txt

 THEN 
python manage.py syncdb
python manage.py createsuperuser
python manage.py create_users

Do not run loaddata before create_users for testing


tests:
python manage.py test games 
