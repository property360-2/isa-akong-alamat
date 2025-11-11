from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from users.models import User
from enrollment.models import Student
from academics.models import Program, Curriculum


class Command(BaseCommand):
    help = 'Seed the database with test users for all roles'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing users before seeding (except superusers)',
        )
        parser.add_argument(
            '--password',
            type=str,
            default='password123',
            help='Default password for all seeded users (default: password123)',
        )

    def handle(self, *args, **options):
        clear = options['clear']
        default_password = options['password']

        self.stdout.write(self.style.WARNING('Starting user seeding...'))

        # Clear existing users if requested
        if clear:
            deleted_count = User.objects.filter(is_superuser=False).delete()[0]
            self.stdout.write(self.style.WARNING(f'Cleared {deleted_count} existing users'))

        # Users to create
        users_data = [
            # Admins
            {
                'username': 'admin1',
                'email': 'admin1@richwell.edu',
                'first_name': 'John',
                'last_name': 'Administrator',
                'role': 'admin',
                'is_staff': True,
            },
            {
                'username': 'admin2',
                'email': 'admin2@richwell.edu',
                'first_name': 'Jane',
                'last_name': 'Admin',
                'role': 'admin',
                'is_staff': True,
            },

            # Registrars
            {
                'username': 'registrar1',
                'email': 'registrar1@richwell.edu',
                'first_name': 'Maria',
                'last_name': 'Santos',
                'role': 'registrar',
                'is_staff': True,
            },
            {
                'username': 'registrar2',
                'email': 'registrar2@richwell.edu',
                'first_name': 'Robert',
                'last_name': 'Cruz',
                'role': 'registrar',
                'is_staff': True,
            },

            # Professors
            {
                'username': 'prof1',
                'email': 'prof1@richwell.edu',
                'first_name': 'Dr. Michael',
                'last_name': 'Garcia',
                'role': 'professor',
            },
            {
                'username': 'prof2',
                'email': 'prof2@richwell.edu',
                'first_name': 'Dr. Sarah',
                'last_name': 'Reyes',
                'role': 'professor',
            },
            {
                'username': 'prof3',
                'email': 'prof3@richwell.edu',
                'first_name': 'Dr. David',
                'last_name': 'Gonzales',
                'role': 'professor',
            },
            {
                'username': 'prof4',
                'email': 'prof4@richwell.edu',
                'first_name': 'Dr. Lisa',
                'last_name': 'Mendoza',
                'role': 'professor',
            },
            {
                'username': 'prof5',
                'email': 'prof5@richwell.edu',
                'first_name': 'Dr. James',
                'last_name': 'Torres',
                'role': 'professor',
            },

            # Deans
            {
                'username': 'dean1',
                'email': 'dean1@richwell.edu',
                'first_name': 'Dr. Elizabeth',
                'last_name': 'Ramos',
                'role': 'dean',
                'is_staff': True,
            },
            {
                'username': 'dean2',
                'email': 'dean2@richwell.edu',
                'first_name': 'Dr. William',
                'last_name': 'Flores',
                'role': 'dean',
                'is_staff': True,
            },

            # Admission Officers
            {
                'username': 'admission1',
                'email': 'admission1@richwell.edu',
                'first_name': 'Anna',
                'last_name': 'Bautista',
                'role': 'admission',
                'is_staff': True,
            },
            {
                'username': 'admission2',
                'email': 'admission2@richwell.edu',
                'first_name': 'Mark',
                'last_name': 'Villanueva',
                'role': 'admission',
                'is_staff': True,
            },

            # Students
            {
                'username': 'student1',
                'email': 'student1@richwell.edu',
                'first_name': 'Juan',
                'last_name': 'Dela Cruz',
                'role': 'student',
            },
            {
                'username': 'student2',
                'email': 'student2@richwell.edu',
                'first_name': 'Maria',
                'last_name': 'Rodriguez',
                'role': 'student',
            },
            {
                'username': 'student3',
                'email': 'student3@richwell.edu',
                'first_name': 'Pedro',
                'last_name': 'Martinez',
                'role': 'student',
            },
            {
                'username': 'student4',
                'email': 'student4@richwell.edu',
                'first_name': 'Ana',
                'last_name': 'Lopez',
                'role': 'student',
            },
            {
                'username': 'student5',
                'email': 'student5@richwell.edu',
                'first_name': 'Carlos',
                'last_name': 'Hernandez',
                'role': 'student',
            },
            {
                'username': 'student6',
                'email': 'student6@richwell.edu',
                'first_name': 'Sofia',
                'last_name': 'Gonzalez',
                'role': 'student',
            },
            {
                'username': 'student7',
                'email': 'student7@richwell.edu',
                'first_name': 'Miguel',
                'last_name': 'Perez',
                'role': 'student',
            },
            {
                'username': 'student8',
                'email': 'student8@richwell.edu',
                'first_name': 'Isabella',
                'last_name': 'Sanchez',
                'role': 'student',
            },
            {
                'username': 'student9',
                'email': 'student9@richwell.edu',
                'first_name': 'Diego',
                'last_name': 'Ramirez',
                'role': 'student',
            },
            {
                'username': 'student10',
                'email': 'student10@richwell.edu',
                'first_name': 'Lucia',
                'last_name': 'Torres',
                'role': 'student',
            },
        ]

        created_users = []
        skipped_users = []

        for user_data in users_data:
            username = user_data['username']

            # Check if user already exists
            if User.objects.filter(username=username).exists():
                skipped_users.append(username)
                continue

            # Create user
            user = User.objects.create(
                username=user_data['username'],
                email=user_data['email'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                role=user_data['role'],
                is_staff=user_data.get('is_staff', False),
                password=make_password(default_password),
            )
            created_users.append(f"{username} ({user_data['role']})")

        # Create Student profiles for student users
        student_users = User.objects.filter(role='student', student__isnull=True)

        if student_users.exists():
            # Get or create a default program and curriculum
            program, _ = Program.objects.get_or_create(
                name='Bachelor of Science in Computer Science',
                defaults={
                    'level': 'bachelor',
                    'passing_grade': 3.00,
                }
            )

            curriculum, _ = Curriculum.objects.get_or_create(
                program=program,
                version='CHED 2021',
                defaults={
                    'effective_sy': 'AY 2021-2022',
                    'active': True,
                }
            )

            students_created = 0
            for user in student_users:
                Student.objects.create(
                    user=user,
                    program=program,
                    curriculum=curriculum,
                    status='active',
                )
                students_created += 1

            self.stdout.write(
                self.style.SUCCESS(f'Created {students_created} Student profiles')
            )

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('USER SEEDING COMPLETE'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write('')

        if created_users:
            self.stdout.write(self.style.SUCCESS(f'Created {len(created_users)} users:'))
            for user in created_users:
                self.stdout.write(f'  - {user}')

        if skipped_users:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING(f'Skipped {len(skipped_users)} existing users:'))
            for user in skipped_users:
                self.stdout.write(f'  - {user}')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Default password for all users: ') + self.style.WARNING(default_password))
        self.stdout.write('')
        self.stdout.write('User credentials summary:')
        self.stdout.write('  Admins: admin1, admin2')
        self.stdout.write('  Registrars: registrar1, registrar2')
        self.stdout.write('  Professors: prof1, prof2, prof3, prof4, prof5')
        self.stdout.write('  Deans: dean1, dean2')
        self.stdout.write('  Admission: admission1, admission2')
        self.stdout.write('  Students: student1-student10')
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('You can now login with any username and the default password'))
