from django.test import TestCase
from django.contrib.auth import get_user_model

# Create your tests here.
class UserAccountTests(TestCase):

    def test_new_superuser(self):
        db = get_user_model()
        super_user = db.objects.create_superuser("testuser@super.com", "password", "username")
        self.assertEqual(super_user.email, 'testuser@super.com')
        self.assertEqual(super_user.user_name, 'username')
        self.assertTrue(super_user.is_superuser)
        self.assertTrue(super_user.is_staff)
        self.assertTrue(super_user.is_active)
        self.assertEqual(str(super_user), "username")

        with self.assertRaises(ValueError):
            db.objects.create_superuser(
                email='testuser@super.com', user_name='username1', password='password', is_superuser=False)

        with self.assertRaises(ValueError):
            db.objects.create_superuser(
                email='testuser@super.com', user_name='username1', password='password', is_staff=False)

        with self.assertRaises(ValueError):
            db.objects.create_superuser(
                email='', user_name='username1', password='password', is_superuser=True)

    def test_new_user(self):
        db = get_user_model()
        user = db.objects.create_user(
            'testuser@user.com', 'username', 'password')
        self.assertEqual(user.email, 'testuser@user.com')
        self.assertEqual(user.user_name, 'username')
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_active)

        with self.assertRaises(ValueError):
            db.objects.create_user(
                email='', user_name='a', first_name='first_name', password='password')