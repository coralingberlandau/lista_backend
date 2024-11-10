from django.db import models
from django.contrib.auth.models import User

class ListItem(models.Model):
    title = models.CharField(max_length=255, default="No items")  # Title of the list
    items = models.TextField(default="No items")  # Store items as a plain string
    # description = models.JSONField(default=list)  # Store an array of strings
    date_created = models.DateField(auto_now_add=True)  # Automatically adds creation date
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_lists')  # The owner of the list
    is_active = models.BooleanField(default=True)  # Indicates if the list is active

    def __str__(self):
        return str(self.title)

class GroupList(models.Model):
    ROLE_CHOICES = [
        ('member', 'Member'),
        ('admin', 'Admin'),
    ]

    PERMISSION_CHOICES = [
        ('read_only', 'Read-Only'),
        ('full_access', 'Full Access'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="group_lists")  # קשר עם משתמשים
    list_item = models.ForeignKey(ListItem, on_delete=models.CASCADE, related_name="shared_with")  # קשר עם מסמכים
    date_joined = models.DateField(auto_now_add=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')
    permission_type = models.CharField(max_length=20, choices=PERMISSION_CHOICES, default='read_only')

    def __str__(self):
        return f"{self.user.username} - {self.list_item.title} - {self.role} - {self.permission_type}"


class ListItemImage(models.Model):
    list_item = models.ForeignKey(ListItem, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(null=True,blank=True,default='/placeholder.png' ,upload_to='list_item_images/')

    def __str__(self):
        return f"Image for {self.list_item.title} - {self.image.name}"

