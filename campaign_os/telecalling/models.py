"""
Telecalling assignment and feedback models
"""
from django.db import models
from campaign_os.core.models import BaseModel


class TelecallingAssignment(BaseModel):
    """One assignment session: a telecaller + a list of voters for a given date."""
    telecaller_id    = models.IntegerField(null=True, blank=True)   # Volunteer PK (denormalised)
    telecaller_name  = models.CharField(max_length=200)
    telecaller_phone = models.CharField(max_length=20, blank=True)
    assigned_date    = models.DateField(db_index=True)

    class Meta:
        ordering = ['-assigned_date', '-created_at']
        indexes = [
            models.Index(fields=['assigned_date', 'telecaller_id'], name='telecall_asg_date_tid_idx'),
            models.Index(fields=['telecaller_name'], name='telecall_asg_name_idx'),
        ]

    def __str__(self):
        return f"{self.telecaller_name} — {self.assigned_date}"


class TelecallingAssignmentVoter(models.Model):
    """A voter row inside an assignment."""
    ENTITY_TYPE_CHOICES = [
        ('voter', 'Voter'),
        ('volunteer', 'Volunteer'),
        ('beneficiary', 'Beneficiary'),
    ]

    assignment  = models.ForeignKey(
        TelecallingAssignment, on_delete=models.CASCADE,
        related_name='voters'
    )
    voter       = models.ForeignKey(
        'voters.Voter', on_delete=models.SET_NULL,
        null=True, blank=True, db_constraint=False
    )
    voter_name  = models.CharField(max_length=200)
    voter_id_no = models.CharField(max_length=50, blank=True)   # voter card ID
    phone       = models.CharField(max_length=20, blank=True)
    address     = models.CharField(max_length=500, blank=True)
    booth_no    = models.CharField(max_length=20, blank=True)
    booth_name  = models.CharField(max_length=200, blank=True)
    age         = models.IntegerField(null=True, blank=True)
    gender      = models.CharField(max_length=10, blank=True)
    entity_type = models.CharField(max_length=20, choices=ENTITY_TYPE_CHOICES, default='voter')
    source_id   = models.IntegerField(null=True, blank=True)
    relation_label = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['voter_name']
        indexes = [
            models.Index(fields=['voter_name'], name='telecall_asgv_name_idx'),
            models.Index(fields=['assignment', 'voter'], name='telecall_asgv_asg_voter_idx'),
            models.Index(fields=['assignment', 'voter_name'], name='telecall_asgv_asg_name_idx'),
            models.Index(fields=['entity_type', 'source_id'], name='telecall_asgv_entity_idx'),
        ]

    def __str__(self):
        return f"{self.voter_name} → {self.assignment}"


class TelecallingFeedback(BaseModel):
    """Review decision recorded against a submitted FieldSurvey record."""
    ACTION_CHOICES = [
        ('followup_required',     'Followup Required'),
        ('followup_not_required', 'Followup Not Required'),
    ]
    FOLLOWUP_TYPE_CHOICES = [
        ('telephonic',   'Telephonic'),
        ('field_survey', 'Field Survey'),
    ]

    survey          = models.ForeignKey(
        'activities.FieldSurvey', on_delete=models.SET_NULL,
        null=True, blank=True, db_constraint=False,
        related_name='feedback_decisions'
    )
    voter_name      = models.CharField(max_length=200)
    telecaller_name = models.CharField(max_length=200, blank=True)
    action          = models.CharField(max_length=30, choices=ACTION_CHOICES)
    followup_type   = models.CharField(max_length=30, choices=FOLLOWUP_TYPE_CHOICES, blank=True)
    date            = models.DateField()

    class Meta:
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['survey', 'date'], name='telecall_fb_survey_date_idx'),
            models.Index(fields=['action', 'followup_type'], name='telecall_fb_action_type_idx'),
            models.Index(fields=['followup_type', 'date'], name='telecall_fb_type_date_idx'),
        ]

    def __str__(self):
        return f"{self.voter_name} — {self.action} ({self.date})"
