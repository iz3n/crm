"""
URL configuration for contacts app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from contacts import views

router = DefaultRouter()
router.register(r'contacts', views.ContactViewSet, basename='contact')

urlpatterns = [
    path('api/', include(router.urls)),
]

