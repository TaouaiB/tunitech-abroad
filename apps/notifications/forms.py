from django import forms

class EmailPreferenceForm(forms.Form):
    weekly_digest_enabled = forms.BooleanField(required=False, label="Weekly Recommendation Digest")
    product_updates_enabled = forms.BooleanField(required=False, label="Product Updates")
    cv_analysis_email_enabled = forms.BooleanField(required=False, label="CV Analysis Alerts")
