from django.test import TestCase
from apps.jobs.services.france_travail.client import FranceTravailClient, FranceTravailException


from unittest.mock import patch
from django.test import override_settings

class FranceTravailClientTest(TestCase):
    @override_settings(FRANCE_TRAVAIL_CLIENT_ID='', FRANCE_TRAVAIL_CLIENT_SECRET='')
    def test_client_initialization(self):
        client = FranceTravailClient()
        with self.assertRaises(FranceTravailException):
            client.search_offers({})

        with self.assertRaises(FranceTravailException):
            client.get_offer_detail("123")

    @patch('apps.jobs.services.france_travail.client.requests.post')
    @patch('apps.jobs.services.france_travail.client.requests.get')
    def test_client_with_credentials(self, mock_get, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"access_token": "fake_token"}
        
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"resultats": [{"id": "123"}]}
        
        client = FranceTravailClient(client_id="dummy", client_secret="secret")
        res = client.search_offers({})
        self.assertIn("resultats", res)
        
        mock_get.return_value.json.return_value = {"id": "123", "title": "Job"}
        res = client.get_offer_detail("123")
        self.assertEqual(res.get("id"), "123")
