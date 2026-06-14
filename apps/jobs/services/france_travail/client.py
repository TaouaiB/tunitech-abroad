class FranceTravailException(Exception):
    pass


class FranceTravailClient:
    def __init__(self, client_id: str = "", client_secret: str = ""):
        self.client_id = client_id
        self.client_secret = client_secret
        self._access_token = None

    def search_offers(self, params: dict) -> dict:
        """
        Skeleton method to search for jobs on France Travail.
        In Phase 4, we don't do live network calls.
        """
        if not self.client_id or not self.client_secret:
            raise FranceTravailException("France Travail credentials not configured.")
        return {"resultats": []}

    def get_offer_detail(self, source_job_id: str) -> dict:
        """
        Skeleton method to fetch a specific job.
        """
        if not self.client_id or not self.client_secret:
            raise FranceTravailException("France Travail credentials not configured.")
        return {}
