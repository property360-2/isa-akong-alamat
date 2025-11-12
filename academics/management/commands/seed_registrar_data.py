"""
Django management command to seed registrar data.

This command creates sample data for:
- Programs
- Subjects (with prerequisites)
- Curricula
- Curriculum Subjects
- Terms
- Sections
- Sample Professors (if none exist)

Usage: python manage.py seed_registrar_data
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal

from academics.models import Program, Subject, Curriculum, CurriculumSubject, Prereq
from enrollment.models import Term, Section
from users.models import User


class Command(BaseCommand):
    help = 'Seed registrar database with sample data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting registrar data seeding...'))

        # Create sample professors
        self.create_professors()

        # Create programs
        programs = self.create_programs()

        # Create subjects
        subjects = self.create_subjects(programs)

        # Create prerequisites
        self.create_prerequisites(subjects)

        # Create curricula
        curricula = self.create_curricula(programs)

        # Create curriculum subjects
        self.create_curriculum_subjects(curricula, subjects)

        # Create terms
        terms = self.create_terms()

        # Create sections
        self.create_sections(terms, subjects)

        self.stdout.write(self.style.SUCCESS('Data seeding completed successfully!'))

    def create_professors(self):
        """Create sample professor accounts if they don't exist"""
        self.stdout.write('Creating professors...')

        professors = [
            {
                'username': 'prof_smith',
                'email': 'smith@richwell.edu',
                'first_name': 'John',
                'last_name': 'Smith',
                'role': 'professor',
            },
            {
                'username': 'prof_johnson',
                'email': 'johnson@richwell.edu',
                'first_name': 'Sarah',
                'last_name': 'Johnson',
                'role': 'professor',
            },
            {
                'username': 'prof_williams',
                'email': 'williams@richwell.edu',
                'first_name': 'Michael',
                'last_name': 'Williams',
                'role': 'professor',
            },
            {
                'username': 'prof_davis',
                'email': 'davis@richwell.edu',
                'first_name': 'Emily',
                'last_name': 'Davis',
                'role': 'professor',
            },
        ]

        created_count = 0
        for prof_data in professors:
            if not User.objects.filter(username=prof_data['username']).exists():
                user = User.objects.create_user(
                    username=prof_data['username'],
                    email=prof_data['email'],
                    password='defaultpassword123',
                    first_name=prof_data['first_name'],
                    last_name=prof_data['last_name'],
                    role=prof_data['role'],
                )
                created_count += 1
                self.stdout.write(f"  ✓ Created professor: {user.username}")

        if created_count == 0:
            self.stdout.write(self.style.WARNING('  ℹ Professors already exist'))

    def create_programs(self):
        """Create sample programs"""
        self.stdout.write('Creating programs...')

        programs_data = [
            {
                'name': 'Bachelor of Science in Computer Science',
                'level': 'Bachelor',
                'passing_grade': Decimal('1.50'),
            },
            {
                'name': 'Bachelor of Science in Information Technology',
                'level': 'Bachelor',
                'passing_grade': Decimal('1.50'),
            },
            {
                'name': 'Bachelor of Science in Business Administration',
                'level': 'Bachelor',
                'passing_grade': Decimal('1.75'),
            },
        ]

        programs = []
        for prog_data in programs_data:
            program, created = Program.objects.get_or_create(
                name=prog_data['name'],
                defaults={
                    'level': prog_data['level'],
                    'passing_grade': prog_data['passing_grade'],
                }
            )
            if created:
                self.stdout.write(f"  ✓ Created program: {program.name}")
            else:
                self.stdout.write(self.style.WARNING(f"  ℹ Program already exists: {program.name}"))
            programs.append(program)

        return programs

    def create_subjects(self, programs):
        """Create sample subjects"""
        self.stdout.write('Creating subjects...')

        subjects_data = {
            'Bachelor of Science in Computer Science': [
                {
                    'code': 'CS101',
                    'title': 'Introduction to Computer Science',
                    'units': Decimal('3.0'),
                    'type': 'major',
                    'recommended_year': 1,
                    'recommended_sem': 1,
                },
                {
                    'code': 'CS102',
                    'title': 'Programming Fundamentals',
                    'units': Decimal('3.0'),
                    'type': 'major',
                    'recommended_year': 1,
                    'recommended_sem': 1,
                },
                {
                    'code': 'CS201',
                    'title': 'Data Structures',
                    'units': Decimal('3.0'),
                    'type': 'major',
                    'recommended_year': 1,
                    'recommended_sem': 2,
                },
                {
                    'code': 'CS202',
                    'title': 'Discrete Mathematics',
                    'units': Decimal('3.0'),
                    'type': 'major',
                    'recommended_year': 1,
                    'recommended_sem': 2,
                },
                {
                    'code': 'CS301',
                    'title': 'Algorithms and Complexity',
                    'units': Decimal('4.0'),
                    'type': 'major',
                    'recommended_year': 2,
                    'recommended_sem': 1,
                },
                {
                    'code': 'CS302',
                    'title': 'Database Systems',
                    'units': Decimal('3.0'),
                    'type': 'major',
                    'recommended_year': 2,
                    'recommended_sem': 1,
                },
                {
                    'code': 'CS303',
                    'title': 'Operating Systems',
                    'units': Decimal('3.0'),
                    'type': 'major',
                    'recommended_year': 2,
                    'recommended_sem': 2,
                },
                {
                    'code': 'CS401',
                    'title': 'Software Engineering',
                    'units': Decimal('3.0'),
                    'type': 'major',
                    'recommended_year': 3,
                    'recommended_sem': 1,
                },
                {
                    'code': 'GEN101',
                    'title': 'Filipino',
                    'units': Decimal('3.0'),
                    'type': 'minor',
                    'recommended_year': 1,
                    'recommended_sem': 1,
                },
                {
                    'code': 'GEN102',
                    'title': 'English Communication',
                    'units': Decimal('3.0'),
                    'type': 'minor',
                    'recommended_year': 1,
                    'recommended_sem': 1,
                },
            ],
            'Bachelor of Science in Information Technology': [
                {
                    'code': 'IT101',
                    'title': 'Introduction to IT',
                    'units': Decimal('3.0'),
                    'type': 'major',
                    'recommended_year': 1,
                    'recommended_sem': 1,
                },
                {
                    'code': 'IT102',
                    'title': 'Web Development Basics',
                    'units': Decimal('3.0'),
                    'type': 'major',
                    'recommended_year': 1,
                    'recommended_sem': 2,
                },
                {
                    'code': 'IT201',
                    'title': 'Network Administration',
                    'units': Decimal('3.0'),
                    'type': 'major',
                    'recommended_year': 2,
                    'recommended_sem': 1,
                },
                {
                    'code': 'IT202',
                    'title': 'Systems Security',
                    'units': Decimal('3.0'),
                    'type': 'major',
                    'recommended_year': 2,
                    'recommended_sem': 2,
                },
            ],
            'Bachelor of Science in Business Administration': [
                {
                    'code': 'BUS101',
                    'title': 'Introduction to Business',
                    'units': Decimal('3.0'),
                    'type': 'major',
                    'recommended_year': 1,
                    'recommended_sem': 1,
                },
                {
                    'code': 'BUS102',
                    'title': 'Accounting Principles',
                    'units': Decimal('3.0'),
                    'type': 'major',
                    'recommended_year': 1,
                    'recommended_sem': 2,
                },
                {
                    'code': 'BUS201',
                    'title': 'Business Finance',
                    'units': Decimal('3.0'),
                    'type': 'major',
                    'recommended_year': 2,
                    'recommended_sem': 1,
                },
            ],
        }

        subjects = {}
        for program in programs:
            program_subjects = subjects_data.get(program.name, [])
            for subj_data in program_subjects:
                subject, created = Subject.objects.get_or_create(
                    code=subj_data['code'],
                    defaults={
                        'program': program,
                        'title': subj_data['title'],
                        'units': subj_data['units'],
                        'type': subj_data['type'],
                        'recommended_year': subj_data['recommended_year'],
                        'recommended_sem': subj_data['recommended_sem'],
                    }
                )
                if created:
                    self.stdout.write(f"  ✓ Created subject: {subject.code}")
                else:
                    self.stdout.write(self.style.WARNING(f"  ℹ Subject already exists: {subject.code}"))
                subjects[subject.code] = subject

        return subjects

    def create_prerequisites(self, subjects):
        """Create prerequisite relationships"""
        self.stdout.write('Creating prerequisites...')

        prerequisites = [
            ('CS201', 'CS102'),  # Data Structures requires Programming Fundamentals
            ('CS301', 'CS201'),  # Algorithms requires Data Structures
            ('CS302', 'CS201'),  # Database Systems requires Data Structures
            ('CS303', 'CS301'),  # Operating Systems requires Algorithms
            ('CS401', 'CS301'),  # Software Engineering requires Algorithms
            ('IT201', 'IT101'),  # Network Admin requires Intro to IT
            ('IT202', 'IT201'),  # Systems Security requires Network Admin
            ('BUS201', 'BUS102'), # Business Finance requires Accounting
        ]

        created_count = 0
        for subject_code, prereq_code in prerequisites:
            if subject_code in subjects and prereq_code in subjects:
                prereq, created = Prereq.objects.get_or_create(
                    subject=subjects[subject_code],
                    prereq_subject=subjects[prereq_code],
                )
                if created:
                    self.stdout.write(f"  ✓ {prereq_code} is prerequisite for {subject_code}")
                    created_count += 1

        if created_count == 0:
            self.stdout.write(self.style.WARNING('  ℹ Prerequisites already exist'))

    def create_curricula(self, programs):
        """Create sample curricula"""
        self.stdout.write('Creating curricula...')

        curricula_data = [
            {
                'program': programs[0],
                'version': '2025 Rev A',
                'effective_sy': '2025-2026',
            },
            {
                'program': programs[1],
                'version': '2025 Rev A',
                'effective_sy': '2025-2026',
            },
            {
                'program': programs[2],
                'version': '2025 Rev A',
                'effective_sy': '2025-2026',
            },
        ]

        curricula = []
        for curr_data in curricula_data:
            curriculum, created = Curriculum.objects.get_or_create(
                program=curr_data['program'],
                version=curr_data['version'],
                defaults={
                    'effective_sy': curr_data['effective_sy'],
                    'active': True,
                }
            )
            if created:
                self.stdout.write(f"  ✓ Created curriculum: {curriculum.program.name} - {curriculum.version}")
            else:
                self.stdout.write(self.style.WARNING(f"  ℹ Curriculum already exists: {curriculum}"))
            curricula.append(curriculum)

        return curricula

    def create_curriculum_subjects(self, curricula, subjects):
        """Map subjects to curricula"""
        self.stdout.write('Mapping subjects to curricula...')

        cs_program = [c for c in curricula if 'Computer Science' in c.program.name][0]
        it_program = [c for c in curricula if 'Information Technology' in c.program.name][0]
        ba_program = [c for c in curricula if 'Business' in c.program.name][0]

        curriculum_subjects = [
            # Computer Science subjects
            (cs_program, 'CS101', 1, 1, True),
            (cs_program, 'CS102', 1, 1, True),
            (cs_program, 'CS201', 1, 2, True),
            (cs_program, 'CS202', 1, 2, True),
            (cs_program, 'CS301', 2, 1, True),
            (cs_program, 'CS302', 2, 1, True),
            (cs_program, 'CS303', 2, 2, True),
            (cs_program, 'CS401', 3, 1, True),
            (cs_program, 'GEN101', 1, 1, False),
            (cs_program, 'GEN102', 1, 1, False),
            # IT subjects
            (it_program, 'IT101', 1, 1, True),
            (it_program, 'IT102', 1, 2, True),
            (it_program, 'IT201', 2, 1, True),
            (it_program, 'IT202', 2, 2, True),
            # Business subjects
            (ba_program, 'BUS101', 1, 1, True),
            (ba_program, 'BUS102', 1, 2, True),
            (ba_program, 'BUS201', 2, 1, True),
        ]

        created_count = 0
        for curriculum, subject_code, year_level, term_no, is_recommended in curriculum_subjects:
            if subject_code in subjects:
                cs, created = CurriculumSubject.objects.get_or_create(
                    curriculum=curriculum,
                    subject=subjects[subject_code],
                    defaults={
                        'year_level': year_level,
                        'term_no': term_no,
                        'is_recommended': is_recommended,
                    }
                )
                if created:
                    self.stdout.write(f"  ✓ Added {subject_code} to {curriculum}")
                    created_count += 1

        if created_count == 0:
            self.stdout.write(self.style.WARNING('  ℹ Curriculum subjects already exist'))

    def create_terms(self):
        """Create sample academic terms"""
        self.stdout.write('Creating terms...')

        terms_data = [
            {
                'name': '1st Semester 2024-2025',
                'level': 'Bachelor',
                'start_date': date(2024, 8, 1),
                'end_date': date(2024, 12, 20),
                'add_drop_deadline': date(2024, 8, 15),
                'grade_encoding_deadline': date(2025, 1, 10),
                'is_active': False,
            },
            {
                'name': '2nd Semester 2024-2025',
                'level': 'Bachelor',
                'start_date': date(2025, 1, 6),
                'end_date': date(2025, 5, 10),
                'add_drop_deadline': date(2025, 1, 20),
                'grade_encoding_deadline': date(2025, 5, 25),
                'is_active': True,
            },
            {
                'name': 'Summer 2025',
                'level': 'Bachelor',
                'start_date': date(2025, 5, 19),
                'end_date': date(2025, 7, 18),
                'add_drop_deadline': date(2025, 5, 26),
                'grade_encoding_deadline': date(2025, 7, 25),
                'is_active': False,
            },
        ]

        terms = []
        for term_data in terms_data:
            term, created = Term.objects.get_or_create(
                name=term_data['name'],
                level=term_data['level'],
                defaults={
                    'start_date': term_data['start_date'],
                    'end_date': term_data['end_date'],
                    'add_drop_deadline': term_data['add_drop_deadline'],
                    'grade_encoding_deadline': term_data['grade_encoding_deadline'],
                    'is_active': term_data['is_active'],
                }
            )
            if created:
                self.stdout.write(f"  ✓ Created term: {term.name}")
            else:
                self.stdout.write(self.style.WARNING(f"  ℹ Term already exists: {term.name}"))
            terms.append(term)

        return terms

    def create_sections(self, terms, subjects):
        """Create sample sections"""
        self.stdout.write('Creating sections...')

        # Get professors
        professors = User.objects.filter(role='professor')
        if not professors.exists():
            self.stdout.write(self.style.ERROR('No professors found. Please create professors first.'))
            return

        section_data = [
            {
                'section_code': 'A101',
                'subjects': ['CS101'],
                'professors': [professors[0]],
                'capacity': 40,
                'status': 'open',
                'term': terms[1],  # 2nd Semester
            },
            {
                'section_code': 'A102',
                'subjects': ['CS101'],
                'professors': [professors[1]],
                'capacity': 35,
                'status': 'open',
                'term': terms[1],
            },
            {
                'section_code': 'B101',
                'subjects': ['CS102'],
                'professors': [professors[0]],
                'capacity': 40,
                'status': 'open',
                'term': terms[1],
            },
            {
                'section_code': 'C101',
                'subjects': ['CS201'],
                'professors': [professors[2]],
                'capacity': 30,
                'status': 'open',
                'term': terms[1],
            },
            {
                'section_code': 'D101',
                'subjects': ['IT101'],
                'professors': [professors[1]],
                'capacity': 40,
                'status': 'open',
                'term': terms[1],
            },
            {
                'section_code': 'E101',
                'subjects': ['BUS101'],
                'professors': [professors[3]],
                'capacity': 45,
                'status': 'open',
                'term': terms[1],
            },
        ]

        created_count = 0
        for sect_data in section_data:
            try:
                section, created = Section.objects.get_or_create(
                    term=sect_data['term'],
                    section_code=sect_data['section_code'],
                    defaults={
                        'capacity': sect_data['capacity'],
                        'status': sect_data['status'],
                    }
                )

                # Add subjects
                for subject_code in sect_data['subjects']:
                    if subject_code in subjects:
                        section.subjects.add(subjects[subject_code])

                # Add professors
                for professor in sect_data['professors']:
                    section.professors.add(professor)

                if created:
                    self.stdout.write(f"  ✓ Created section: {section.section_code} ({sect_data['subjects'][0]})")
                    created_count += 1
                else:
                    self.stdout.write(self.style.WARNING(f"  ℹ Section already exists: {section.section_code}"))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ✗ Error creating section {sect_data['section_code']}: {str(e)}"))

        if created_count > 0:
            self.stdout.write(f"  Created {created_count} new sections")
