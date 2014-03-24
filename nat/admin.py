from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import User

from game.models import Gamer

class GamerInline(admin.TabularInline):
    model = Gamer

class UserAdmin(DjangoUserAdmin):
    inlines = (GamerInline,)

admin.site.unregister(User)
admin.site.register(User, UserAdmin)
