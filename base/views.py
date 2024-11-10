from rest_framework.response import Response
from rest_framework import viewsets, status

from django.db import models
from .models import ListItem, GroupList, ListItemImage
from base.serializer import ListItemImageSerializer, ListItemSerializer, GroupListSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.models import User 

from rest_framework.decorators import action  
from django.utils import timezone 

from django.db.models import Q

from .logging_utils import log  # ייבוא הדקורטור


# GET http://127.0.0.1:8000/listitem/by-user/1/

class ListItemViewSet(viewsets.ModelViewSet):
    queryset = ListItem.objects.all()
    serializer_class = ListItemSerializer

    @log(user_id=123, object_id=456)
    def get_queryset(self):
        user_id = self.request.query_params.get('user_id')
        return ListItem.objects.filter(user_id=user_id) if user_id else ListItem.objects.all()

    @log(user_id=123, object_id=456)
    @action(detail=False, methods=['get'], url_path='by-user/(?P<user_id>\d+)')
    def get_by_user(self, request, user_id=None):
        user = request.user  # המשתמש המחובר מזוהה על ידי הטוקן
        user_items = ListItem.objects.filter(user=user)  # חיפוש הרשומות של המשתמש המחובר בלבד
        serializer = ListItemSerializer(user_items, many=True)
        return Response(serializer.data)
    
    def perform_update(self, serializer):

        serializer.save(user_id=self.request.user)  # שמירת user_id של המשתמש המחובר

    #     list_item = serializer.save()  # שמירה של הפריט אחרי עדכון

    # # הוספת התמונות החדשות אם יש
    #     if 'images' in self.request.data:
    #         new_images = self.request.data['images']

    #     # אם יש תמונות נוספות, הוספתן לרשימה הקיימת
    #         if new_images:
    #         # נוודא שהתמונות לא חוזרות על עצמן
    #             existing_images = list_item.images or []
    #             list_item.images = list(set(existing_images + new_images))  # הוספת תמונות חדשות (אם יש)

    #             list_item.save()
    @log(user_id=123, object_id=456)
    def perform_create(self, serializer):
        list_item = serializer.save(user=self.request.user)  # יצירת פריט חדש

    # אם יש תמונות נוספות, הוספתן לרשימה
        if 'images' in self.request.data:
            new_images = self.request.data['images']
            if new_images:
                list_item.images = new_images  # שמירת התמונות החדשות בפריט
                list_item.save()

            # הוספת התמונות לרשימה הקיימת
                list_item.images.extend(new_images)
                list_item.save()


class ListItemImageViewSet(viewsets.ModelViewSet):
    queryset = ListItemImage.objects.all()
    serializer_class = ListItemImageSerializer

# ViewSet for GroupList
class GroupListViewSet(viewsets.ModelViewSet):
    queryset = GroupList.objects.all()
    serializer_class = GroupListSerializer
    permission_classes = [IsAuthenticated]

    @log(user_id=123, object_id=456)
    def get_queryset(self):
        user_id = self.request.query_params.get('user_id', None)

        groupList = GroupList.objects.filter(models.Q(user__id=user_id) | models.Q(shared_with__id=user_id))
        list_item_ids = groupList.values_list('id', flat=True)
        return ListItem.objects.filter(id__in=list_item_ids)   
                                            
    @log(user_id=123, object_id=456)
    def create(self, request, *args, **kwargs):
        # הוספת המשתמש המחובר כמשתמש ברשומה החדשה
        data = request.data.copy()
        data['user'] = request.user.id  # אנחנו שולחים את ה-ID ולא את האובייקט

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        # שמירת הרשומה בבסיס הנתונים
        self.perform_create(serializer)
        
        # החזרת נתוני הרשומה החדשה
        return Response(
            {'message': 'GroupList created successfully', 'data': serializer.data},
            status=status.HTTP_201_CREATED
        )
    
    @log(user_id=123, object_id=456)
    def update(self, request, *args, **kwargs):
        # קבלת הרשומה לפי ה-PK
        instance = self.get_object()

        # בדיקה אם היוזר המחובר הוא הבעלים של הרשומה או נמצא ברשימת המשתמשים המורשים
        if instance.user.id != request.user.id and request.user not in instance.shared_with.all():
            return Response(
                {'message': 'You are not authorized to update this group list.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # אם יש לי הרשאה לעדכן, אני עובר לעדכון
        data = request.data.copy()
        data['user'] = request.user.id  # לוודא שהיוזר לא משתנה

        serializer = self.get_serializer(instance, data=data)
        serializer.is_valid(raise_exception=True)
        
        # שמירת העדכון
        self.perform_update(serializer)
        
        # החזרת הנתונים לאחר העדכון
        return Response(
            {'message': 'GroupList updated successfully', 'data': serializer.data},
            status=status.HTTP_200_OK
        )
    
    @log(user_id=123, object_id=456)
    @action(detail=False, methods=['get'], url_path='by-user/(?P<user_id>\d+)')
    def list_by_user(self, request, user_id=None):
        user_id = request.user.id
        groupList = GroupList.objects.filter(models.Q(user_id=user_id))
        list_item_ids = groupList.values_list('id', flat=True)
        items = ListItem.objects.filter(id__in=list_item_ids)     
        serializer = ListItemSerializer(items, many=True)
        return Response(serializer.data)   

    
# login -- http://127.0.0.1:8000/login

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    @log(user_id=123, object_id=456)
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token['username'] = user.username
        token['user_id'] = user.id

        # עדכון last_login
        user.last_login = timezone.now()  # קביעת הזמן הנוכחי
        user.save()  # שמירת השינויים בדאטה בייס
        
        return token
   
class MyTokenObtainPairView(TokenObtainPairView):
   serializer_class = MyTokenObtainPairSerializer


# register --- http://127.0.0.1:8000/register

@log(user_id=123, object_id=456)
@api_view(['POST'])
def register(request):
    if User.objects.filter(username=request.data['username']).exists():
        return Response({'error': 'Username already exists.'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(
                username=request.data['username'],
                email=request.data['email'],
                password=request.data['password'],
                first_name = request.data.get('first_name', ''),  # תיקון כאן
                last_name = request.data.get('last_name', '')
            )
    user.is_active = True
    user.is_staff = True
    user.is_superuser = True
     # עדכון last_login
    user.last_login = timezone.now()  # קביעת הזמן הנוכחי
    user.save()
    refresh = MyTokenObtainPairSerializer.get_token(user)
    access = str(refresh.access_token)

    return Response({
        'Success': 'New user created',
        'username': user.username,
        'user_id': user.id,
        'access': access  # מחזיר את הטוקן
        # 'token': token.key  # החזרת הטוקן שנוצר
    }, status=status.HTTP_201_CREATED)
    
@log(user_id=123, object_id=456)
@api_view(['GET'])
def index(req):
   return Response({'hello': 'world'})

@log(user_id=123, object_id=456)
@api_view(['GET'])
def test(req):
   return Response({'test': 'success'}) 

@log(user_id=123, object_id=456)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def priverty(req):
  return Response({'priverty': 'success'})