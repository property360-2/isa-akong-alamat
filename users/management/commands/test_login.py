from django.core.management.base import BaseCommand
from django.contrib.auth import authenticate
from users.models import User


class Command(BaseCommand):
    help = 'Test login credentials for seeded users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Test specific username',
        )
        parser.add_argument(
            '--password',
            type=str,
            default='password123',
            help='Password to test (default: password123)',
        )

    def handle(self, *args, **options):
        username = options.get('username')
        password = options['password']

        if username:
            # Test specific user
            self.test_user_login(username, password)
        else:
            # Test all seeded users
            self.test_all_users(password)

    def test_user_login(self, username, password):
        """Test login for a specific user"""
        self.stdout.write(f'\nTesting login for: {username}')
        self.stdout.write('-' * 60)

        try:
            user = User.objects.get(username=username)
            self.stdout.write(f'User found: {user.get_full_name() or user.username}')
            self.stdout.write(f'Email: {user.email}')
            self.stdout.write(f'Role: {user.role}')
            self.stdout.write(f'Staff: {user.is_staff}')
            self.stdout.write(f'Active: {user.is_active}')

            # Try authentication
            auth_user = authenticate(username=username, password=password)

            if auth_user:
                self.stdout.write(self.style.SUCCESS('\nAuthentication: SUCCESS'))
                self.stdout.write(self.style.SUCCESS(f'Login URL: http://127.0.0.1:8000/login/'))
                self.stdout.write(self.style.SUCCESS(f'Credentials: {username} / {password}'))
            else:
                self.stdout.write(self.style.ERROR('\nAuthentication: FAILED'))
                self.stdout.write(self.style.ERROR('Password may be incorrect'))

        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User "{username}" not found'))

    def test_all_users(self, password):
        """Test login for all users by role"""
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 60))
        self.stdout.write(self.style.SUCCESS('TESTING ALL SEEDED USERS'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

        roles = ['admin', 'registrar', 'professor', 'dean', 'admission', 'student']

        successful = 0
        failed = 0

        for role in roles:
            users = User.objects.filter(role=role).order_by('username')

            if users.exists():
                self.stdout.write(f'\n{role.upper()}S ({users.count()})'.center(60, '-'))

                for user in users:
                    auth_user = authenticate(username=user.username, password=password)

                    if auth_user:
                        status = self.style.SUCCESS('OK')
                        successful += 1
                    else:
                        status = self.style.ERROR('FAIL')
                        failed += 1

                    self.stdout.write(
                        f'  [{status}] {user.username:15} | {user.get_full_name():30} | {user.email}'
                    )

        # Summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS(f'SUMMARY: {successful} successful, {failed} failed'))
        self.stdout.write('=' * 60)

        if successful > 0:
            self.stdout.write('\n' + self.style.SUCCESS('All users can login with:'))
            self.stdout.write(self.style.WARNING(f'  Password: {password}'))
            self.stdout.write(self.style.SUCCESS(f'  Login URL: http://127.0.0.1:8000/login/'))
            self.stdout.write('')
            self.stdout.write('Example logins:')
            self.stdout.write('  admin1 / password123 -> Admin Dashboard')
            self.stdout.write('  registrar1 / password123 -> Registrar Dashboard')
            self.stdout.write('  prof1 / password123 -> Professor Dashboard')
            self.stdout.write('  student1 / password123 -> Student Dashboard')
            self.stdout.write('  dean1 / password123 -> Dean Dashboard')
            self.stdout.write('  admission1 / password123 -> Admission Dashboard')
