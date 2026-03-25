"""
Seed initial opinion poll data for Modakkurichi Constituency 100
"""
from django.core.management.base import BaseCommand
from campaign_os.polls.models import Poll, PollOption


class Command(BaseCommand):
    help = 'Seed initial opinion poll data'

    def handle(self, *args, **options):
        poll, created = Poll.objects.get_or_create(
            title='Modakkurichi Constituency Opinion Poll',
            defaults={
                'title_ta': 'மொடக்குறிச்சி தொகுதி கருத்துக் கணிப்பு',
                'constituency_name': 'Modakkurichi',
                'constituency_no': 100,
                'is_active': True,
            }
        )
        if not created:
            self.stdout.write('Poll already exists, updating options...')

        # Clear existing options
        poll.options.all().delete()

        # Q1 - Alliance options
        q1_options = [
            {'key': 'bjp',    'name': 'ADMK + BJP',          'name_ta': 'பாஜக + அதிமுக கூட்டணி',     'sub_label': '', 'icon_bg': 'linear-gradient(135deg,#FF9933,#e07010)', 'bar_color': '#FF9933', 'is_winner': True,  'display_order': 1},
            {'key': 'inc',    'name': 'DMK + INC',            'name_ta': 'காங்கிரஸ் + திமுக கூட்டணி', 'sub_label': '',                                       'icon_bg': 'linear-gradient(135deg,#1a56db,#1e40af)', 'bar_color': '#3b82f6', 'is_winner': False, 'display_order': 2},
            {'key': 'tvk',    'name': 'TVK',                  'name_ta': 'தமிழக வெற்றி கழகம்',        'sub_label': '',                                       'icon_bg': 'linear-gradient(135deg,#d97706,#92400e)', 'bar_color': '#f59e0b', 'is_winner': False, 'display_order': 3},
            {'key': 'ntk',    'name': 'Naam Tamilar Katchi',  'name_ta': 'நாம் தமிழர் கட்சி',         'sub_label': '',                                       'icon_bg': 'linear-gradient(135deg,#dc2626,#991b1b)', 'bar_color': '#ef4444', 'is_winner': False, 'display_order': 4},
            {'key': 'others', 'name': 'Others / வேறு',       'name_ta': 'சுயேட்சை / Independent',     'sub_label': '',                                       'icon_bg': 'linear-gradient(135deg,#4b5563,#374151)', 'bar_color': '#6b7280', 'is_winner': False, 'display_order': 5},
        ]
        for opt in q1_options:
            PollOption.objects.create(poll=poll, question_no=1, **opt)

        # Q2 - Candidate options
        q2_options = [
            {'key': 'kirthika', 'name': 'Kirthika Shivkumar', 'sub_label': 'BJP · Constituency 100',       'icon_bg': 'linear-gradient(135deg,#FF9933,#e07010)', 'bar_color': '#FF9933', 'display_order': 1},
            {'key': 'dmk',      'name': 'DMK Candidate',      'sub_label': 'DMK + INC Alliance',            'icon_bg': 'linear-gradient(135deg,#1a56db,#1e40af)', 'bar_color': '#3b82f6', 'display_order': 2},
            {'key': 'tvk',      'name': 'TVK Candidate',      'sub_label': 'Tamilaga Vettri Kazhagam',      'icon_bg': 'linear-gradient(135deg,#d97706,#92400e)', 'bar_color': '#f59e0b', 'display_order': 3},
            {'key': 'ntk',      'name': 'NTK Candidate',      'sub_label': 'Naam Tamilar Katchi',            'icon_bg': 'linear-gradient(135deg,#dc2626,#991b1b)', 'bar_color': '#ef4444', 'display_order': 4},
        ]
        for opt in q2_options:
            PollOption.objects.create(poll=poll, question_no=2, **opt)

        self.stdout.write(self.style.SUCCESS(f'Poll seeded: {poll.title} (id={poll.id})'))
        self.stdout.write(f'  Q1 options: {len(q1_options)}')
        self.stdout.write(f'  Q2 options: {len(q2_options)}')
