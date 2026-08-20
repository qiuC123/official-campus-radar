from django import forms

from radar.models import ApplicationProgress, RecruitmentNotice


class NoticeFilterForm(forms.Form):
    company = forms.CharField(required=False)
    company_type = forms.CharField(required=False)
    industry = forms.CharField(required=False)
    recruitment_type = forms.CharField(required=False)
    target_audience = forms.CharField(required=False)
    city = forms.ChoiceField(required=False, choices=[("", "全部城市"), ("北京", "北京"), ("上海", "上海"), ("广州", "广州"), ("深圳", "深圳")])
    position = forms.CharField(required=False)
    deadline_before = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    status = forms.ChoiceField(required=False, choices=[("", "招聘中")] + list(RecruitmentNotice.Status.choices))


class ApplicationProgressForm(forms.ModelForm):
    class Meta:
        model = ApplicationProgress
        fields = ["status"]
