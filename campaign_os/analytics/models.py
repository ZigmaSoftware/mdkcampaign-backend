"""
Analytics models
"""
from django.db import models
from campaign_os.core.models import BaseModel


class DashboardSnapshot(BaseModel):
    """Daily snapshot of campaign statistics"""
    snapshot_date = models.DateField()
    
    # Voter stats
    total_voters = models.IntegerField(default=0)
    voters_contacted = models.IntegerField(default=0)
    voters_by_sentiment = models.JSONField(default=dict)  # {positive, neutral, negative, undecided}
    
    # Booth coverage
    total_booths = models.IntegerField(default=0)
    booths_assigned = models.IntegerField(default=0)
    booths_working = models.IntegerField(default=0)
    
    # Volunteer stats
    total_volunteers = models.IntegerField(default=0)
    active_volunteers = models.IntegerField(default=0)
    avg_performance_score = models.FloatField(default=0.0)
    
    # Campaign
    total_events = models.IntegerField(default=0)
    completed_events = models.IntegerField(default=0)
    total_attendees = models.IntegerField(default=0)
    
    # Survey/Poll
    surveys_conducted = models.IntegerField(default=0)
    feedback_received = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ['snapshot_date']
        ordering = ['-snapshot_date']
    
    def __str__(self):
        return f"Snapshot - {self.snapshot_date}"
