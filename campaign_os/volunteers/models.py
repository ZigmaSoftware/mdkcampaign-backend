"""
Volunteer management models
"""
from django.db import models
from campaign_os.core.models import BaseModel


class Volunteer(BaseModel):
    """Volunteer/Campaign Worker"""
    user = models.OneToOneField(
        'accounts.User', on_delete=models.CASCADE,
        related_name='volunteer_profile', db_constraint=False
    )

    # Assignment
    booth = models.ForeignKey(
        'masters.Booth', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='volunteers', db_constraint=False
    )
    ward = models.ForeignKey(
        'masters.Ward', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='volunteers', db_constraint=False
    )

    # Profile
    VOLUNTEER_TYPE_CHOICES = [
        ('paid_volunteer',         'Paid Volunteer'),
        ('social_media_volunteer', 'Social Media Volunteer'),
        ('alliance_volunteer',     'Alliance Volunteer'),
    ]
    volunteer_type = models.CharField(
        max_length=30, choices=VOLUNTEER_TYPE_CHOICES, blank=True, null=True, default='',
    )

    block       = models.CharField(max_length=100, blank=True, null=True)
    role        = models.CharField(max_length=100, blank=True, null=True)
    age         = models.IntegerField(null=True, blank=True)
    gender      = models.CharField(max_length=20, blank=True, null=True)
    joined_date = models.DateField(null=True, blank=True)
    source      = models.CharField(max_length=100, blank=True, null=True)
    skills      = models.CharField(max_length=300, blank=True, null=True)
    vehicle     = models.CharField(max_length=50, blank=True, null=True)
    notes       = models.TextField(blank=True, null=True)
    phone2      = models.CharField(max_length=15, blank=True, null=True)

    # Experience
    experience_months  = models.IntegerField(default=0, null=True, blank=True)
    previous_campaigns = models.IntegerField(default=0, null=True, blank=True)

    # Activity
    status = models.CharField(
        max_length=20,
        choices=[('active', 'Active'), ('inactive', 'Inactive'), ('on_leave', 'On Leave')],
        default='active', null=True, blank=True
    )

    # Stats
    voters_contacted  = models.IntegerField(default=0, null=True, blank=True)
    events_attended   = models.IntegerField(default=0, null=True, blank=True)
    hours_contributed = models.IntegerField(default=0, null=True, blank=True)

    # Rating/Performance
    performance_score = models.FloatField(default=0.0, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['booth']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} (Volunteer)"


class VolunteerTask(BaseModel):
    """Task assigned to volunteer"""
    volunteer = models.ForeignKey(
        Volunteer, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='tasks', db_constraint=False
    )
    assigned_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_tasks', db_constraint=False
    )

    title       = models.CharField(max_length=200, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    # Assignment
    assignment_type = models.CharField(
        max_length=50,
        choices=[
            ('voter_contact', 'Voter Contact'),
            ('event_setup',   'Event Setup'),
            ('survey',        'Survey Collection'),
            ('distribution',  'Material Distribution'),
            ('patrol',        'Election Patrol'),
            ('other',         'Other'),
        ],
        null=True, blank=True
    )

    target_count = models.IntegerField(null=True, blank=True)

    # Timeline
    due_date = models.DateField(null=True, blank=True)
    priority = models.IntegerField(default=0, null=True, blank=True)

    # Status
    STATUS_CHOICES = [
        ('pending',     'Pending'),
        ('in_progress', 'In Progress'),
        ('completed',   'Completed'),
        ('abandoned',   'Abandoned'),
    ]
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Result
    actual_count      = models.IntegerField(null=True, blank=True)
    completion_notes  = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-due_date']

    def __str__(self):
        vol_name = self.volunteer.user.get_full_name() if self.volunteer_id else '?'
        return f"{self.title} - {vol_name}"


class VolunteerAttendance(BaseModel):
    """Track volunteer attendance"""
    volunteer = models.ForeignKey(
        Volunteer, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='attendances', db_constraint=False
    )

    date           = models.DateField(null=True, blank=True)
    check_in_time  = models.TimeField(null=True, blank=True)
    check_out_time = models.TimeField(null=True, blank=True)
    location       = models.CharField(max_length=200, blank=True, null=True)

    notes = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ['volunteer', 'date']
        ordering = ['-date']

    def __str__(self):
        vol_name = self.volunteer.user.get_full_name() if self.volunteer_id else '?'
        return f"{vol_name} - {self.date}"
