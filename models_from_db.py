# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class AccountsPagepermission(models.Model):
    id = models.BigAutoField(primary_key=True)
    role = models.CharField(max_length=20)
    page_id = models.CharField(max_length=50)
    can_access = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'accounts_pagepermission'
        unique_together = (('role', 'page_id'),)


class AccountsRole(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    is_active = models.IntegerField()
    name = models.CharField(unique=True, max_length=100)
    description = models.TextField()
    created_by = models.ForeignKey('AccountsUser', models.DO_NOTHING, blank=True, null=True)
    updated_by = models.ForeignKey('AccountsUser', models.DO_NOTHING, related_name='accountsrole_updated_by_set', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'accounts_role'


class AccountsRolePermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    role = models.ForeignKey(AccountsRole, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'accounts_role_permissions'
        unique_together = (('role', 'permission'),)


class AccountsUser(models.Model):
    id = models.BigAutoField(primary_key=True)
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.IntegerField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.IntegerField()
    is_active = models.IntegerField()
    date_joined = models.DateTimeField()
    phone = models.CharField(unique=True, max_length=20, blank=True, null=True)
    role = models.CharField(max_length=20)
    profile_photo = models.CharField(max_length=100, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    is_verified = models.IntegerField()
    last_login_at = models.DateTimeField(blank=True, null=True)
    booth = models.ForeignKey('MastersBooth', models.DO_NOTHING, blank=True, null=True)
    constituency = models.ForeignKey('MastersConstituency', models.DO_NOTHING, blank=True, null=True)
    district = models.ForeignKey('MastersDistrict', models.DO_NOTHING, blank=True, null=True)
    state = models.ForeignKey('MastersState', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'accounts_user'


class AccountsUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AccountsUser, models.DO_NOTHING)
    group = models.ForeignKey('AuthGroup', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'accounts_user_groups'
        unique_together = (('user', 'group'),)


class AccountsUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AccountsUser, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'accounts_user_user_permissions'
        unique_together = (('user', 'permission'),)


class AccountsUserlog(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    is_active = models.IntegerField()
    action = models.CharField(max_length=100)
    resource_type = models.CharField(max_length=100)
    resource_id = models.BigIntegerField(blank=True, null=True)
    details = models.JSONField()
    ip_address = models.CharField(max_length=39, blank=True, null=True)
    user_agent = models.TextField()
    created_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, blank=True, null=True)
    updated_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, related_name='accountsuserlog_updated_by_set', blank=True, null=True)
    user = models.ForeignKey(AccountsUser, models.DO_NOTHING, related_name='accountsuserlog_user_set')

    class Meta:
        managed = False
        db_table = 'accounts_userlog'


class ActivitiesActivitylog(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    is_active = models.IntegerField()
    category = models.CharField(max_length=20)
    activity_type = models.CharField(max_length=100)
    date = models.DateField()
    hours_worked = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)
    village = models.CharField(max_length=200)
    booth_no = models.CharField(max_length=20)
    notes = models.TextField()
    username = models.CharField(max_length=150)
    user_role = models.CharField(max_length=50)
    created_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, blank=True, null=True)
    updated_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, related_name='activitiesactivitylog_updated_by_set', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'activities_activitylog'


class ActivitiesFieldsurvey(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    is_active = models.IntegerField()
    survey_date = models.DateField()
    block = models.CharField(max_length=100)
    village = models.CharField(max_length=200)
    booth_no = models.CharField(max_length=20)
    voter_name = models.CharField(max_length=200)
    age = models.IntegerField(blank=True, null=True)
    gender = models.CharField(max_length=10)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    is_registered = models.CharField(max_length=10)
    aware_of_candidate = models.CharField(max_length=10)
    likely_to_vote = models.CharField(max_length=10)
    support_level = models.CharField(max_length=50)
    party_preference = models.CharField(max_length=50)
    key_issues = models.TextField()
    remarks = models.TextField()
    surveyed_by = models.CharField(max_length=150)
    created_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, blank=True, null=True)
    updated_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, related_name='activitiesfieldsurvey_updated_by_set', blank=True, null=True)
    response_status = models.CharField(max_length=20)

    class Meta:
        managed = False
        db_table = 'activities_fieldsurvey'


class AnalyticsDashboardsnapshot(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    is_active = models.IntegerField()
    snapshot_date = models.DateField(unique=True)
    total_voters = models.IntegerField()
    voters_contacted = models.IntegerField()
    voters_by_sentiment = models.JSONField()
    total_booths = models.IntegerField()
    booths_assigned = models.IntegerField()
    booths_working = models.IntegerField()
    total_volunteers = models.IntegerField()
    active_volunteers = models.IntegerField()
    avg_performance_score = models.FloatField()
    total_events = models.IntegerField()
    completed_events = models.IntegerField()
    total_attendees = models.IntegerField()
    surveys_conducted = models.IntegerField()
    feedback_received = models.IntegerField()
    created_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, blank=True, null=True)
    updated_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, related_name='analyticsdashboardsnapshot_updated_by_set', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'analytics_dashboardsnapshot'


class AttendanceAttendance(models.Model):
    id = models.BigAutoField(primary_key=True)
    punch_in = models.DateTimeField()
    punch_out = models.DateTimeField(blank=True, null=True)
    attendance_date = models.DateField()
    status = models.CharField(max_length=12)
    total_work_hours = models.DecimalField(max_digits=5, decimal_places=2)
    notes = models.TextField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    user = models.ForeignKey(AccountsUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'attendance_attendance'
        unique_together = (('user', 'attendance_date'),)


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class CampaignsCampaignevent(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    is_active = models.IntegerField()
    title = models.CharField(max_length=200)
    description = models.TextField()
    event_type = models.CharField(max_length=50)
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField(blank=True, null=True)
    location = models.CharField(max_length=300)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    expected_attendees = models.IntegerField()
    actual_attendees = models.IntegerField()
    status = models.CharField(max_length=20)
    materials_prepared = models.TextField()
    outcome_notes = models.TextField()
    success_score = models.IntegerField(blank=True, null=True)
    constituency = models.ForeignKey('MastersConstituency', models.DO_NOTHING)
    created_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, blank=True, null=True)
    organized_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, related_name='campaignscampaignevent_organized_by_set', blank=True, null=True)
    updated_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, related_name='campaignscampaignevent_updated_by_set', blank=True, null=True)
    ward = models.ForeignKey('MastersWard', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'campaigns_campaignevent'


class CampaignsEventattendee(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    is_active = models.IntegerField()
    attendee_type = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    email = models.CharField(max_length=254)
    feedback = models.TextField()
    sentiment = models.CharField(max_length=20)
    created_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, blank=True, null=True)
    event = models.ForeignKey(CampaignsCampaignevent, models.DO_NOTHING)
    updated_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, related_name='campaignseventattendee_updated_by_set', blank=True, null=True)
    voter = models.ForeignKey('VotersVoter', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'campaigns_eventattendee'
        unique_together = (('event', 'voter'),)


class CampaignsTask(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    is_active = models.IntegerField()
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=30)
    details = models.TextField()
    expected_datetime = models.DateTimeField()
    venue = models.CharField(max_length=300)
    qty = models.IntegerField()
    status = models.CharField(max_length=20)
    completed_datetime = models.DateTimeField(blank=True, null=True)
    notes = models.TextField()
    coordinator = models.ForeignKey(AccountsUser, models.DO_NOTHING, blank=True, null=True)
    created_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, related_name='campaignstask_created_by_set', blank=True, null=True)
    delivery_incharge = models.ForeignKey(AccountsUser, models.DO_NOTHING, related_name='campaignstask_delivery_incharge_set', blank=True, null=True)
    updated_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, related_name='campaignstask_updated_by_set', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'campaigns_task'


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.PositiveSmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AccountsUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class ElectionsElection(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    is_active = models.IntegerField()
    name = models.CharField(unique=True, max_length=200)
    description = models.TextField()
    election_type = models.CharField(max_length=20)
    announcement_date = models.DateField(blank=True, null=True)
    nomination_start_date = models.DateField()
    nomination_end_date = models.DateField()
    election_date = models.DateField()
    result_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20)
    created_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, blank=True, null=True)
    state = models.ForeignKey('MastersState', models.DO_NOTHING)
    updated_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, related_name='electionselection_updated_by_set', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'elections_election'


class ElectionsPoll(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    is_active = models.IntegerField()
    name = models.CharField(max_length=200)
    sample_size = models.IntegerField()
    sampling_method = models.CharField(max_length=100)
    poll_date_start = models.DateField()
    poll_date_end = models.DateField()
    poll_results = models.JSONField()
    accuracy_notes = models.TextField()
    conducted_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, blank=True, null=True)
    constituency = models.ForeignKey('MastersConstituency', models.DO_NOTHING)
    created_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, related_name='electionspoll_created_by_set', blank=True, null=True)
    election = models.ForeignKey(ElectionsElection, models.DO_NOTHING)
    updated_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, related_name='electionspoll_updated_by_set', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'elections_poll'


class ElectionsPollquestion(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    is_active = models.IntegerField()
    question_text = models.CharField(max_length=500)
    question_type = models.CharField(max_length=20)
    order = models.IntegerField()
    options = models.JSONField()
    created_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, blank=True, null=True)
    poll = models.ForeignKey(ElectionsPoll, models.DO_NOTHING)
    updated_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, related_name='electionspollquestion_updated_by_set', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'elections_pollquestion'


class ElectionsPollresponse(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    is_active = models.IntegerField()
    response_text = models.CharField(max_length=500)
    response_value = models.IntegerField(blank=True, null=True)
    created_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, blank=True, null=True)
    poll = models.ForeignKey(ElectionsPoll, models.DO_NOTHING)
    question = models.ForeignKey(ElectionsPollquestion, models.DO_NOTHING)
    updated_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, related_name='electionspollresponse_updated_by_set', blank=True, null=True)
    voter = models.ForeignKey('VotersVoter', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'elections_pollresponse'
        unique_together = (('poll', 'question', 'voter'),)


class MastersAchievement(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    is_active = models.IntegerField()
    name = models.CharField(max_length=200)
    description = models.TextField()
    booth = models.ForeignKey('MastersBooth', models.DO_NOTHING, blank=True, null=True)
    ward = models.ForeignKey('MastersWard', models.DO_NOTHING, blank=True, null=True)
    created_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, blank=True, null=True)
    updated_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, related_name='mastersachievement_updated_by_set', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'masters_achievement'


class MastersBooth(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    is_active = models.IntegerField()
    number = models.CharField(max_length=10)
    name = models.CharField(max_length=200)
    code = models.CharField(unique=True, max_length=5)
    address = models.TextField()
    village = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    total_voters = models.IntegerField()
    male_voters = models.IntegerField()
    female_voters = models.IntegerField()
    third_gender_voters = models.IntegerField()
    status = models.CharField(max_length=20)
    sentiment = models.CharField(max_length=20)
    notes = models.TextField()
    created_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, blank=True, null=True)
    primary_agent = models.ForeignKey(AccountsUser, models.DO_NOTHING, related_name='mastersbooth_primary_agent_set', blank=True, null=True)
    updated_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, related_name='mastersbooth_updated_by_set', blank=True, null=True)
    ward = models.ForeignKey('MastersWard', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'masters_booth'
        unique_together = (('ward', 'number'),)


class MastersBoothAgents(models.Model):
    id = models.BigAutoField(primary_key=True)
    booth = models.ForeignKey(MastersBooth, models.DO_NOTHING)
    user = models.ForeignKey(AccountsUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'masters_booth_agents'
        unique_together = (('booth', 'user'),)


class MastersCandidate(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    is_active = models.IntegerField()
    name = models.CharField(max_length=200)
    father_name = models.CharField(max_length=200)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=1)
    phone = models.CharField(max_length=20)
    email = models.CharField(max_length=254)
    address = models.TextField()
    educational_qualification = models.CharField(max_length=200)
    professional_background = models.TextField()
    photo = models.CharField(max_length=100, blank=True, null=True)
    bio = models.TextField()
    is_incumbent = models.IntegerField()
    election_symbol = models.CharField(max_length=100)
    created_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, blank=True, null=True)
    updated_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, related_name='masterscandidate_updated_by_set', blank=True, null=True)
    constituency = models.ForeignKey('MastersConstituency', models.DO_NOTHING)
    party = models.ForeignKey('MastersParty', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'masters_candidate'
        unique_together = (('party', 'constituency'),)


class MastersConstituency(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    is_active = models.IntegerField()
    name = models.CharField(max_length=100)
    code = models.CharField(unique=True, max_length=5)
    election_type = models.CharField(max_length=20)
    description = models.TextField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    total_population = models.IntegerField()
    created_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, blank=True, null=True)
    updated_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, related_name='mastersconstituency_updated_by_set', blank=True, null=True)
    district = models.ForeignKey('MastersDistrict', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'masters_constituency'
        unique_together = (('district', 'code'),)


class MastersCountry(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    is_active = models.IntegerField()
    name = models.CharField(unique=True, max_length=100)
    code = models.CharField(unique=True, max_length=3)
    created_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, blank=True, null=True)
    updated_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, related_name='masterscountry_updated_by_set', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'masters_country'


class MastersDistrict(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    is_active = models.IntegerField()
    name = models.CharField(max_length=100)
    code = models.CharField(unique=True, max_length=5)
    description = models.TextField()
    office_address = models.TextField()
    office_phone = models.CharField(max_length=20)
    office_email = models.CharField(max_length=254)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    created_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, blank=True, null=True)
    updated_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, related_name='mastersdistrict_updated_by_set', blank=True, null=True)
    state = models.ForeignKey('MastersState', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'masters_district'
        unique_together = (('state', 'code'),)


class MastersIssue(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    is_active = models.IntegerField()
    name = models.CharField(unique=True, max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50)
    priority = models.IntegerField()
    created_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, blank=True, null=True)
    updated_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, related_name='mastersissue_updated_by_set', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'masters_issue'


class MastersParty(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    is_active = models.IntegerField()
    name = models.CharField(unique=True, max_length=200)
    code = models.CharField(unique=True, max_length=5)
    description = models.TextField()
    abbreviation = models.CharField(unique=True, max_length=10)
    founded_year = models.IntegerField(blank=True, null=True)
    headquarters = models.CharField(max_length=200)
    president_name = models.CharField(max_length=200)
    primary_color = models.CharField(max_length=7)
    secondary_color = models.CharField(max_length=7)
    logo = models.CharField(max_length=100, blank=True, null=True)
    is_national = models.IntegerField()
    created_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, blank=True, null=True)
    updated_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, related_name='mastersparty_updated_by_set', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'masters_party'


class MastersPollingarea(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    is_active = models.IntegerField()
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)
    description = models.TextField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    constituency = models.ForeignKey(MastersConstituency, models.DO_NOTHING)
    created_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, blank=True, null=True)
    updated_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, related_name='masterspollingarea_updated_by_set', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'masters_pollingarea'
        unique_together = (('constituency', 'code'),)


class MastersScheme(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    is_active = models.IntegerField()
    name = models.CharField(unique=True, max_length=200)
    description = models.TextField()
    scheme_type = models.CharField(max_length=100)
    launch_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    target_population = models.IntegerField()
    beneficiaries = models.IntegerField()
    budget = models.BigIntegerField()
    responsible_ministry = models.CharField(max_length=200)
    constituency = models.ForeignKey(MastersConstituency, models.DO_NOTHING, blank=True, null=True)
    created_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, blank=True, null=True)
    updated_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, related_name='mastersscheme_updated_by_set', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'masters_scheme'


class MastersState(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    is_active = models.IntegerField()
    name = models.CharField(max_length=100)
    code = models.CharField(unique=True, max_length=3)
    country = models.ForeignKey(MastersCountry, models.DO_NOTHING)
    created_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, blank=True, null=True)
    updated_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, related_name='mastersstate_updated_by_set', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'masters_state'
        unique_together = (('country', 'code'),)


class MastersWard(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    is_active = models.IntegerField()
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=5)
    description = models.TextField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    constituency = models.ForeignKey(MastersConstituency, models.DO_NOTHING)
    created_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, blank=True, null=True)
    updated_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, related_name='mastersward_updated_by_set', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'masters_ward'
        unique_together = (('constituency', 'code'),)


class PollsPoll(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    title = models.CharField(max_length=200)
    title_ta = models.CharField(max_length=200)
    constituency_name = models.CharField(max_length=200)
    constituency_no = models.IntegerField(blank=True, null=True)
    is_active = models.IntegerField()
    starts_at = models.DateTimeField(blank=True, null=True)
    ends_at = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, blank=True, null=True)
    updated_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, related_name='pollspoll_updated_by_set', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'polls_poll'


class PollsPolloption(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    is_active = models.IntegerField()
    question_no = models.IntegerField()
    key = models.CharField(max_length=50)
    name = models.CharField(max_length=200)
    name_ta = models.CharField(max_length=200)
    sub_label = models.CharField(max_length=200)
    icon_bg = models.CharField(max_length=200)
    bar_color = models.CharField(max_length=20)
    is_winner = models.IntegerField()
    display_order = models.IntegerField()
    created_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, blank=True, null=True)
    poll = models.ForeignKey(PollsPoll, models.DO_NOTHING)
    updated_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, related_name='pollspolloption_updated_by_set', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'polls_polloption'
        unique_together = (('poll', 'question_no', 'key'),)


class PollsPollvote(models.Model):
    id = models.BigAutoField(primary_key=True)
    voter_ip = models.CharField(max_length=39)
    voted_at = models.DateTimeField()
    poll = models.ForeignKey(PollsPoll, models.DO_NOTHING)
    q1_option = models.ForeignKey(PollsPolloption, models.DO_NOTHING, blank=True, null=True)
    q2_option = models.ForeignKey(PollsPolloption, models.DO_NOTHING, related_name='pollspollvote_q2_option_set', blank=True, null=True)
    voter_user = models.ForeignKey(AccountsUser, models.DO_NOTHING, blank=True, null=True)
    voter_name = models.CharField(max_length=200)
    voter_phone = models.CharField(max_length=20)
    voter_city = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'polls_pollvote'
        unique_together = (('poll', 'voter_ip'),)


class VolunteersVolunteer(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    is_active = models.IntegerField()
    experience_months = models.IntegerField()
    previous_campaigns = models.IntegerField()
    status = models.CharField(max_length=20)
    voters_contacted = models.IntegerField()
    events_attended = models.IntegerField()
    hours_contributed = models.IntegerField()
    performance_score = models.FloatField()
    booth = models.ForeignKey(MastersBooth, models.DO_NOTHING, blank=True, null=True)
    created_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, blank=True, null=True)
    updated_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, related_name='volunteersvolunteer_updated_by_set', blank=True, null=True)
    user = models.OneToOneField(AccountsUser, models.DO_NOTHING, related_name='volunteersvolunteer_user_set')
    ward = models.ForeignKey(MastersWard, models.DO_NOTHING, blank=True, null=True)
    age = models.IntegerField(blank=True, null=True)
    gender = models.CharField(max_length=20)
    joined_date = models.DateField(blank=True, null=True)
    notes = models.TextField()
    phone2 = models.CharField(max_length=15)
    role = models.CharField(max_length=100)
    skills = models.CharField(max_length=300)
    source = models.CharField(max_length=100)
    vehicle = models.CharField(max_length=50)
    block = models.CharField(max_length=100)
    volunteer_type = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'volunteers_volunteer'


class VolunteersVolunteerattendance(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    is_active = models.IntegerField()
    date = models.DateField()
    check_in_time = models.TimeField(blank=True, null=True)
    check_out_time = models.TimeField(blank=True, null=True)
    location = models.CharField(max_length=200)
    notes = models.TextField()
    created_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, blank=True, null=True)
    updated_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, related_name='volunteersvolunteerattendance_updated_by_set', blank=True, null=True)
    volunteer = models.ForeignKey(VolunteersVolunteer, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'volunteers_volunteerattendance'
        unique_together = (('volunteer', 'date'),)


class VolunteersVolunteertask(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    is_active = models.IntegerField()
    title = models.CharField(max_length=200)
    description = models.TextField()
    assignment_type = models.CharField(max_length=50)
    target_count = models.IntegerField(blank=True, null=True)
    due_date = models.DateField()
    priority = models.IntegerField()
    status = models.CharField(max_length=20)
    completed_at = models.DateTimeField(blank=True, null=True)
    actual_count = models.IntegerField(blank=True, null=True)
    completion_notes = models.TextField()
    assigned_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, blank=True, null=True)
    created_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, related_name='volunteersvolunteertask_created_by_set', blank=True, null=True)
    updated_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, related_name='volunteersvolunteertask_updated_by_set', blank=True, null=True)
    volunteer = models.ForeignKey(VolunteersVolunteer, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'volunteers_volunteertask'


class VotersVoter(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    is_active = models.IntegerField()
    name = models.CharField(max_length=200)
    father_name = models.CharField(max_length=200, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=10)
    voter_id = models.CharField(unique=True, max_length=20)
    aadhaar = models.CharField(unique=True, max_length=12, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.CharField(max_length=254, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    education_level = models.CharField(max_length=50, blank=True, null=True)
    occupation = models.CharField(max_length=100, blank=True, null=True)
    sentiment = models.CharField(max_length=20, blank=True, null=True)
    is_contacted = models.IntegerField(blank=True, null=True)
    last_contacted_at = models.DateTimeField(blank=True, null=True)
    contact_count = models.IntegerField(blank=True, null=True)
    has_attended_event = models.IntegerField(blank=True, null=True)
    is_volunteer = models.IntegerField(blank=True, null=True)
    feedback_score = models.IntegerField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    booth = models.ForeignKey(MastersBooth, models.DO_NOTHING)
    created_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, blank=True, null=True)
    preferred_party = models.ForeignKey(MastersParty, models.DO_NOTHING, blank=True, null=True)
    updated_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, related_name='votersvoter_updated_by_set', blank=True, null=True)
    caste = models.CharField(max_length=100, blank=True, null=True)
    issue_name = models.CharField(max_length=200, blank=True, null=True)
    religion = models.CharField(max_length=50, blank=True, null=True)
    scheme_name = models.CharField(max_length=200, blank=True, null=True)
    age = models.IntegerField(blank=True, null=True)
    current_location = models.CharField(max_length=20, blank=True, null=True)
    sub_caste = models.CharField(max_length=100, blank=True, null=True)
    phone2 = models.CharField(max_length=20)
    village = models.ForeignKey(MastersWard, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'voters_voter'


class VotersVotercontact(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    is_active = models.IntegerField()
    method = models.CharField(max_length=20)
    duration_minutes = models.IntegerField(blank=True, null=True)
    notes = models.TextField()
    sentiment_after = models.CharField(max_length=20)
    contacted_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, blank=True, null=True)
    created_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, related_name='votersvotercontact_created_by_set', blank=True, null=True)
    updated_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, related_name='votersvotercontact_updated_by_set', blank=True, null=True)
    voter = models.ForeignKey(VotersVoter, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'voters_votercontact'


class VotersVoterfeedback(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    is_active = models.IntegerField()
    feedback_type = models.CharField(max_length=20)
    subject = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20)
    resolution = models.TextField()
    resolved_at = models.DateTimeField(blank=True, null=True)
    assigned_to = models.ForeignKey(AccountsUser, models.DO_NOTHING, blank=True, null=True)
    created_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, related_name='votersvoterfeedback_created_by_set', blank=True, null=True)
    issue = models.ForeignKey(MastersIssue, models.DO_NOTHING, blank=True, null=True)
    updated_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, related_name='votersvoterfeedback_updated_by_set', blank=True, null=True)
    voter = models.ForeignKey(VotersVoter, models.DO_NOTHING, blank=True, null=True)
    voter_name = models.CharField(max_length=200)
    voter_phone = models.CharField(max_length=20)

    class Meta:
        managed = False
        db_table = 'voters_voterfeedback'


class VotersVoterpreference(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    is_active = models.IntegerField()
    preferred_language = models.CharField(max_length=50)
    best_time_to_contact = models.CharField(max_length=50)
    do_not_contact = models.IntegerField()
    created_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, blank=True, null=True)
    updated_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, related_name='votersvoterpreference_updated_by_set', blank=True, null=True)
    voter = models.OneToOneField(VotersVoter, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'voters_voterpreference'


class VotersVoterpreferenceIssuesOfInterest(models.Model):
    id = models.BigAutoField(primary_key=True)
    voterpreference = models.ForeignKey(VotersVoterpreference, models.DO_NOTHING)
    issue = models.ForeignKey(MastersIssue, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'voters_voterpreference_issues_of_interest'
        unique_together = (('voterpreference', 'issue'),)


class VotersVotersurvey(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    is_active = models.IntegerField()
    survey_type = models.CharField(max_length=50)
    responses = models.JSONField()
    score = models.IntegerField(blank=True, null=True)
    created_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, blank=True, null=True)
    updated_by = models.ForeignKey(AccountsUser, models.DO_NOTHING, related_name='votersvotersurvey_updated_by_set', blank=True, null=True)
    voter = models.ForeignKey(VotersVoter, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'voters_votersurvey'
        unique_together = (('voter', 'survey_type'),)
