from django.test import TestCase
from django.conf import settings
from django.utils.module_loading import import_string

class CeleryBeatScheduleTests(TestCase):
    def test_celery_beat_schedule_is_configured(self):
        self.assertTrue(hasattr(settings, 'CELERY_BEAT_SCHEDULE'))
        self.assertTrue(len(settings.CELERY_BEAT_SCHEDULE) > 0)

    def test_scheduled_tasks_are_valid(self):
        for schedule_name, schedule_config in settings.CELERY_BEAT_SCHEDULE.items():
            task_name = schedule_config.get('task')
            self.assertIsNotNone(task_name, f"Schedule '{schedule_name}' has no task defined.")
            
            # Verify the task actually exists and is a Celery task
            try:
                task_func = import_string(task_name)
                self.assertTrue(hasattr(task_func, 'delay'), f"'{task_name}' does not appear to be a celery task.")
            except ImportError:
                self.fail(f"Scheduled task '{task_name}' could not be imported.")
