from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from accounts.models import Admin

class EmailOrPhoneBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()
        try:
            # Try to find user by email or phone_number
            user = User.objects.filter(email=username).first()
            if not user:
                admin = Admin.objects.filter(phone_number=username).first()
                if admin:
                    user = admin.user
            if user and user.check_password(password):
                return user
        except User.DoesNotExist:
            return None
        return None