from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.llm.services.request_runner import run_llm_request
from apps.llm.models import LLMRequestLog
import uuid

User = get_user_model()

class Command(BaseCommand):
    help = 'Run a controlled LLM smoke test'

    def add_arguments(self, parser):
        parser.add_argument('--kind', type=str, default='cv_extraction', help='Kind of test')

    def handle(self, *args, **options):
        kind = options['kind']
        user = User.objects.first()
        if not user:
            self.stdout.write(self.style.ERROR("FAIL: No user found. Exiting."))
            return

        self.stdout.write(f"--- Starting LLM Smoke Test for {kind} ---")
        
        # Use a unique payload to bypass old cache
        unique_token = str(uuid.uuid4())
        messages = [{"role": "user", "content": f"Say 'hello world {unique_token}' exactly"}]

        # Clear previous logs for accurate test (for this specific user and purpose)
        LLMRequestLog.objects.filter(user=user, purpose=kind).delete()

        # Call 1
        self.stdout.write("Call 1: Sending request...")
        try:
            res1 = run_llm_request(user.id, purpose=kind, messages=messages)
            self.stdout.write("Response 1 received (content hidden)")
        except Exception as e:
            # Report the error class and message
            self.stdout.write(self.style.ERROR(f"FAIL: Call 1 Exception: {e.__class__.__name__} - {str(e)}"))
            return

        # Call 2
        self.stdout.write("Call 2: Sending exact same request...")
        try:
            res2 = run_llm_request(user.id, purpose=kind, messages=messages)
            self.stdout.write("Response 2 received (content hidden)")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"FAIL: Call 2 Exception: {e.__class__.__name__} - {str(e)}"))
            return

        # Verification
        log_count = LLMRequestLog.objects.filter(user=user, purpose=kind).count()
        self.stdout.write(f"LLMRequestLog records created for {kind}: {log_count}")
        
        if log_count > 1:
            self.stdout.write(self.style.WARNING("FAIL: Cache failed! More than 1 request logged for same prompt."))
        elif log_count == 1:
            self.stdout.write(self.style.SUCCESS("PASS: Cache worked! Only 1 real request logged."))
        elif log_count == 0:
            self.stdout.write(self.style.WARNING("FAIL: 0 real requests logged. Expected 1 real log if API call was successful."))
        
        self.stdout.write("--- End LLM Smoke Test ---")
