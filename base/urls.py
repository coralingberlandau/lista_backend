########### application ############

from . import views
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ListItemViewSet, GroupListViewSet

router = DefaultRouter()
router.register(r'listitem', ListItemViewSet, basename='listitem')
router.register(r'grouplists', GroupListViewSet)

urlpatterns = [
   path('', views.index),
   path('test', views.test),
   path('', include(router.urls)),
   path('login', views.MyTokenObtainPairView.as_view()),
   path('priverty', views.priverty),
   path('register', views.register),
]
