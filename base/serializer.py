from rest_framework import serializers
from .models import ListItem, GroupList
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

class ListItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListItem
        fields = '__all__'
        extra_kwargs = {
            'user': {'required': True},  # שדה חובה
            'images': {'required': False},  # הפוך את השדה images לא חובה
        }

class GroupListSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())  # מוודא שה-user הוא מפתח זר (FK) עם ה-ID של המשתמש
    list_item = serializers.PrimaryKeyRelatedField(queryset=ListItem.objects.all())  # אם יש לך מודל ListItem, שים לב להגדיר אותו כראוי

    class Meta:
        model = GroupList
        fields = '__all__'

    def validate(self, attrs):
        # כאן תוכל להוסיף לוגיקה לוודא שהשדות נדרשים או לא
        if 'user' not in attrs:
            raise serializers.ValidationError({"user": "This field is required."})
        return attrs