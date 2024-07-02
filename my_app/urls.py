from django.urls import path
from . import views

urlpatterns = [
    path('hello-world/', views.hello_world, name='hello_world'),
    path('test/', views.test, name='test'),
    path('register/', views.register, name='register'),
    path('logout/', views.logoutuser, name='logout'),
]


