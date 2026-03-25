"""
Management command to seed demo users for each role type.
Usage: python manage.py seed_demo_users
"""
from django.core.management.base import BaseCommand
from campaign_os.accounts.models import User, PagePermission, seed_default_permissions


DEMO_USERS = [
    {
        'username': 'admin',
        'password': 'Admin@1234',
        'first_name': 'System',
        'last_name': 'Admin',
        'email': 'admin@campaign.local',
        'role': 'admin',
        'is_staff': True,
        'is_superuser': True,
    },
    {
        'username': 'district_head',
        'password': 'Demo@1234',
        'first_name': 'Rajesh',
        'last_name': 'Kumar',
        'email': 'rajesh@campaign.local',
        'role': 'district_head',
        'phone': '9876543001',
    },
    {
        'username': 'const_mgr',
        'password': 'Demo@1234',
        'first_name': 'Priya',
        'last_name': 'Sharma',
        'email': 'priya@campaign.local',
        'role': 'constituency_mgr',
        'phone': '9876543002',
    },
    {
        'username': 'booth_agent',
        'password': 'Demo@1234',
        'first_name': 'Murugan',
        'last_name': 'S',
        'email': 'murugan@campaign.local',
        'role': 'booth_agent',
        'phone': '9876543003',
    },
    {
        'username': 'volunteer1',
        'password': 'Demo@1234',
        'first_name': 'Anitha',
        'last_name': 'R',
        'email': 'anitha@campaign.local',
        'role': 'volunteer',
        'phone': '9876543004',
    },
    {
        'username': 'voter1',
        'password': 'Demo@1234',
        'first_name': 'Selvam',
        'last_name': 'P',
        'email': 'selvam@campaign.local',
        'role': 'voter',
        'phone': '9876543005',
    },
    {
        'username': 'analyst1',
        'password': 'Demo@1234',
        'first_name': 'Kavitha',
        'last_name': 'M',
        'email': 'kavitha@campaign.local',
        'role': 'analyst',
        'phone': '9876543006',
    },
    {
        'username': 'observer1',
        'password': 'Demo@1234',
        'first_name': 'Ravi',
        'last_name': 'N',
        'email': 'ravi@campaign.local',
        'role': 'observer',
        'phone': '9876543007',
    },
]


class Command(BaseCommand):
    help = 'Seed demo users for each role type and set up default permissions'

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0

        for u in DEMO_USERS:
            is_staff = u.pop('is_staff', False)
            is_superuser = u.pop('is_superuser', False)
            password = u.pop('password')

            user, created = User.objects.get_or_create(
                username=u['username'],
                defaults={**u, 'is_staff': is_staff, 'is_superuser': is_superuser}
            )
            user.set_password(password)
            user.is_staff = is_staff
            user.is_superuser = is_superuser
            for k, v in u.items():
                setattr(user, k, v)
            user.save()

            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'  Created: {user.username} ({user.role})'))
            else:
                updated_count += 1
                self.stdout.write(f'  Updated: {user.username} ({user.role})')

        self.stdout.write(f'\nUsers: {created_count} created, {updated_count} updated')

        # Seed default permissions
        self.stdout.write('\nSeeding default permissions...')
        seed_default_permissions()
        self.stdout.write(self.style.SUCCESS('Default permissions seeded.'))

        self.stdout.write(self.style.SUCCESS('\nDemo credentials:'))
        self.stdout.write('  admin / Admin@1234')
        self.stdout.write('  district_head / Demo@1234')
        self.stdout.write('  const_mgr / Demo@1234')
        self.stdout.write('  booth_agent / Demo@1234')
        self.stdout.write('  volunteer1 / Demo@1234')
        self.stdout.write('  voter1 / Demo@1234')
        self.stdout.write('  analyst1 / Demo@1234')
        self.stdout.write('  observer1 / Demo@1234')
