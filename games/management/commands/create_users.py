from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = "run this to create dummy users"
    def handle(self, *args, **options):
        for name in [ 'jim', 'tim', 'tom',
                'betty', 'sam', 'bob',
                'jen', 'joe', 'rich',
                'john', 'ann', 'mary' ]:
            try:
                email = "%s@localhost.com" % name
                user = User.objects.create_user(name, email, 'nat')
                user.is_staff = False
                user.save()
            except Exception as e:
                raise CommandError("Could not create user: %s, %s" % (name, e))
            else:
                self.stdout.write("created non-staff user %s with password %s" % ( name, "nat"))
                
