from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from .models import Profile


class CustomUserCreationForm(UserCreationForm):
    # این فرم مربوط به مدل User است فقط این فیلدها را نشان بده
    # فرم را از روی مدل User بساز
    class Meta:
        model = User
        # فیلدهایی که در فرم ثبت‌نام نمایش داده می‌شوند
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):

        # گرفتن User ساخته‌شده توسط فرم اصلی Django
        user = super().save(commit=False)

        # اضافه کردن ایمیل (چون Django پیش‌فرض ایمیل را مدیریت نمی‌کند)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


# Validation settings
ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"]
MAX_AVATAR_SIZE = 2 * 1024 * 1024  # 2MB


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("username", "email")

    # وقتی فرم ساخته می‌شود، این تابع خودکار اجرا می‌شود
    def __init__(self, *args, **kwargs):
        # اول فرم اصلی Django ساخته شود، بعد من تغییرش بدهم
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            # به HTML input یک کلاس CSS اضافه کن
            f.widget.attrs.update({"class": "form-input"})


#این فرم اجازه آپلود عکس می‌دهد ولی قبل از ذخیره، هم سایز و هم نوع فایل را چک می‌کند
class ProfileUpdateForm(forms.ModelForm):
    # یک فیلد آپلود عکس به فرم اضافه کن (ولی اجباری نیست)
    avatar = forms.ImageField(required=False)

    class Meta:
        model = Profile
        fields = ['bio']
        widgets = {
            # bio تبدیل به textarea, شود, 4 خطی باشد CSS داشته باشد
            'bio': forms.Textarea(attrs={'class': 'form-input', 'rows': 4}),
        }

    #وقتی فرم ساخته می‌شود، این تابع خودکار اجرا می‌شود
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs.update({"class": "form-input"})

        self.fields["avatar"].widget.attrs.update({
            "class": "form-input",
            "accept": "image/png,image/jpeg,image/webp",
        })

    # وقتی کاربر عکس آپلود کرد، قبل از ذخیره اینجا بررسی کن
    def clean_avatar(self):
        avatar = self.cleaned_data.get("avatar")
        if not avatar:
            return avatar

        # size check
        if avatar.size > MAX_AVATAR_SIZE:
            raise forms.ValidationError("You Can Not Upload An Avatar More Than 2 mb.")

        # content-type check (MIME)
        content_type = getattr(avatar, "content_type", None)
        if content_type not in ALLOWED_IMAGE_TYPES:
            raise forms.ValidationError("Only jpg, png, webp are allowed.")

        return avatar