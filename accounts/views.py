from django.contrib.auth.decorators import login_required
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import RegistrationForm


class RegisterView(SuccessMessageMixin, CreateView):
    form_class = RegistrationForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("accounts:login")
    success_message = "Tạo tài khoản thành công. Hãy đăng nhập để tiếp tục."

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("core:home")
        return super().dispatch(request, *args, **kwargs)


@login_required
def profile(request):
    return render(request, "accounts/profile.html")
