"""
Campaign, Event, and Task models
"""
from django.db import models
from campaign_os.core.models import BaseModel


class CampaignEvent(BaseModel):
    """Campaign event/rally/meeting"""
    title       = models.CharField(max_length=200, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    # Type and scope
    event_type = models.CharField(
        max_length=50,
        choices=[
            ('rally',       'Public Rally'),
            ('meeting',     'Community Meeting'),
            ('training',    'Volunteer Training'),
            ('door_door',   'Door-to-Door'),
            ('nagar_kirtan','Nagar Kirtan'),
            ('stage_show',  'Stage Show'),
            ('other',       'Other'),
        ],
        null=True, blank=True
    )
    constituency = models.ForeignKey(
        'masters.Constituency', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='events', db_constraint=False
    )
    ward = models.ForeignKey(
        'masters.Ward', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='events', db_constraint=False
    )

    # Timeline and location
    scheduled_date = models.DateField(null=True, blank=True)
    scheduled_time = models.TimeField(null=True, blank=True)
    location       = models.CharField(max_length=300, null=True, blank=True)
    latitude       = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude      = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # Organizer
    organized_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='organized_events', db_constraint=False
    )

    # Attendance
    expected_attendees = models.IntegerField(default=0, null=True, blank=True)
    actual_attendees   = models.IntegerField(default=0, null=True, blank=True)

    # Status
    STATUS_CHOICES = [
        ('planned',    'Planned'),
        ('confirmed',  'Confirmed'),
        ('completed',  'Completed'),
        ('cancelled',  'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned', null=True, blank=True)

    # Material
    materials_prepared = models.TextField(blank=True, null=True)

    # Feedback
    outcome_notes      = models.TextField(blank=True, null=True)
    special_guest_name = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        ordering = ['scheduled_date']
        indexes = [
            models.Index(fields=['constituency']),
            models.Index(fields=['scheduled_date']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.title} - {self.scheduled_date}"


class EventAttendee(BaseModel):
    """Attendee for an event"""
    event = models.ForeignKey(
        CampaignEvent, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='attendees', db_constraint=False
    )
    attendee_type = models.CharField(
        max_length=20,
        choices=[
            ('voter',     'Voter'),
            ('volunteer', 'Volunteer'),
            ('media',     'Media'),
            ('vip',       'VIP'),
            ('other',     'Other'),
        ],
        null=True, blank=True
    )

    # Attendee info
    name  = models.CharField(max_length=200, null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    # For voter attendees
    voter = models.ForeignKey(
        'voters.Voter', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='event_attendances', db_constraint=False
    )

    # Feedback
    feedback  = models.TextField(blank=True, null=True)
    sentiment = models.CharField(
        max_length=20,
        choices=[('positive', 'Positive'), ('neutral', 'Neutral'), ('negative', 'Negative')],
        default='neutral', null=True, blank=True
    )

    class Meta:
        unique_together = ['event', 'voter']

    def __str__(self):
        return f"{self.name} - {self.event}"


class Task(BaseModel):
    """Campaign task management"""

    CATEGORY_CHOICES = [
        ('material_preparation', 'Material Preparation'),
        ('distribution',         'Distribution'),
        ('event_coordination',   'Event Coordination'),
        ('voter_outreach',       'Voter Outreach'),
        ('social_media',         'Social Media'),
        ('logistics',            'Logistics'),
        ('communication',        'Communication'),
        ('data_entry',           'Data Entry'),
        ('finance',              'Finance'),
        ('other',                'Other'),
    ]

    STATUS_CHOICES = [
        ('pending',     'Pending'),
        ('in_progress', 'In Progress'),
        ('completed',   'Completed'),
        ('cancelled',   'Cancelled'),
    ]

    task_type         = models.ForeignKey(
        'masters.TaskType', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='tasks', db_constraint=False,
    )
    title             = models.CharField(max_length=200, null=True, blank=True)
    category          = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='other', null=True, blank=True)
    task_category     = models.ForeignKey(
        'masters.TaskCategory', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='tasks', db_constraint=False,
    )
    details           = models.TextField(blank=True, null=True)
    expected_datetime = models.DateTimeField(null=True, blank=True)
    venue             = models.CharField(max_length=300, blank=True, null=True)

    # Location (all optional)
    block     = models.ForeignKey(
        'masters.PollingArea', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='tasks', db_constraint=False,
    )
    union     = models.ForeignKey(
        'masters.Union', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='tasks', db_constraint=False,
    )
    panchayat = models.ForeignKey(
        'masters.Panchayat', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='tasks', db_constraint=False,
    )
    booth     = models.ForeignKey(
        'masters.Booth', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='tasks', db_constraint=False,
    )
    ward      = models.ForeignKey(
        'masters.Ward', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='tasks', db_constraint=False,
    )

    volunteer_role = models.ForeignKey(
        'masters.VolunteerRole', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='tasks', db_constraint=False,
    )
    delivery_incharge = models.ForeignKey(
        'volunteers.Volunteer', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='incharge_tasks', db_constraint=False,
    )
    coordinator = models.ForeignKey(
        'volunteers.Volunteer', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='coordinating_tasks', db_constraint=False,
    )

    qty                = models.IntegerField(default=1, null=True, blank=True)
    status             = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', null=True, blank=True)
    completed_datetime = models.DateTimeField(null=True, blank=True)
    notes              = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['expected_datetime']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['expected_datetime']),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"
