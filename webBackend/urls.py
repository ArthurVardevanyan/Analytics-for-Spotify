
from django.urls import path
from . import views

urlpatterns = [
    path('', views.redirect),
    path('spotify/', views.redirect),
    path('analytics/', views.redirect),
    path('health/', views.health),
    path('authenticated/', views.authenticated),
    path('login/', views.login, name='login'),
    path('loginResponse', views.loginResponse, name='loginResponse'),
    path('logout/', views.logout),
    path('status/', views.status),
    path('start/', views.start),
    path('stop/', views.stop),
    path('deleteUser/', views.deleteUser),
    path('listeningHistory/', views.listeningHistory, name='listeningHistory'),
    path('stats/', views.stats, name='stats'),
    path('dailyAggregation/', views.dailyAggregation, name='dailyAggregation'),
    path('hourlyAggregation/', views.hourlyAggregation, name='hourlyAggregation'),
    path('songs/', views.songs, name='songs'),
    path('playlistSubmission/', views.playlistSubmission),
    path('deletePlaylist/', views.deletePlaylist),
    path('playlistSongs/', views.playlistSongs, name='playlistSongs'),
    path('globalDailyAggregation/', views.globalDailyAggregation, name='globalDailyAggregation'),
    path('globalHourlyAggregation/', views.globalHourlyAggregation, name='globalHourlyAggregation'),
    path('globalStats/', views.globalStats, name='globalStats'),
    path('analyzeHistoricalImport/', views.analyzeHistoricalImport, name='analyzeHistoricalImport'),
    path('executeHistoricalImport/', views.executeHistoricalImport, name='executeHistoricalImport'),
]
