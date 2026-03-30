"""
Master data models for geographic hierarchy and election-related masters
"""
from django.db import models
from campaign_os.core.models import BaseModel


class Country(BaseModel):
    """Country (typically India)"""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=3, unique=True)  # ISO 3166

    class Meta:
        verbose_name_plural = 'Countries'

    def __str__(self):
        return self.name


class State(BaseModel):
    """State/Union Territory"""
    country = models.ForeignKey(
        Country, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='states', db_constraint=False
    )
    name = models.CharField(max_length=100, null=True, blank=True)
    code = models.CharField(max_length=3, unique=True)  # State code

    class Meta:
        unique_together = ['country', 'code']
        indexes = [
            models.Index(fields=['country']),
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"


class District(BaseModel):
    """District within a State"""
    state = models.ForeignKey(
        State, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='districts', db_constraint=False
    )
    name = models.CharField(max_length=100, null=True, blank=True)
    code = models.CharField(max_length=5, unique=True)
    description = models.TextField(blank=True, null=True)

    # Office location
    office_address = models.TextField(blank=True, null=True)
    office_phone   = models.CharField(max_length=20, blank=True, null=True)
    office_email   = models.EmailField(blank=True, null=True)

    # Geography
    latitude  = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        unique_together = ['state', 'code']
        indexes = [
            models.Index(fields=['state']),
            models.Index(fields=['name']),
        ]

    def __str__(self):
        state_code = self.state.code if self.state_id else '?'
        return f"{self.name} ({state_code})"


class Constituency(BaseModel):
    """Assembly/Parliament Constituency (Thoguthi)"""
    district = models.ForeignKey(
        District, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='constituencies', db_constraint=False
    )
    name = models.CharField(max_length=100, null=True, blank=True)
    code = models.CharField(max_length=5, unique=True)
    election_type = models.CharField(
        max_length=20,
        choices=[('assembly', 'Assembly'), ('parliament', 'Parliament')],
        default='assembly', null=True, blank=True
    )
    description = models.TextField(blank=True, null=True)

    # Geography
    latitude  = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # Activity info
    total_population = models.IntegerField(default=0, null=True, blank=True)

    class Meta:
        unique_together = ['district', 'code']
        indexes = [
            models.Index(fields=['district']),
            models.Index(fields=['election_type']),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"

    @property
    def voters_count(self):
        """Get total registered voters"""
        return self.wards.aggregate(total=models.Sum('booths__total_voters'))['total'] or 0


class Ward(BaseModel):
    """Ward within Constituency (Thoguthi Ward)"""
    constituency = models.ForeignKey(
        Constituency, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='wards', db_constraint=False
    )
    name = models.CharField(max_length=100, null=True, blank=True)
    code = models.CharField(max_length=5, null=True, blank=True)
    description = models.TextField(blank=True, null=True)

    # Geography
    latitude  = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        unique_together = ['constituency', 'code']
        indexes = [
            models.Index(fields=['constituency']),
        ]

    def __str__(self):
        const_name = self.constituency.name if self.constituency_id else '?'
        return f"{self.name} - {const_name}"

    @property
    def booths_count(self):
        return self.booths.filter(is_active=True).count()

    @property
    def voters_count(self):
        return self.booths.aggregate(
            total=models.Sum('total_voters')
        )['total'] or 0


class Booth(BaseModel):
    """Polling Booth"""
    ward = models.ForeignKey(
        Ward, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='booths', db_constraint=False
    )
    panchayat = models.ForeignKey(
        'masters.Panchayat', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='booths', db_constraint=False
    )
    number = models.CharField(max_length=10, null=True, blank=True)
    name   = models.CharField(max_length=200, null=True, blank=True)
    code   = models.CharField(max_length=5, unique=True)

    # Address and location
    address   = models.TextField(blank=True, null=True)
    village   = models.CharField(max_length=100, blank=True, null=True)
    latitude  = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # Voter information
    total_voters        = models.IntegerField(default=0, null=True, blank=True)
    male_voters         = models.IntegerField(default=0, null=True, blank=True)
    female_voters       = models.IntegerField(default=0, null=True, blank=True)
    third_gender_voters = models.IntegerField(default=0, null=True, blank=True)

    # Booth assignment
    primary_agent = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='primary_booths', db_constraint=False
    )
    primary_volunteer = models.ForeignKey(
        'volunteers.Volunteer', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='primary_booths', db_constraint=False
    )
    agents = models.ManyToManyField('accounts.User', blank=True, related_name='agent_booths')

    # Status tracking
    BOOTH_STATUS_CHOICES = [
        ('assigned',  'Assigned'),
        ('working',   'Working'),
        ('completed', 'Completed'),
        ('pending',   'Pending'),
        ('issue',     'Issue Flagged'),
    ]
    status    = models.CharField(max_length=20, choices=BOOTH_STATUS_CHOICES, default='pending', null=True, blank=True)
    sentiment = models.CharField(
        max_length=20,
        choices=[('positive', 'Positive'), ('neutral', 'Neutral'), ('negative', 'Negative')],
        default='neutral', null=True, blank=True
    )
    notes = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ['ward', 'number']
        indexes = [
            models.Index(fields=['ward']),
            models.Index(fields=['status']),
            models.Index(fields=['latitude', 'longitude']),
        ]

    def __str__(self):
        return f"Booth {self.number} - {self.name}"

    def get_google_maps_url(self):
        if self.latitude and self.longitude:
            return f"https://maps.google.com/?q={self.latitude},{self.longitude}"
        return None

    @property
    def coverage_percentage(self):
        from campaign_os.voters.models import Voter
        covered = Voter.objects.filter(booth=self, is_contacted=True).count()
        if not self.total_voters:
            return 0
        return (covered / self.total_voters) * 100


class PollingArea(BaseModel):
    """Polling Area for organisation purposes"""
    constituency = models.ForeignKey(
        Constituency, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='areas', db_constraint=False
    )
    name        = models.CharField(max_length=100, null=True, blank=True)
    code        = models.CharField(max_length=10, null=True, blank=True)
    description = models.TextField(blank=True, null=True)

    latitude  = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        unique_together = ['constituency', 'code']
        verbose_name_plural = 'Polling Areas'

    def __str__(self):
        const_name = self.constituency.name if self.constituency_id else '?'
        return f"{self.name} - {const_name}"


class Candidate(BaseModel):
    """Political Candidate"""
    GENDER_CHOICES = [('m', 'Male'), ('f', 'Female'), ('o', 'Other')]

    name        = models.CharField(max_length=200, null=True, blank=True)
    father_name = models.CharField(max_length=200, blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='m', null=True, blank=True)

    # Political association
    party = models.ForeignKey(
        'masters.Party', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='candidates', db_constraint=False
    )
    constituency = models.ForeignKey(
        Constituency, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='candidates', db_constraint=False
    )

    # Contact
    phone   = models.CharField(max_length=20, blank=True, null=True)
    email   = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    # Profile
    educational_qualification = models.CharField(max_length=200, blank=True, null=True)
    professional_background   = models.TextField(blank=True, null=True)
    photo = models.ImageField(upload_to='candidates/', null=True, blank=True)
    bio   = models.TextField(blank=True, null=True)

    is_incumbent     = models.BooleanField(default=False)
    election_symbol  = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        unique_together = ['party', 'constituency']
        indexes = [
            models.Index(fields=['constituency']),
            models.Index(fields=['party']),
        ]

    def __str__(self):
        party_name = self.party.name if self.party_id else '?'
        const_name = self.constituency.name if self.constituency_id else '?'
        return f"{self.name} - {party_name} ({const_name})"


class Party(BaseModel):
    """Political Party"""
    name         = models.CharField(max_length=200, unique=True)
    code         = models.CharField(max_length=5, unique=True)
    abbreviation = models.CharField(max_length=10, unique=True)
    description  = models.TextField(blank=True, null=True)

    # Party details
    founded_year   = models.IntegerField(null=True, blank=True)
    headquarters   = models.CharField(max_length=200, blank=True, null=True)
    president_name = models.CharField(max_length=200, blank=True, null=True)

    # Appearance
    primary_color   = models.CharField(max_length=7, blank=True, null=True)
    secondary_color = models.CharField(max_length=7, blank=True, null=True)
    logo = models.ImageField(upload_to='party_logos/', null=True, blank=True)

    is_national = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'Parties'

    def __str__(self):
        return self.name


class Scheme(BaseModel):
    """Government/Campaign Scheme or Program"""
    name        = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True, null=True)
    scheme_type = models.CharField(max_length=100, blank=True, null=True)

    # Scope
    constituency = models.ForeignKey(
        Constituency, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='schemes', db_constraint=False
    )

    # Timeline
    launch_date = models.DateField(null=True, blank=True)
    end_date    = models.DateField(null=True, blank=True)

    # Beneficiaries
    target_population = models.IntegerField(default=0, null=True, blank=True)
    beneficiaries     = models.IntegerField(default=0, null=True, blank=True)

    # Details
    budget               = models.BigIntegerField(default=0, null=True, blank=True)
    responsible_ministry = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['constituency']),
            models.Index(fields=['scheme_type']),
        ]

    def __str__(self):
        return self.name


class Issue(BaseModel):
    """Community Issue/Grievance Type"""
    name        = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True, null=True)
    category    = models.CharField(max_length=50, default='other', null=True, blank=True)
    priority    = models.IntegerField(default=0, null=True, blank=True)

    class Meta:
        verbose_name_plural = 'Issues'

    def __str__(self):
        return self.name


class TaskCategory(BaseModel):
    """Task Category master — used by campaign tasks"""
    name        = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    color       = models.CharField(max_length=7, blank=True, null=True, help_text='Hex colour e.g. #FF9933')
    icon        = models.CharField(max_length=60, blank=True, null=True, help_text='Phosphor icon class e.g. ph-truck')
    priority    = models.IntegerField(default=0, null=True, blank=True)

    class Meta:
        verbose_name_plural = 'Task Categories'
        ordering = ['priority', 'name']

    def __str__(self):
        return self.name


class CampaignActivityType(BaseModel):
    """Master list of campaign activity types shown in the Campaign Activity dropdown"""
    EVENT_TYPE_CHOICES = [
        ('rally',     'Rally'),
        ('meeting',   'Meeting'),
        ('door_door', 'Door-to-Door'),
        ('training',  'Training / Digital'),
    ]
    name       = models.CharField(max_length=200, unique=True)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES, default='meeting')
    description = models.TextField(blank=True, null=True)
    order       = models.IntegerField(default=0)
    is_active   = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'Campaign Activity Types'

    def __str__(self):
        return self.name


class Panchayat(BaseModel):
    """Panchayat — local government unit within a Ward/Constituency"""
    ward = models.ForeignKey(
        'masters.Ward', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='panchayats', db_constraint=False
    )
    CATEGORY_CHOICES = [
        ('village_panchayat', 'Village Panchayat'),
        ('town_panchayat',    'Town Panchayat'),
    ]
    name        = models.CharField(max_length=200)
    code        = models.CharField(max_length=20, blank=True, null=True)
    category    = models.CharField(max_length=30, choices=CATEGORY_CHOICES, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Panchayats'

    def __str__(self):
        ward_name = self.ward.name if self.ward_id else '?'
        return f"{self.name} ({ward_name})"


class VolunteerType(BaseModel):
    """Volunteer Type master — drives the volunteer type dropdown in Volunteer Entry"""
    name        = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    order       = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'Volunteer Types'

    def __str__(self):
        return self.name


class VolunteerRole(BaseModel):
    """Volunteer Role master — drives the role dropdown in Volunteer Entry"""
    name        = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    order       = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'Volunteer Roles'

    def __str__(self):
        return self.name


class Achievement(BaseModel):
    """Campaign Achievement"""
    name        = models.CharField(max_length=200, null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    ward = models.ForeignKey(
        'masters.Ward', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='achievements', db_constraint=False
    )
    booth = models.ForeignKey(
        'masters.Booth', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='achievements', db_constraint=False
    )

    class Meta:
        verbose_name_plural = 'Achievements'

    def __str__(self):
        return self.name or ''
