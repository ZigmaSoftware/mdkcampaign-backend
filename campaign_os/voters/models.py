"""
Voter models
"""
from django.db import models
from campaign_os.core.models import BaseModel


class Voter(BaseModel):
    """Registered voter"""
    # Personal details
    name        = models.CharField(max_length=200, null=True, blank=True)
    father_name = models.CharField(max_length=200, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)

    GENDER_CHOICES = [('m', 'Male'), ('f', 'Female'), ('o', 'Other')]
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='m', null=True, blank=True)

    # Voter ID
    voter_id = models.CharField(max_length=20, unique=True)  # EPIC – keep required
    aadhaar  = models.CharField(max_length=12, unique=True, null=True, blank=True)
    phone    = models.CharField(max_length=20, null=True, blank=True, db_index=True)
    phone2   = models.CharField(max_length=20, blank=True, null=True)
    alt_phoneno2 = models.CharField(max_length=20, blank=True, null=True)
    alt_phoneno3 = models.CharField(max_length=20, blank=True, null=True)
    email    = models.EmailField(null=True, blank=True)

    # Location
    booth = models.ForeignKey(
        'masters.Booth', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='voters', db_constraint=False
    )
    village = models.ForeignKey(
        'masters.Ward', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='voters', db_constraint=False
    )

    # Address details
    address   = models.TextField(null=True, blank=True)
    latitude  = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # Personal / social
    religion  = models.CharField(max_length=50,  blank=True, null=True)
    caste     = models.CharField(max_length=100, blank=True, null=True)
    sub_caste = models.CharField(max_length=100, blank=True, null=True)

    # Scheme & issue
    scheme_name = models.CharField(max_length=200, blank=True, null=True)
    issue_name  = models.CharField(max_length=200, blank=True, null=True)

    # Demographics
    education_level = models.CharField(
        max_length=50,
        choices=[
            ('illiterate',     'Illiterate'),
            ('primary',        'Primary'),
            ('middle',         'Middle'),
            ('high_school',    'High School'),
            ('graduate',       'Graduate'),
            ('post_graduate',  'Post Graduate'),
        ],
        blank=True, null=True
    )
    occupation = models.CharField(max_length=100, blank=True, null=True)

    # Political preference
    SENTIMENT_CHOICES = [
        ('positive',  'Positive'),
        ('neutral',   'Neutral'),
        ('negative',  'Negative'),
        ('undecided', 'Undecided'),
    ]
    sentiment = models.CharField(max_length=20, choices=SENTIMENT_CHOICES, default='undecided', null=True, blank=True)
    preferred_party = models.ForeignKey(
        'masters.Party', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='preferred_voters', db_constraint=False
    )

    # Contact history
    is_contacted      = models.BooleanField(null=True, blank=True, default=None)
    last_contacted_at = models.DateTimeField(null=True, blank=True)
    contact_count     = models.IntegerField(null=True, blank=True)

    # Engagement
    has_attended_event = models.BooleanField(null=True, blank=True, default=None)
    is_volunteer       = models.BooleanField(null=True, blank=True, default=None)
    feedback_score     = models.IntegerField(null=True, blank=True)

    # Current location status
    LOCATION_CHOICES = [
        ('home',           'Home Location'),
        ('out_of_station', 'Out of Station'),
    ]
    current_location = models.CharField(
        max_length=20, choices=LOCATION_CHOICES, default='home', blank=True, null=True
    )

    # Notes
    notes = models.TextField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['booth']),
            models.Index(fields=['voter_id']),
            models.Index(fields=['phone']),
            models.Index(fields=['sentiment']),
            models.Index(fields=['is_contacted']),
        ]
        verbose_name = 'Voter'
        verbose_name_plural = 'Voters'

    def __str__(self):
        return f"{self.name} ({self.voter_id})"


class VoterContact(BaseModel):
    """Track voter contact history"""
    voter = models.ForeignKey(
        Voter, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='contacts', db_constraint=False
    )
    contacted_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='voter_contacts', db_constraint=False
    )

    CONTACT_METHOD_CHOICES = [
        ('phone',     'Phone Call'),
        ('sms',       'SMS'),
        ('visit',     'Personal Visit'),
        ('event',     'Event Interaction'),
        ('whatsapp',  'WhatsApp'),
        ('email',     'Email'),
        ('other',     'Other'),
    ]
    method = models.CharField(max_length=20, choices=CONTACT_METHOD_CHOICES, null=True, blank=True)

    # Feedback
    duration_minutes = models.IntegerField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    sentiment_after = models.CharField(
        max_length=20,
        choices=[('positive', 'Positive'), ('neutral', 'Neutral'), ('negative', 'Negative')],
        default='neutral', null=True, blank=True
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.voter} - {self.method} - {self.created_at}"


class VoterSurvey(BaseModel):
    """Voter opinion survey response"""
    voter = models.ForeignKey(
        Voter, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='surveys', db_constraint=False
    )
    survey_type = models.CharField(
        max_length=50,
        choices=[
            ('opinion_poll',          'Opinion Poll'),
            ('issue_feedback',        'Issue Feedback'),
            ('candidate_preference',  'Candidate Preference'),
            ('scheme_awareness',      'Scheme Awareness'),
        ],
        null=True, blank=True
    )

    # Questions and responses in JSON format
    responses = models.JSONField(default=dict, blank=True)

    # Score
    score = models.IntegerField(null=True, blank=True)

    class Meta:
        unique_together = ['voter', 'survey_type']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.voter} - {self.survey_type}"


class VoterPreference(BaseModel):
    """Voter preferences and interests"""
    voter = models.OneToOneField(
        Voter, on_delete=models.CASCADE, related_name='preference', db_constraint=False
    )

    # Issues of interest
    issues_of_interest = models.ManyToManyField(
        'masters.Issue', related_name='interested_voters', blank=True
    )

    # Preferred communication
    preferred_language = models.CharField(
        max_length=50,
        choices=[('tamil', 'Tamil'), ('english', 'English'), ('both', 'Both')],
        default='tamil', null=True, blank=True
    )
    best_time_to_contact = models.CharField(
        max_length=50,
        choices=[
            ('morning',   '6 AM - 12 PM'),
            ('afternoon', '12 PM - 5 PM'),
            ('evening',   '5 PM - 9 PM'),
            ('any',       'Any time'),
        ],
        default='evening', null=True, blank=True
    )

    do_not_contact = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Voter Preference'
        verbose_name_plural = 'Voter Preferences'

    def __str__(self):
        return f"Preferences - {self.voter.name}"


class VoterFeedback(BaseModel):
    """Voter grievances and feedback"""
    FEEDBACK_TYPE_CHOICES = [
        ('complaint',     'Complaint'),
        ('suggestion',    'Suggestion'),
        ('appreciation',  'Appreciation'),
        ('query',         'Query'),
    ]

    voter = models.ForeignKey(
        Voter, on_delete=models.CASCADE, related_name='feedbacks',
        null=True, blank=True, db_constraint=False,
    )
    voter_name  = models.CharField(max_length=200, blank=True, null=True)
    voter_phone = models.CharField(max_length=20,  blank=True, null=True)
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPE_CHOICES, null=True, blank=True)
    subject     = models.CharField(max_length=200, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    # Issue association
    issue = models.ForeignKey(
        'masters.Issue', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='feedbacks', db_constraint=False
    )

    # Status
    STATUS_CHOICES = [
        ('new',         'New'),
        ('assigned',    'Assigned'),
        ('in_progress', 'In Progress'),
        ('resolved',    'Resolved'),
        ('closed',      'Closed'),
    ]
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', null=True, blank=True)
    assigned_to = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_feedbacks', db_constraint=False
    )
    resolution  = models.TextField(blank=True, null=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        voter_label = self.voter.name if self.voter_id else self.voter_name or '—'
        return f"{self.subject} - {voter_label}"
