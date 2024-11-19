from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import viewsets, status

from django.db import models
from .models import ListItem, GroupList, ListItemImage, Customization, Recommendation
from base.serializer import ListItemImageSerializer, ListItemSerializer, GroupListSerializer, CustomizationSerializer, RecommendationSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.models import User 
from .serializer import UserSerializer

from rest_framework.decorators import action  
from django.utils import timezone 

from django.db.models import Q

from .logging_utils import log  # ייבוא הדקורטור

from django.core.exceptions import PermissionDenied


from django.core.mail import send_mail
from rest_framework.views import APIView

from django.core.files.base import ContentFile
import base64

from django.conf import settings
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, Content

import os

from django.core.files.storage import default_storage
import json


# import numpy as np
# import cv2
# import face_recognition
# import jwt
# import datetime


import openai
from rest_framework.exceptions import NotFound


openai.api_key = settings.OPENAI_API_KEY

class RecommendationViewSet(viewsets.ModelViewSet):
    queryset = Recommendation.objects.all()
    serializer_class = RecommendationSerializer

    def recommendations(self, request, listItemId):
        try:

            list_item = ListItem.objects.filter(id=listItemId).first()

            if not list_item or not list_item.items:
                raise NotFound("No items found in the list.")


            items = [item.strip() for item in list_item.items.split('|')]
            prompt = f"Recommend items for a shopping list that includes: {', '.join(items)}"


            response = openai.completions.create(
                model="gpt-3.5-turbo",  
                prompt=prompt,
                max_tokens=50
        )

            recommendations = response['choices'][0]['message']['content'].strip().split(',')

            # Create a new recommendation record
            recommendation = Recommendation.objects.create(
                list_item=list_item,
                recommended_items=",".join(recommendations)
            )

            # Serialize and return the recommendation
            serializer = self.get_serializer(recommendation)
            return Response(serializer.data)

        except openai.error.OpenAIError as e:
            return Response({"error": f"OpenAI error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except NotFound as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            # Log the error for debugging purposes
            print(f"Unexpected error: {str(e)}")
            return Response({"error": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# GET http://127.0.0.1:8000/listitem/by-user/1/

class ListItemViewSet(viewsets.ModelViewSet):
    queryset = ListItem.objects.all()
    serializer_class = ListItemSerializer

    @log(user_id="request.user.id", object_id="list_item.id")
    def get_queryset(self):
        user_id = self.request.query_params.get('user_id')
        return ListItem.objects.filter(user_id=user_id) if user_id else ListItem.objects.all()
    
    @log(user_id="request.user.id", object_id="list_item.id")
    @action(detail=False, methods=['get'], url_path='by-user/(?P<user_id>\ d+)')
    def get_by_user(self, request, user_id=None):
        user = request.user  # המשתמש המחובר מזוהה על ידי הטוקן
        if user.is_anonymous:
            raise PermissionDenied("User not logged in.")
        user_items = ListItem.objects.filter(user=user)  # חיפוש הרשומות של המשתמש המחובר בלבד
        serializer = ListItemSerializer(user_items, many=True)
        return Response(serializer.data)

    # זה אחרייי השילוב של הai זיהוי פנים
  
    @log(user_id="request.user.id", object_id="list_item.id")
    def perform_update(self, serializer):
        user = self.request.user
        if user.is_anonymous:
            raise PermissionDenied("User not logged in.")
        serializer.save(user=user)  # שמירה של המשתמש המחובר

    @log(user_id="request.user.id", object_id="list_item.id")
    def perform_create(self, serializer):
        user = self.request.user
        if user.is_anonymous:
            raise PermissionDenied("User not logged in.")
        serializer.save(user=user)

    @log(user_id="request.user.id", object_id="list_item.id")
    @action(detail=True, methods=['patch'])
    def delete_item(self, request, pk=None):
        """
        פעולה למחיקת פריט (soft delete) - סימון כלא פעיל
        """
        user = request.user
        if user.is_anonymous:
            raise PermissionDenied("User not logged in.")
        try:
            list_item = self.get_object()
            list_item.is_active = False  # מניח ששדה 'is_active' קיים במודל שלך
            list_item.save()
            return Response({"message": "Item successfully deleted!"}, status=200)
        
        except ListItem.DoesNotExist:
            return Response({"error": "Item not found!"}, status=404)
        

# ViewSet for GroupList
class GroupListViewSet(viewsets.ModelViewSet):
    queryset = GroupList.objects.all()
    serializer_class = GroupListSerializer
    permission_classes = [IsAuthenticated]

    @log(user_id="request.user.id", object_id="list_item.id")
    def get_queryset(self):
        user_id = self.request.query_params.get('user_id', None)

        groupList = GroupList.objects.filter(models.Q(user__id=user_id) | models.Q(shared_with__id=user_id))
        list_item_ids = groupList.values_list('id', flat=True)
        return ListItem.objects.filter(id__in=list_item_ids)   
                                            
    @log(user_id="request.user.id", object_id="list_item.id")
    def create(self, request, *args, **kwargs):
        # הוספת המשתמש המחובר כמשתמש ברשומה החדשה
        data = request.data.copy()
        data['user'] = request.data.get('user')  # אנחנו שולחים את ה-ID ולא את האובייקט

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        # שמירת הרשומה בבסיס הנתונים
        self.perform_create(serializer)
        
        # החזרת נתוני הרשומה החדשה
        return Response(
            {'message': 'GroupList created successfully', 'data': serializer.data},
            status=status.HTTP_201_CREATED
        )
    
    @log(user_id="request.user.id", object_id="list_item.id")
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
    
    @log(user_id="request.user.id", object_id="list_item.id")
    @action(detail=False, methods=['get'], url_path='by-user/(?P<user_id>\d+)')
    def list_by_user(self, request, user_id):
        user_id = request.user.id
        groupList = GroupList.objects.filter(models.Q(user_id=user_id))
        list_item_ids = groupList.values_list('list_item_id', flat=True)
        items = ListItem.objects.filter(id__in=list_item_ids)     
        serializer = ListItemSerializer(items, many=True)
        return Response(serializer.data)   

    
# login -- http://127.0.0.1:8000/login

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod

    @log(user_id="request.user.id", object_id="list_item.id")
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
@log(user_id="request.user.id", object_id="list_item.id")
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


# update--- http://127.0.0.1:8000/user/<int:user_id>/

@log(user_id="request.user.id", object_id="list_item.id")
@api_view(['GET', 'PATCH'])
def update_user(request, user_id):
    # קבלת המשתמש או הודעת שגיאה אם לא קיים
    user = get_object_or_404(User, pk=user_id)

    if request.method == 'GET':
        # החזרת נתוני המשתמש בתגובה
        user_data = {
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email
        }
        return Response(user_data, status=status.HTTP_200_OK)

    elif request.method == 'PATCH':
        data = request.data
        # עדכון רק השדות שהועברו בבקשה
        user.username = data.get('username', user.username)
        user.first_name = data.get('first_name', user.first_name)
        user.last_name = data.get('last_name', user.last_name)
        user.email = data.get('email', user.email)
        user.save()

        return Response({"message": "Profile updated successfully!"}, status=status.HTTP_200_OK)



    
@log(user_id="request.user.id", object_id="list_item.id")
@api_view(['GET'])
def index(req):
   return Response({'hello': 'world'})

@log(user_id="request.user.id", object_id="list_item.id")
@api_view(['GET'])
def test(req):
   return Response({'test': 'success'}) 

@log(user_id="request.user.id", object_id="list_item.id")
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def priverty(req):
  return Response({'priverty': 'success'})

@log(user_id="request.user.id", object_id="list_item.id")
@api_view(['GET'])
def get_user_info_by_email(request, email):
    email = email
    
    if not email:
        return Response({"error": "Email parameter is required."}, status=400)

    try:
        user = User.objects.get(email=email)
        serializer = UserSerializer(user)
        return Response(serializer.data)

    except User.DoesNotExist:
        return Response({"error": "User not found."}, status=404)
    

class ResetPasswordView(APIView):

    @log(user_id="request.user.id", object_id="list_item.id")
    def post(self, request):
        email = request.data.get("email")
        new_password = request.data.get("password")

        if not email or not new_password:
            return Response({"error": "Email and new password are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            user.set_password(new_password)  # עדכון הסיסמה
            user.save()

            return Response({"message": "Password reset successfully."}, status=status.HTTP_200_OK)
        
        except User.DoesNotExist:
            return Response({"error": "User with this email does not exist."}, status=status.HTTP_404_NOT_FOUND)
        

@log(user_id="request.user.id", object_id="list_item.id")
def send_password_reset_email(email):
    sg = SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
    from_email = Email(settings.DEFAULT_FROM_EMAIL)
    to_email = Email(email)  # ודא שמדובר ב-Email ולא ב-string
    subject = "Password Reset Request"
    content = Content("text/plain", f"Click the link to reset your password: {settings.FRONTEND_URL}/change-password?email={email}")

    mail = Mail(from_email=from_email, to_email=to_email, subject=subject, content=content)
    try:
        response = sg.client.mail.send.post(request_body=mail.get())
        print(f"Email sent to {email} with status code {response.status_code}")
        return response
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        raise e

# קלאס לפונקציה שמטפלת בבקשה לשליחת מייל איפוס סיסמה
class ResetPasswordRequestView(APIView):
    @log(user_id="request.user.id", object_id="list_item.id")
    def post(self, request):
        email = request.data.get("email")
        print(f"Received email: {email}")

        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # יצירת הקישור לאיפוס סיסמה
            reset_url = f"{settings.FRONTEND_URL}/reset-password?email={email}"
            print(f"Reset URL: {reset_url}")

            # שלח מייל עם הקישור לאיפוס סיסמה דרך SendGrid
            send_password_reset_email(email)  # קריאה לפונקציה שנשלחת את המייל

            return Response({"message": "Password reset email has been sent."}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({"error": "User with this email does not exist."}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            # לוג את השגיאה המלאה בקונסול כדי לראות פרטים נוספים
            print(f"Error: {str(e)}")
            return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class ListItemImageViewSet(viewsets.ModelViewSet):
    queryset = ListItemImage.objects.all()
    serializer_class = ListItemImageSerializer

    @log(user_id="request.user.id", object_id="list_item.id")
    @action(detail=False, methods=['post'], url_path='upload_images')
    def upload_images(self, request):
        list_item_id = request.data.get('list_item')
        images_data = request.data.getlist('images')

        if not list_item_id:
            return Response({"error": "list_item is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not images_data:
            return Response({"error": "images array is required."}, status=status.HTTP_400_BAD_REQUEST)

        # בדיקת קיום הפריט
        try:
            list_item = ListItem.objects.get(id=list_item_id)
        except ListItem.DoesNotExist:
            return Response({"error": "List item not found."}, status=status.HTTP_404_NOT_FOUND)

        image_instances = []
        for image_data in images_data:
            try:
                # המרת Base64 לנתוני JSON
                image_json = json.loads(image_data)
                base64_image = image_json['uri']
                file_name = image_json['fileName']
                mime_type = image_json['mimeType']
                index = image_json['index']

                    # הגדרת סיומת הקובץ מ-MIME type (jpeg, png, וכו')
                extension = mime_type.split('/')[1] if '/' in mime_type else 'jpeg'
                image_file_name = f"{file_name or f'image_{index}'}.{extension}"

                    # יצירת ContentFile ושמירה

                image_data = base64.b64decode(base64_image)
                image_content = ContentFile(image_data, name=image_file_name)
                file_path = default_storage.save(os.path.join('list_item_images', image_file_name), image_content)

                    # יצירת מופע ListItemImage עם הנתיב
                image_instance = ListItemImage(
                    list_item=list_item,
                    image=file_path,  # שמירת הנתיב לשימוש עתידי
                    index=index,
                    mime_type=mime_type
                )
                image_instances.append(image_instance)
            except Exception as e:
                return Response({"error": "Failed to decode base64 image", "details": str(e)}, status=status.HTTP_400_BAD_REQUEST)

            # שמירת כל המופעים בבסיס הנתונים
        ListItemImage.objects.bulk_create(image_instances)
        return Response({"status": "Images uploaded successfully"}, status=status.HTTP_201_CREATED)
        

    @log(user_id="request.user.id", object_id="list_item.id")
    @action(detail=True, methods=['get'], url_path='get_images_for_list_item')
    def get_images_for_list_item(self, request, *args, **kwargs):
        # קבלת ה- pk מה-kwargs
        list_item_id = kwargs.get('pk')
        
        images = ListItemImage.objects.filter(list_item_id=list_item_id)
        if not images.exists():
            return Response({"images": [], "message": "No images found for this list item."}, status=200)
        
        image_data = [
            {
                "id": image.id,
                "url": image.image.url,
                "index": image.index
            } for image in images
        ]
        return Response({"images": image_data})



# ViewSet למודל Customization
class CustomizationViewSet(viewsets.ModelViewSet):
    queryset = Customization.objects.all()
    serializer_class = CustomizationSerializer
    permission_classes = [IsAuthenticated]

    @log(user_id="request.user.id", object_id="list_item.id")
    def create(self, request, *args, **kwargs):
        """
        Handle POST request to create or update a user's background customization.
        """
        user = request.user
        background_image_id = request.data.get('background_image_id', '')

        if not background_image_id:
            return Response(
                {"error": "background_image_id is required."},
                status=400
            )

        customization, created = Customization.objects.update_or_create(
            user=user,
            defaults={'background_image_id': background_image_id}
        )

        serializer = CustomizationSerializer(customization)
        return Response(
            {
                "message": "Background updated successfully.",
                "data": serializer.data,
                "status": "created" if created else "updated"
            },
            status=201 if created else 200

        )
    @log(user_id="request.user.id", object_id="list_item.id")
    @action(detail=False, methods=['get'], url_path='get_user_customization')
    def get_customization_for_user(self, request, *args, **kwargs):
        """
        Handle GET request to retrieve the customization for the authenticated user.
        """
        user = request.user

        try:
            customization = Customization.objects.get(user=user)
        except Customization.DoesNotExist:
            return Response({
                "message": "Customization not found for this user.",
                "data": {}
            }, status=200)

        serializer = CustomizationSerializer(customization)
        return Response({
            "message": "Customization retrieved successfully.",
            "data": serializer.data
        }, status=200)
    
