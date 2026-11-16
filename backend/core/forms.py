
from django import forms
from django.contrib.auth.models import User
from PIL import Image, UnidentifiedImageError

from .models import UserProfile


class UserProfileForm(forms.ModelForm):

    first_name = forms.CharField(
        max_length=150,
        required=True
    )

    last_name = forms.CharField(
        max_length=150,
        required=False
    )

    email = forms.EmailField(
        required=True
    )

    class Meta:
        model = UserProfile
        fields = ["profile_image"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

        self.fields["first_name"].initial = self.user.first_name
        self.fields["last_name"].initial = self.user.last_name
        self.fields["email"].initial = self.user.email

    def clean_email(self):
        email = self.cleaned_data["email"].strip()

        if User.objects.filter(
            email__iexact=email
        ).exclude(pk=self.user.pk).exists():
            raise forms.ValidationError(
                "This email address is already registered."
            )

        return email

    def clean_profile_image(self):
        image = self.cleaned_data.get("profile_image")

        if not image:
            return image

        # Maximum upload size: 2 MB
        if image.size > 2 * 1024 * 1024:
            raise forms.ValidationError(
                "Image size must not exceed 2 MB."
            )

        try:
            image.seek(0)

            with Image.open(image) as img:
                if img.format not in ["JPEG", "PNG", "WEBP"]:
                    raise forms.ValidationError(
                        "Only JPG, JPEG, PNG and WEBP images are allowed."
                    )

                width, height = img.size

                if width > 4000 or height > 4000:
                    raise forms.ValidationError(
                        "Image dimensions cannot exceed 4000 × 4000 pixels."
                    )

                img.verify()

            image.seek(0)

        except (UnidentifiedImageError, OSError, ValueError):
            raise forms.ValidationError(
                "Please upload a valid image file."
            )

        return image

    def save(self, commit=True):
        profile = super().save(commit=False)

        self.user.first_name = self.cleaned_data["first_name"].strip()
        self.user.last_name = self.cleaned_data["last_name"].strip()
        self.user.email = self.cleaned_data["email"].strip()

        if commit:
            self.user.save()
            profile.save()

        return profile
