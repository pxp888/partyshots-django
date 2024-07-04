from django.urls import path
from . import views

urlpatterns = [
    path('hello-world/', views.hello_world, name='hello_world'),
    path('test/', views.test, name='test'),
    path('register/', views.register, name='register'),
    path('logout/', views.logoutuser, name='logout'),
    path('search/', views.search, name='search'),
    path('abcreate/', views.createAlbum, name='abcreate'),
    path('getalbums/', views.getAlbums, name='getalbums'),
    path('getalbum/', views.getAlbum, name='getalbum'),
    path('getshots/', views.getShots, name='getshots'),
    path('getshot/', views.getShot, name='getshot'),
    path('upload/', views.upload, name='upload'),
    path('killshot/', views.killshot, name='killshot'),
]


