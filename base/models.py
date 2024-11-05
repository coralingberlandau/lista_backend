from django.db import models
from django.contrib.auth.models import User

class ListItem(models.Model):
    title = models.CharField(max_length=255)  # Title of the list
    description = models.JSONField(default=list)  # Store an array of strings
    date_created = models.DateField(auto_now_add=True)  # Automatically adds creation date
    images = models.JSONField(default=list, blank=True, null=True)  # רשימת כתובות התמונות
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_lists')  # The owner of the list
    is_active = models.BooleanField(default=True)  # Indicates if the list is active

    def __str__(self):
        return str(self.title)
    
        # description = models.TextField(default="No description", null=False)

# Model for GroupList - Relationship table between Customer and Lists
# class GroupList(models.Model):
#     ROLE_CHOICES = [
#         ('member', 'Member'),
#         ('admin', 'Admin'),
#     ]

#     PERMISSION_CHOICES = [
#         ('read_only', 'Read-Only'),
#         ('full_access', 'Full Access'),
#     ]

#     user_id = models.ForeignKey(User, on_delete=models.CASCADE) # string
#     list_item = models.ForeignKey(ListItem, on_delete=models.CASCADE) # list_item_id number
#     date_joined = models.DateField(auto_now_add=True) 
#     role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')
#     permission_type = models.CharField(max_length=20, choices=PERMISSION_CHOICES, default='read_only')

#     def __str__(self):
#         return f"{self.user.username} - {self.list_item.title}"  # גישה למאפיין title


class GroupList(models.Model):
    ROLE_CHOICES = [
        ('member', 'Member'),
        ('admin', 'Admin'),
    ]

    PERMISSION_CHOICES = [
        ('read_only', 'Read-Only'),
        ('full_access', 'Full Access'),
    ]

    user_id = models.ForeignKey(User, on_delete=models.CASCADE)  # שדה ForeignKey למודל User
    user_id_string = models.CharField(max_length=150, blank=True)  # שדה סטרינג נוסף
    list_item = models.ForeignKey(ListItem, on_delete=models.CASCADE)  # שדה ForeignKey למודל ListItem
    date_joined = models.DateField(auto_now_add=True) 
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')
    permission_type = models.CharField(max_length=20, choices=PERMISSION_CHOICES, default='read_only')

    def save(self, *args, **kwargs):
        self.user_id_string = self.user_id.username if self.user_id else ''  # עדכון המידע לשם המשתמש
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user_id_string} - {self.list_item.title}"
