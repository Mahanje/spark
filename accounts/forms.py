from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from .models import Profile


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs.update({"class": "form-input"})


class ProfileUpdateForm(forms.ModelForm):
    avatar = forms.ImageField(required=False)

    class Meta:
        model = Profile
        fields = ['bio']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-input', 'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs.update({"class": "form-input"})

        self.fields["avatar"].widget.attrs.update({
            "class": "form-input",
            "accept": "image/png,image/jpeg,image/webp",
        })

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