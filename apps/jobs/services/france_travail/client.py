import requests

class FranceTravailException(Exception):
    pass

from django.conf import settings

class FranceTravailClient:
    AUTH_URL = "https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=%2Fpartenaire"
    SEARCH_URL = "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search"

    def __init__(self, client_id: str = "", client_secret: str = ""):
        self.client_id = client_id or getattr(settings, "FRANCE_TRAVAIL_CLIENT_ID", "")
        self.client_secret = client_secret or getattr(settings, "FRANCE_TRAVAIL_CLIENT_SECRET", "")
        self._access_token = None

    def _authenticate(self):
        if not self.client_id or not self.client_secret:
            raise FranceTravailException("France Travail credentials not configured.")
        
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "api_offresdemploiv2 o2dsoffre"
        }
        
        try:
            resp = requests.post(self.AUTH_URL, data=data, timeout=10)
            if resp.status_code == 200:
                self._access_token = resp.json().get("access_token")
            else:
                raise FranceTravailException(f"Auth failed: HTTP {resp.status_code}")
        except Exception as e:
            raise FranceTravailException(f"Auth network error: {e}")

    def search_offers(self, params: dict) -> dict:
        if not self._access_token:
            self._authenticate()

        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Accept": "application/json"
        }

        try:
            resp = requests.get(self.SEARCH_URL, headers=headers, params=params, timeout=10)
            if resp.status_code in [200, 204, 206]:
                if resp.status_code == 204:
                    return {"resultats": []}
                return resp.json()
            else:
                raise FranceTravailException(f"Search API error: HTTP {resp.status_code}")
        except requests.RequestException as e:
            raise FranceTravailException(f"Search network error: {e}")

    def get_offer_detail(self, source_job_id: str) -> dict:
        if not self._access_token:
            self._authenticate()
        
        detail_url = f"https://api.francetravail.io/partenaire/offresdemploi/v2/offres/{source_job_id}"
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Accept": "application/json"
        }
        try:
            resp = requests.get(detail_url, headers=headers, timeout=10)
            if resp.status_code == 200:
                return resp.json()
            else:
                raise FranceTravailException(f"Detail API error: HTTP {resp.status_code}")
        except requests.RequestException as e:
            raise FranceTravailException(f"Detail network error: {e}")
