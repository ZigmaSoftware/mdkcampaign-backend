"""
Django management command to seed user data
Run with: python manage.py seed_user_data
Creates admin, district heads, constituency managers, booth agents, and volunteers.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from campaign_os.accounts.models import User
from campaign_os.masters.models import District, Constituency, Booth, State


DEFAULT_PASSWORD = 'Campaign@123'


class Command(BaseCommand):
    help = 'Seed user data for Tamil Nadu election campaign system'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Seeding user data...'))

        try:
            state = State.objects.get(code='TN')
            erode = District.objects.get(code='ERD')
            mod   = Constituency.objects.get(code='MOD')
            ere   = Constituency.objects.get(code='ERE')
            erw   = Constituency.objects.get(code='ERW')
            siv   = Constituency.objects.get(code='SIV')
        except (State.DoesNotExist, District.DoesNotExist, Constituency.DoesNotExist) as e:
            self.stdout.write(self.style.ERROR(
                f'Master data missing: {e}\nRun seed_initial_data first.'
            ))
            return

        # ── Admin ─────────────────────────────────────────────────────
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'first_name': 'System',
                'last_name':  'Admin',
                'email':      'admin@campaign.local',
                'role':       'admin',
                'is_staff':   True,
                'is_superuser': True,
                'password':   make_password(DEFAULT_PASSWORD),
                'state':      state,
            }
        )
        self._log(created, 'Admin', admin.username)

        # ── Analyst ───────────────────────────────────────────────────
        analyst, created = User.objects.get_or_create(
            username='analyst01',
            defaults={
                'first_name': 'Karthik',
                'last_name':  'Analyst',
                'email':      'analyst@campaign.local',
                'role':       'analyst',
                'password':   make_password(DEFAULT_PASSWORD),
                'state':      state,
                'district':   erode,
            }
        )
        self._log(created, 'Analyst', analyst.username)

        # ── District Head ─────────────────────────────────────────────
        dh_erode, created = User.objects.get_or_create(
            username='dh_erode',
            defaults={
                'first_name': 'Murugan',
                'last_name':  'Erode',
                'email':      'dh.erode@campaign.local',
                'role':       'district_head',
                'password':   make_password(DEFAULT_PASSWORD),
                'state':      state,
                'district':   erode,
            }
        )
        self._log(created, 'District Head', dh_erode.username)

        # ── Constituency Managers ─────────────────────────────────────
        cm_data = [
            ('cm_mod', 'Selvam',    'Modakkurichi', 'cm.mod@campaign.local', mod),
            ('cm_ere', 'Rajan',     'ErodeEast',    'cm.ere@campaign.local', ere),
            ('cm_erw', 'Prabhu',    'ErodeWest',    'cm.erw@campaign.local', erw),
            ('cm_siv', 'Anbarasan', 'Sivagiri',     'cm.siv@campaign.local', siv),
        ]
        for username, first_name, last_name, email, const in cm_data:
            u, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name':   first_name,
                    'last_name':    last_name,
                    'email':        email,
                    'role':         'constituency_mgr',
                    'password':     make_password(DEFAULT_PASSWORD),
                    'state':        state,
                    'district':     erode,
                    'constituency': const,
                }
            )
            self._log(created, 'Constituency Manager', u.username)

        # ── Booth Agents (one per booth in Modakkurichi) ──────────────
        booths = Booth.objects.filter(ward__constituency=mod).order_by('number')
        agent_names = [
            ('Arun',       'Kumar'),
            ('Balu',       'Raj'),
            ('Chandru',    'Vel'),
            ('Dinesh',     'Mani'),
            ('Elan',       'Selvan'),
            ('Faisal',     'Ahmed'),
            ('Gopal',      'Krishnan'),
            ('Hari',       'Prasad'),
            ('Ilavarasan', 'R'),
            ('Jegan',      'K'),
            ('Kalaivanan', 'S'),
            ('Loganathan', 'P'),
            ('Manoj',      'T'),
            ('Nandha',     'Kumar'),
            ('Oviya',      'Devi'),
            ('Pradeep',    'R'),
            ('Rajesh',     'M'),
            ('Suresh',     'N'),
            ('Thilak',     'V'),
            ('Umar',       'Farooq'),
            ('Vijay',      'S'),
            ('Winson',     'A'),
            ('Xavier',     'D'),
        ]
        agent_count = 0
        for booth, (first, last) in zip(booths, agent_names):
            username = f'agent_{booth.number}'
            u, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name':   first,
                    'last_name':    last,
                    'email':        f'{username}@campaign.local',
                    'role':         'booth_agent',
                    'password':     make_password(DEFAULT_PASSWORD),
                    'state':        state,
                    'district':     erode,
                    'constituency': mod,
                    'booth':        booth,
                }
            )
            if created:
                # Assign as primary agent on the booth
                booth.primary_agent = u
                booth.save(update_fields=['primary_agent'])
                agent_count += 1
        self.stdout.write(f'  Booth Agents: {agent_count} new agents created')

        # ── Volunteers ────────────────────────────────────────────────
        volunteer_data = [
            ('vol_001', 'Akila',    'S',        'vol001@campaign.local', mod),
            ('vol_002', 'Bharath',  'V',        'vol002@campaign.local', mod),
            ('vol_003', 'Chitra',   'M',        'vol003@campaign.local', mod),
            ('vol_004', 'Deepak',   'R',        'vol004@campaign.local', mod),
            ('vol_005', 'Eswari',   'K',        'vol005@campaign.local', mod),
            ('vol_006', 'Farhan',   'A',        'vol006@campaign.local', siv),
            ('vol_007', 'Geetha',   'P',        'vol007@campaign.local', siv),
            ('vol_008', 'Harini',   'T',        'vol008@campaign.local', ere),
            ('vol_009', 'Ilakkiya', 'N',        'vol009@campaign.local', ere),
            ('vol_010', 'Jeeva',    'L',        'vol010@campaign.local', erw),
        ]
        vol_count = 0
        for username, first, last, email, const in volunteer_data:
            u, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name':   first,
                    'last_name':    last,
                    'email':        email,
                    'role':         'volunteer',
                    'password':     make_password(DEFAULT_PASSWORD),
                    'state':        state,
                    'district':     erode,
                    'constituency': const,
                }
            )
            if created:
                vol_count += 1
        self.stdout.write(f'  Volunteers: {vol_count} new volunteers created')

        self.stdout.write(self.style.SUCCESS(
            f'\n✅ User seed complete!\n'
            f'   Default password for all users: {DEFAULT_PASSWORD}\n'
            f'   Roles created: admin, analyst, district_head, constituency_mgr, booth_agent, volunteer'
        ))

    def _log(self, created, role, username):
        status = 'created' if created else 'already exists'
        self.stdout.write(f'  {role}: {username} ({status})')
