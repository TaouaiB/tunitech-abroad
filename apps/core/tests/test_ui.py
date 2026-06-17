from django.test import TestCase
from django.template import Context, Template


class UIMessagesTests(TestCase):
    def test_toast_messages_present_in_base_template(self):
        class MockMessage:
            def __init__(self, message, tags):
                self.message = message
                self.tags = tags

            def __str__(self):
                return self.message

        messages = [
            MockMessage("Test success toast", "success"),
            MockMessage("Test error toast", "error")
        ]

        template = Template('''
        {% extends "base.html" %}
        {% block content %}Test{% endblock %}
        ''')

        context = Context({
            "messages": messages,
            "user": None,
        })

        rendered = template.render(context)

        self.assertIn("fixed top-20 right-4 z-50", rendered)
        self.assertIn("setTimeout(() => show = false, 5000)", rendered)
        self.assertIn("Test success toast", rendered)
        self.assertIn("Test error toast", rendered)
        self.assertIn("bg-green-50", rendered)
        self.assertIn("bg-red-50", rendered)
