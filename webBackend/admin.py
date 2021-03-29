from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Artists)
admin.site.register(Listeninghistory)
admin.site.register(Playlistsongs)
admin.site.register(Playlists)
admin.site.register(Songartists)
admin.site.register(Songs)

