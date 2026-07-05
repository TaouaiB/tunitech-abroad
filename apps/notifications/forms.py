from django import forms

class EmailPreferenceForm(forms.Form):
    weekly_digest_enabled = forms.BooleanField(
        required=False,
        label="Résumé hebdomadaire des recommandations"
    )
