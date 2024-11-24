from django.contrib import admin

# Register your models here.
from .models import (Customization, GroupList, ListItem, ListItemImage,
                     Recommendation)

admin.site.register(ListItem)
admin.site.register(GroupList)
admin.site.register(ListItemImage)
admin.site.register(Customization)
admin.site.register(Recommendation)
