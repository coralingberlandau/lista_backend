########### application ############

from . import views
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CustomizationViewSet, ListItemImageViewSet, ListItemViewSet, GroupListViewSet, RecommendationViewSet

router = DefaultRouter()
router.register(r'listitem', ListItemViewSet, basename='listitem')
router.register(r'grouplists', GroupListViewSet)
router.register(r'listitemimages', ListItemImageViewSet)
router.register(r'customizations', CustomizationViewSet)  
router.register(r'recommendations', RecommendationViewSet, basename='recommendations')

urlpatterns = [
    
   path('index/', views.index),
   path('test/', views.test),
   path('priverty/', views.priverty),
   path('login/', views.MyTokenObtainPairView.as_view()),
   path('register/', views.register),
   path('', include(router.urls)),
   path('get_user_info/<str:email>/', views.get_user_info_by_email, name='get_user_info_by_email'),
   path('user/<int:user_id>/', views.update_user, name='update_user'),
   path('reset_password_request/', views.ResetPasswordRequestView.as_view(), name='reset_password_request'),
   path('reset_password/', views.ResetPasswordView.as_view(), name='reset_password'),
   path('recommendations/<int:listItemId>/', RecommendationViewSet.as_view({'get': 'recommendations'}), name='recommendations'),

]

