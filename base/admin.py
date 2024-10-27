from django.contrib import admin
# Register your models here.
from .models import ListItem, GroupList

admin.site.register(ListItem)
admin.site.register(GroupList)