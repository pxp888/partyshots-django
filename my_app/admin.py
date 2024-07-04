from django.contrib import admin
from .models import Album, Photo, Tag, Subs

# Register your models here.
admin.site.register(Album)
admin.site.register(Photo)
admin.site.register(Tag)
admin.site.register(Subs)

