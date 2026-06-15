from django import forms
from .models import CVUpload
from django.conf import settings

class CVUploadForm(forms.ModelForm):
    consent_accepted = forms.BooleanField(
        required=True,
        label="Je consens au traitement de mon CV pour la création de mon profil."
    )

    class Meta:
        model = CVUpload
        fields = ['file']
        
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            if file.size > settings.MAX_CV_UPLOAD_SIZE_MB * 1024 * 1024:
                raise forms.ValidationError(f"La taille du fichier doit être inférieure à {settings.MAX_CV_UPLOAD_SIZE_MB} Mo.")
            if not file.name.lower().endswith('.pdf') or file.content_type != 'application/pdf':
                raise forms.ValidationError("Seuls les fichiers PDF sont autorisés.")
        return file
