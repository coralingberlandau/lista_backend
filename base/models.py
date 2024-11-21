from django.db import models
from django.contrib.auth.models import User

class ListItem(models.Model):
    title = models.CharField(max_length=255, default="No items") 
    items = models.TextField(default="No items") 
    date_created = models.DateField(auto_now_add=True) 
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_lists')  
    is_active = models.BooleanField(default=True) 

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
    index = models.PositiveIntegerField(default=0)
    mime_type = models.CharField(max_length=50, blank=True, null=True) 

    def __str__(self):
        return f"Image for {self.list_item.title} - {self.image.name}"


class Customization(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # קשר עם המשתמש
    background_image_id = models.CharField(max_length=20, default='')  # ברירת מחדל ריקה

    def __str__(self):
        return f"Customization for user {self.user.username or self.user.pk} - image ID: {self.background_image_id}"

   
class Recommendation(models.Model):
    list_item = models.ForeignKey(ListItem, on_delete=models.CASCADE, related_name="recommendations")  # רשימה קשורה
    recommended_items = models.TextField()  # שדות הממליצים, מופרדים בפסיק
    created_at = models.DateTimeField(auto_now_add=True)  # זמן יצירת ההמלצה

    def __str__(self):
        return f"Recommendation for {self.list_item.title} at {self.created_at}"
