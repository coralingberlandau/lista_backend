from rest_framework.response import Response
from rest_framework import viewsets
from .models import ListItem, GroupList
from base.serializer import ListItemSerializer, GroupListSerializer

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.models import User 

from rest_framework.decorators import action  # ייבוא של action

# from rest_framework.authtoken.models import Token
from rest_framework import status




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
        serializer.save(user_id=self.request.user)  # שמירת user_id של המשתמש המחובר

# ViewSet for GroupList
class GroupListViewSet(viewsets.ModelViewSet):
    queryset = GroupList.objects.all()
    serializer_class = GroupListSerializer

# login -- http://127.0.0.1:8000/login

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token['username'] = user.username
        token['user_id'] = user.id
        return token
   
class MyTokenObtainPairView(TokenObtainPairView):
   serializer_class = MyTokenObtainPairSerializer


# register --- http://127.0.0.1:8000/register
@api_view(['POST'])
def register(request):
    # בדוק אם השם משתמש כבר קיים
    if User.objects.filter(username=request.data['username']).exists():
        return Response({'error': 'Username already exists.'})

    user = User.objects.create_user(
                username=request.data['username'],
                email=request.data['email'],
                password=request.data['password'],
                first_name = request.data.get('first_name', ''),  # תיקון כאן
                last_name = request.data.get('last_name', '')
            )
    user.is_active = True
    user.is_staff = True
    user.save()

    refresh = MyTokenObtainPairSerializer.get_token(user)
    access = str(refresh.access_token)

          # כאן אפשר ליצור טוקן ולהחזיר אותו
    # token, _ = Token.objects.get_or_create(user=user)

    return Response({
        'Success': 'New user created',
        'username': user.username,
        'user_id': user.id,
        'access': access  # מחזיר את הטוקן
        # 'token': token.key  # החזרת הטוקן שנוצר
    }, status=status.HTTP_201_CREATED)
    
        
        
        
        # {'Success': 'new user born', 'username': user.username, 'user_id': user.id,  'access': token.key) status=status.HTTP_201_CREATED})

    # return Response({'Success': 'new user born', 'username': user.username, 'user_id': user.id, 'access': str(user.access_token)})


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


#    #  shares

# class DocumentShareViewSet(viewsets.ModelViewSet):
#     queryset = DocumentShare.objects.all()
#     serializer_class = DocumentShareSerializer

#     def create(self, request, *args, **kwargs):
#         # יצירת שיתוף חדש
#         data = request.data
#         document_id = data.get('document')
#         content_type_model = data.get('content_type')
#         object_id = data.get('shared_with_id')
#         can_edit = data.get('can_edit', True)

#         document = get_object_or_404(Document, title=document_id)
#         content_type = get_object_or_404(ContentType, model=content_type_model)

#         # יצירת רשומה חדשה של DocumentShare
#         share = DocumentShare.objects.create(
#             document=document,
#             content_type=content_type,
#             object_id=object_id,
#             can_edit=can_edit
#         )

#         # יצירת לינק לשיתוף
#         share_link = f"http://yourdomain.com/documents/{document.id}/edit/"

#          # יצירת לינק לוואטסאפ
#         whatsapp_message = f"Check out this document: {share_link}"
#         whatsapp_link = f"https://api.whatsapp.com/send?text={whatsapp_message}"


#         # שליחה בדוא"ל (לא חובה)
#         new_user = get_object_or_404(User, id=object_id)  # חיפוש המשתמש שאיתו משתפים
#         send_mail(
#             'Document Shared with You',
#             f'You have been shared a document. Access it here: {share_link}',
#             'from@example.com',
#             [new_user.email],
#             fail_silently=False,
#         )

#         serializer = self.get_serializer(share)
#         return Response({
#             "message": f"Document shared successfully with {new_user.username}",
#             "share_link": share_link,
#             "whatsapp_link": whatsapp_link,
#             "data": serializer.data
#         }, status=status.HTTP_201_CREATED)

#     def update(self, request, *args, **kwargs):
#         # עדכון הרשומה הקיימת
#         partial = kwargs.pop('partial', False)
#         instance = self.get_object()

#         serializer = self.get_serializer(instance, data=request.data, partial=partial)
#         serializer.is_valid(raise_exception=True)
#         self.perform_update(serializer)

#         return Response(serializer.data)

#     def destroy(self, request, *args, **kwargs):
#         # מחיקת הרשומה
#         instance = self.get_object()
#         self.perform_destroy(instance)
#         return Response(status=status.HTTP_204_NO_CONTENT)

# def share_document_with_additional_user(request, document_id):
#     """פונקציה לשיתוף מסמך עם משתמש נוסף."""
#     document = get_object_or_404(Document, id=document_id, owner=request.user)
#     user_id = request.POST.get('user_id')
#     can_edit = request.POST.get('can_edit', False)

#     # חיפוש המשתמש החדש שאיתו רוצים לשתף
#     new_user = get_object_or_404(User, id=user_id)

#     # יצירת רשומת שיתוף חדשה עבור המשתמש החדש
#     content_type = ContentType.objects.get_for_model(User)
#     DocumentShare.objects.create(
#         document=document, 
#         content_type=content_type, 
#         object_id=new_user.id, 
#         can_edit=can_edit
#     )

#     return Response({"message": f"Document shared successfully with {new_user.user_name}"})
