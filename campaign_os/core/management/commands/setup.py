"""
One-shot setup command for a fresh installation.
Usage: python manage.py setup

Runs:
  1. migrate
  2. seed_initial_data  (country, state, districts, constituencies, wards, booths, schemes, issues)
  3. seed_demo_users    (all role accounts + page permissions)
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Full setup: migrate + seed masters + seed login accounts'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('\n=== Step 1: Running migrations ==='))
        call_command('migrate', verbosity=1)

        self.stdout.write(self.style.MIGRATE_HEADING('\n=== Step 2: Seeding masters data ==='))
        call_command('seed_initial_data', verbosity=1)

        self.stdout.write(self.style.MIGRATE_HEADING('\n=== Step 3: Seeding login accounts ==='))
        call_command('seed_demo_users', verbosity=1)

        self.stdout.write(self.style.SUCCESS('\n✅ Setup complete! Login credentials:\n'))
        self.stdout.write('  Role              Username         Password')
        self.stdout.write('  ─────────────────────────────────────────────')
        self.stdout.write('  Admin             admin            Admin@1234')
        self.stdout.write('  District Head     district_head    Demo@1234')
        self.stdout.write('  Constituency Mgr  const_mgr        Demo@1234')
        self.stdout.write('  Booth Agent       booth_agent      Demo@1234')
        self.stdout.write('  Volunteer         volunteer1       Demo@1234')
        self.stdout.write('  Voter             voter1           Demo@1234')
        self.stdout.write('  Analyst           analyst1         Demo@1234')
        self.stdout.write('  Observer          observer1        Demo@1234')
