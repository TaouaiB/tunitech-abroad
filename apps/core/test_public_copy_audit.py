import os
import tempfile

from django.test import SimpleTestCase

from apps.core.services.public_copy_audit import PublicCopyAuditService


class PublicCopyAuditServiceTest(SimpleTestCase):
    def test_flags_france_centric_public_copy_variants(self):
        phrases = [
            "offres françaises",
            "offres IT françaises",
            "offres françaises actualisées",
            "offres en France",
            "Objectif France",
            "France-only",
            "France first",
            "France-first",
        ]

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "public.html")
            with open(path, "w", encoding="utf-8") as handle:
                for phrase in phrases:
                    handle.write(f"<p>{phrase}</p>\n")

            result = PublicCopyAuditService.find_forbidden_terms(paths=[path])

        self.assertFalse(result["ok"])
        found = {violation["phrase"] for violation in result["violations"]}
        self.assertIn("offres it françaises", found)
        self.assertIn("france-first", found)

    def test_allows_source_and_job_data_contexts(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "job_detail.html")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write('<a href="{{ job.source_url }}">Postuler sur France Travail</a>\n')
                handle.write("<span>{{ job.location }}</span>\n")
                handle.write("<span>{{ job.country }}</span>\n")

            result = PublicCopyAuditService.find_forbidden_terms(paths=[path])

        self.assertTrue(result["ok"])
