from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

from django.contrib.auth.models import User
from django.contrib.auth import logout

import time 

@api_view(['GET'])
def hello_world(request):
    return Response({'message': str(time.asctime()) })


@api_view(['POST'])
def test(request):
    reps = {
        'message': f' {request.user.username} {request.user.is_authenticated} { str(time.asctime())}  '  
    }
    print(reps)
    return Response(reps)


@api_view(['POST'])
def register(request):
    if request.user.is_authenticated:
        return Response({'message': f'already logged in as {request.user.username}'})

    name = request.data.get('name')
    email = request.data.get('email')
    password = request.data.get('password')
    password2 = request.data.get('password_confirmation')

    if name=='' or name==None:
        return Response({'message': 'name is required'})
    if password=='' or password==None:
        return Response({'message': 'password is required'})
    if password != password2:
        return Response({'message': 'passwords do not match'})
    if len(password) < 6:
        return Response({'message': 'password is too short'})
    old = User.objects.filter(username=name)
    if old:
        return Response({'message': 'user already exists'})
    
    user = User.objects.create_user(name, email, password)
    user.save()
    return Response({'message': 'registered', 'time': str(time.asctime())})


@api_view(['POST'])
def logoutuser(request):
    refresh_token = request.data.get('refresh_token')
    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
    except Exception as e:
        return Response({'error': str(e)}, status=400)

    logout(request)
    request.session.flush()

    print('logged out')
    return Response({'message': 'logged out', 'time': str(time.asctime())})

