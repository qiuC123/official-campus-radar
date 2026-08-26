from django import forms

from radar.models import ApplicationProgress


class ApplicationProgressForm(forms.ModelForm):
    class Meta:
        model = ApplicationProgress
        fields = ["status"]
