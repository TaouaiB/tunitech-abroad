import csv
import json
import os
import re
from pathlib import Path
from typing import Any

from django.utils import timezone

from apps.cvs.services.deterministic_extractor import CVDeterministicExtractorService
from apps.cvs.services.text_extraction import CVTextExtractionService


class CVParserAuditService:
    DEFAULT_THRESHOLDS = {
        "name_exact_accuracy": 0.85,
        "name_acceptable_accuracy": 0.90,
        "email_accuracy": 0.90,
        "phone_accuracy": 0.80,
        "skill_precision": 0.80,
        "skill_recall": 0.60,
        "false_skill_rate": 0.20,
    }

    @classmethod
    def run(
        cls,
        cv_dir: str,
        expected_dir: str,
        output_path: str,
        thresholds: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        effective_thresholds = {**cls.DEFAULT_THRESHOLDS, **(thresholds or {})}
        cv_path = Path(cv_dir)
        expected_path = Path(expected_dir)
        csv_path, json_path = cls._report_paths(output_path)
        scope = {
            "cv_dir": cls._safe_scope_path(cv_path),
            "expected_dir": cls._safe_scope_path(expected_path),
            "output": cls._safe_scope_path(csv_path),
        }
        counts: dict[str, int | float] = {
            "cv_count": 0,
            "passed_count": 0,
            "failed_count": 0,
            "low_confidence_count": 0,
            "parse_failed_count": 0,
        }
        statuses: dict[str, int] = {"passed": 0, "failed": 0, "parse_failed": 0}
        reasons: dict[str, int] = {}
        errors: list[str] = []
        warnings: list[str] = []
        cases: list[dict[str, Any]] = []

        if not cv_path.exists() or not cv_path.is_dir():
            errors.append("cv_dir_missing")
            return cls._response(False, scope, counts, statuses, reasons, warnings, errors, effective_thresholds)
        if not expected_path.exists() or not expected_path.is_dir():
            errors.append("expected_dir_missing")
            return cls._response(False, scope, counts, statuses, reasons, warnings, errors, effective_thresholds)

        expected_by_case = cls._load_expected(expected_path)
        pdfs = sorted(path for path in cv_path.iterdir() if path.suffix.lower() == ".pdf")
        if not pdfs:
            errors.append("no_pdf_cases_found")
            return cls._response(False, scope, counts, statuses, reasons, warnings, errors, effective_thresholds)

        totals = {
            "name_expected": 0,
            "name_exact": 0,
            "name_acceptable": 0,
            "email_expected": 0,
            "email_correct": 0,
            "phone_expected": 0,
            "phone_correct": 0,
            "expected_skills": 0,
            "actual_skills": 0,
            "true_positive_skills": 0,
            "false_positive_skills": 0,
        }

        for pdf in pdfs:
            case_id = pdf.stem
            counts["cv_count"] += 1
            expected = expected_by_case.get(case_id, {})
            if not expected:
                warnings.append(f"missing_expected:{case_id}")

            text_result = CVTextExtractionService.extract_from_path(str(pdf))
            if not text_result["success"]:
                counts["parse_failed_count"] += 1
                counts["failed_count"] += 1
                statuses["parse_failed"] += 1
                cls._increment(reasons, "text_extraction_failed")
                cases.append({"case_id": case_id, "passed": False, "failure_reasons": ["text_extraction_failed"], "name_confidence": 0})
                continue

            actual = CVDeterministicExtractorService.extract(text_result["raw_text"])
            if actual.get("name_confidence", 0) < 70:
                counts["low_confidence_count"] += 1

            case = cls._compare_case(case_id, expected, actual, totals)
            cases.append(case)
            if case["passed"]:
                counts["passed_count"] += 1
                statuses["passed"] += 1
            else:
                counts["failed_count"] += 1
                statuses["failed"] += 1
                for reason in case["failure_reasons"]:
                    cls._increment(reasons, reason)

        metrics = cls._metrics(totals, counts)
        counts.update(metrics)
        threshold_failures = cls._threshold_failures(metrics, effective_thresholds)
        for failure in threshold_failures:
            cls._increment(reasons, failure)

        csv_path.parent.mkdir(parents=True, exist_ok=True)
        cls._write_csv(csv_path, cases)
        cls._write_json(
            json_path,
            {
                "generated_at": timezone.now().isoformat(),
                "thresholds": effective_thresholds,
                "counts": counts,
                "statuses": statuses,
                "reasons": reasons,
                "cases": cases,
            },
        )

        ok = not errors and counts["parse_failed_count"] == 0 and not threshold_failures
        return cls._response(
            ok,
            scope,
            counts,
            statuses,
            reasons,
            warnings,
            errors,
            effective_thresholds,
            recommended_actions=["review_failed_cases"] if not ok else [],
            artifacts={"report_csv": csv_path.name, "report_json": json_path.name},
            top_items=cases[:10],
        )

    @classmethod
    def _compare_case(cls, case_id: str, expected: dict[str, Any], actual: dict[str, Any], totals: dict[str, int]) -> dict[str, Any]:
        failure_reasons: list[str] = []
        expected_name = cls._clean_str(expected.get("name") or expected.get("extracted_name"))
        expected_names = {expected_name.lower()} if expected_name else set()
        expected_names.update(cls._clean_str(name).lower() for name in expected.get("acceptable_names", []) if cls._clean_str(name))
        actual_name = cls._clean_str(actual.get("extracted_name"))

        name_exact = True
        name_acceptable = True
        if expected_name:
            totals["name_expected"] += 1
            name_exact = actual_name.lower() == expected_name.lower()
            name_acceptable = actual_name.lower() in expected_names
            totals["name_exact"] += int(name_exact)
            totals["name_acceptable"] += int(name_acceptable)
            if not name_acceptable:
                failure_reasons.append("name_mismatch")
        elif actual_name and actual.get("name_confidence", 0) >= 70:
            failure_reasons.append("unexpected_confident_name")

        email_correct = cls._compare_optional_text(
            expected,
            actual,
            expected_keys=("email", "extracted_email"),
            actual_key="extracted_email",
            totals=totals,
            expected_total_key="email_expected",
            correct_key="email_correct",
            failure_reasons=failure_reasons,
            failure_reason="email_mismatch",
        )
        phone_correct = cls._compare_optional_text(
            expected,
            actual,
            expected_keys=("phone", "extracted_phone"),
            actual_key="extracted_phone",
            totals=totals,
            expected_total_key="phone_expected",
            correct_key="phone_correct",
            failure_reasons=failure_reasons,
            failure_reason="phone_mismatch",
            normalizer=cls._digits_only,
        )

        expected_skills = cls._normalize_skill_set(expected.get("skills") or expected.get("raw_skills") or [])
        actual_skills = cls._normalize_skill_set(actual.get("raw_skills") or [])
        true_positive_skills = expected_skills.intersection(actual_skills)
        false_positive_skills = actual_skills - expected_skills
        totals["expected_skills"] += len(expected_skills)
        totals["actual_skills"] += len(actual_skills)
        totals["true_positive_skills"] += len(true_positive_skills)
        totals["false_positive_skills"] += len(false_positive_skills)

        return {
            "case_id": case_id,
            "passed": not failure_reasons,
            "failure_reasons": failure_reasons,
            "name_exact": name_exact,
            "name_acceptable": name_acceptable,
            "email_correct": email_correct,
            "phone_correct": phone_correct,
            "name_confidence": actual.get("name_confidence", 0),
            "skill_true_positive_count": len(true_positive_skills),
            "skill_false_positive_count": len(false_positive_skills),
            "expected_skill_count": len(expected_skills),
            "actual_skill_count": len(actual_skills),
            "warnings": actual.get("warnings", []),
        }

    @classmethod
    def _compare_optional_text(cls, expected: dict[str, Any], actual: dict[str, Any], *, expected_keys: tuple[str, ...], actual_key: str, totals: dict[str, int], expected_total_key: str, correct_key: str, failure_reasons: list[str], failure_reason: str, normalizer=None) -> bool:
        normalizer = normalizer or cls._clean_str
        expected_value = ""
        for key in expected_keys:
            expected_value = cls._clean_str(expected.get(key))
            if expected_value:
                break
        if not expected_value:
            return True
        totals[expected_total_key] += 1
        is_correct = normalizer(actual.get(actual_key, "")) == normalizer(expected_value)
        totals[correct_key] += int(is_correct)
        if not is_correct:
            failure_reasons.append(failure_reason)
        return is_correct

    @classmethod
    def _metrics(cls, totals: dict[str, int], counts: dict[str, int | float]) -> dict[str, float]:
        skill_precision = cls._ratio(totals["true_positive_skills"], totals["actual_skills"])
        return {
            "name_exact_accuracy": cls._ratio(totals["name_exact"], totals["name_expected"]),
            "name_acceptable_accuracy": cls._ratio(totals["name_acceptable"], totals["name_expected"]),
            "email_accuracy": cls._ratio(totals["email_correct"], totals["email_expected"]),
            "phone_accuracy": cls._ratio(totals["phone_correct"], totals["phone_expected"]),
            "skill_precision": skill_precision,
            "skill_recall": cls._ratio(totals["true_positive_skills"], totals["expected_skills"]),
            "false_skill_rate": round(1 - skill_precision, 4) if totals["actual_skills"] else 0.0,
            "low_confidence_rate": cls._ratio(int(counts["low_confidence_count"]), int(counts["cv_count"])),
        }

    @staticmethod
    def _threshold_failures(metrics: dict[str, float], thresholds: dict[str, float]) -> list[str]:
        failures: list[str] = []
        for metric, threshold in thresholds.items():
            actual = metrics.get(metric)
            if actual is None:
                continue
            if metric == "false_skill_rate":
                if actual > threshold:
                    failures.append(f"threshold_failed:{metric}")
            elif actual < threshold:
                failures.append(f"threshold_failed:{metric}")
        return failures

    @staticmethod
    def _load_expected(expected_dir: Path) -> dict[str, dict[str, Any]]:
        expected_by_case: dict[str, dict[str, Any]] = {}
        for path in sorted(expected_dir.glob("*.json")):
            with path.open(encoding="utf-8") as handle:
                data = json.load(handle)
            if isinstance(data, dict) and "case_id" in data:
                expected_by_case[str(data["case_id"])] = data
            elif isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, dict):
                        expected_by_case[Path(key).stem] = value
        return expected_by_case

    @staticmethod
    def _report_paths(output_path: str) -> tuple[Path, Path]:
        output = Path(output_path)
        if output.suffix.lower() == ".csv":
            return output, output.with_suffix(".json")
        if output.suffix.lower() == ".json":
            return output.with_suffix(".csv"), output
        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
        return output / f"audit_report_{timestamp}.csv", output / f"audit_report_{timestamp}.json"

    @staticmethod
    def _write_csv(path: Path, cases: list[dict[str, Any]]) -> None:
        fieldnames = [
            "case_id",
            "passed",
            "failure_reasons",
            "name_exact",
            "name_acceptable",
            "email_correct",
            "phone_correct",
            "name_confidence",
            "skill_true_positive_count",
            "skill_false_positive_count",
            "expected_skill_count",
            "actual_skill_count",
        ]
        with path.open("w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for case in cases:
                writer.writerow({key: case.get(key, "") for key in fieldnames})

    @staticmethod
    def _write_json(path: Path, payload: dict[str, Any]) -> None:
        with path.open("w", encoding="utf-8") as jsonfile:
            json.dump(payload, jsonfile, indent=2, ensure_ascii=False)

    @staticmethod
    def _response(ok: bool, scope: dict[str, Any], counts: dict[str, int | float], statuses: dict[str, int], reasons: dict[str, int], warnings: list[str], errors: list[str], thresholds: dict[str, float], *, recommended_actions: list[str] | None = None, artifacts: dict[str, str] | None = None, top_items: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        return {
            "ok": ok,
            "service": "cv_parser_audit",
            "generated_at": timezone.now().isoformat(),
            "scope": scope,
            "counts": counts,
            "statuses": statuses,
            "reasons": reasons,
            "top_items": top_items or [],
            "warnings": warnings,
            "errors": errors,
            "recommended_actions": recommended_actions or [],
            "artifacts": artifacts or {},
            "thresholds": thresholds,
        }

    @staticmethod
    def _safe_scope_path(path: Path) -> str:
        parts = path.parts
        if "private_test_corpus" in parts:
            index = parts.index("private_test_corpus")
            return os.path.join(*parts[index:])
        return path.name

    @staticmethod
    def _normalize_skill_set(values: list[Any]) -> set[str]:
        return {str(value).strip().lower() for value in values if str(value).strip()}

    @staticmethod
    def _clean_str(value: Any) -> str:
        return str(value or "").strip()

    @staticmethod
    def _digits_only(value: Any) -> str:
        return re.sub(r"\D", "", str(value or ""))

    @staticmethod
    def _ratio(numerator: int, denominator: int) -> float:
        if denominator == 0:
            return 1.0
        return round(numerator / denominator, 4)

    @staticmethod
    def _increment(bucket: dict[str, int], key: str) -> None:
        bucket[key] = bucket.get(key, 0) + 1
