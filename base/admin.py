from django.contrib import admin
# Register your models here.
from .models import ListItem, GroupList, ListItemImage, Customization

admin.site.register(ListItem)
admin.site.register(GroupList)
admin.site.register(ListItemImage)
admin.site.register(Customization)