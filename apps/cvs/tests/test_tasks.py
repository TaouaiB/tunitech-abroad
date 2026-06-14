from unittest.mock import patch
from django.test import TestCase
from apps.cvs.tasks import parse_cv

class CVTaskTests(TestCase):
    @patch('apps.cvs.services.parsing.CVParsingService.parse_by_id')
    def test_parse_cv_task(self, mock_parse):
        parse_cv(1)
        mock_parse.assert_called_once_with(1)
