from django.contrib import admin
# Register your models here.
from .models import ListItem, GroupList, ListItemImage, Customization, Recommendation

admin.site.register(ListItem)
admin.site.register(GroupList)
admin.site.register(ListItemImage)
admin.site.register(Customization)
admin.site.register(Recommendation)