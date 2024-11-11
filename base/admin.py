from django.contrib import admin
# Register your models here.
from .models import ListItem, GroupList, ListItemImage

admin.site.register(ListItem)
admin.site.register(GroupList)
admin.site.register(ListItemImage)