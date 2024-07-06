from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

from django.contrib.auth.models import User
from django.contrib.auth import logout

from .models import Album, Photo, Tag, Subs

import time 
from PIL import Image
import base64 
import random
import string
import io 
import os 

from .aws import * 

if os.path.exists('env.py'): import env 


incoming = {}
path='scratch'
if not os.path.exists(path):
    os.makedirs(path)


@api_view(['GET'])
def hello_world(request):
    return Response({'message': str(time.asctime()) })


@api_view(['POST'])
def test(request):
    reps = {
        'message': f' {request.user.username} {request.user.is_authenticated} { str(time.asctime())}',
        'user': request.user.username,
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


@api_view(['GET'])
def search(request):
    scode = request.GET.get('sword')

    try:
        user = User.objects.get(username=scode)
        return Response({'found': 'user' , 'user': user.username})
    except User.DoesNotExist:
        pass

    try:
        album = Album.objects.get(code=scode)
        return Response({'found': 'album' , 'abcode': album.code})
    except Album.DoesNotExist:
        pass 
    
    return Response({'found': 'nada', 'scode': scode})


@api_view(['POST'])
def createAlbum(request):
    if not request.user.is_authenticated:
        return Response({'message': 'not logged in'})

    user = request.user
    abname = request.data.get('abname')

    if abname=='' or abname==None:
        return Response({'message': 'album name is required'})
    
    try:
        album = Album.objects.get(name=abname, user=user)
        return Response({'message': 'album already exists'})
    except Album.DoesNotExist:
        pass

    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=32))
        if Album.objects.filter(code=code).count() == 0:
            break
    
    album = Album(name=abname, user=user, code=code)
    album.save()

    bums = {}
    try:
        albums = Album.objects.filter(user=user)
        for album in albums:
            bums[album.code]=album.name 
    except Album.DoesNotExist:
        return Response({'message': 'no albums found'})
    
    return Response({'message':'ok', 'albums': bums})


@api_view(['GET'])
def getAlbums(request):
    vuname = request.GET.get('sword')
    
    try:
        user = User.objects.get(username=vuname)
    except User.DoesNotExist:
        return Response({'message': 'user not found'})
    
    bums = {}
    try:
        albums = Album.objects.filter(user=user)
        for album in albums:
            bums[album.code]=album.name 
    except Album.DoesNotExist:
        return Response({'message': 'no albums found'})
    
    subs = Subs.objects.filter(user=user)
    for sub in subs:
        bums[sub.album.code] = sub.album.name
    
    msg = {
        'message':'ok',
        'albums': bums,
        'user': request.user.username,
    }

    return Response(msg)


@api_view(['GET'])
def getAlbum(request):
    abcode = request.GET.get('code')
    user = request.user

    try:
        album = Album.objects.get(code=abcode)
    except Album.DoesNotExist:
        return Response({'message': 'album not found'})
            
    rep = {
        'name': album.name,
        'code': album.code,
        'thumbnail': create_presigned_url(album.thumbnail),
        'created': album.created_at.strftime("%B %d, %Y %H:%M"),
        'user': album.user.username,
    }

    if user.is_authenticated:
        sub = Subs.objects.filter(album=album, user=user)
        rep['status'] = 1 # logged in guest
        if sub: 
            rep['status'] = 2 # subscribed
        if album.user == user: 
            rep['status'] = 3 # owner
    else:
        rep['status'] = 0  # not logged in

    return Response(rep)
    

@api_view(['GET'])
def getShots(request):
    abcode = request.GET.get('code')
    try:
        album = Album.objects.get(code=abcode)
    except Album.DoesNotExist:
        return Response({'message': 'album not found', 'code': 0})

    ids = {}
    try:
        photos = Photo.objects.filter(album=album)
        for photo in photos:
            ids[photo.code] = ''
    except Photo.DoesNotExist:
        return Response({'message': 'no photos found', 'code': 1})
    
    return Response({'code':abcode, 'shots': ids})


@api_view(['GET'])
def getShot(request):
    pcode = request.GET.get('code')
    try:
        photo = Photo.objects.get(code=pcode)
        rep = {
            'code': photo.code,
            'filename': photo.filename,
            'link': create_presigned_url(photo.link),
            'tlink': create_presigned_url(photo.tlink),
            'created': photo.created_at.strftime("%B %d, %Y %H:%M"),
            'album': photo.album.name,
            'user': photo.user.username,
        }
        return Response(rep)
    except Photo.DoesNotExist:
        return Response({'message': 'photo not found'})


def processPhoto(target, meta):
    while True:
        idcode = ''.join(random.choices(string.ascii_uppercase + string.digits, k=32))
        if Photo.objects.filter(code=idcode).count() == 0:
            break
    
    user = User.objects.get(username=meta['user'])
    album = Album.objects.get(code=meta['code'])
    filename = meta['filename']
    code = idcode
    
    photo = Photo.objects.create(code=code, user=user, album=album, filename=filename)
    photo.save()

    data = ''.join(target)
    mt, encoded = data.split(',', 1)
    decoded = base64.b64decode(encoded)

    # create thumbnail
    try:
        image_bytes_io = io.BytesIO(decoded)
        image = Image.open(image_bytes_io)
        thumb = image.resize((300, 300))

        path='scratch/' + str(photo.code) + '.jpg'
        thumb.save(path)

        tlink = 'sm-' + str(photo.code)
        if (upload_file_to_s3(path, tlink)):
            os.remove(path)

        photo.tlink = tlink
        photo.save()

        if album.thumbnail is None:
            album.thumbnail = tlink
            album.save()
    except Exception as e:
        print('thumbnail error: ', e)
        photo.tlink = None 
        photo.save()


    #save original 
    path='scratch/' + str(photo.code) + '/' 
    if not os.path.exists(path):
        os.makedirs(path)
    path += filename
    with open(path, 'wb') as f:
        f.write(decoded)
    
    link = 'og-' + str(photo.code)
    if (upload_file_to_s3(path, link)):
        os.remove(path)
    
    photo.link = link
    photo.save()
    return photo.code 


@api_view(['POST'])
def upload(request):
    if not request.user.is_authenticated:
        return Response({'message': 'not logged in'})

    user = request.user
    code = request.data.get('code')
    chunk = request.data.get('chunk')
    chunks = request.data.get('chunks')
    data = request.data.get('data')
    filename = request.data.get('filename')
    hash = request.data.get('hash')

    if not hash in incoming:
        target = [None] * chunks
        meta = {
            'code': code,
            'chunks': chunks,
            'user': user,
            'filename': filename,
            'hash': hash,
            'count': 0,
        }
        incoming[hash] = [target, meta]
    else:
        target, meta = incoming[hash] 
    
    target[chunk] = data
    meta['count'] += 1
    if meta['count'] == chunks:
        pcode = processPhoto(target, meta)
        del incoming[hash]
        return Response({'message': 'up', 'pcode': pcode})

    return Response({'message': 'incomplete'})


@api_view(['POST'])
def killshot(request):
    if not request.user.is_authenticated:
        return Response({'message': 'not logged in'})

    user = request.user
    pcode = request.data.get('code')
    try:
        photo = Photo.objects.get(code=pcode)
    except Photo.DoesNotExist:
        return Response({'message': 'photo not found'})
    
    ok = False
    if photo.user == user:
        ok = True
    if photo.album.user == user:
        ok = True
    if not ok:
        return Response({'message': 'not authorized'})
    
    try:
        delete_file_from_s3(photo.link)
    except Exception as e:
        print('delete error: ', e)
        
    try:
        delete_file_from_s3(photo.tlink)
    except Exception as e:
        print('delete error: ', e)

    photo.delete()
    return Response({'message': 'deleted'})
    

@api_view(['POST'])
def subscribe(request):
    if not request.user.is_authenticated:
        return Response({'message': 'not logged in'})

    user = request.user
    abcode = request.data.get('code')
    try:
        album = Album.objects.get(code=abcode)
    except Album.DoesNotExist:
        return Response({'message': 'album not found'})
    
    sub = Subs(album=album, user=user)
    sub.save()
    return Response({'message': 'subscribed'})


@api_view(['POST'])
def unsubscribe(request):
    if not request.user.is_authenticated:
        return Response({'message': 'not logged in'})

    user = request.user
    abcode = request.data.get('code')
    try:
        album = Album.objects.get(code=abcode)
    except Album.DoesNotExist:
        return Response({'message': 'album not found'})
    
    sub = Subs.objects.get(album=album, user=user)
    sub.delete()
    return Response({'message': 'unsubscribed'})


@api_view(['POST'])
def killbum(request):
    if not request.user.is_authenticated:
        return Response({'message': 'not logged in'})

    user = request.user
    abcode = request.data.get('code')
    try:
        album = Album.objects.get(code=abcode)
    except Album.DoesNotExist:
        return Response({'message': 'album not found'})
    
    if album.user != user:
        return Response({'message': 'not authorized'})
    
    photos = Photo.objects.filter(album=album)
    for photo in photos:
        try:
            delete_file_from_s3(photo.link)
        except Exception as e:
            print('delete error: ', e)
        
        try:
            delete_file_from_s3(photo.tlink)
        except Exception as e:
            print('delete error: ', e)

        photo.delete()

    album.delete()
    return Response({'message': 'deleted'})


@api_view(['GET'])
def get_album_links(request):
    code = request.GET.get('code')
    try:
        album = Album.objects.get(code=code)
    except Album.DoesNotExist:
        return Response({'message': 'album not found'})
    
    links = []
    names = []
    photos = Photo.objects.filter(album=album)
    for photo in photos:
        links.append(create_presigned_url(photo.link))
        names.append(photo.filename)
    response = {
        'links': links,
        'names': names,
    }
    return Response(response)


@api_view(['GET'])
def whoami(request):
    if request.user.is_authenticated:
        return Response({'message': 'logged in', 'user': request.user.username})
    return Response({'message': 'not logged in'})



def homepage(request):
    context = {}
    return render(request, 'my_app/index.html', context)