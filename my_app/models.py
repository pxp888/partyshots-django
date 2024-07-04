from django.db import models

# Create your models here.
class Album(models.Model):
    id = models.AutoField(primary_key=True)
    code = models.TextField()
    name = models.TextField()
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    thumbnail = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name


class Photo(models.Model):
    id = models.AutoField(primary_key=True)
    code = models.TextField()
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    album = models.ForeignKey(Album, on_delete=models.CASCADE)
    link = models.TextField()
    tlink = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    filename = models.TextField()

    def __str__(self):
        return str(self.album.name) + ' - ' + str(self.id)
    

class Tag(models.Model):
    id = models.AutoField(primary_key=True)
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE)
    key= models.TextField(null=True, blank=True)
    value = models.TextField(null=True, blank=True)

    def __str__(self):
        return str(self.id)


class Subs(models.Model):
    id = models.AutoField(primary_key=True)
    album = models.ForeignKey(Album, on_delete=models.CASCADE)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    
    def __str__(self):
        return str(self.album.name) + ' - ' + str(self.user.username)


