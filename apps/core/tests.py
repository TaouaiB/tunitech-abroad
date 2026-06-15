from django.test import TestCase
from .models import SystemSetting
from .services.system_setting import SystemSettingService

class CoreTests(TestCase):
    def test_system_setting_creation_and_lookup(self):
        SystemSetting.objects.create(key="max_upload_size", value={"mb": 5})
        
        val = SystemSettingService.get_value("max_upload_size")
        self.assertEqual(val, {"mb": 5})
        
        default_val = SystemSettingService.get_value("missing_key", default="fallback")
        self.assertEqual(default_val, "fallback")
