from django import forms


class AnalyzeForm(forms.Form):
    preview = forms.CharField(widget=forms.HiddenInput)
    consent = forms.BooleanField(
        label="Tôi đồng ý gửi bản dữ liệu xem trước dùng mã đến Groq để phân tích. Gói miễn phí có hạn mức; chỉ gửi khi tôi xác nhận.",
    )
