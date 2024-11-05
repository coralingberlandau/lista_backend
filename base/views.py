from rest_framework.response import Response
from rest_framework import viewsets, status
# from django.core.exceptions import ValidationError

from .models import ListItem, GroupList
from base.serializer import ListItemSerializer, GroupListSerializer

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.models import User 

from rest_framework.decorators import action  # ייבוא של action
from django.utils import timezone  # הוספת ייבוא כדי להשתמש בזמנים

# from rest_framework.authtoken.models import Token



# GET http://127.0.0.1:8000/listitem/by-user/1/

class ListItemViewSet(viewsets.ModelViewSet):
    queryset = ListItem.objects.all()
    serializer_class = ListItemSerializer

    def get_queryset(self):
        user_id = self.request.query_params.get('user_id')
        return ListItem.objects.filter(user_id=user_id) if user_id else ListItem.objects.all()

    @action(detail=False, methods=['get'], url_path='by-user/(?P<user_id>\d+)')
    def get_by_user(self, request, user_id=None):
        # Filter the queryset based on user_id
        user_items = ListItem.objects.filter(user_id=user_id)  # Change `user_id` to the actual field name if different
        serializer = ListItemSerializer(user_items, many=True)
        return Response(serializer.data)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)  # ודא שאתה שומר את המשתמש הנוכחי


    # def perform_create(self, serializer):
    #     serializer.save(user_id=self.request.user)  # שמירת user_id של המשתמש המחובר

    # def perform_create(self, serializer):
    #     images_data = self.request.data.get('images', [])
    #     if not isinstance(images_data, list):
    #         raise serializer.ValidationError({"images": "Must be a list."})
    #     serializer.save(user_id=self.request.user)


# ViewSet for GroupList
class GroupListViewSet(viewsets.ModelViewSet):
    queryset = GroupList.objects.all()
    serializer_class = GroupListSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # ביצוע השמירה בבסיס הנתונים
        self.perform_create(serializer)
        
        # החזרת הנתונים של הרשומה החדשה
        return Response(
            {'message': 'GroupList created successfully', 'data': serializer.data},
            status=status.HTTP_201_CREATED
        )
    
# login -- http://127.0.0.1:8000/login

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
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
    # user.is_superuser = True
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
    

@api_view(['GET'])
def index(req):
   return Response({'hello': 'world'})

@api_view(['GET'])
def test(req):
   return Response({'test': 'success'}) 

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def priverty(req):
  return Response({'priverty': 'success'})