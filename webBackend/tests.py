from django.test import TestCase
import webBackend.views as views

class TestCase(TestCase):
    def test(self):
        views.boot()
        self.assertEqual(1, 1)
