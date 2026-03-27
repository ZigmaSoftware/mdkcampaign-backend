"""
Seed default Task Categories.
Run with: python manage.py seed_task_categories
"""
from django.core.management.base import BaseCommand
from campaign_os.masters.models import TaskCategory

TASK_CATEGORIES = [
    {'name': 'Material Preparation',  'color': '#7c3aed', 'icon': 'ph-package',           'priority': 1,  'description': 'Preparing banners, pamphlets, and campaign materials'},
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


class Command(BaseCommand):
    help = 'Seed default Task Categories for campaign task management'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete all existing task categories before seeding',
        )

    def handle(self, *args, **options):
        if options['reset']:
            deleted, _ = TaskCategory.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'  Deleted {deleted} existing task categories'))

        created_count = 0
        updated_count = 0

        for cat in TASK_CATEGORIES:
            name = cat['name']
            defaults = {k: v for k, v in cat.items() if k != 'name'}
            obj, created = TaskCategory.objects.get_or_create(name=name, defaults=defaults)
            if created:
                created_count += 1
                self.stdout.write(f'  + Created: {name}')
            else:
                # Update fields if already exists
                for k, v in defaults.items():
                    setattr(obj, k, v)
                obj.save(update_fields=list(defaults.keys()))
                updated_count += 1
                self.stdout.write(f'  ~ Updated: {name}')

        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Task categories seeded: {created_count} created, {updated_count} updated.'
        ))
