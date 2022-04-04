from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm
from django import forms
from .models import User

class RegistrationForm(UserCreationForm):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields['user_name'].widget.attrs.update({
            'id': "text18",
            'maxlength': "100",
            'type': "text",
        }) 
        self.fields['user_name'].label = 'USERNAME'
        self.fields['user_name'].help_text = 'Required. 100 characters or fewer. Letters, digits and @/./+/-/_ only.'
        email = forms.EmailField(max_length=100, help_text="Enter a valid email adress.")
        self.fields['email'].widget.attrs.update({
            'id': "text18",
            'maxlength':"100",
            'type':"email",
        })
        self.fields['email'].label = 'EMAIL'
        self.fields['email'].help_text = 'Enter a valid email adress.'
        self.fields['password1'].widget.attrs.update({
            'id': "text18",
            'maxlength':"254",
            'type':"password",
        })
        self.fields['password1'].label = 'Password'
        self.fields['password1'].help_text = 'Enter a strong password.'
        self.fields['password2'].widget.attrs.update({
            'id': "text18",
            'maxlength':"254",
            'type':"password",
        })
        self.fields['password2'].label = 'Confirm Password'
        self.fields['password2'].help_text = 'Repeat your password.'

    class Meta:
        model = User
        fields = ("email", "user_name", 
                  "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.email = self.cleaned_data.get('email')
        user.user_name = self.cleaned_data.get('user_name')

        if commit:
            user.save()
        return user

class UserLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'id': "text18",
            'type': "text",
        }) 
        self.fields['username'].label = 'EMAIL'

        self.fields['password'].widget.attrs.update({
            'id': "text18",
            'type': "text",
        }) 
        self.fields['password'].label = 'PASSWORD'

class UserCangeForm(UserChangeForm):
    pass