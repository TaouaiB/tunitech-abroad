from django import forms

class EmailPreferenceForm(forms.Form):
    weekly_digest_enabled = forms.BooleanField(required=False, label="Résumé hebdomadaire des recommandations")
    product_updates_enabled = forms.BooleanField(required=False, label="Mises à jour du produit")
    cv_analysis_email_enabled = forms.BooleanField(required=False, label="Alertes d'analyse de CV")
