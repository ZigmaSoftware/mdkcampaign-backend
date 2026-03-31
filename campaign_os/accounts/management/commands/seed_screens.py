"""
Management command to seed MainScreen, UserScreen, and UserScreenPermission data.

Usage:
    python manage.py seed_screens

This seeds:
  - All main screens (Entry, Masters Config, Reports, Opinion Poll)
  - All sub-screens for each main screen (master forms + entry forms)
  - Default CRUD permissions for system roles: admin, volunteer, district_head, …
  - Default CRUD permissions for volunteer types:
      party_worker, alliance_volunteer, paid_volunteer, social_media_volunteer,
      community_leader, women_volunteer, youth_volunteer, temporary_volunteer
"""
from django.core.management.base import BaseCommand
from campaign_os.accounts.models import MainScreen, UserScreen, UserScreenPermission


# ── Main screens ──────────────────────────────────────────────────────────────
MAIN_SCREENS = [
    {'slug': 'dashboard',     'name': 'Dashboard',     'icon': 'ph ph-gauge',          'order': 1},
    {'slug': 'entry',         'name': 'Entry',         'icon': 'ph ph-pencil-simple',  'order': 2},
    {'slug': 'masters-config','name': 'Masters Config','icon': 'ph ph-sliders',         'order': 3},
    {'slug': 'report',        'name': 'Reports',       'icon': 'ph ph-chart-bar',       'order': 4},
    {'slug': 'opinion-poll',  'name': 'Opinion Poll',  'icon': 'ph ph-megaphone',       'order': 5},
]

# ── User screens per main screen ───────────────────────────────────────────────
# (main_screen_slug, slug, name, icon, order)
USER_SCREENS = [
    # ── Entry forms ──────────────────────────────────────────────────────────
    ('entry', 'voter',               'Voter Details',        'ph ph-user',                1),
    ('entry', 'booth',               'Booth Info',           'ph ph-map-pin',             2),
    ('entry', 'volunteer',           'Volunteers',           'ph ph-users-three',         3),
    ('entry', 'event',               'Task Management',      'ph ph-clipboard-text',      4),
    ('entry', 'campaign',            'Campaign',             'ph ph-megaphone',           5),
    ('entry', 'user',                'User Management',      'ph ph-user-gear',           6),
    ('entry', 'warroom',             'War Room',             'ph ph-castle-turret',       7),
    ('entry', 'alliance',            'Alliance',             'ph ph-handshake',           8),
    ('entry', 'keypeople',           'Key People',           'ph ph-star',                9),
    ('entry', 'feedback',            'Feedback',             'ph ph-chats',               10),
    ('entry', 'commitment',          'Commitments',          'ph ph-push-pin',            11),
    ('entry', 'grievance',           'Grievance',            'ph ph-warning',             12),
    ('entry', 'agent-activity',      'Agent Log',            'ph ph-identification-card', 13),
    ('entry', 'field-activity',      'Field Log',            'ph ph-map-trifold',         14),
    ('entry', 'volunteer-activity',  'Volunteer Log',        'ph ph-clipboard-text',      15),
    ('entry', 'voter-survey',        'Voter Survey',         'ph ph-notepad',             16),
    ('entry', 'attendance',          'Attendance',           'ph ph-clock',               17),
    ('entry', 'assign-telecalling',  'Assign Telecalling',   'ph ph-phone-outgoing',      18),
    ('entry', 'telecalling-assigned','Telecalling Assigned', 'ph ph-clipboard-text',      19),
    ('entry', 'feedback-review',     'Feedback Review',      'ph ph-git-branch',          20),
    ('entry', 'beneficiary',         'Beneficiary',          'ph ph-hand-heart',           21),

    # ── Master forms ──────────────────────────────────────────────────────────
    ('masters-config', 'district',          'District',          'ph ph-map-trifold',  1),
    ('masters-config', 'constituency',      'Constituency',      'ph ph-buildings',    2),
    ('masters-config', 'ward',              'Ward',              'ph ph-house-line',   3),
    ('masters-config', 'area',              'Block / Area',      'ph ph-map-pin-area', 4),
    ('masters-config', 'booth-master',      'Booth Master',      'ph ph-map-pin',      5),
    ('masters-config', 'scheme',            'Scheme',            'ph ph-file-text',    6),
    ('masters-config', 'achievement',       'Achievements',      'ph ph-trophy',       7),
    ('masters-config', 'candidate',         'Candidate',         'ph ph-user-circle',  8),
    ('masters-config', 'party',             'Party',             'ph ph-flag',         9),
    ('masters-config', 'task-category',     'Task Category',     'ph ph-tag',          10),
    ('masters-config', 'campaign-activity', 'Campaign Activity', 'ph ph-megaphone',            11),
    ('masters-config', 'volunteer-role',    'Vol. Roles',        'ph ph-identification-badge', 12),
    ('masters-config', 'volunteer-type',    'Vol. Types',        'ph ph-tag',                  13),
    ('masters-config', 'panchayat',         'Panchayat',         'ph ph-tree-structure',        14),
    ('masters-config', 'union',             'Union',             'ph ph-buildings',             15),
    ('masters-config', 'user-mgmt',         'User Management',   'ph ph-user-gear',             16),
    ('masters-config', 'permissions',       'Permissions',       'ph ph-shield-check',          17),

    # ── Report sub-screens ────────────────────────────────────────────────────
    ('report', 'report-overview',   'Report Overview',   'ph ph-chart-pie',    1),
    ('report', 'voter-report',      'Voter Report',      'ph ph-user-list',    2),
    ('report', 'volunteer-report',  'Volunteer Report',  'ph ph-users',        3),
    ('report', 'campaign-report',   'Campaign Report',   'ph ph-megaphone',    4),
    ('report', 'activity-report',   'Activity Report',   'ph ph-activity',     5),

    # ── Opinion Poll sub-screens ──────────────────────────────────────────────
    ('opinion-poll', 'poll-questions', 'Poll Questions', 'ph ph-question',     1),
    ('opinion-poll', 'poll-results',   'Poll Results',   'ph ph-chart-bar',    2),
    ('opinion-poll', 'poll-analysis',  'Poll Analysis',  'ph ph-magnifying-glass', 3),
]


# ── Default permissions per role ───────────────────────────────────────────────
# Format: (role, screen_slug, can_view, can_add, can_edit, can_delete)
# Geographic master slugs that operational roles need view access to for form dropdowns
_GEO_MASTERS = ['district', 'constituency', 'ward', 'area', 'booth-master',
                 'party', 'candidate', 'scheme', 'task-category', 'campaign-activity',
                 'volunteer-role', 'volunteer-type', 'panchayat', 'union']

ROLE_PERMISSIONS = [
    # ── admin: full access to everything ────────────────────────────────────
    *[('admin', s[1], True, True, True, True) for s in USER_SCREENS],

    # ── volunteer: entry data with limited CRUD ──────────────────────────────
    # Geographic masters — view-only (needed for dropdown lookups in forms)
    *[('volunteer', slug, True, False, False, False) for slug in _GEO_MASTERS],
    ('volunteer', 'beneficiary',        True,  True,  True,  False),
    ('volunteer', 'voter',              True,  True,  True,  False),
    ('volunteer', 'booth',              True,  False, False, False),
    ('volunteer', 'volunteer',          True,  True,  True,  False),
    ('volunteer', 'event',              True,  True,  False, False),
    ('volunteer', 'campaign',           True,  False, False, False),
    ('volunteer', 'feedback',           True,  True,  False, False),
    ('volunteer', 'commitment',         True,  True,  False, False),
    ('volunteer', 'grievance',          True,  True,  False, False),
    ('volunteer', 'volunteer-activity', True,  True,  True,  False),
    ('volunteer', 'voter-survey',       True,  True,  False, False),
    ('volunteer', 'attendance',         True,  True,  False, False),
    ('volunteer', 'poll-questions',     True,  False, False, False),
    ('volunteer', 'poll-results',       True,  False, False, False),

    # ── member: read-only on core data + poll participation ──────────────────
    *[('member', slug, True, False, False, False) for slug in _GEO_MASTERS],
    ('member', 'beneficiary',    True,  False, False, False),
    ('member', 'voter',          True,  False, False, False),
    ('member', 'booth',          True,  False, False, False),
    ('member', 'campaign',       True,  False, False, False),
    ('member', 'voter-survey',   True,  True,  False, False),
    ('member', 'poll-questions', True,  False, False, False),
    ('member', 'poll-results',   True,  False, False, False),

    # ── district_head: broad access with delete on field records ─────────────
    # Geographic masters — view-only for dropdowns + manage district/constituency
    *[('district_head', slug, True, False, False, False) for slug in _GEO_MASTERS],
    ('district_head', 'user-mgmt',          True, True,  True,  False),
    ('district_head', 'beneficiary',        True, True,  True,  True),
    ('district_head', 'voter',              True, True,  True,  True),
    ('district_head', 'booth',              True, True,  True,  False),
    ('district_head', 'volunteer',          True, True,  True,  True),
    ('district_head', 'event',              True, True,  True,  True),
    ('district_head', 'campaign',           True, True,  True,  False),
    ('district_head', 'feedback',           True, True,  True,  False),
    ('district_head', 'commitment',         True, True,  True,  False),
    ('district_head', 'grievance',          True, True,  True,  False),
    ('district_head', 'agent-activity',     True, True,  True,  False),
    ('district_head', 'field-activity',     True, True,  True,  False),
    ('district_head', 'volunteer-activity', True, True,  True,  False),
    ('district_head', 'voter-survey',       True, True,  False, False),
    ('district_head', 'attendance',         True, True,  True,  False),
    ('district_head', 'report-overview',    True, False, False, False),
    ('district_head', 'voter-report',       True, False, False, False),
    ('district_head', 'volunteer-report',   True, False, False, False),
    ('district_head', 'campaign-report',    True, False, False, False),
    ('district_head', 'poll-questions',     True, False, False, False),
    ('district_head', 'poll-results',       True, False, False, False),

    # ── constituency_mgr: same as district_head ──────────────────────────────
    *[('constituency_mgr', slug, True, False, False, False) for slug in _GEO_MASTERS],
    ('constituency_mgr', 'user-mgmt',          True, True,  True,  False),
    ('constituency_mgr', 'beneficiary',        True, True,  True,  True),
    ('constituency_mgr', 'voter',              True, True,  True,  True),
    ('constituency_mgr', 'booth',              True, True,  True,  False),
    ('constituency_mgr', 'volunteer',          True, True,  True,  True),
    ('constituency_mgr', 'event',              True, True,  True,  True),
    ('constituency_mgr', 'campaign',           True, True,  True,  False),
    ('constituency_mgr', 'feedback',           True, True,  True,  False),
    ('constituency_mgr', 'commitment',         True, True,  True,  False),
    ('constituency_mgr', 'grievance',          True, True,  True,  False),
    ('constituency_mgr', 'agent-activity',     True, True,  True,  False),
    ('constituency_mgr', 'field-activity',     True, True,  True,  False),
    ('constituency_mgr', 'volunteer-activity', True, True,  True,  False),
    ('constituency_mgr', 'voter-survey',       True, True,  False, False),
    ('constituency_mgr', 'attendance',         True, True,  True,  False),
    ('constituency_mgr', 'report-overview',    True, False, False, False),
    ('constituency_mgr', 'voter-report',       True, False, False, False),
    ('constituency_mgr', 'poll-questions',     True, False, False, False),
    ('constituency_mgr', 'poll-results',       True, False, False, False),

    # ── booth_agent: limited field ops ───────────────────────────────────────
    *[('booth_agent', slug, True, False, False, False) for slug in _GEO_MASTERS],
    ('booth_agent', 'beneficiary',    True, True,  False, False),
    ('booth_agent', 'voter',          True, True,  True,  False),
    ('booth_agent', 'booth',          True, False, False, False),
    ('booth_agent', 'agent-activity', True, True,  True,  False),
    ('booth_agent', 'voter-survey',   True, True,  False, False),
    ('booth_agent', 'attendance',     True, True,  False, False),
    ('booth_agent', 'poll-questions', True, False, False, False),

    # ── voter: view + survey only ────────────────────────────────────────────
    ('voter', 'voter',          True, False, False, False),
    ('voter', 'voter-survey',   True, True,  False, False),
    ('voter', 'poll-questions', True, False, False, False),
    ('voter', 'poll-results',   True, False, False, False),

    # ── analyst: read-only everywhere ────────────────────────────────────────
    ('analyst', 'voter',             True, False, False, False),
    ('analyst', 'booth',             True, False, False, False),
    ('analyst', 'volunteer',         True, False, False, False),
    ('analyst', 'report-overview',   True, False, False, False),
    ('analyst', 'voter-report',      True, False, False, False),
    ('analyst', 'volunteer-report',  True, False, False, False),
    ('analyst', 'campaign-report',   True, False, False, False),
    ('analyst', 'activity-report',   True, False, False, False),
    ('analyst', 'poll-questions',    True, False, False, False),
    ('analyst', 'poll-results',      True, False, False, False),
    ('analyst', 'poll-analysis',     True, False, False, False),

    # ── observer: read-only on reports and polls ──────────────────────────────
    ('observer', 'report-overview',  True, False, False, False),
    ('observer', 'voter-report',     True, False, False, False),
    ('observer', 'poll-questions',   True, False, False, False),
    ('observer', 'poll-results',     True, False, False, False),

    # ══════════════════════════════════════════════════════════════════════════
    # VOLUNTEER TYPE PERMISSIONS
    # Slugs match Volunteer.volunteer_type lowercased + spaces→underscore
    # ══════════════════════════════════════════════════════════════════════════

    # ── party_worker: full-time dedicated party worker — broad field access ──
    *[('party_worker', slug, True, False, False, False) for slug in _GEO_MASTERS],
    ('party_worker', 'voter',              True,  True,  True,  False),
    ('party_worker', 'booth',              True,  True,  False, False),
    ('party_worker', 'volunteer',          True,  True,  True,  False),
    ('party_worker', 'beneficiary',        True,  True,  True,  False),
    ('party_worker', 'event',              True,  True,  True,  False),
    ('party_worker', 'campaign',           True,  True,  False, False),
    ('party_worker', 'feedback',           True,  True,  True,  False),
    ('party_worker', 'commitment',         True,  True,  False, False),
    ('party_worker', 'grievance',          True,  True,  False, False),
    ('party_worker', 'field-activity',     True,  True,  True,  False),
    ('party_worker', 'volunteer-activity', True,  True,  True,  False),
    ('party_worker', 'voter-survey',       True,  True,  False, False),
    ('party_worker', 'attendance',         True,  True,  False, False),
    ('party_worker', 'assign-telecalling', True,  True,  False, False),
    ('party_worker', 'poll-questions',     True,  False, False, False),
    ('party_worker', 'poll-results',       True,  False, False, False),

    # ── alliance_volunteer: contributed by allied party — limited access ──────
    *[('alliance_volunteer', slug, True, False, False, False) for slug in _GEO_MASTERS],
    ('alliance_volunteer', 'voter',              True,  True,  False, False),
    ('alliance_volunteer', 'booth',              True,  False, False, False),
    ('alliance_volunteer', 'volunteer',          True,  True,  False, False),
    ('alliance_volunteer', 'volunteer-activity', True,  True,  False, False),
    ('alliance_volunteer', 'voter-survey',       True,  True,  False, False),
    ('alliance_volunteer', 'attendance',         True,  True,  False, False),
    ('alliance_volunteer', 'poll-questions',     True,  False, False, False),
    ('alliance_volunteer', 'poll-results',       True,  False, False, False),

    # ── paid_volunteer: receives stipend — dedicated data entry ops ───────────
    *[('paid_volunteer', slug, True, False, False, False) for slug in _GEO_MASTERS],
    ('paid_volunteer', 'voter',              True,  True,  True,  False),
    ('paid_volunteer', 'booth',              True,  True,  False, False),
    ('paid_volunteer', 'beneficiary',        True,  True,  True,  False),
    ('paid_volunteer', 'volunteer',          True,  True,  False, False),
    ('paid_volunteer', 'event',              True,  True,  False, False),
    ('paid_volunteer', 'campaign',           True,  False, False, False),
    ('paid_volunteer', 'feedback',           True,  True,  False, False),
    ('paid_volunteer', 'volunteer-activity', True,  True,  False, False),
    ('paid_volunteer', 'voter-survey',       True,  True,  False, False),
    ('paid_volunteer', 'attendance',         True,  True,  False, False),
    ('paid_volunteer', 'assign-telecalling', True,  True,  False, False),
    ('paid_volunteer', 'poll-questions',     True,  False, False, False),
    ('paid_volunteer', 'poll-results',       True,  False, False, False),

    # ── social_media_volunteer: WhatsApp / online campaign only ──────────────
    *[('social_media_volunteer', slug, True, False, False, False) for slug in _GEO_MASTERS],
    ('social_media_volunteer', 'campaign',           True,  True,  False, False),
    ('social_media_volunteer', 'feedback',           True,  True,  False, False),
    ('social_media_volunteer', 'voter-survey',       True,  True,  False, False),
    ('social_media_volunteer', 'poll-questions',     True,  False, False, False),
    ('social_media_volunteer', 'poll-results',       True,  False, False, False),

    # ── community_leader: caste/community influencer — people management ──────
    *[('community_leader', slug, True, False, False, False) for slug in _GEO_MASTERS],
    ('community_leader', 'voter',              True,  True,  True,  False),
    ('community_leader', 'booth',              True,  False, False, False),
    ('community_leader', 'volunteer',          True,  True,  True,  False),
    ('community_leader', 'beneficiary',        True,  True,  True,  False),
    ('community_leader', 'feedback',           True,  True,  False, False),
    ('community_leader', 'commitment',         True,  True,  False, False),
    ('community_leader', 'grievance',          True,  True,  False, False),
    ('community_leader', 'voter-survey',       True,  True,  False, False),
    ('community_leader', 'attendance',         True,  True,  False, False),
    ('community_leader', 'poll-questions',     True,  False, False, False),
    ('community_leader', 'poll-results',       True,  False, False, False),

    # ── women_volunteer: women wing / community ───────────────────────────────
    *[('women_volunteer', slug, True, False, False, False) for slug in _GEO_MASTERS],
    ('women_volunteer', 'voter',              True,  True,  False, False),
    ('women_volunteer', 'beneficiary',        True,  True,  False, False),
    ('women_volunteer', 'voter-survey',       True,  True,  False, False),
    ('women_volunteer', 'attendance',         True,  True,  False, False),
    ('women_volunteer', 'poll-questions',     True,  False, False, False),
    ('women_volunteer', 'poll-results',       True,  False, False, False),

    # ── youth_volunteer: college/school student or youth wing ─────────────────
    *[('youth_volunteer', slug, True, False, False, False) for slug in _GEO_MASTERS],
    ('youth_volunteer', 'voter',              True,  True,  False, False),
    ('youth_volunteer', 'campaign',           True,  True,  False, False),
    ('youth_volunteer', 'voter-survey',       True,  True,  False, False),
    ('youth_volunteer', 'attendance',         True,  True,  False, False),
    ('youth_volunteer', 'poll-questions',     True,  False, False, False),
    ('youth_volunteer', 'poll-results',       True,  False, False, False),

    # ── temporary_volunteer: short-term / event-specific ─────────────────────
    *[('temporary_volunteer', slug, True, False, False, False) for slug in _GEO_MASTERS],
    ('temporary_volunteer', 'voter-survey',   True,  True,  False, False),
    ('temporary_volunteer', 'attendance',     True,  True,  False, False),
    ('temporary_volunteer', 'poll-questions', True,  False, False, False),
    ('temporary_volunteer', 'poll-results',   True,  False, False, False),
]


def seed_screen_permissions():
    """
    Idempotently create MainScreen, UserScreen, and UserScreenPermission records.
    Safe to run multiple times — uses get_or_create throughout.
    """
    # 1. Main screens
    ms_map = {}
    for ms in MAIN_SCREENS:
        obj, _ = MainScreen.objects.get_or_create(
            slug=ms['slug'],
            defaults={'name': ms['name'], 'icon': ms['icon'], 'order': ms['order']},
        )
        ms_map[ms['slug']] = obj

    # 2. User screens
    us_map = {}
    for (ms_slug, us_slug, name, icon, order) in USER_SCREENS:
        ms = ms_map[ms_slug]
        obj, _ = UserScreen.objects.get_or_create(
            slug=us_slug,
            defaults={'main_screen': ms, 'name': name, 'icon': icon, 'order': order},
        )
        us_map[us_slug] = obj

    # 3. Role permissions
    for (role, us_slug, can_view, can_add, can_edit, can_delete) in ROLE_PERMISSIONS:
        us = us_map.get(us_slug)
        if not us:
            continue
        UserScreenPermission.objects.update_or_create(
            role=role,
            user_screen=us,
            defaults={
                'can_view':   can_view,
                'can_add':    can_add,
                'can_edit':   can_edit,
                'can_delete': can_delete,
            },
        )


class Command(BaseCommand):
    help = 'Seed MainScreen, UserScreen, and UserScreenPermission defaults'

    def handle(self, *args, **options):
        self.stdout.write('Seeding screens and permissions...')
        seed_screen_permissions()
        self.stdout.write(self.style.SUCCESS(
            f'Done. {MainScreen.objects.count()} main screens, '
            f'{UserScreen.objects.count()} user screens, '
            f'{UserScreenPermission.objects.count()} permission records.'
        ))
