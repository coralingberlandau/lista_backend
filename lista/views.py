"""
This module contains views related to user management, including registration, password reset,
and recommendation generation. It utilizes Django REST framework and integrates with external 
services like OpenAI and SendGrid.
"""

# Standard imports
import os
import json
import base64

# Third-party imports
from jsonschema import ValidationError
import openai
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, Content
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.exceptions import NotFound
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.core.validators import validate_email

# Django imports
from django.shortcuts import get_object_or_404
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

# Local imports
from lista.serializer import (
    ListItemImageSerializer,
    ListItemSerializer,
    GroupListSerializer,
    CustomizationSerializer,
    RecommendationSerializer
)

from .models import ListItem, GroupList, ListItemImage, Customization, Recommendation
from .serializer import UserSerializer
from .logging_utils import log

openai.api_key = settings.OPENAI_API_KEY

class RecommendationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling recommendations related to list items.
    Allows creating and viewing recommendations for items in a shopping list.
    """
    queryset = Recommendation.objects.all()
    serializer_class = RecommendationSerializer

    @log(user_id="request.user.id", object_id="list_item.id")
    def recommendations(self, request, list_item_id):
        """
        Generates recommendations for a shopping list based on the provided list item ID.
        Uses OpenAI to generate a list of recommended items.
        """
        try:
            list_item = ListItem.objects.filter(id=list_item_id).first()
            print(f"Fetching recommendations for list item with ID: {list_item_id}")

            if not list_item or not list_item.items:
                raise NotFound("No items found in the list.")

            items = [item.strip() for item in list_item.items.split('|')]
            prompt = f"Recommend items for a shopping list that includes: {', '.join(items)}"

            response = openai.completions.create(
                model="gpt-3.5-turbo",
                prompt=prompt,
                max_tokens=100
            )

            recommendations = response['choices'][0]['message']['content'].strip().split(',')

            recommendation = Recommendation.objects.create(
                list_item=list_item,
                recommended_items=",".join(recommendations)
            )

            serializer = self.get_serializer(recommendation)
            return Response(serializer.data)

        except NotFound as e:
            return Response({"error": str(e)},
                            status=status.HTTP_404_NOT_FOUND)
        except openai.error.OpenAIError as e:
            print(f"Error occurred with OpenAI: {str(e)}")
            return Response({"error": f"OpenAI error: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return Response({"error": "An unexpected error occurred."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@log(user_id="request.user.id", object_id="list_item.id")
@api_view(['GET'])
def index():
    """
    A simple index view for testing the API.
    """
    return Response({'hello': 'world'})


@log(user_id="request.user.id", object_id="list_item.id")
@api_view(['GET'])
def test():
    """
    A test view to check basic functionality.
    """
    return Response({'test': 'success'})


@log(user_id="request.user.id", object_id="list_item.id")
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def priverty():
    """
    A view to test access for authenticated users.
    """
    return Response({'privacy': 'success'})


@log(user_id="request.user.id", object_id="list_item.id")
@api_view(['GET'])
def get_user_info_by_email(request, email):
    """
    Fetch user information by email.
    Returns user details if found, otherwise an error.
    """
    if not email:
        return Response({"error": "Email parameter is required."}, status=400)

    try:
        user = User.objects.get(email=email)
        serializer = UserSerializer(user)
        return Response(serializer.data)

    except User.DoesNotExist:
        return Response({"error": "User not found."}, status=404)


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom serializer for obtaining JWT tokens with additional claims.
    This serializer is customized to include additional claims like 
    `username` and `user_id` in the generated JWT token.

    Note:
    - The `create` and `update` methods are not implemented in this class.
    - If you are using this serializer as part of a `ModelSerializer`, 
      you may need to implement the `create` and `update` methods.
    """
    @classmethod
    @log(user_id="request.user.id", object_id="list_item.id")
    def get_token(cls, user):
        """
        Generates a JWT token for the user with additional custom claims.

        This method calls the parent class's `get_token` method to generate
        a basic token, and then adds the `username` and `user_id` claims
        to it. The user's `last_login` is also updated here.

        Args:
            user (User): The user object for whom the token is generated.

        Returns:
            dict: The generated JWT token with added claims.
        """
        token = super().get_token(user)
        token['username'] = user.username
        token['user_id'] = user.id
        user.last_login = timezone.now()
        user.save()
        return token


class MyTokenObtainPairView(TokenObtainPairView):
    """
    Custom view for obtaining JWT tokens.
    """
    serializer_class = MyTokenObtainPairSerializer


@log(user_id="request.user.id", object_id="list_item.id")
@api_view(['POST'])
def register(request):
    """
    Register a new user with username, email, and password.

    This endpoint allows the creation of a new user by providing a username, email, password, 
    first name, and last name. The server checks whether the username or email already exists 
    in the database, and if so, returns an error. If the registration is successful, 
    a new user is created, and an authentication token is returned for further use.
    """
    if User.objects.filter(username=request.data['username']).exists():
        return Response({'error': 'Username already exists.'},
                        status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(email=request.data['email']).exists():
        return Response({'error': 'Email already in use.'},
                        status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(
        username=request.data['username'],
        email=request.data['email'],
        password=request.data['password'],
        first_name=request.data.get('first_name', ''),
        last_name=request.data.get('last_name', '')
    )
    user.is_active = True
    user.is_staff = True
    user.last_login = timezone.now()
    user.save()
    refresh = MyTokenObtainPairSerializer.get_token(user)
    access = str(refresh.access_token)

    return Response({
        'Success': 'New user created',
        'username': user.username,
        'user_id': user.id,
        'access': access
    }, status=status.HTTP_201_CREATED)


@log(user_id="request.user.id", object_id="list_item.id")
@api_view(['GET', 'PATCH'])
def update_user(request, user_id):
    """
    Update user profile information.

    This view handles two types of requests:
    1. GET: Fetches the current profile data (username, first name, last name, email).
    2. PATCH: Updates the user's profile with the provided data.

    When updating, the function performs several checks:
    - Ensures that the provided email is valid and unique.
    - Ensures that the provided username is unique.
    - Ensures that the request is being made by the user themselves 
    (no one else can update the profile of another user).

    If any of the required fields (email, username) already exist in the system,
    a 400 error will be returned.
    If the request is successful, a 200 status with a success message is returned.
    If the request is unauthorized, a 403 error is returned.
    """
    user = get_object_or_404(User, pk=user_id)

    if request.method == 'GET':
        user_data = {
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email
        }
        return Response(user_data, status=status.HTTP_200_OK)

    if request.method == 'PATCH':
        data = request.data

        if 'username' in data:
            username = data['username']
            if User.objects.filter(username=username).exclude(id=user.id).exists():
                return Response({'error': 'Username already exists.'},
                                status=status.HTTP_400_BAD_REQUEST)

        if 'email' in data:
            email = data['email']
            try:
                validate_email(email)
            except ValidationError:
                return Response(
                    {"error": "Invalid email format."}, status=status.HTTP_400_BAD_REQUEST)

            if User.objects.filter(email=email).exclude(id=user.id).exists():
                return Response({'error': 'Email already in use.'},
                                status=status.HTTP_400_BAD_REQUEST)

        user.username = data.get('username', user.username)
        user.first_name = data.get('first_name', user.first_name)
        user.last_name = data.get('last_name', user.last_name)
        user.email = data.get('email', user.email)
        user.save()

        return Response({"message": "Profile updated successfully!"}, status=status.HTTP_200_OK)

    return Response({"error": "Invalid request method."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


class ResetPasswordView(APIView):
    """
    View for resetting the user's password.
    """
    @log(user_id="request.user.id", object_id="list_item.id")
    def post(self, request):
        """
        Resets the user's password using the provided email and new password.
        """
        email = request.data.get("email")
        new_password = request.data.get("password")

        if not email or not new_password:
            return Response(
                {"error": "Email and new password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()

            return Response(
                {"message": "Password reset successfully."},
                status=status.HTTP_200_OK,
            )
        except User.DoesNotExist:
            return Response(
                {"error": "User with this email does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )


@log(user_id="request.user.id", object_id="list_item.id")
def send_password_reset_email(email):
    """
    Sends a password reset email to the provided address.
    """
    sg = SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
    from_email = Email(settings.DEFAULT_FROM_EMAIL)
    to_email = Email(email)
    subject = "Password Reset Request"

    content = Content(
        "text/plain",
        (
            "Click the link to reset your password: "
            f"{settings.FRONTEND_URL}/change-password?email={email}"
        )
    )

    mail = Mail(
        from_email=from_email,
        to_email=to_email,
        subject=subject,
        content=content,
    )

    try:
        response = sg.client.mail.send.post(request_body=mail.get())
        return response.status_code
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return None


class ResetPasswordRequestView(APIView):
    """
    View for handling password reset requests.

    This view processes a password reset request by verifying the user's email 
    and sending a reset email containing a link if the user exists in the database.
    """
    @log(user_id="request.user.id", object_id="None")
    def post(self, request):
        """
        Handles the POST request for initiating a password reset.
        Takes an email and sends a reset email if the user exists.
        """
        email = request.data.get("email")
        if not email:
            return Response(
                {"error": "Email is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            User.objects.get(email=email)

            send_password_reset_email(email)

            return Response(
                {"message": "Password reset email has been sent."},
                status=status.HTTP_200_OK,
            )

        except User.DoesNotExist:
            return Response(
                {"error": "User with this email does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )

        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class ListItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing ListItems, including CRUD operations
    and functionality for soft deletion of items.
    """
    queryset = ListItem.objects.all()
    serializer_class = ListItemSerializer

    @log(user_id="request.user.id", object_id="list_item.id")
    def get_queryset(self):
        """
        Retrieves the list items filtered by user_id if provided.
        """
        user_id = self.request.query_params.get('user_id')
        return ListItem.objects.filter(user_id=user_id) if user_id else ListItem.objects.all()

    @log(user_id="request.user.id", object_id="list_item.id")
    @action(detail=False, methods=['GET'], url_path=r'by-user/(?P<user_id>\d+)')
    def get_by_user(self, request, user_id=None):
        """
        Retrieves the list items for a specific user.
        """
        user = request.user
        if user.is_anonymous:
            raise PermissionDenied("User not logged in.")
        user_items = ListItem.objects.filter(user=user)
        serializer = ListItemSerializer(user_items, many=True)
        return Response(serializer.data)

    @log(user_id="request.user.id", object_id="list_item.id")
    def perform_update(self, serializer):
        """
        Perform update of list item, ensuring the user is authenticated.
        """
        user = self.request.user
        if user.is_anonymous:
            raise PermissionDenied("User not logged in.")
        serializer.save(user=user)

    @log(user_id="request.user.id", object_id="list_item.id")
    def perform_create(self, serializer):
        """
        Perform creation of a list item, ensuring the user is authenticated.
        """
        user = self.request.user
        if user.is_anonymous:
            raise PermissionDenied("User not logged in.")
        serializer.save(user=user)

    @log(user_id="request.user.id", object_id="list_item.id")
    @action(detail=True, methods=['patch'])
    def delete_item(self, request, pk=None):
        """
        Soft delete the list item by setting `is_active` to False.
        """
        user = request.user
        if user.is_anonymous:
            raise PermissionDenied("User not logged in.")
        try:
            list_item = self.get_object()
            list_item.is_active = False
            list_item.save()
            return Response(
                {"message": "Item successfully deleted!"}, status=200)

        except ListItem.DoesNotExist:
            return Response({"error": "Item not found!"}, status=404)


class GroupListViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing GroupLists and interacting with associated ListItems.
    Includes creation, update, and permission checks for groups.
    """
    queryset = GroupList.objects.all()
    serializer_class = GroupListSerializer
    permission_classes = [IsAuthenticated]

    @log(user_id="request.user.id", object_id="list_item.id")
    def get_queryset(self):
        """
        Returns the list of GroupLists for the user with specific permissions.
        The query is performed based on the user ID obtained from the URL.

        If the user is associated with a GroupList or is included in the list of people with whom
        the GroupList is shared, the function returns all the ListItems related to that GroupList.

        Returns:
            Response: List of ListItems connected to the GroupList of the user or
            those shared with the user.
        """
        user_id = self.request.query_params.get('user_id', None)

        group_list = GroupList.objects.filter(
            models.Q(user__id=user_id) | models.Q(shared_with__id=user_id)
        )
        list_item_ids = group_list.values_list('id', flat=True)
        return ListItem.objects.filter(id__in=list_item_ids)

    @log(user_id="request.user.id", object_id="list_item.id")
    def create(self, request, *args, **kwargs):
        """
        Creates a new GroupList and associates it with the currently logged-in user.
        The function accepts data from the request, validates it, and creates a new GroupList.

        Returns:
            Response: A message with the details of the created GroupList or an error 
            if creation fails.
        """
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
        """
        Updates the GroupList if the user has the necessary permissions for the update.

        If the user does not have permission to update (i.e., the user is neither the owner of the
        GroupList nor a shared user), the function returns a forbidden response.

        Returns:
            Response: A message with the updated GroupList details or an error message
            if the user is unauthorized.
        """
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
    @action(detail=False, methods=['GET'], url_path=r'by-user/(?P<user_id>\d+)')
    def list_by_user(self, request, user_id):
        """
        Returns the ListItems associated with a specific user based on the user_id.

        The function fetches GroupLists where the logged-in user is associated and retrieves 
        the ListItems related to those GroupLists.

        Args:
            user_id (str): The ID of the user whose ListItems are to be fetched.

        Returns:
            Response: A list of serialized ListItems associated with the user.
        """
        user_id = request.user.id
        group_list = GroupList.objects.filter(models.Q(user_id=user_id))
        list_item_ids = group_list.values_list('list_item_id', flat=True)
        items = ListItem.objects.filter(id__in=list_item_ids)
        serializer = ListItemSerializer(items, many=True)
        return Response(serializer.data)

    @log(user_id="request.user.id", object_id="list_item.id")
    @action(detail=False, methods=['GET'], url_path='permission_type')
    def get_permission_type(self, request):
        """
        Fetches the permission type for a specific user and ListItem based on 
        the provided user_id and list_item_id.

        The function checks if both user_id and list_item_id are provided. If either is missing,
        it returns an error message. If valid, it returns the permission type 
        for the specified user and ListItem.

        Args:
            user_id (str): The ID of the user whose permission type is being checked.
            list_item_id (str): The ID of the ListItem for which the permission type
            is being checked.

        Returns:
            Response: The permission type for the specified user and ListItem or an error message 
            if parameters are missing or the group list is not found.
        """
        user_id = request.query_params.get('user_id')
        list_item_id = request.query_params.get('list_item_id')

        if not user_id or not list_item_id:
            return Response({'message': 'user_id and list_item_id are required'},
                            status=status.HTTP_400_BAD_REQUEST)

        print(f"Fetching permission for user_id: {user_id} "
              f"and list_item_id: {list_item_id}")

        group_list = GroupList.objects.filter(
            user_id=user_id, list_item_id=list_item_id).first()

        if not group_list:
            return Response(
                {'message': 'No group list found for the given user and item'},
                status=status.HTTP_404_NOT_FOUND
            )

        print(f"Permission type found: {group_list.permission_type}")

        return Response({'permission_type': group_list.permission_type}, status=status.HTTP_200_OK)

class ListItemImageViewSet(viewsets.ModelViewSet):
    """
    A viewset for handling image uploads, retrieval, and updates for list items.

    This viewset provides three key actions:
    1. `upload_images`: Allows the user to upload multiple images for a specific list item.
    2. `get_images_for_list_item`: Retrieves all images associated with a given list item.
    3. `update_images`: Allows the user to update or delete images for a list item,
    including modifying their index.

    Each action handles different HTTP methods (POST, GET) and validates inputs to ensure
    correct handling of list item images.
    """

    queryset = ListItemImage.objects.all()
    serializer_class = ListItemImageSerializer

    @log(user_id="request.user.id", object_id="list_item.id")
    @action(detail=False, methods=['post'], url_path='upload_images')
    def upload_images(self, request):
        """
        Handle POST request to upload images for a given list item.

        This endpoint allows the user to upload multiple images for a specific 
        list item by providing the list item ID and an array of base64 encoded 
        image data. Each image is saved to the file system, and the corresponding 
        `ListItemImage` instances are created in the database.

        Request data:
        - list_item (required): The ID of the list item to associate images with.
        - images (required): A list of base64 encoded image data containing 
          'uri', 'fileName', 'mimeType', and 'index'.

        Returns:
        - HTTP 201 Created with a success message if the upload is successful.
        - HTTP 400 Bad Request if the list_item or images array is missing, 
          or if the base64 decoding fails.
        """
        list_item_id = request.data.get('list_item')
        images_data = request.data.getlist('images')

        if not list_item_id:
            return Response({"error": "list_item is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not images_data:
            return Response({"error": "images array is required."},
                            status=status.HTTP_400_BAD_REQUEST)

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
                image_index = image_json['index']

                extension = mime_type.split(
                    '/')[1] if '/' in mime_type else 'jpeg'
                image_file_name = (
                    f"{file_name or f'image_{index}'}."
                    f"{extension}"
                )

                image_data = base64.b64decode(base64_image)
                image_content = ContentFile(image_data, name=image_file_name)
                file_path = default_storage.save(os.path.join('list_item_images', image_file_name),
                                                 image_content)

                image_instance = ListItemImage(
                    list_item=list_item,
                    image=file_path,
                    index=image_index,
                    mime_type=mime_type
                )
                image_instances.append(image_instance)
            except Exception as e:
                return Response({"error": "Failed to decode base64 image", "details": str(e)},
                                status=status.HTTP_400_BAD_REQUEST)

        ListItemImage.objects.bulk_create(image_instances)
        return Response({"status": "Images uploaded successfully"}, status=status.HTTP_201_CREATED)

    @log(user_id="request.user.id", object_id="list_item.id")
    @action(detail=True, methods=['GET'], url_path='get_images_for_list_item')
    def get_images_for_list_item(self, request, *args, **kwargs):
        """
        Handle GET request to retrieve all images associated with a 
        given list item.

        This endpoint retrieves all images related to a specific list item by 
        its ID. The images are returned in a JSON response containing the 
        image URL, index, and image ID.

        Request parameters:
        - pk (required): The ID of the list item.

        Returns:
        - HTTP 200 OK with a list of images if found.
        - HTTP 200 OK with an empty list and a message if no images are found.
        """
        list_item_id = kwargs.get('pk')

        images = ListItemImage.objects.filter(list_item_id=list_item_id)
        if not images.exists():
            return Response(
                {"images": [], "message": "No images found for this list item."}, status=200)

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
        """
        Handle POST request to update or delete images for a given list item.

        This endpoint allows the user to update the indexes of existing images 
        and delete images by their index. The `list_item_id` must be provided 
        along with the indices of images to update or delete.

        Request data:
        - list_item_id (required): The ID of the list item.
        - updatedImagesIndex[] (optional): A list of indices of images to 
          update.
        - deletedImagesIndex[] (optional): A list of indices of images to 
          delete.

        Returns:
        - HTTP 200 OK with a success message if the images are updated and/or 
          deleted successfully.
        - HTTP 400 Bad Request if any errors occur during the update or 
          deletion process.
        """
        list_item_id = request.data.get('list_item_id')
        updated_images_index = request.data.getlist('updatedImagesIndex[]')
        deleted_images_index = request.data.getlist('deletedImagesIndex[]')
        try:

            for deleted_index in deleted_images_index:
                images_to_delete = ListItemImage.objects.filter(
                    index=deleted_index, list_item_id=list_item_id)
                print(f"Found images to delete with index {
                      deleted_index}: {images_to_delete}")
                for image in images_to_delete:
                    print(f"Deleting image {
                          image.id} with index {image.index}")
                    image.delete()

            for updated_index in updated_images_index:
                images_to_update = ListItemImage.objects.filter(
                    index=updated_index, list_item_id=list_item_id)
                print(f"Found images with index {
                      updated_index}: {images_to_update}")
                for image in images_to_update:
                    print(
                        f"Updating image {image.id} - Old index: {image.index}"
                    )
                    image.index -= 1

                    try:
                        image.save()
                        print(
                            f"Image {image.id} saved successfully with new index {image.index}")
                    except Exception as e:
                        print(f"Failed to save image {image.id}: {e}")

            return Response(
                {"message": "Images updated and deleted successfully"}, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Error during update: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CustomizationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling user background customizations. Allows users to create, update,
    and retrieve their customization settings (e.g., background image).
    """
    queryset = Customization.objects.all()
    serializer_class = CustomizationSerializer
    permission_classes = [IsAuthenticated]

    @log(user_id="request.user.id", object_id="list_item.id")
    def create(self, request, *args, **kwargs):
        """
        Handle POST request to create or update a user's background customization.

        This method is responsible for:
        - Checking if the required 'background_image_id' is provided.
        - Creating or updating the Customization model instance for the authenticated user.
        - Responding with a success message and the updated data.

        If 'background_image_id' is missing, a 400 error is returned.

        Args:
            request: The HTTP request object containing user data.

        Returns:
            Response: HTTP response with a success or error message.
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

        This method retrieves the background customization for the authenticated user.
        If the customization does not exist, a message indicating the absence of customization
        is returned with a 200 status.

        Args:
            request: The HTTP request object containing user data.

        Returns:
            Response: HTTP response with the user's customization data or a not found message.
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
