"""
Management command to seed VolunteerRole, VolunteerType, and CampaignActivityType master data.

Usage:
    python manage.py seed_masters           # idempotent upsert
    python manage.py seed_masters --clear   # wipe and recreate from scratch
"""
from django.core.management.base import BaseCommand
from campaign_os.masters.models import VolunteerRole, VolunteerType, CampaignActivityType


# ── Volunteer Roles ────────────────────────────────────────────────────────────
# Exactly the roles shown in the UI dropdown (screenshot order → sorted alpha in UI)
# (order, name, description)
VOLUNTEER_ROLES = [
    (1,  'AIADMK functionary',    'Active member or office bearer of AIADMK'),
    (2,  'BJP functionary',       'Active member or office bearer of BJP'),
    (3,  'Coordinator',           'Area or booth coordinator overseeing volunteers'),
    (4,  'DMK functionary',       'Active member or office bearer of DMK'),
    (5,  'Execution Army',        'Ground-level field execution team member'),
    (6,  'ITK volunteer',         'Volunteer under ITK / Iyarkai Thozhilalar Katchi wing'),
    (7,  'Local Volunteer',       'General local volunteer not attached to a specific wing'),
    (8,  'Panchayat incharge',    'In-charge for a panchayat or village cluster'),
    (9,  'PMK functionary',       'Active member or office bearer of PMK'),
    (10, 'Sakthiendra Volunteer', 'Volunteer directly under the Sakthiendra organisation'),
    (11, 'SK Local Volunteer',    'Street-level local volunteer under Sakthiendra wing'),
]

# ── Volunteer Types ────────────────────────────────────────────────────────────
VOLUNTEER_TYPES = [
    (1,  'Party Worker',          'Full-time dedicated party worker'),
    (2,  'Alliance Volunteer',    'Volunteer contributed by an allied party'),
    (3,  'Paid Volunteer',        'Volunteer receiving a stipend or daily wage'),
    (4,  'Social Media Volunteer','Primarily active on WhatsApp / social media channels'),
    (5,  'Community Leader',      'Influential person from a caste or community group'),
    (6,  'Women Volunteer',       'Female volunteer from any wing or community'),
    (7,  'Youth Volunteer',       'College / school student or youth wing member'),
    (8,  'Temporary Volunteer',   'Short-term volunteer for a specific event or period'),
]

# ── Campaign Activity Types ────────────────────────────────────────────────────
CAMPAIGN_ACTIVITY_TYPES = [
    (1,  'Door-to-Door Canvassing',  'Direct voter contact at residences'),
    (2,  'Nukkad Sabha',             'Small neighbourhood / street-corner meeting'),
    (3,  'Public Rally',             'Large public meeting or rally'),
    (4,  'Padayatra / Road Show',    'Walking procession or vehicle road show'),
    (5,  'Pamphlet Distribution',    'Distribution of printed campaign material'),
    (6,  'Wall Painting',            'Campaign wall painting and poster work'),
    (7,  'Volunteer Meeting',        'Internal volunteer coordination meeting'),
    (8,  'Booth Committee Meeting',  'Meeting with booth-level committee members'),
    (9,  "Women's Group Meeting",    'Meeting targeting women voters / SHG groups'),
    (10, "Farmers' Meeting",         'Meeting targeting the farming community'),
    (11, 'Youth Meeting',            'Meeting targeting young / first-time voters'),
    (12, 'Social Media Drive',       'Coordinated social media / WhatsApp campaign activity'),
    (13, 'Voter Slip Distribution',  'Distributing voter slip / ID reminder cards'),
    (14, 'Telecalling Session',      'Outbound phone calling to voters'),
    (15, 'Survey / Opinion Poll',    'Field survey or voter opinion collection'),
    (16, 'Scheme Awareness Camp',    'Camp explaining central / state government schemes'),
    (17, 'Beneficiary Meet',         'Meeting with scheme beneficiaries'),
    (18, 'Leader Visit',             'Visit / road show by candidate or party leader'),
    (19, 'Cultural Programme',       'Cultural / entertainment event used for outreach'),
    (20, 'Other',                    'Any other campaign activity not listed above'),
]


def _upsert(model, rows, name_idx=1, desc_idx=2):
    """Upsert rows into model. Returns (created, updated) counts."""
    created = updated = 0
    for row in rows:
        order, name, desc = row[0], row[name_idx], row[desc_idx]
        obj, is_new = model.objects.get_or_create(
            name=name,
            defaults={'description': desc, 'order': order},
        )
        if is_new:
            created += 1
        else:
            changed = False
            if obj.order != order:
                obj.order = order
                changed = True
            if obj.description != desc:
                obj.description = desc
                changed = True
            if changed:
                obj.save(update_fields=['order', 'description'])
                updated += 1
    return created, updated


class Command(BaseCommand):
    help = 'Seed VolunteerRole, VolunteerType, and CampaignActivityType master data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete all existing records before seeding (full reset)',
        )

    def handle(self, *args, **options):
        if options['clear']:
            VolunteerRole.objects.all().delete()
            VolunteerType.objects.all().delete()
            CampaignActivityType.objects.all().delete()
            self.stdout.write('  Cleared existing VolunteerRole, VolunteerType, CampaignActivityType records.')

        self.stdout.write('Seeding master data...')

        r_c, r_u = _upsert(VolunteerRole, VOLUNTEER_ROLES)
        self.stdout.write(
            f'  VolunteerRole    : {VolunteerRole.objects.count()} total '
            f'({r_c} created, {r_u} updated)'
        )

        t_c, t_u = _upsert(VolunteerType, VOLUNTEER_TYPES)
        self.stdout.write(
            f'  VolunteerType    : {VolunteerType.objects.count()} total '
            f'({t_c} created, {t_u} updated)'
        )

        a_c, a_u = _upsert(CampaignActivityType, CAMPAIGN_ACTIVITY_TYPES)
        self.stdout.write(
            f'  CampaignActivity : {CampaignActivityType.objects.count()} total '
            f'({a_c} created, {a_u} updated)'
        )

        self.stdout.write(self.style.SUCCESS('Done. Master data seeded successfully.'))
