from django.test import TestCase
from apps.jobs.services.france_travail.client import FranceTravailClient, FranceTravailException


class FranceTravailClientTest(TestCase):
    def test_client_initialization(self):
        client = FranceTravailClient()
        with self.assertRaises(FranceTravailException):
            client.search_offers({})

        with self.assertRaises(FranceTravailException):
            client.get_offer_detail("123")

    def test_client_with_credentials(self):
        client = FranceTravailClient(client_id="dummy", client_secret="secret")
        res = client.search_offers({})
        self.assertIn("resultats", res)
        
        res = client.get_offer_detail("123")
        self.assertIsInstance(res, dict)
