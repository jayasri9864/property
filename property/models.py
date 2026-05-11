from django.db import models
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.auth.hashers import make_password

from django.db import models
from django.contrib.auth.models import User

class Property(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('sold', 'Sold'),
        ('rented', 'Rented'),
    ]
    name     = models.CharField(max_length=200)
    location = models.CharField(max_length=300, blank=True)
    price    = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status   = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')

    def __str__(self):
        return self.name

class Transaction(models.Model):
    TYPE_CHOICES = [
        ('buy',  'Buy'),
        ('rent', 'Rent'),
        ('sell', 'Sell'),
    ]
    user             = models.ForeignKey(User, on_delete=models.CASCADE)
    property         = models.ForeignKey(Property, on_delete=models.CASCADE)
    amount           = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    transaction_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    status           = models.CharField(max_length=20, default='completed')
    transaction_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.property} - {self.transaction_type}"
class BuyerListing(models.Model):
    house_name  = models.CharField(max_length=200)
    owner_name  = models.CharField(max_length=200)
    sqft        = models.PositiveIntegerField()
    price       = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField()
    address     = models.TextField()
    location    = models.CharField(max_length=200)
    house_photo = models.ImageField(upload_to='buyer_photos/', blank=True, null=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.house_name} — ₹{self.price}"

    class Meta:
        ordering = ['-created_at']


class TenantListing(models.Model):
    house_name      = models.CharField(max_length=200)
    owner_name      = models.CharField(max_length=200)
    sqft            = models.PositiveIntegerField()
    rent_amount     = models.DecimalField(max_digits=10, decimal_places=2)
    advance_amount  = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # ✅ NEW
    description     = models.TextField()
    address         = models.TextField()
    location        = models.CharField(max_length=200)
    house_photo     = models.ImageField(upload_to='tenant_photos/', blank=True, null=True)
    tenant_rules    = models.TextField(blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.house_name} — ₹{self.rent_amount}/mo"

    class Meta:
        ordering = ['-created_at']
class UserRegister(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)   # ✅ add this properly
    phone = models.CharField(max_length=15, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.email})"

    class Meta:
        db_table = 'user_register'
        verbose_name = 'User'

class House(models.Model):
    user = models.OneToOneField(
        UserRegister,
        on_delete=models.CASCADE,
        related_name='house'
    )
    house_id = models.CharField(max_length=20, unique=True)  # e.g. HSE-AB12-001
    tenant_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    city = models.CharField(max_length=100)
    floor_unit = models.CharField(max_length=50, blank=True, null=True)
    month = models.IntegerField()  # 1 to 12    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.house_id} — {self.tenant_name}"

    class Meta:
        db_table = 'house'
        verbose_name = 'House'


class Payment(models.Model):
    BILL_TYPES = [
        ('rent', 'Rent'),
        ('eb', 'EB Bill'),
        ('water', 'Water Bill'),
    ]

    user = models.ForeignKey(
        UserRegister,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    house = models.ForeignKey(
        House,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    bill_type = models.CharField(max_length=10, choices=BILL_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    month = models.CharField(max_length=20)   # e.g. "May"
    year = models.IntegerField()              # e.g. 2025
    units_used = models.IntegerField(blank=True, null=True)  # EB bill மட்டும்
    payment_id = models.CharField(max_length=30, unique=True)  # PAY-XXXXXX
    paid_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.payment_id} | {self.bill_type} | {self.month} {self.year}"

    class Meta:
        db_table = 'payment'
        verbose_name = 'Payment'
        # ஒரே month+year+bill_type-க்கு duplicate payment வரக்கூடாது
        unique_together = ('house', 'bill_type', 'month', 'year')
        ordering = ['-paid_on']