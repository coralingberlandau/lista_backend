########### application ############

"""
This file contains the URL routing configuration for the Django application.
It registers view sets with a router and maps various API endpoints to their corresponding views.

Key Features:
- A DefaultRouter is used to automatically generate URLs for the viewsets.
- Several API endpoints are registered for models like ListItem, GroupList, ListItemImage,
  Customization, and Recommendation.
- Each URL path is associated with a specific view or viewset that handles the respective request.

Registered Endpoints:
1. /index/ - Home or index page.
2. /test/ - A test endpoint for debugging or testing purposes.
3. /priverty/ - Endpoint related to privacy, likely a privacy policy page.
4. /login/ - Endpoint for token-based authentication login.
5. /register/ - User registration endpoint.
6. /get_user_info/<email>/ - Retrieve user information by email.
7. /user/<user_id>/ - Update user information based on user ID.
8. /reset_password_request/ - Request a password reset.
9. /reset_password/ - Reset user password.
10. /recommendations/<listItemId>/ - Get recommendations for a specific ListItem by ID.

The URLs are dynamically generated using the DefaultRouter for 
models that follow the RESTful pattern.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views
from .views import (CustomizationViewSet, GroupListViewSet,
                    ListItemImageViewSet, ListItemViewSet,
                    RecommendationViewSet)

router = DefaultRouter()
router.register(r'listitem', ListItemViewSet, basename='listitem')
router.register(r'grouplists', GroupListViewSet)
router.register(r'listitemimages', ListItemImageViewSet)
router.register(r'customizations', CustomizationViewSet)
# router.register(r'recommendations', RecommendationViewSet,
#                 basename='recommendations')

urlpatterns = [
    path('index/', views.index),
    path('test/', views.test),
    path('priverty/', views.priverty),
    path('login/', views.MyTokenObtainPairView.as_view()),
    path('register/', views.register),
    path('', include(router.urls)),
    path('get_user_info/<str:email>/', views.get_user_info_by_email,
         name='get_user_info_by_email'),
    path('user/<int:user_id>/', views.update_user, name='update_user'),
    path('reset_password_request/', views.ResetPasswordRequestView.as_view(),
         name='reset_password_request'),
    path('reset_password/', views.ResetPasswordView.as_view(), name='reset_password'),
#     path('recommendations/<int:list_item_id>/', RecommendationViewSet.as_view({'get': 'recommendations'}), 
#          name='recommendations-list-item'),
#     path('recommendations/<int:listItemId>/', RecommendationViewSet.as_view({'get': 'recommendations'}), name='recommendations'),
    path('recommendations/<int:list_item_id>/', RecommendationViewSet.as_view({'get': 'recommendations'})),




#     path('recommendations/<int:listItemId>/',
#          RecommendationViewSet.as_view({'get': 'recommendations'}), name='recommendations'),
]
