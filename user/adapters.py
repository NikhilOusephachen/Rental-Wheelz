from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from .models import UserType


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    print("hi")

    def save_user(self, request, sociallogin, form=None):
        # Call the default implementation, which creates the user
        user = super().save_user(request, sociallogin, form)

        # Automatically set usertype to 'Customer' if not already set
        if user.usertype is None:
            try:
                user_type = "Customer"
                customer_usertype = UserType.objects.get(name=user_type)
                user.usertype = customer_usertype
                user.save()
            except UserType.DoesNotExist:
                pass  # Handle if the 'Customer' UserType doesn't exist

        return user
