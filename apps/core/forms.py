from django import forms
from apps.core.models import ContactMessage


class ContactForm(forms.ModelForm):
    website = forms.CharField(required=False, widget=forms.HiddenInput())
    subject = forms.ChoiceField(
        choices=[
            ("", "Sélectionnez un motif"),
            ("Compte", "Compte"),
            ("Analyse CV", "Analyse CV"),
            ("Problème offre", "Problème d'offre"),
            ("Partenariat", "Partenariat"),
            ("Autre", "Autre"),
        ],
        required=True,
    )

    class Meta:
        model = ContactMessage
        fields = ["name", "email", "subject", "message"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "input", "autocomplete": "name"}),
            "email": forms.EmailInput(attrs={"class": "input", "autocomplete": "email"}),
            "message": forms.Textarea(
                attrs={
                    "class": "textarea",
                    "placeholder": "Écrivez votre message ici...",
                    "rows": 5,
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["subject"].widget.attrs.update({"class": "select"})

    def clean(self):
        cleaned_data = super().clean()
        website = cleaned_data.get('website')
        if website:
            raise forms.ValidationError("Soumission invalide.")
        return cleaned_data
