"""
Beneficiary management models
"""
from django.db import models
from campaign_os.core.models import BaseModel


class Beneficiary(BaseModel):
    """Scheme/government beneficiary record"""

    GENDER_CHOICES = [('m', 'Male'), ('f', 'Female'), ('o', 'Other')]
    STATUS_CHOICES = [
        ('pending',   'Pending'),
        ('approved',  'Approved'),
        ('received',  'Received'),
        ('rejected',  'Rejected'),
    ]

    name        = models.CharField(max_length=200)
    voter_id    = models.CharField(max_length=20, blank=True, null=True, db_index=True)
    phone       = models.CharField(max_length=20, blank=True, null=True)
    phone2      = models.CharField(max_length=20, blank=True, null=True)
    age         = models.IntegerField(null=True, blank=True)
    gender      = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True)
    address     = models.TextField(blank=True, null=True)
    pincode     = models.CharField(max_length=10, blank=True, null=True)

    # Location
    booth = models.ForeignKey(
        'masters.Booth', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='beneficiary_records', db_constraint=False
    )
    ward = models.ForeignKey(
        'masters.Ward', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='beneficiary_records', db_constraint=False
    )
    block = models.CharField(max_length=100, blank=True, null=True)

    # Scheme info
    scheme = models.ForeignKey(
        'masters.Scheme', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='beneficiary_records', db_constraint=False
    )
    scheme_name   = models.CharField(max_length=200, blank=True, null=True)
    benefit_type   = models.CharField(max_length=200, blank=True, null=True)
    benefit_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', blank=True, null=True)
    benefit_amount = models.CharField(max_length=100, blank=True, null=True)

    source       = models.CharField(max_length=100, blank=True, null=True)
    is_contacted = models.BooleanField(default=False, null=True, blank=True)
    notes        = models.TextField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['booth']),
            models.Index(fields=['benefit_status']),
        ]
        verbose_name = 'Beneficiary'
        verbose_name_plural = 'Beneficiaries'

    def __str__(self):
        return f"{self.name} — {self.scheme_name or (self.scheme.name if self.scheme_id else 'No Scheme')}"
