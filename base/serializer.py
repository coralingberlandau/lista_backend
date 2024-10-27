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

class GroupListSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    list = ListItemSerializer()

    class Meta:
        model = GroupList
        fields = '__all__'