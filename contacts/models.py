from django.db import models
from django.utils import timezone
import uuid


def generate_customer_id():
    """Generate a unique customer ID in format: CUST-{12-char-hex-uppercase}"""
    return f"CUST-{uuid.uuid4().hex[:12].upper()}"


class Address(models.Model):
    street = models.CharField(max_length=255)
    street_number = models.CharField(max_length=50)
    city_code = models.CharField(max_length=20)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)

    class Meta:
        db_table = 'address'

    def __str__(self):
        return f"{self.street} {self.street_number}, {self.city}, {self.country}"


class AppUser(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True)
    customer_id = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        default=generate_customer_id,
        editable=False,
        help_text="Automatically generated unique customer identifier"
    )
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    created = models.DateTimeField(default=timezone.now, db_index=True)
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    birthday = models.DateField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        db_table = 'appuser'

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.customer_id})"


class CustomerRelationship(models.Model):
    appuser = models.OneToOneField(AppUser, on_delete=models.CASCADE, related_name='relationship')
    points = models.IntegerField(default=0, db_index=True)
    created = models.DateTimeField(default=timezone.now, db_index=True)
    last_activity = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = 'customer_relationship'

    def __str__(self):
        return f"Relationship for {self.appuser.customer_id} - {self.points} points"
