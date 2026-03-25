"""
Attendance tracking with punch-in / punch-out logic
"""
from django.db import models
from django.utils import timezone
from decimal import Decimal


class Attendance(models.Model):
    """
    Daily attendance record per user.
    Status is PRESENT only when BOTH punch_in AND punch_out exist.
    """
    STATUS_CHOICES = [
        ('PRESENT',    'Present'),
        ('ABSENT',     'Absent'),
        ('INCOMPLETE', 'Incomplete'),
    ]

    user            = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='attendance_records',
        db_constraint=False,
    )
    punch_in        = models.DateTimeField()
    punch_out       = models.DateTimeField(null=True, blank=True)
    attendance_date = models.DateField(db_index=True)
    status          = models.CharField(max_length=12, choices=STATUS_CHOICES, default='INCOMPLETE', db_index=True)
    total_work_hours = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    notes           = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'attendance_date']
        ordering = ['-attendance_date', '-punch_in']
        indexes = [
            models.Index(fields=['user', 'attendance_date']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.user.username} — {self.attendance_date} — {self.status}"

    def calculate_work_hours(self):
        """Calculate total_work_hours from punch_in and punch_out."""
        if self.punch_in and self.punch_out:
            delta = self.punch_out - self.punch_in
            hours = Decimal(str(round(delta.total_seconds() / 3600, 2)))
            return hours
        return Decimal('0.00')

    def save(self, *args, **kwargs):
        # Auto-update status and work hours on every save
        if self.punch_in and self.punch_out:
            self.status = 'PRESENT'
            self.total_work_hours = self.calculate_work_hours()
        elif self.punch_in:
            self.status = 'INCOMPLETE'
            self.total_work_hours = Decimal('0.00')
        super().save(*args, **kwargs)
