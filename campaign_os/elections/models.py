"""
Election-specific models
"""
from django.db import models
from campaign_os.core.models import BaseModel


class Election(BaseModel):
    """Election metadata"""
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    
    # Type and scope
    election_type = models.CharField(
        max_length=20,
        choices=[('assembly', 'Assembly'), ('parliament', 'Parliament'), ('local', 'Local')],
        default='assembly'
    )
    
    # Geographic scope
    state = models.ForeignKey(
        'masters.State',
        on_delete=models.CASCADE,
        related_name='elections',
        db_constraint=False
    )
    
    # Important dates
    announcement_date = models.DateField(null=True, blank=True)
    nomination_start_date = models.DateField()
    nomination_end_date = models.DateField()
    election_date = models.DateField()
    result_date = models.DateField(null=True, blank=True)
    
    # Status
    STATUS_CHOICES = [
        ('announced', 'Announced'),
        ('nominations_open', 'Nominations Open'),
        ('nominations_closed', 'Nominations Closed'),
        ('campaigning', 'Campaigning'),
        ('polling_day', 'Polling Day'),
        ('counting', 'Counting'),
        ('completed', 'Completed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='announced')
    
    class Meta:
        ordering = ['-election_date']
    
    def __str__(self):
        return f"{self.name} - {self.election_date.year}"


class Poll(BaseModel):
    """Opinion poll/survey for election prediction"""
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='polls', db_constraint=False)
    
    name = models.CharField(max_length=200)
    conducted_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='polls_conducted',
        db_constraint=False
    )

    # Scope
    constituency = models.ForeignKey(
        'masters.Constituency',
        on_delete=models.CASCADE,
        related_name='polls',
        db_constraint=False
    )
    
    # Sample
    sample_size = models.IntegerField()
    sampling_method = models.CharField(max_length=100, blank=True)
    
    # Timeline
    poll_date_start = models.DateField()
    poll_date_end = models.DateField()
    
    # Results (as JSON for flexibility)
    poll_results = models.JSONField(default=dict)
    
    # Accuracy
    accuracy_notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-poll_date_end']
    
    def __str__(self):
        return f"{self.name} - {self.constituency.name}"


class PollQuestion(BaseModel):
    """Questions in an opinion poll"""
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='questions', db_constraint=False)
    
    question_text = models.CharField(max_length=500)
    question_type = models.CharField(
        max_length=20,
        choices=[
            ('candidate_choice', 'Candidate Choice'),
            ('issue_preference', 'Issue Preference'),
            ('satisfaction', 'Satisfaction'),
            ('likelihood', 'Likelihood to Vote'),
            ('other', 'Other'),
        ]
    )
    
    order = models.IntegerField(default=0)
    
    # Options (JSON)
    options = models.JSONField(default=list)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"Q{self.order}: {self.question_text[:50]}"


class PollResponse(BaseModel):
    """Individual poll response"""
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='responses', db_constraint=False)
    question = models.ForeignKey(PollQuestion, on_delete=models.CASCADE, related_name='responses', db_constraint=False)
    voter = models.ForeignKey(
        'voters.Voter',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='poll_responses',
        db_constraint=False
    )
    
    # Response
    response_text = models.CharField(max_length=500, blank=True)
    response_value = models.IntegerField(null=True, blank=True)
    
    class Meta:
        unique_together = ['poll', 'question', 'voter']
    
    def __str__(self):
        return f"Poll: {self.poll.name} - Q{self.question.order}"
