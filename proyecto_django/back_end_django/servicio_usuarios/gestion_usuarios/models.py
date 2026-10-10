from django.db import models
import uuid
from django.utils import timezone
from decimal import Decimal

# Create your models here.


class Usuario(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(null=True, blank=True)
    is_superuser = models.BooleanField(default=False)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    username = models.CharField(max_length=20, unique=True)
    email = models.EmailField(max_length=254, unique=True)
    profile_picture = models.CharField(max_length=100, null=True, blank=True)
    email_verified = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    nationality = models.CharField(max_length=7, null=True, blank=True)
    occupation = models.CharField(max_length=17, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    contact_phone_number = models.CharField(max_length=20, null=True, blank=True)
    gender = models.CharField(max_length=6, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    address_number = models.CharField(max_length=25, null=True, blank=True)
    address_interior_number = models.CharField(max_length=26, null=True, blank=True)
    address_complement = models.TextField(null=True, blank=True)
    address_neighborhood = models.CharField(max_length=100, null=True, blank=True)
    address_zip_code = models.CharField(max_length=10, null=True, blank=True)
    address_city = models.CharField(max_length=100, null=True, blank=True)
    address_state = models.CharField(max_length=100, null=True, blank=True)
    role = models.CharField(max_length=24, null=True, blank=True)
    # Se creo esto para el Token
    reset_password_token = models.UUIDField(null=True, blank=True, unique=True)

    reset_password_expires_at = models.DateTimeField(null=True, blank=True)


def __str__(self):
    return self.username
