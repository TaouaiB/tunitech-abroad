from django import forms
from .models import CVUpload
from django.conf import settings

class CVUploadForm(forms.ModelForm):
    consent_accepted = forms.BooleanField(
        required=True,
        label="I consent to the processing of my CV for profile completion."
    )

    class Meta:
        model = CVUpload
        fields = ['file']
        
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            if file.size > settings.MAX_CV_UPLOAD_SIZE_MB * 1024 * 1024:
                raise forms.ValidationError(f"File size must be under {settings.MAX_CV_UPLOAD_SIZE_MB}MB.")
            if not file.name.lower().endswith('.pdf') or file.content_type != 'application/pdf':
                raise forms.ValidationError("Only PDF files are allowed.")
        return file
