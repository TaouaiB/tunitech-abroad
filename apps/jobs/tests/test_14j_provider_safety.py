from unittest.mock import patch

from django.test import TestCase, override_settings

from apps.jobs.models import JobIngestionConfig
from apps.jobs.services.france_travail.client import FranceTravailException
from apps.jobs.services.ingestion import JobIngestionService


def make_ft_jobs(count):
    return {
        "resultats": [
            {
                "id": f"FT-{index}",
                "intitule": f"Developpeur Python {index}",
                "description": "Developpement Django et PostgreSQL.",
                "lieuTravail": {"libelle": "Paris"},
                "typeContrat": "CDI",
                "entreprise": {"nom": "Example"},
            }
            for index in range(count)
        ]
    }


class FranceTravailProviderSafetyTests(TestCase):
    @override_settings(
        FRANCE_TRAVAIL_MAX_REQUESTS_PER_RUN=2,
        FRANCE_TRAVAIL_REQUEST_DELAY_SECONDS=0,
        FRANCE_TRAVAIL_BACKOFF_ON_429_SECONDS=0,
    )
    @patch("apps.jobs.services.ingestion.FranceTravailClient")
    def test_request_cap_stops_further_pages_and_keywords_with_warning(self, mock_client_class):
        config = JobIngestionConfig.objects.create(
            name="provider-cap",
            custom_keywords=["python", "django"],
            preset="custom",
            limit_per_keyword=10,
            max_total_per_run=100,
            max_pages_per_keyword=10,
            dry_run=True,
            normalize_after_fetch=False,
            enrichment_enabled=False,
        )
        mock_client = mock_client_class.return_value
        mock_client.search_offers.return_value = make_ft_jobs(10)

        run = JobIngestionService.run(config, trigger="manual")

        self.assertEqual(mock_client.search_offers.call_count, 2)
        self.assertEqual(run.status, "partial_success")
        self.assertIn("WARNING: France Travail request cap reached", run.error_summary)
        self.assertEqual(run.error_count, 0)

    @override_settings(
        FRANCE_TRAVAIL_MAX_REQUESTS_PER_RUN=10,
        FRANCE_TRAVAIL_REQUEST_DELAY_SECONDS=0,
        FRANCE_TRAVAIL_BACKOFF_ON_429_SECONDS=0,
    )
    @patch("apps.jobs.services.ingestion.FranceTravailClient")
    def test_429_is_classified_as_backoff_warning_without_secret_payload(self, mock_client_class):
        config = JobIngestionConfig.objects.create(
            name="provider-429",
            custom_keywords=["python"],
            preset="custom",
            limit_per_keyword=10,
            max_total_per_run=100,
            max_pages_per_keyword=2,
            dry_run=True,
            normalize_after_fetch=False,
            enrichment_enabled=False,
        )
        mock_client = mock_client_class.return_value
        mock_client.search_offers.side_effect = FranceTravailException("Search API error: HTTP 429")

        run = JobIngestionService.run(config, trigger="manual")

        self.assertEqual(mock_client.search_offers.call_count, 1)
        self.assertEqual(run.status, "partial_success")
        self.assertIn("France Travail rate limited", run.error_summary)
        self.assertIn("configured backoff 0s", run.error_summary)
        self.assertNotIn("Bearer", run.error_summary)
        self.assertNotIn("client_secret", run.error_summary)
