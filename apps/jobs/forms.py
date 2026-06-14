from django import forms


class JobSearchForm(forms.Form):
    q = forms.CharField(required=False)
    location = forms.CharField(required=False)
    contract_type = forms.CharField(required=False)
    job_type = forms.CharField(required=False)
    remote_type = forms.CharField(required=False)
    experience_level = forms.CharField(required=False)
    skill = forms.CharField(required=False)
    sort = forms.CharField(required=False)
    page = forms.CharField(required=False)
    page_size = forms.CharField(required=False)
