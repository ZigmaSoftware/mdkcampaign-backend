"""
User and authentication models
"""
from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from campaign_os.core.models import BaseModel

class User(AbstractUser):
    """
    Extended Django User with additional fields for campaign system
    """
    ROLE_CHOICES = (
        ('admin',            'System Administrator'),
        ('district_head',    'District Head'),
        ('constituency_mgr', 'Constituency Manager'),
        ('booth_agent',      'Booth Agent'),
        ('volunteer',        'Campaign Volunteer'),
        ('voter',            'Registered Voter'),
        ('analyst',          'Data Analyst'),
        ('observer',         'Observer'),
    )
    
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='volunteer')
    
    # Override M2M fields with custom related_names to avoid clashes
    groups = models.ManyToManyField(
        Group,
        related_name='campaign_user_set',
        blank=True,
        help_text='The groups this user belongs to.'
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='campaign_user_set',
        blank=True,
        help_text='Specific permissions for this user.'
    )
    
    # Hierarchical access control
    state = models.ForeignKey(
        'masters.State',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        db_constraint=False
    )
    district = models.ForeignKey(
        'masters.District',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        db_constraint=False
    )
    constituency = models.ForeignKey(
        'masters.Constituency',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        db_constraint=False
    )
    booth = models.ForeignKey(
        'masters.Booth',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        db_constraint=False
    )
    
    profile_photo = models.ImageField(upload_to='profile_photos/', null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    last_login_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['phone']),
            models.Index(fields=['role']),
            models.Index(fields=['district']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"
    
    def has_access_to_district(self, district):
        """Check if user has access to view/modify district data"""
        if self.role == 'admin':
            return True
        if self.role == 'district_head' and self.district == district:
            return True
        return False
    
    def has_access_to_constituency(self, constituency):
        """Check if user has access to view/modify constituency data"""
        if self.role == 'admin':
            return True
        if self.role == 'district_head' and self.district == constituency.district:
            return True
        if self.role == 'constituency_mgr' and self.constituency == constituency:
            return True
        return False
    
    def get_accessible_districts(self):
        """Get all districts accessible to the user"""
        if self.role == 'admin':
            from campaign_os.masters.models import District
            return District.objects.all()
        if self.role == 'district_head':
            return self.state.districts.all() if self.state else []
        return []
    
    def get_accessible_constituencies(self):
        """Get all constituencies accessible to the user"""
        if self.role == 'admin':
            from campaign_os.masters.models import Constituency
            return Constituency.objects.all()
        if self.role == 'district_head':
            from campaign_os.masters.models import Constituency
            return Constituency.objects.filter(district=self.district)
        if self.role == 'constituency_mgr':
            from campaign_os.masters.models import Constituency
            return Constituency.objects.filter(id=self.constituency.id)
        return []


class Role(BaseModel):
    """
    RBAC Role definition
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='roles',
        blank=True
    )
    
    class Meta:
        verbose_name = 'Role'
        verbose_name_plural = 'Roles'
    
    def __str__(self):
        return self.name


class UserLog(BaseModel):
    """
    Audit log for user activities
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='logs', db_constraint=False)
    action = models.CharField(max_length=100)
    resource_type = models.CharField(max_length=100, blank=True)
    resource_id = models.BigIntegerField(null=True, blank=True)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'User Log'
        verbose_name_plural = 'User Logs'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['action']),
        ]
    
    def __str__(self):
        return f"{self.user} - {self.action} - {self.created_at}"


# ── Pages available in the frontend ──
PAGE_IDS = [
    ('dashboard',     'Dashboard'),
    ('master',        'Overview'),
    ('entry',         'Data Entry'),
    ('masters-config','Masters Config'),
    ('report',        'Reports'),
    ('opinion-poll',  'Opinion Poll'),
]

# ── Entry sub-modules ──
ENTRY_MODULE_IDS = [
    ('voter',               'Voter Details'),
    ('booth',               'Booth Info'),
    ('volunteer',           'Volunteers'),
    ('event',               'Event Mgmt'),
    ('campaign',            'Campaign'),
    ('user',                'User Mgmt'),
    ('warroom',             'War Room'),
    ('dashboard',           'Dashboard'),
    ('alliance',            'Alliance'),
    ('keypeople',           'Key People'),
    ('feedback',            'Feedback'),
    ('commitment',          'Commitments'),
    ('grievance',           'Grievance'),
    ('agent-activity',      'Agent Log'),
    ('field-activity',      'Field Log'),
    ('volunteer-activity',  'Vol. Log'),
    ('voter-survey',        'Survey'),
]


class PagePermission(models.Model):
    """Controls which pages/modules each role can access."""
    role       = models.CharField(max_length=20, choices=User.ROLE_CHOICES, db_index=True)
    page_id    = models.CharField(max_length=50, db_index=True)
    can_access = models.BooleanField(default=False)

    class Meta:
        unique_together = ['role', 'page_id']
        verbose_name = 'Page Permission'
        verbose_name_plural = 'Page Permissions'

    def __str__(self):
        return f"{self.role} → {self.page_id}: {'✓' if self.can_access else '✗'}"


def seed_default_permissions():
    """
    Call once after migration to populate default page permissions.
    Admin gets everything; others get limited access.
    """
    defaults = {
        'admin':            ['dashboard', 'master', 'entry', 'masters-config', 'report', 'opinion-poll',
                             'voter', 'booth', 'volunteer', 'event', 'campaign', 'user', 'warroom',
                             'dashboard', 'alliance', 'keypeople', 'feedback', 'commitment', 'grievance',
                             'agent-activity', 'field-activity', 'volunteer-activity', 'voter-survey'],
        'district_head':    ['dashboard', 'master', 'entry', 'report', 'opinion-poll',
                             'voter', 'booth', 'volunteer', 'event', 'campaign',
                             'agent-activity', 'field-activity', 'volunteer-activity', 'voter-survey'],
        'constituency_mgr': ['dashboard', 'master', 'entry', 'report', 'opinion-poll',
                             'voter', 'booth', 'volunteer', 'event', 'campaign',
                             'agent-activity', 'field-activity', 'volunteer-activity', 'voter-survey'],
        'booth_agent':      ['dashboard', 'entry', 'opinion-poll',
                             'voter', 'booth', 'agent-activity', 'voter-survey'],
        'volunteer':        ['dashboard', 'entry', 'opinion-poll',
                             'voter', 'volunteer-activity', 'voter-survey'],
        'voter':            ['dashboard', 'opinion-poll'],
        'analyst':          ['dashboard', 'master', 'report', 'opinion-poll'],
        'observer':         ['dashboard', 'master', 'report', 'opinion-poll'],
    }

    all_pages = [p[0] for p in PAGE_IDS] + [m[0] for m in ENTRY_MODULE_IDS]

    for role, allowed in defaults.items():
        for page_id in all_pages:
            PagePermission.objects.get_or_create(
                role=role,
                page_id=page_id,
                defaults={'can_access': page_id in allowed},
            )
