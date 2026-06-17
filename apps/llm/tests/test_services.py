from unittest.mock import patch
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.llm.models import LLMRequestLog
from apps.llm.services.extraction import suggest_cv_extraction
from apps.llm.services.explanation import explain_match
from apps.llm.services.safety import mask_sensitive_data
from apps.llm.services.suggestions import suggest_skills
from apps.llm.tasks import run_llm_request_task

User = get_user_model()


class LLMServicesTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(email="test@example.test")
        self.user.set_password("password123")
        self.user.save()

    @patch("apps.llm.services.extraction.OpenRouterClient")
    def test_suggest_cv_extraction_success(self, mock_client_class):
        mock_client = mock_client_class.return_value
        mock_client.chat.return_value = ('{"skills": ["Python"]}', {"total_tokens": 15})
        mock_client.default_model = "test-model"

        result = suggest_cv_extraction(
            "My CV with Python, test@example.test, +216 12 345 678",
            self.user,
        )
        self.assertEqual(result, {"skills": ["Python"]})
        sent_messages = mock_client.chat.call_args.args[0]
        self.assertNotIn("test@example.test", sent_messages[1]["content"])
        self.assertNotIn("+216 12 345 678", sent_messages[1]["content"])
        
        log = LLMRequestLog.objects.first()
        self.assertIsNotNone(log)
        self.assertEqual(log.purpose, "cv_extraction")
        self.assertEqual(log.status, "success")
        self.assertEqual(log.user, self.user)

    @patch("apps.llm.services.extraction.OpenRouterClient")
    def test_suggest_cv_extraction_error(self, mock_client_class):
        mock_client = mock_client_class.return_value
        mock_client.chat.side_effect = Exception("API down")
        mock_client.default_model = "test-model"

        result = suggest_cv_extraction("My CV with Python", self.user)
        self.assertEqual(result, {})
        
        log = LLMRequestLog.objects.first()
        self.assertIsNotNone(log)
        self.assertEqual(log.status, "error")
        self.assertIn("API down", log.error_message)

    @patch("apps.llm.services.explanation.OpenRouterClient")
    def test_explain_match_success(self, mock_client_class):
        mock_client = mock_client_class.return_value
        mock_client.chat.return_value = ("Good match", {"total_tokens": 10})
        mock_client.default_model = "test-model"

        result = explain_match("Profile", "Job", 80, "None", self.user)
        self.assertEqual(result, "Good match")
        
        log = LLMRequestLog.objects.first()
        self.assertEqual(log.purpose, "match_explanation")
        self.assertEqual(log.status, "success")

    @patch("apps.llm.services.suggestions.OpenRouterClient")
    def test_suggest_skills_success(self, mock_client_class):
        mock_client = mock_client_class.return_value
        mock_client.chat.return_value = ("Learn Docker", {"total_tokens": 5})
        mock_client.default_model = "test-model"

        result = suggest_skills("Docker", "DevOps Engineer", self.user)
        self.assertEqual(result, "Learn Docker")

        log = LLMRequestLog.objects.first()
        self.assertEqual(log.purpose, "skill_suggestion")
        self.assertEqual(log.status, "success")

    @patch("apps.llm.tasks.run_llm_request")
    def test_run_llm_request_task_delegates_to_service(self, mock_run_llm_request):
        mock_run_llm_request.return_value = "Response"
        messages = [{"role": "user", "content": "hi"}]
        result = run_llm_request_task(self.user.id, "test_task", messages)
        self.assertEqual(result, "Response")
        mock_run_llm_request.assert_called_once_with(
            self.user.id,
            "test_task",
            messages,
            model=None,
        )

    def test_mask_sensitive_data_removes_direct_identifiers(self):
        masked = mask_sensitive_data(
            "Email test@example.test phone +216 12 345 678 portfolio https://example.test/me"
        )

        self.assertNotIn("test@example.test", masked)
        self.assertNotIn("+216 12 345 678", masked)
        self.assertNotIn("https://example.test/me", masked)
        self.assertIn("[email redacted]", masked)
        self.assertIn("[phone redacted]", masked)
        self.assertIn("[url redacted]", masked)
