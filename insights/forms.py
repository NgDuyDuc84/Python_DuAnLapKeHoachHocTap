from django import forms


class AnalyzeForm(forms.Form):
    preview = forms.CharField(widget=forms.HiddenInput)
    consent = forms.BooleanField(
        label="Tôi đồng ý gửi dữ liệu trên đến Groq để phân tích.",
    )
