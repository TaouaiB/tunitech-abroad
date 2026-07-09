import json
import tempfile
from pathlib import Path

import fitz
from django.test import TestCase

from apps.cvs.services.parser_audit import CVParserAuditService


class CVParserAuditServiceTests(TestCase):
    def _write_synthetic_case(self, root: Path) -> tuple[Path, Path, Path]:
        cv_dir = root / "private_test_corpus" / "cvs"
        expected_dir = root / "private_test_corpus" / "expected"
        reports_dir = root / "private_test_corpus" / "reports"
        cv_dir.mkdir(parents=True)
        expected_dir.mkdir(parents=True)

        pdf_path = cv_dir / "case_001.pdf"
        document = fitz.open()
        page = document.new_page()
        page.insert_text(
            (72, 72),
            "Jane Doe\nEmail: jane.doe@example.test\nPhone: +216 22 123 456\nSkills: Python, Django",
        )
        document.save(pdf_path)
        document.close()

        (expected_dir / "case_001.json").write_text(
            json.dumps(
                {
                    "case_id": "case_001",
                    "name": "Jane Doe",
                    "email": "jane.doe@example.test",
                    "phone": "+216 22 123 456",
                    "skills": ["Python", "Django"],
                }
            ),
            encoding="utf-8",
        )
        return cv_dir, expected_dir, reports_dir

    def test_run_generates_structured_reports_without_raw_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cv_dir, expected_dir, reports_dir = self._write_synthetic_case(root)

            result = CVParserAuditService.run(
                str(cv_dir),
                str(expected_dir),
                str(reports_dir / "latest.csv"),
                thresholds={
                    "name_exact_accuracy": 1.0,
                    "name_acceptable_accuracy": 1.0,
                    "email_accuracy": 1.0,
                    "phone_accuracy": 1.0,
                    "skill_precision": 1.0,
                    "skill_recall": 1.0,
                },
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["service"], "cv_parser_audit")
            self.assertEqual(result["counts"]["cv_count"], 1)
            self.assertEqual(result["counts"]["name_exact_accuracy"], 1.0)
            self.assertEqual(result["scope"]["cv_dir"], "private_test_corpus/cvs")
            self.assertTrue((reports_dir / "latest.csv").exists())
            self.assertTrue((reports_dir / "latest.json").exists())
            report_json = (reports_dir / "latest.json").read_text(encoding="utf-8")
            self.assertNotIn("Jane Doe\nEmail", report_json)

    def test_run_fails_when_thresholds_are_not_met(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cv_dir, expected_dir, reports_dir = self._write_synthetic_case(root)

            result = CVParserAuditService.run(
                str(cv_dir),
                str(expected_dir),
                str(reports_dir / "latest.csv"),
                thresholds={"skill_recall": 1.1},
            )

            self.assertFalse(result["ok"])
            self.assertEqual(result["reasons"]["threshold_failed:skill_recall"], 1)
