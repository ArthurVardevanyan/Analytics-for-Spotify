from django.test import TestCase
import webBackend.views as views
import monitoringBackend.database as database
import monitoringBackend.playlistSongs as playlistSongs
import monitoringBackend.spotify as spotify


class testObject(object):
    pass


class TestCase(TestCase):

    def test_environment(self):
        import os
        self.assertEqual(os.environ.get('TEST'), "test")

    def test_boot(self):
        import webBackend.apps as apps
        self.assertEqual(apps.boot(), True)

    def test_authenticated(self):
        req = testObject()
        req.session = {}
        req.COOKIES = {}
        req.META = {}
        req.method = "GET"
        views.authenticated(req)
        self.assertEqual(1, 1)

    def test_get_playlists(self):
        database.get_playlists('')
        self.assertEqual(1, 1)
