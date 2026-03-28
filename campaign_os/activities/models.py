"""
Activity log and field survey models
"""
from django.db import models
from campaign_os.core.models import BaseModel


class ActivityLog(BaseModel):
    """Tracks agent, field, and volunteer activities in the field."""

    CATEGORY_CHOICES = [
        ('agent',     'Agent Activity'),
        ('field',     'Field Activity'),
        ('volunteer', 'Volunteer Activity'),
    ]

    category     = models.CharField(max_length=20, choices=CATEGORY_CHOICES, db_index=True)
    activity_type = models.CharField(max_length=100)
    date         = models.DateField(db_index=True)
    hours_worked = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    village      = models.CharField(max_length=200, blank=True)
    booth_no     = models.CharField(max_length=20, blank=True)
    notes        = models.TextField(blank=True)

    # Who logged it
    username     = models.CharField(max_length=150, blank=True)
    user_role    = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['category', 'date']),
        ]

    def __str__(self):
        return f"{self.get_category_display()} — {self.activity_type} on {self.date}"


class FieldSurvey(BaseModel):
    """Captures field survey data collected during door-to-door voter surveys."""

    YNS_CHOICES = [
        ('Yes',      'Yes'),
        ('No',       'No'),
        ('Not Sure', 'Not Sure'),
    ]
    GENDER_CHOICES = [
        ('Male',   'Male'),
        ('Female', 'Female'),
        ('Other',  'Other'),
    ]
    SUPPORT_CHOICES = [
        ('positive', 'Positive'),
        ('negative', 'Negative'),
        ('neutral',  'Neutral'),
    ]
    RESPONSE_STATUS_CHOICES = [
        ('not_reach',    'Not Reach'),
        ('no_answer',    'No Answer'),
        ('need_followup', 'Need Followup'),
    ]

    survey_date         = models.DateField(db_index=True)
    block               = models.CharField(max_length=100, blank=True)
    village             = models.CharField(max_length=200, blank=True)
    booth_no            = models.CharField(max_length=20, blank=True)

    # Voter info
    voter_name          = models.CharField(max_length=200)
    age                 = models.IntegerField(null=True, blank=True)
    gender              = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    phone               = models.CharField(max_length=15, blank=True)
    address             = models.TextField(blank=True)

    # Survey answers
    is_registered       = models.CharField(max_length=10, choices=YNS_CHOICES, blank=True)
    aware_of_candidate  = models.CharField(max_length=10, choices=YNS_CHOICES, blank=True)
    likely_to_vote      = models.CharField(max_length=10, choices=YNS_CHOICES, blank=True)
    support_level       = models.CharField(max_length=50, choices=SUPPORT_CHOICES, blank=True)
    party_preference    = models.CharField(max_length=50, blank=True)
    key_issues          = models.TextField(blank=True)
    remarks             = models.TextField(blank=True)
    response_status     = models.CharField(
        max_length=20, choices=RESPONSE_STATUS_CHOICES, blank=True
    )

    # Who surveyed
    surveyed_by         = models.CharField(max_length=150, blank=True)

    class Meta:
        ordering = ['-survey_date', '-created_at']
        indexes = [
            models.Index(fields=['survey_date']),
            models.Index(fields=['support_level']),
        ]

    def __str__(self):
        return f"Survey — {self.voter_name} ({self.survey_date})"
