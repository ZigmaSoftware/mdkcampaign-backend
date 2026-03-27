"""
Django management command to seed initial data
Run with: python manage.py seed_initial_data
"""
from django.core.management.base import BaseCommand
from campaign_os.masters.models import (
    Country, State, District, Constituency, Ward, Booth, Party, Scheme, Issue, TaskCategory
)


class Command(BaseCommand):
    help = 'Seed initial data for Tamil Nadu election campaign system'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Seeding initial data...'))

        # ── Country ──────────────────────────────────────────────────
        country, _ = Country.objects.get_or_create(name='India', code='IND')
        self.stdout.write(f'  Country: {country.name}')

        # ── State ────────────────────────────────────────────────────
        state, _ = State.objects.get_or_create(country=country, name='Tamil Nadu', code='TN')
        self.stdout.write(f'  State: {state.name}')

        # ── Districts ────────────────────────────────────────────────
        erode, _    = District.objects.get_or_create(state=state, code='ERD',  defaults={'name': 'Erode'})
        coim, _     = District.objects.get_or_create(state=state, code='CBE',  defaults={'name': 'Coimbatore'})
        salem, _    = District.objects.get_or_create(state=state, code='SLM',  defaults={'name': 'Salem'})
        namak, _    = District.objects.get_or_create(state=state, code='NMK',  defaults={'name': 'Namakkal'})
        self.stdout.write(f'  Districts: {erode.name}, {coim.name}, {salem.name}, {namak.name}')

        # ── Constituencies ───────────────────────────────────────────
        mod, _  = Constituency.objects.get_or_create(district=erode, code='MOD', defaults={'name': 'Modakkurichi', 'election_type': 'assembly'})
        ere, _  = Constituency.objects.get_or_create(district=erode, code='ERE', defaults={'name': 'Erode East',    'election_type': 'assembly'})
        erw, _  = Constituency.objects.get_or_create(district=erode, code='ERW', defaults={'name': 'Erode West',    'election_type': 'assembly'})
        siv, _  = Constituency.objects.get_or_create(district=erode, code='SIV', defaults={'name': 'Sivagiri',      'election_type': 'assembly'})
        self.stdout.write(f'  Constituencies: {mod.name}, {ere.name}, {erw.name}, {siv.name}')

        # ── Parties ──────────────────────────────────────────────────
        bjp, _    = Party.objects.get_or_create(code='BJP',    defaults={'name': 'Bharatiya Janata Party',                       'abbreviation': 'BJP',    'primary_color': '#FF9933', 'is_national': True})
        dmk, _    = Party.objects.get_or_create(code='DMK',    defaults={'name': 'Dravida Munnetra Kazhagam',                    'abbreviation': 'DMK',    'primary_color': '#E31837'})
        aidmk, _  = Party.objects.get_or_create(code='ADMK',   defaults={'name': 'All India Anna Dravida Munnetra Kazhagam',     'abbreviation': 'AIADMK', 'primary_color': '#006633'})
        cong, _   = Party.objects.get_or_create(code='INC',    defaults={'name': 'Indian National Congress',                     'abbreviation': 'INC',    'primary_color': '#138808', 'is_national': True})
        self.stdout.write(f'  Parties: BJP, DMK, AIADMK, INC')

        # ── Wards for Modakkurichi ────────────────────────────────────
        ward_data = [
            {'name': 'Modakkurichi Town',   'code': 'W001'},
            {'name': 'Sivagiri Village',    'code': 'W002'},
            {'name': 'Kunnathur',           'code': 'W003'},
            {'name': 'Kavindapadi',         'code': 'W004'},
            {'name': 'Thalavadi',           'code': 'W005'},
            {'name': 'Bhavani Road',        'code': 'W006'},
            {'name': 'Alamelumanagar',      'code': 'W007'},
            {'name': 'Dhasarathapuram',     'code': 'W008'},
            {'name': 'Periyasemur',         'code': 'W009'},
            {'name': 'Nallanahalli',        'code': 'W010'},
        ]
        wards = {}
        for wd in ward_data:
            w, _ = Ward.objects.get_or_create(constituency=mod, code=wd['code'], defaults={'name': wd['name']})
            wards[wd['code']] = w
        self.stdout.write(f'  Wards: {len(wards)} wards for Modakkurichi')

        # ── Wards for Sivagiri ───────────────────────────────────────
        siv_ward_data = [
            {'name': 'Sivagiri Central',  'code': 'S001'},
            {'name': 'Sivagiri North',    'code': 'S002'},
            {'name': 'Vellottamparai',    'code': 'S003'},
        ]
        for wd in siv_ward_data:
            Ward.objects.get_or_create(constituency=siv, code=wd['code'], defaults={'name': wd['name']})
        self.stdout.write(f'  Wards: 3 wards for Sivagiri')

        # ── Booths for Modakkurichi ──────────────────────────────────
        booth_data = [
            # W001 - Modakkurichi Town
            {'ward': 'W001', 'number': '001', 'name': 'Modakkurichi Town Panchayat School',         'total_voters': 892,  'male_voters': 450, 'female_voters': 442},
            {'ward': 'W001', 'number': '002', 'name': 'Modakkurichi Higher Secondary School',       'total_voters': 1021, 'male_voters': 515, 'female_voters': 506},
            {'ward': 'W001', 'number': '003', 'name': 'Modakkurichi Municipal Office Hall',         'total_voters': 776,  'male_voters': 390, 'female_voters': 386},
            # W002 - Sivagiri Village
            {'ward': 'W002', 'number': '004', 'name': 'Sivagiri Village Panchayat Office',          'total_voters': 654,  'male_voters': 330, 'female_voters': 324},
            {'ward': 'W002', 'number': '005', 'name': 'Sivagiri Primary School',                   'total_voters': 812,  'male_voters': 408, 'female_voters': 404},
            # W003 - Kunnathur
            {'ward': 'W003', 'number': '006', 'name': 'Kunnathur Panchayat School',                 'total_voters': 734,  'male_voters': 370, 'female_voters': 364},
            {'ward': 'W003', 'number': '007', 'name': 'Kunnathur Community Hall',                  'total_voters': 698,  'male_voters': 352, 'female_voters': 346},
            # W004 - Kavindapadi
            {'ward': 'W004', 'number': '008', 'name': 'Kavindapadi Town Panchayat Office',          'total_voters': 945,  'male_voters': 476, 'female_voters': 469},
            {'ward': 'W004', 'number': '009', 'name': 'Kavindapadi Higher Secondary School',        'total_voters': 1102, 'male_voters': 556, 'female_voters': 546},
            {'ward': 'W004', 'number': '010', 'name': 'Kavindapadi Elementary School',             'total_voters': 823,  'male_voters': 415, 'female_voters': 408},
            # W005 - Thalavadi
            {'ward': 'W005', 'number': '011', 'name': 'Thalavadi Tribal Welfare School',            'total_voters': 512,  'male_voters': 258, 'female_voters': 254},
            {'ward': 'W005', 'number': '012', 'name': 'Thalavadi Village Office',                  'total_voters': 447,  'male_voters': 225, 'female_voters': 222},
            # W006 - Bhavani Road
            {'ward': 'W006', 'number': '013', 'name': 'Bhavani Road School',                       'total_voters': 1234, 'male_voters': 622, 'female_voters': 612},
            {'ward': 'W006', 'number': '014', 'name': 'Bhavani Overbridge Community Hall',         'total_voters': 986,  'male_voters': 496, 'female_voters': 490},
            {'ward': 'W006', 'number': '015', 'name': 'Bhavani Road South Panchayat School',       'total_voters': 875,  'male_voters': 441, 'female_voters': 434},
            # W007 - Alamelumanagar
            {'ward': 'W007', 'number': '016', 'name': 'Alamelumanagar Panchayat Union School',     'total_voters': 761,  'male_voters': 384, 'female_voters': 377},
            {'ward': 'W007', 'number': '017', 'name': 'Alamelumanagar Community Centre',           'total_voters': 689,  'male_voters': 347, 'female_voters': 342},
            # W008 - Dhasarathapuram
            {'ward': 'W008', 'number': '018', 'name': 'Dhasarathapuram Primary School',            'total_voters': 534,  'male_voters': 269, 'female_voters': 265},
            {'ward': 'W008', 'number': '019', 'name': 'Dhasarathapuram Village Panchayat',         'total_voters': 612,  'male_voters': 308, 'female_voters': 304},
            # W009 - Periyasemur
            {'ward': 'W009', 'number': '020', 'name': 'Periyasemur Government School',             'total_voters': 823,  'male_voters': 414, 'female_voters': 409},
            {'ward': 'W009', 'number': '021', 'name': 'Periyasemur Town Hall',                     'total_voters': 745,  'male_voters': 375, 'female_voters': 370},
            # W010 - Nallanahalli
            {'ward': 'W010', 'number': '022', 'name': 'Nallanahalli Elementary School',            'total_voters': 467,  'male_voters': 235, 'female_voters': 232},
            {'ward': 'W010', 'number': '023', 'name': 'Nallanahalli Panchayat Office',             'total_voters': 389,  'male_voters': 196, 'female_voters': 193},
        ]

        booth_count = 0
        for bd in booth_data:
            ward = wards.get(bd['ward'])
            if not ward:
                continue
            code = f"B{bd['number']}"
            b, created = Booth.objects.get_or_create(
                ward=ward,
                number=bd['number'],
                defaults={
                    'name':          bd['name'],
                    'code':          code,
                    'address':       bd['name'],
                    'total_voters':  bd['total_voters'],
                    'male_voters':   bd['male_voters'],
                    'female_voters': bd['female_voters'],
                    'status':        'pending',
                    'sentiment':     'neutral',
                }
            )
            if created:
                booth_count += 1
        self.stdout.write(f'  Booths: {booth_count} new booths created for Modakkurichi')

        # ── Schemes ──────────────────────────────────────────────────
        schemes = [
            {'name': 'PM Awas Yojana (PMAY)',   'description': 'Pradhan Mantri Awas Yojana – Housing for All', 'scheme_type': 'central', 'responsible_ministry': 'Ministry of Housing'},
            {'name': 'Ayushman Bharat',          'description': 'Health insurance cover of ₹5 lakh per family', 'scheme_type': 'central', 'responsible_ministry': 'Ministry of Health'},
            {'name': 'PM Kisan Samman Nidhi',    'description': '₹6000/year direct income support for farmers', 'scheme_type': 'central', 'responsible_ministry': 'Ministry of Agriculture'},
            {'name': 'Ujjwala Yojana 2.0',       'description': 'Free LPG connection to BPL women', 'scheme_type': 'central', 'responsible_ministry': 'Ministry of Petroleum'},
            {'name': 'Skill India Mission',      'description': 'Free skill development training for youth', 'scheme_type': 'central', 'responsible_ministry': 'Ministry of Skill Development'},
            {'name': 'Arram Free Coaching',      'description': 'Free NEET/JEE coaching by Arram Trust', 'scheme_type': 'party', 'responsible_ministry': 'Arram Charity Trust'},
            {'name': 'Arram Jobs Portal',        'description': 'Employment placement programme by Arram Trust', 'scheme_type': 'party', 'responsible_ministry': 'Arram Charity Trust'},
        ]
        for s in schemes:
            Scheme.objects.get_or_create(name=s['name'], defaults=s)
        self.stdout.write(f'  Schemes: {len(schemes)} schemes seeded')

        # ── Issues ───────────────────────────────────────────────────
        issues = [
            {'name': 'Unemployment / Jobs',      'description': 'Lack of local employment opportunities for youth', 'category': 'other',          'priority': 10},
            {'name': 'Road Infrastructure',      'description': 'Poor road conditions in villages and towns',       'category': 'road',           'priority': 9},
            {'name': 'Healthcare Access',         'description': 'Lack of hospitals and primary health centres',    'category': 'health',         'priority': 8},
            {'name': 'Farmers / PM Kisan',        'description': 'Delay in PM Kisan disbursement and crop issues',  'category': 'other',          'priority': 8},
            {'name': 'Drinking Water',            'description': 'Inadequate clean water supply in rural areas',    'category': 'water',          'priority': 7},
            {'name': 'Housing / PMAY',            'description': 'Pending PMAY applications and housing issues',    'category': 'other',          'priority': 7},
            {'name': 'Women Safety',              'description': 'Safety concerns for women especially at night',   'category': 'other',          'priority': 6},
            {'name': 'Education Quality',         'description': 'Poor school infrastructure and teacher shortage', 'category': 'education',      'priority': 6},
            {'name': 'Electricity Supply',        'description': 'Irregular power supply and high tariffs',         'category': 'electricity',    'priority': 5},
            {'name': 'LPG / Ujjwala',             'description': 'Delay in Ujjwala connections and high cylinder costs', 'category': 'other',   'priority': 5},
        ]
        for i in issues:
            Issue.objects.get_or_create(name=i['name'], defaults=i)
        self.stdout.write(f'  Issues: {len(issues)} issues seeded')

        # ── Task Categories ───────────────────────────────────────────
        task_categories = [
            {'name': 'Material Preparation', 'color': '#7c3aed', 'icon': 'ph-package',           'priority': 1,  'description': 'Preparing banners, pamphlets, and campaign materials'},
            {'name': 'Distribution',          'color': '#ea580c', 'icon': 'ph-truck',              'priority': 2,  'description': 'Distributing materials, gifts, or items to voters'},
            {'name': 'Event Coordination',    'color': '#0d9488', 'icon': 'ph-calendar-star',      'priority': 3,  'description': 'Planning and managing campaign events and rallies'},
            {'name': 'Voter Outreach',        'color': '#2563eb', 'icon': 'ph-handshake',          'priority': 4,  'description': 'Door-to-door canvassing and direct voter contact'},
            {'name': 'Social Media',          'color': '#db2777', 'icon': 'ph-share-network',      'priority': 5,  'description': 'Managing social media posts, reels, and campaigns'},
            {'name': 'Logistics',             'color': '#b45309', 'icon': 'ph-van',                'priority': 6,  'description': 'Transport, vehicles, and logistics arrangements'},
            {'name': 'Communication',         'color': '#0891b2', 'icon': 'ph-chat-circle-dots',   'priority': 7,  'description': 'Phone banking, WhatsApp, and communication tasks'},
            {'name': 'Data Entry',            'color': '#475569', 'icon': 'ph-database',           'priority': 8,  'description': 'Entering voter data, survey results, and records'},
            {'name': 'Finance',               'color': '#16a34a', 'icon': 'ph-currency-inr',       'priority': 9,  'description': 'Budget tracking, expense management, and finance tasks'},
            {'name': 'Booth Management',      'color': '#dc2626', 'icon': 'ph-map-pin',            'priority': 10, 'description': 'Booth-level coordination and agent management'},
            {'name': 'Volunteer Coordination','color': '#9333ea', 'icon': 'ph-users-three',        'priority': 11, 'description': 'Organising and managing campaign volunteers'},
            {'name': 'Other',                 'color': '#6b7280', 'icon': 'ph-dots-three-outline', 'priority': 99, 'description': 'Miscellaneous tasks not covered by other categories'},
        ]
        created_cats = 0
        for cat in task_categories:
            _, created = TaskCategory.objects.get_or_create(
                name=cat['name'],
                defaults={k: v for k, v in cat.items() if k != 'name'},
            )
            if created:
                created_cats += 1
        self.stdout.write(f'  Task Categories: {len(task_categories)} total, {created_cats} newly created')

        total_voters = sum(b['total_voters'] for b in booth_data)
        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Seed complete! '
            f'{len(ward_data)} wards, {len(booth_data)} booths, '
            f'~{total_voters:,} total voters registered for Modakkurichi.'
        ))
