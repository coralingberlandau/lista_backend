from django.db import models
from django.contrib.auth.models import User

class ListItem(models.Model):
    title = models.CharField(max_length=255)  # Title of the list
    description = models.TextField(default="No description", null=False)
    date_created = models.DateField(auto_now_add=True)  # Automatically adds creation date
    image = models.ImageField(null=True,blank=True,default='/placeholder.png')
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_lists')  # The owner of the list
    is_active = models.BooleanField(default=True)  # Indicates if the list is active

    def __str__(self):
        return str(self.title)

# Model for GroupList - Relationship table between Customer and Lists
class GroupList(models.Model):
    ROLE_CHOICES = [
        ('member', 'Member'),
        ('admin', 'Admin'),
    ]

    PERMISSION_CHOICES = [
        ('read_only', 'Read-Only'),
        ('full_access', 'Full Access'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    list_item = models.ForeignKey(ListItem, on_delete=models.CASCADE)
    date_joined = models.DateField(auto_now_add=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')
    permission_type = models.CharField(max_length=20, choices=PERMISSION_CHOICES, default='read_only')

    def __str__(self):
        return f"{self.user.username} - {self.list_item.title}"  # גישה למאפיין title
