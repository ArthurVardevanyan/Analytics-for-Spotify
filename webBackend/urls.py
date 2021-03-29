
from django.urls import path
from . import views

urlpatterns = [
    path('listeningHistory/', views.listeningHistory, name='listeningHistory'),
    path('listeningHistoryAll/', views.listeningHistoryAll, name='listeningHistoryAll'),
    path('listeningHistoryShort/', views.listeningHistoryShort, name='listeningHistoryShort'),
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
