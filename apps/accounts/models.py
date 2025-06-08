from django.contrib.auth.models import User
from django.db import models

# If you need to extend the User model in the future, use this:
# class Profile(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)
#     # Add additional fields here 