from django import forms


class AnalyzeForm(forms.Form):
    preview = forms.CharField(widget=forms.HiddenInput)
    consent = forms.BooleanField(
        label="Tôi đồng ý gửi bản dữ liệu xem trước dùng mã đến OpenAI để phân tích; yêu cầu có thể phát sinh phí API.",
    )
