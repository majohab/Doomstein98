from django.contrib.auth.tokens import PasswordResetTokenGenerator
import six


class TokenGenerator(PasswordResetTokenGenerator):
    """Generates a token for the email verification.

    Inheritance:
        PasswordResetTokenGenerator (Class): Generates one time tokens for password resets.
    """
    def _make_hash_value(self, user, timestamp):
        """Generates a hash value.

        Args:
            user (Object): Currently logged in user
            timestamp (datetime): Current time

        Returns:
            Hash: User and time specific hash to verify email adress
        """
        return (six.text_type(user.pk)+six.text_type(timestamp)+six.text_type(user.is_active))


generate_token = TokenGenerator()