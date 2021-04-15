from django.test import TestCase
import webBackend.views as views
import songMonitoringBackend.database as database
import songMonitoringBackend.playlistSongs as playlistSongs
import songMonitoringBackend.spotify as spotify


class testObject(object):
    pass


class TestCase(TestCase):
    def test_boot(self):
        views.boot()
        self.assertEqual(1, 1)

    def test_authenticated(self):
        req = testObject()
        req.session = {}
        views.authenticated(req)
        self.assertEqual(1, 1)

    def test_get_playlists(self):
        database.get_playlists('')
        self.assertEqual(1, 1)
