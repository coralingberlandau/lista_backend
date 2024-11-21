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
from .logging_utils import log 
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

    @log(user_id="request.user.id", object_id="list_item.id")
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

            recommendation = Recommendation.objects.create(
                list_item=list_item,
                recommended_items=",".join(recommendations)
            )

            serializer = self.get_serializer(recommendation)
            return Response(serializer.data)

        except openai.error.OpenAIError as e:
            return Response({"error": f"OpenAI error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except NotFound as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return Response({"error": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


   
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
    

    
# login -- http://127.0.0.1:8000/login

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod

    @log(user_id="request.user.id", object_id="list_item.id")
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token['username'] = user.username
        token['user_id'] = user.id
        user.last_login = timezone.now()  
        user.save() 
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
    user.last_login = timezone.now()  # קביעת הזמן הנוכחי
    user.save()
    refresh = MyTokenObtainPairSerializer.get_token(user)
    access = str(refresh.access_token)

    return Response({
        'Success': 'New user created',
        'username': user.username,
        'user_id': user.id,
        'access': access 
    }, status=status.HTTP_201_CREATED)


# update--- http://127.0.0.1:8000/user/<int:user_id>/

@log(user_id="request.user.id", object_id="list_item.id")
@api_view(['GET', 'PATCH'])
def update_user(request, user_id):
    user = get_object_or_404(User, pk=user_id)

    if request.method == 'GET':
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


class ResetPasswordView(APIView):

    @log(user_id="request.user.id", object_id="list_item.id")
    def post(self, request):
        email = request.data.get("email")
        new_password = request.data.get("password")

        if not email or not new_password:
            return Response({"error": "Email and new password are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            user.set_password(new_password)  
            user.save()

            return Response({"message": "Password reset successfully."}, status=status.HTTP_200_OK)
        
        except User.DoesNotExist:
            return Response({"error": "User with this email does not exist."}, status=status.HTTP_404_NOT_FOUND)
        

@log(user_id="request.user.id", object_id="list_item.id")
def send_password_reset_email(email):
    sg = SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
    from_email = Email(settings.DEFAULT_FROM_EMAIL)
    to_email = Email(email)  
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

class ResetPasswordRequestView(APIView):
    @log(user_id="request.user.id", object_id="list_item.id")
    def post(self, request):
        email = request.data.get("email")
        print(f"Received email: {email}")

        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            reset_url = f"{settings.FRONTEND_URL}/reset-password?email={email}"
            print(f"Reset URL: {reset_url}")

            send_password_reset_email(email)  

            return Response({"message": "Password reset email has been sent."}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({"error": "User with this email does not exist."}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            print(f"Error: {str(e)}")
            return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# GET http://127.0.0.1:8000/listitem/by-user/1/

class ListItemViewSet(viewsets.ModelViewSet):
    queryset = ListItem.objects.all()
    serializer_class = ListItemSerializer

    @log(user_id="request.user.id", object_id="list_item.id")
    def get_queryset(self):
        user_id = self.request.query_params.get('user_id')
        return ListItem.objects.filter(user_id=user_id) if user_id else ListItem.objects.all()
    
    @log(user_id="request.user.id", object_id="list_item.id")
    @action(detail=False, methods=['GET'], url_path='by-user/(?P<user_id>\ d+)')
    def get_by_user(self, request, user_id=None):
        user = request.user  
        if user.is_anonymous:
            raise PermissionDenied("User not logged in.")
        user_items = ListItem.objects.filter(user=user) 
        serializer = ListItemSerializer(user_items, many=True)
        return Response(serializer.data)

  
    @log(user_id="request.user.id", object_id="list_item.id")
    def perform_update(self, serializer):
        user = self.request.user
        if user.is_anonymous:
            raise PermissionDenied("User not logged in.")
        serializer.save(user=user)  

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
            list_item.is_active = False 
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
        data = request.data.copy()
        data['user'] = request.data.get('user')  

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        self.perform_create(serializer)
        
        return Response(
            {'message': 'GroupList created successfully', 'data': serializer.data},
            status=status.HTTP_201_CREATED
        )
    
    @log(user_id="request.user.id", object_id="list_item.id")
    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.user.id != request.user.id and request.user not in instance.shared_with.all():
            return Response(
                {'message': 'You are not authorized to update this group list.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        data = request.data.copy()
        data['user'] = request.user.id 

        serializer = self.get_serializer(instance, data=data)
        serializer.is_valid(raise_exception=True)
        
        self.perform_update(serializer)
        
        return Response(
            {'message': 'GroupList updated successfully', 'data': serializer.data},
            status=status.HTTP_200_OK
        )
    
    @log(user_id="request.user.id", object_id="list_item.id")
    @action(detail=False, methods=['GET'], url_path='by-user/(?P<user_id>\d+)')
    def list_by_user(self, request, user_id):
        user_id = request.user.id
        groupList = GroupList.objects.filter(models.Q(user_id=user_id))
        list_item_ids = groupList.values_list('list_item_id', flat=True)
        items = ListItem.objects.filter(id__in=list_item_ids)     
        serializer = ListItemSerializer(items, many=True)
        return Response(serializer.data)   
    
    @log(user_id="request.user.id", object_id="list_item.id")
    @action(detail=False, methods=['GET'], url_path='permission_type')
    def get_permission_type(self, request):
        user_id = request.query_params.get('user_id')
        list_item_id = request.query_params.get('list_item_id')

        # בדוק אם ה-user_id ו-list_item_id לא null
        if not user_id or not list_item_id:
            return Response({'message': 'user_id and list_item_id are required'}, status=status.HTTP_400_BAD_REQUEST)

        # הדפסת ערכים לבדיקת השאילתה
        print(f"Fetching permission for user_id: {user_id} and list_item_id: {list_item_id}")

        group_list = GroupList.objects.filter(user_id=user_id, list_item_id=list_item_id).first()

        if not group_list:
            return Response({'message': 'No group list found for the given user and item'}, status=status.HTTP_404_NOT_FOUND)

        # הדפסת ה-permission_type
        print(f"Permission type found: {group_list.permission_type}")

        return Response({'permission_type': group_list.permission_type}, status=status.HTTP_200_OK)


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

        try:
            list_item = ListItem.objects.get(id=list_item_id)
        except ListItem.DoesNotExist:
            return Response({"error": "List item not found."}, status=status.HTTP_404_NOT_FOUND)

        image_instances = []
        for image_data in images_data:
            try:
                image_json = json.loads(image_data)
                base64_image = image_json['uri']
                file_name = image_json['fileName']
                mime_type = image_json['mimeType']
                index = image_json['index']

                extension = mime_type.split('/')[1] if '/' in mime_type else 'jpeg'
                image_file_name = f"{file_name or f'image_{index}'}.{extension}"

                image_data = base64.b64decode(base64_image)
                image_content = ContentFile(image_data, name=image_file_name)
                file_path = default_storage.save(os.path.join('list_item_images', image_file_name), image_content)

                image_instance = ListItemImage(
                    list_item=list_item,
                    image=file_path,  
                    index=index,
                    mime_type=mime_type
                )
                image_instances.append(image_instance)
            except Exception as e:
                return Response({"error": "Failed to decode base64 image", "details": str(e)}, status=status.HTTP_400_BAD_REQUEST)


        ListItemImage.objects.bulk_create(image_instances)
        return Response({"status": "Images uploaded successfully"}, status=status.HTTP_201_CREATED)
        

    @log(user_id="request.user.id", object_id="list_item.id")
    @action(detail=True, methods=['GET'], url_path='get_images_for_list_item')
    def get_images_for_list_item(self, request, *args, **kwargs):
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
    
    @log(user_id="request.user.id", object_id="list_item.id")
    @action(detail=False, methods=['post'], url_path='update_images')
    def update_images(self, request, *args, **kwargs):
        print(request.data)
        list_item_id = request.data.get('list_item_id')
        updated_images_index = request.data.getlist('updatedImagesIndex[]')
        deleted_images_index = request.data.getlist('deletedImagesIndex[]')


        try:

            for index in deleted_images_index:
                images_to_delete = ListItemImage.objects.filter(index=index, list_item_id=list_item_id)
                print(f"Found images to delete with index {index}: {images_to_delete}")
                for image in images_to_delete:
                    print(f"Deleting image {image.id} with index {image.index}")
                    image.delete()

            for index in updated_images_index:
                images_to_update = ListItemImage.objects.filter(index=index, list_item_id=list_item_id)
                print(f"Found images with index {index}: {images_to_update}")
                for image in images_to_update:

                    print(f"Updating image {image.id} - Old index: {image.index}")
                    image.index -= 1

                    try:
                        image.save()
                        print(f"Image {image.id} saved successfully with new index {image.index}")
                    except Exception as e:
                        print(f"Failed to save image {image.id}: {e}")

            return Response({"message": "Images updated and deleted successfully"}, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Error during update: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


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
    @action(detail=False, methods=['GET'], url_path='get_user_customization')
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
    
