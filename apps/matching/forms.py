from django import forms
import re

class QuickMatchForm(forms.Form):
    EXPERIENCE_CHOICES = [
        ('', '---'),
        ('intern', 'Internship / Student'),
        ('junior', 'Junior (0-2 years)'),
        ('mid', 'Mid-Level (2-5 years)'),
        ('senior', 'Senior (5+ years)'),
    ]

    FRENCH_CHOICES = [
        ('', '---'),
        ('none', 'None'),
        ('basic', 'Basic (A1/A2)'),
        ('intermediate', 'Intermediate (B1/B2)'),
        ('advanced', 'Advanced (C1)'),
        ('fluent', 'Fluent / Native (C2)'),
    ]

    skills = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'e.g., Python, React, PostgreSQL'}),
        required=True,
        max_length=3000,
        help_text="Enter your main skills separated by commas or newlines."
    )
    experience_level = forms.ChoiceField(
        choices=EXPERIENCE_CHOICES,
        required=True,
        label="Experience Level"
    )
    french_level = forms.ChoiceField(
        choices=FRENCH_CHOICES,
        required=False,
        label="French Level"
    )

    def clean_skills(self):
        raw_skills = self.cleaned_data.get('skills', '')
        skills_list = [s.strip() for s in re.split(r'[,\n]+', raw_skills) if s.strip()]
        
        if len(skills_list) > 30:
            raise forms.ValidationError("You cannot enter more than 30 skills.")
            
        for skill in skills_list:
            if len(skill) > 80:
                raise forms.ValidationError(f"Skill '{skill[:20]}...' is too long (max 80 characters).")
                
        return skills_list
