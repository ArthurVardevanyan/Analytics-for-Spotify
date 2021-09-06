
from django.urls import path
from . import views

urlpatterns = [
    path('', views.redirect),
    path('spotify/', views.redirect),
    path('listeningHistory/', views.listeningHistory, name='listeningHistory'),
    path('songs/', views.songs, name='songs'),
    path('playlistSongs/', views.playlistSongs, name='playlistSongs'),
    path('login/', views.login, name='login'),
    path('loginResponse', views.loginResponse, name='loginResponse'),
    path('authenticated/', views.authenticated),
    path('status/', views.status),
    path('stop/', views.stop),
    path('start/', views.start),
    path('logout/', views.logout),
    path('boot/', views.boot),
    path('delete/', views.deleteUser),
    path('playlistSubmission/', views.playlistSubmission),
    path('deletePlaylist/', views.deletePlaylist),
]
