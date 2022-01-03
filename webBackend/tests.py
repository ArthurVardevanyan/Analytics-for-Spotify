from django.test import TestCase
from django.http import HttpResponse, HttpResponseRedirect
from unittest.mock import patch

import webBackend.views as views
import monitoringBackend.database as database
import monitoringBackend.playlistSongs as playlistSongs
import monitoringBackend.spotify as spotify


class TestCase(TestCase):

    def test_environment(self):
        import os
        self.assertEqual(os.environ.get('TEST'), "test")

    def test_boot(self):
        import webBackend.apps as apps
        self.assertEqual(apps.boot(), True)

    def test_redirect(self):
        response = self.client.get('')
        self.assertContains(response, "url=/spotify/index.html")

    def test_redirect_spotify(self):
        response = self.client.get('/spotify/')
        self.assertContains(response, "url=/spotify/index.html")

    @patch('webBackend.credentials.getAPI')
    def test_login(self, mock_API):
        mock_API.return_value = {
            "url": "url=https://accounts.spotify.com/authorize"}
        response = self.client.get('/analytics/login', follow=True)
        self.assertContains(
            response, "url=https://accounts.spotify.com/authorize")

    @patch('webBackend.credentials.getAPI')
    def test_login_Error(self, mock_API):
        mock_API.return_value = False
        response = self.client.get('/analytics/login', follow=True)
        self.assertContains(response, "url=/spotify/index.html")

    @patch('webBackend.credentials.accessToken')
    @patch('webBackend.credentials.getUser')
    def test_loginResponce(self, mock_Token, mock_User):
        mock_Token.return_value = "testUser"
        mock_User.return_value = {"expires_in": 3600}
        response = self.client.get(
            '/analytics/loginResponse?code=testCode', follow=True)
        self.assertContains(response, "url=/spotify/analytics.html")

    def test_loginResponce_noCode(self):
        response = self.client.get('/analytics/loginResponse', follow=True)
        self.assertContains(response, "url=/spotify/index.html")

    @patch('webBackend.credentials.accessToken')
    @patch('webBackend.credentials.getUser')
    def test_logout(self, mock_Token, mock_User):
        mock_Token.return_value = "testUser"
        mock_User.return_value = {"expires_in": 3600}
        self.client.get('/analytics/loginResponse?code=testCode', follow=True)
        response = self.client.get('/analytics/logout', follow=True)
        self.assertContains(response, "url=/spotify/index.html")

    def test_logout_noLogin(self):
        response = self.client.get('/analytics/logout', follow=True)
        self.assertContains(response, "url=/spotify/index.html")

    def test_authenticated_False(self):
        response = self.client.get('/analytics/authenticated', follow=True)
        self.assertContains(response, "False", status_code=401)

    @patch('webBackend.credentials.accessToken')
    @patch('webBackend.credentials.getUser')
    def test_authenticated_True(self, mock_Token, mock_User):
        mock_Token.return_value = "testUser"
        mock_User.return_value = {"expires_in": 3600}
        self.client.get('/analytics/loginResponse?code=testCode', follow=True)
        response = self.client.get('/analytics/authenticated', follow=True)
        self.assertContains(response, "True")

    def test_get_playlists(self):
        database.get_playlists('')
        self.assertEqual(1, 1)
