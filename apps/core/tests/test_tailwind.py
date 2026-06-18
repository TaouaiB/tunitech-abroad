import os
from pathlib import Path
from django.test import TestCase
from django.conf import settings

class TailwindConfigurationTests(TestCase):
    def test_tailwind_cdn_removed(self):
        """Verify the Tailwind CDN has been removed from base.html."""
        base_html_path = Path(settings.BASE_DIR) / "templates" / "base.html"
        self.assertTrue(base_html_path.exists())
        
        with open(base_html_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        self.assertNotIn("cdn.tailwindcss.com", content, "Tailwind CDN should not be present in base.html")
        
    def test_local_css_referenced(self):
        """Verify that the local compiled CSS is referenced in base.html."""
        base_html_path = Path(settings.BASE_DIR) / "templates" / "base.html"
        
        with open(base_html_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        self.assertIn("css/app.css", content, "Local compiled CSS should be referenced in base.html")
        
    def test_compiled_css_exists(self):
        """Verify that the compiled CSS file exists."""
        css_path = Path(settings.BASE_DIR) / "static" / "css" / "app.css"
        self.assertTrue(css_path.exists(), "Compiled CSS file should exist at static/css/app.css")
