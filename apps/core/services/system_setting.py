from apps.core.models import SystemSetting

class SystemSettingService:
    @staticmethod
    def get_value(key, default=None):
        try:
            setting = SystemSetting.objects.get(key=key, is_active=True)
            return setting.value
        except SystemSetting.DoesNotExist:
            return default
