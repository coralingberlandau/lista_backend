from rest_framework import serializers
from .models import ListItem, GroupList, ListItemImage, Customization
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
    # שדה של המשתמש שמחובר לרשימה
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())  
    # שדה של המסמך ששייך לרשימה
    list_item = serializers.PrimaryKeyRelatedField(queryset=ListItem.objects.all())  
    # שדה שמתאר את ה-ID של המשתמש ששיתף את הרשימה
    shared_by_user_id = serializers.SerializerMethodField()

    class Meta:
        model = GroupList
        fields = '__all__'

    def get_shared_by_user_id(self, obj):
        """
        מקבל את השדה `obj` שהוא אובייקט של GroupList, ומחזיר את ה-ID של המשתמש ששיתף את הרשימה.
        אם הרשימה שייכת למשתמש אז מחזיר את ה-ID של המשתמש ששיתף.
        """
        shared_with = obj.list_item.shared_with.filter(user=obj.user).first()
        if shared_with:
            return shared_with.user.id
        return None

    def validate(self, attrs):
        # לוודא ש-fields הנדרשים קיימים, לדוג' 'user' לא חסר
        if 'user' not in attrs:
            raise serializers.ValidationError({"user": "This field is required."})
        return attrs
    
class ListItemImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListItemImage
        fields = '__all__'


class CustomizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customization
        fields = '__all__'  # או תוכל לציין את השדות שברצונך להחזיר