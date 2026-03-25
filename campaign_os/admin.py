"""Admin configuration for all apps"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

# Accounts
from campaign_os.accounts.models import User, Role, UserLog

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'get_full_name', 'role', 'district', 'is_active')
    list_filter = ('role', 'is_active', 'is_staff')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Campaign Info', {'fields': ('phone', 'role', 'state', 'district', 'constituency', 'booth')}),
    )

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')

@admin.register(UserLog)
class UserLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('user__username', 'action')

# Masters
from campaign_os.masters.models import (
    Country, State, District, Constituency, Ward, Booth, PollingArea,
    Party, Candidate, Scheme, Issue
)

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')

@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'country')
    list_filter = ('country',)

@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'state', 'is_active')
    list_filter = ('state', 'is_active')
    search_fields = ('name', 'code')

@admin.register(Constituency)
class ConstituencyAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'district', 'election_type')
    list_filter = ('district', 'election_type')
    search_fields = ('name', 'code')

@admin.register(Ward)
class WardAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'constituency')
    list_filter = ('constituency',)
    search_fields = ('name', 'code')

@admin.register(Booth)
class BoothAdmin(admin.ModelAdmin):
    list_display = ('number', 'name', 'ward', 'total_voters', 'status')
    list_filter = ('status', 'ward__constituency')
    search_fields = ('name', 'number', 'code')
    fieldsets = (
        ('Basic Info', {'fields': ('number', 'name', 'code', 'ward')}),
        ('Location', {'fields': ('address', 'village', 'latitude', 'longitude')}),
        ('Voters', {'fields': ('total_voters', 'male_voters', 'female_voters', 'third_gender_voters')}),
        ('Assignments', {'fields': ('primary_agent', 'status', 'sentiment')}),
        ('Notes', {'fields': ('notes',)}),
    )

@admin.register(PollingArea)
class PollingAreaAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'constituency')
    list_filter = ('constituency',)

@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'abbreviation', 'is_national')
    list_filter = ('is_national',)
    search_fields = ('name', 'code')

@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ('name', 'party', 'constituency', 'is_incumbent')
    list_filter = ('party', 'constituency', 'is_incumbent')
    search_fields = ('name', 'father_name')

@admin.register(Scheme)
class SchemeAdmin(admin.ModelAdmin):
    list_display = ('name', 'scheme_type', 'constituency')
    list_filter = ('scheme_type', 'constituency')
    search_fields = ('name',)

@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'priority')
    list_filter = ('category', 'priority')
    search_fields = ('name',)

# Voters
from campaign_os.voters.models import (
    Voter, VoterContact, VoterSurvey, VoterPreference, VoterFeedback
)

@admin.register(Voter)
class VoterAdmin(admin.ModelAdmin):
    list_display = ('name', 'voter_id', 'phone', 'booth', 'sentiment', 'is_contacted')
    list_filter = ('sentiment', 'is_contacted', 'booth__ward__constituency')
    search_fields = ('name', 'voter_id', 'phone')
    fieldsets = (
        ('Personal', {'fields': ('name', 'father_name', 'gender', 'date_of_birth')}),
        ('Voter ID', {'fields': ('voter_id', 'aadhaar', 'phone', 'email')}),
        ('Location', {'fields': ('booth', 'ward', 'address', 'latitude', 'longitude')}),
        ('Demographics', {'fields': ('education_level', 'occupation')}),
        ('Preferences', {'fields': ('sentiment', 'preferred_party', 'is_contacted', 'contact_count')}),
        ('Engagement', {'fields': ('has_attended_event', 'is_volunteer', 'feedback_score')}),
        ('Notes', {'fields': ('notes',)}),
    )

@admin.register(VoterContact)
class VoterContactAdmin(admin.ModelAdmin):
    list_display = ('voter', 'method', 'contacted_by', 'created_at')
    list_filter = ('method', 'created_at')
    search_fields = ('voter__name',)

@admin.register(VoterSurvey)
class VoterSurveyAdmin(admin.ModelAdmin):
    list_display = ('voter', 'survey_type', 'score', 'created_at')
    list_filter = ('survey_type',)

@admin.register(VoterFeedback)
class VoterFeedbackAdmin(admin.ModelAdmin):
    list_display = ('subject', 'voter', 'feedback_type', 'status', 'created_at')
    list_filter = ('feedback_type', 'status', 'created_at')
    search_fields = ('subject', 'voter__name')

@admin.register(VoterPreference)
class VoterPreferenceAdmin(admin.ModelAdmin):
    list_display = ('voter', 'preferred_language', 'best_time_to_contact', 'do_not_contact')
    list_filter = ('preferred_language', 'do_not_contact')

# Volunteers
from campaign_os.volunteers.models import (
    Volunteer, VolunteerTask, VolunteerAttendance
)

@admin.register(Volunteer)
class VolunteerAdmin(admin.ModelAdmin):
    list_display = ('user', 'booth', 'status', 'voters_contacted', 'performance_score')
    list_filter = ('status', 'booth')
    search_fields = ('user__username', 'user__first_name')

@admin.register(VolunteerTask)
class VolunteerTaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'volunteer', 'status', 'due_date')
    list_filter = ('status', 'assignment_type', 'due_date')
    search_fields = ('title', 'volunteer__user__username')

@admin.register(VolunteerAttendance)
class VolunteerAttendanceAdmin(admin.ModelAdmin):
    list_display = ('volunteer', 'date', 'check_in_time', 'check_out_time')
    list_filter = ('date',)
    search_fields = ('volunteer__user__username',)

# Campaigns
from campaign_os.campaigns.models import CampaignEvent, EventAttendee

@admin.register(CampaignEvent)
class CampaignEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_type', 'constituency', 'scheduled_date', 'status')
    list_filter = ('event_type', 'status', 'scheduled_date')
    search_fields = ('title', 'location')

@admin.register(EventAttendee)
class EventAttendeeAdmin(admin.ModelAdmin):
    list_display = ('name', 'event', 'attendee_type', 'sentiment')
    list_filter = ('attendee_type', 'sentiment')
    search_fields = ('name', 'event__title')

# Elections
from campaign_os.elections.models import Election, Poll, PollQuestion, PollResponse

@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'election_type', 'state', 'election_date', 'status')
    list_filter = ('election_type', 'state', 'status')
    search_fields = ('name',)

@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    list_display = ('name', 'election', 'constituency', 'sample_size')
    list_filter = ('election',)
    search_fields = ('name',)

@admin.register(PollQuestion)
class PollQuestionAdmin(admin.ModelAdmin):
    list_display = ('poll', 'question_text', 'question_type')
    list_filter = ('question_type', 'poll__election')

@admin.register(PollResponse)
class PollResponseAdmin(admin.ModelAdmin):
    list_display = ('poll', 'question', 'voter')
    list_filter = ('poll__election',)

# Analytics
from campaign_os.analytics.models import DashboardSnapshot

@admin.register(DashboardSnapshot)
class DashboardSnapshotAdmin(admin.ModelAdmin):
    list_display = ('snapshot_date', 'total_voters', 'voters_contacted', 'total_events')
    list_filter = ('snapshot_date',)
    readonly_fields = (
        'total_voters', 'voters_contacted', 'voters_by_sentiment',
        'total_booths', 'booths_assigned', 'total_volunteers'
    )
