from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django import forms
from .models import User

class RegistrationForm(UserCreationForm):
    """Registration from for user creation

    Inheritance:
        UserCreationForm (Class): Basic form for user registration
    """
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields['user_name'].widget.attrs.update({
            'maxlength': "100",
            'type': "text",
        }) 
        self.fields['user_name'].label = 'USERNAME'
        self.fields['user_name'].help_text = 'Required. 100 characters or fewer. Letters, digits and @/./+/-/_ only.'
        email = forms.EmailField(max_length=100, help_text="Enter a valid email adress.")
        self.fields['email'].widget.attrs.update({
            'maxlength':"100",
            'type':"email",
        })
        self.fields['email'].label = 'EMAIL'
        self.fields['email'].help_text = 'Enter a valid email adress.'
        self.fields['password1'].widget.attrs.update({
            'maxlength':"254",
            'type':"password",
        })
        self.fields['password1'].label = 'PASSWORD'
        self.fields['password1'].help_text = 'Enter a strong password.'
        self.fields['password2'].widget.attrs.update({
            'maxlength':"254",
            'type':"password",
        })
        self.fields['password2'].label = 'CONFIRM PASSWORD'
        self.fields['password2'].help_text = 'Repeat your password.'

    class Meta:
        model = User
        fields = ("email", "user_name", 
                  "password1", "password2")

    def save(self, commit=True):
        """Saves the data from the form

        Args:
            commit (bool, optional): Save the data. Defaults to True.

        Returns:
            User: user data
        """
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.email = self.cleaned_data.get('email')
        user.user_name = self.cleaned_data.get('user_name')

        if commit:
            user.save()
        return user

class UserLoginForm(AuthenticationForm):
    """Login form for user authentification

    Inheritance:
        AuthenticationForm (Class): Basic authentification form
    """
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'type': "text",
        }) 
        self.fields['username'].label = 'EMAIL'

        self.fields['password'].widget.attrs.update({
            'type': "text",
        }) 
        self.fields['password'].label = 'PASSWORD'
