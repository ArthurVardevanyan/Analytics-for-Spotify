
from django.urls import path
from . import views

urlpatterns = [
    path('listeningHistory/', views.listeningHistory, name='listeningHistory'),
    path('songs/', views.songs, name='songs'),
    path('playlistSongs/', views.playlistSongs, name='playlistSongs'),
    path('login/', views.login, name='login'),
    path('loginResponce', views.loginResponce, name='loginResponce'),
    path('authenticated/', views.authenticated),
    path('status/', views.status),
    path('stop/', views.stop),
    path('start/', views.start),
    path('logout/', views.logout),
    path('boot/', views.boot),

]
