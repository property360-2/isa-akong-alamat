"""
Master seeder for complete academic database setup.

Creates all data in the correct order:
1. Programs (CS, IT, Business, etc.)
2. Professors
3. Comprehensive subjects with prerequisites
4. Curricula
5. Curriculum-Subject mappings
6. Terms
7. Sections

Usage: python manage.py seed_all_data
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal

from academics.models import Program, Subject, Curriculum, CurriculumSubject, Prereq
from enrollment.models import Term, Section
from users.models import User


class Command(BaseCommand):
    help = 'Complete seed of all academic data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Starting complete academic data seeding...\n'))

        # Create professors
        self.create_professors()

        # Create programs
        programs = self.create_programs()

        # Create subjects for each program
        all_subjects = {}
        all_subjects.update(self.create_cs_subjects(programs['CS']))
        all_subjects.update(self.create_it_subjects(programs['IT']))
        all_subjects.update(self.create_business_subjects(programs['Business']))
        all_subjects.update(self.create_gen_ed_subjects(programs['CS']))  # Gen Ed under CS program

        # Create prerequisites
        self.create_all_prerequisites()

        # Create curricula
        curricula = self.create_curricula(programs)

        # Add subjects to curricula
        self.add_subjects_to_curricula(curricula)

        # Create terms
        self.create_terms()

        # Create sections
        self.create_sections(all_subjects)

        self.stdout.write(self.style.SUCCESS('\n✅ Complete academic data seeding finished successfully!'))
        self.print_summary(programs, all_subjects, curricula)

    def create_professors(self):
        """Create sample professor accounts"""
        self.stdout.write('\n👨‍🏫 Creating professors...')

        professors = [
            {'username': 'prof_smith', 'email': 'smith@richwell.edu', 'first_name': 'John', 'last_name': 'Smith'},
            {'username': 'prof_johnson', 'email': 'johnson@richwell.edu', 'first_name': 'Sarah', 'last_name': 'Johnson'},
            {'username': 'prof_williams', 'email': 'williams@richwell.edu', 'first_name': 'Michael', 'last_name': 'Williams'},
            {'username': 'prof_davis', 'email': 'davis@richwell.edu', 'first_name': 'Emily', 'last_name': 'Davis'},
            {'username': 'prof_garcia', 'email': 'garcia@richwell.edu', 'first_name': 'Robert', 'last_name': 'Garcia'},
            {'username': 'prof_martinez', 'email': 'martinez@richwell.edu', 'first_name': 'Linda', 'last_name': 'Martinez'},
        ]

        created = 0
        for prof in professors:
            if not User.objects.filter(username=prof['username']).exists():
                User.objects.create_user(
                    username=prof['username'],
                    email=prof['email'],
                    password='defaultpassword123',
                    first_name=prof['first_name'],
                    last_name=prof['last_name'],
                    role='professor'
                )
                self.stdout.write(f"  ✓ {prof['first_name']} {prof['last_name']}")
                created += 1
            else:
                self.stdout.write(f"  ℹ {prof['username']} already exists")

        self.stdout.write(self.style.SUCCESS(f"  Created {created} professors"))

    def create_programs(self):
        """Create all programs"""
        self.stdout.write('\n🎓 Creating programs...')

        programs_data = [
            {'name': 'Bachelor of Science in Computer Science', 'level': 'Bachelor', 'key': 'CS'},
            {'name': 'Bachelor of Science in Information Technology', 'level': 'Bachelor', 'key': 'IT'},
            {'name': 'Bachelor of Science in Business Administration', 'level': 'Bachelor', 'key': 'Business'},
        ]

        programs = {}
        created = 0

        for data in programs_data:
            key = data.pop('key')
            if not Program.objects.filter(name=data['name']).exists():
                program = Program.objects.create(**data, passing_grade=Decimal('2.00'))
                programs[key] = program
                self.stdout.write(f"  ✓ {data['name']}")
                created += 1
            else:
                program = Program.objects.get(name=data['name'])
                programs[key] = program
                self.stdout.write(f"  ℹ {data['name']} already exists")

        self.stdout.write(self.style.SUCCESS(f"  Created {created} programs"))
        return programs

    def create_cs_subjects(self, program):
        """Create Computer Science subjects"""
        self.stdout.write('\n📚 Creating Computer Science subjects...')

        subjects_data = [
            # 1st Year - 1st Semester
            {'code': 'CS101', 'title': 'Introduction to Computer Science', 'units': 3, 'year': 1, 'sem': 1, 'type': 'major'},
            {'code': 'CS102', 'title': 'Programming Fundamentals', 'units': 3, 'year': 1, 'sem': 1, 'type': 'major'},
            {'code': 'MATH101', 'title': 'Discrete Mathematics', 'units': 3, 'year': 1, 'sem': 1, 'type': 'major'},
            {'code': 'ENG101', 'title': 'English Composition', 'units': 3, 'year': 1, 'sem': 1, 'type': 'minor'},

            # 1st Year - 2nd Semester
            {'code': 'CS103', 'title': 'Data Structures', 'units': 3, 'year': 1, 'sem': 2, 'type': 'major'},
            {'code': 'CS104', 'title': 'Logic Design', 'units': 3, 'year': 1, 'sem': 2, 'type': 'major'},
            {'code': 'MATH102', 'title': 'Calculus I', 'units': 4, 'year': 1, 'sem': 2, 'type': 'major'},
            {'code': 'PE101', 'title': 'Physical Education', 'units': 2, 'year': 1, 'sem': 2, 'type': 'minor'},

            # 2nd Year - 1st Semester
            {'code': 'CS201', 'title': 'Algorithms & Analysis', 'units': 3, 'year': 2, 'sem': 1, 'type': 'major'},
            {'code': 'CS202', 'title': 'Computer Architecture', 'units': 3, 'year': 2, 'sem': 1, 'type': 'major'},
            {'code': 'CS203', 'title': 'Database Management Systems', 'units': 3, 'year': 2, 'sem': 1, 'type': 'major'},
            {'code': 'MATH201', 'title': 'Calculus II', 'units': 4, 'year': 2, 'sem': 1, 'type': 'major'},

            # 2nd Year - 2nd Semester
            {'code': 'CS204', 'title': 'Object-Oriented Programming', 'units': 3, 'year': 2, 'sem': 2, 'type': 'major'},
            {'code': 'CS205', 'title': 'Operating Systems', 'units': 3, 'year': 2, 'sem': 2, 'type': 'major'},
            {'code': 'CS206', 'title': 'Software Engineering', 'units': 3, 'year': 2, 'sem': 2, 'type': 'major'},
            {'code': 'MATH202', 'title': 'Linear Algebra', 'units': 3, 'year': 2, 'sem': 2, 'type': 'major'},

            # 3rd Year - 1st Semester
            {'code': 'CS301', 'title': 'Web Development', 'units': 3, 'year': 3, 'sem': 1, 'type': 'major'},
            {'code': 'CS302', 'title': 'Mobile App Development', 'units': 3, 'year': 3, 'sem': 1, 'type': 'major'},
            {'code': 'CS303', 'title': 'Computer Networks', 'units': 3, 'year': 3, 'sem': 1, 'type': 'major'},
            {'code': 'CS304', 'title': 'Cybersecurity Basics', 'units': 3, 'year': 3, 'sem': 1, 'type': 'major'},

            # 3rd Year - 2nd Semester
            {'code': 'CS305', 'title': 'Data Mining & Analytics', 'units': 3, 'year': 3, 'sem': 2, 'type': 'major'},
            {'code': 'CS306', 'title': 'Artificial Intelligence', 'units': 3, 'year': 3, 'sem': 2, 'type': 'major'},
            {'code': 'CS307', 'title': 'Cloud Computing', 'units': 3, 'year': 3, 'sem': 2, 'type': 'major'},
            {'code': 'CS308', 'title': 'Advanced Databases', 'units': 3, 'year': 3, 'sem': 2, 'type': 'major'},

            # 4th Year - 1st Semester
            {'code': 'CS401', 'title': 'Capstone Project I', 'units': 3, 'year': 4, 'sem': 1, 'type': 'major'},
            {'code': 'CS402', 'title': 'Machine Learning', 'units': 3, 'year': 4, 'sem': 1, 'type': 'major'},
            {'code': 'CS403', 'title': 'Advanced Algorithms', 'units': 3, 'year': 4, 'sem': 1, 'type': 'major'},

            # 4th Year - 2nd Semester
            {'code': 'CS404', 'title': 'Capstone Project II', 'units': 3, 'year': 4, 'sem': 2, 'type': 'major'},
            {'code': 'CS405', 'title': 'Professional Practice', 'units': 2, 'year': 4, 'sem': 2, 'type': 'major'},
        ]

        return self._create_subjects(program, subjects_data, 'CS')

    def create_it_subjects(self, program):
        """Create IT subjects"""
        self.stdout.write('\n📚 Creating Information Technology subjects...')

        subjects_data = [
            # 1st Year - 1st Semester
            {'code': 'IT101', 'title': 'Fundamentals of IT', 'units': 3, 'year': 1, 'sem': 1, 'type': 'major'},
            {'code': 'IT102', 'title': 'Introduction to Programming', 'units': 3, 'year': 1, 'sem': 1, 'type': 'major'},
            {'code': 'IT103', 'title': 'Computer Hardware', 'units': 3, 'year': 1, 'sem': 1, 'type': 'major'},

            # 1st Year - 2nd Semester
            {'code': 'IT104', 'title': 'Business Applications', 'units': 3, 'year': 1, 'sem': 2, 'type': 'major'},
            {'code': 'IT105', 'title': 'Systems Administration Basics', 'units': 3, 'year': 1, 'sem': 2, 'type': 'major'},
            {'code': 'IT106', 'title': 'Networking Basics', 'units': 3, 'year': 1, 'sem': 2, 'type': 'major'},

            # 2nd Year - 1st Semester
            {'code': 'IT201', 'title': 'Database Administration', 'units': 3, 'year': 2, 'sem': 1, 'type': 'major'},
            {'code': 'IT202', 'title': 'Network Administration', 'units': 3, 'year': 2, 'sem': 1, 'type': 'major'},
            {'code': 'IT203', 'title': 'Web Technologies', 'units': 3, 'year': 2, 'sem': 1, 'type': 'major'},

            # 2nd Year - 2nd Semester
            {'code': 'IT204', 'title': 'Systems Security', 'units': 3, 'year': 2, 'sem': 2, 'type': 'major'},
            {'code': 'IT205', 'title': 'Enterprise Systems', 'units': 3, 'year': 2, 'sem': 2, 'type': 'major'},
            {'code': 'IT206', 'title': 'IT Project Management', 'units': 3, 'year': 2, 'sem': 2, 'type': 'major'},

            # 3rd Year - 1st Semester
            {'code': 'IT301', 'title': 'Cloud Architecture', 'units': 3, 'year': 3, 'sem': 1, 'type': 'major'},
            {'code': 'IT302', 'title': 'Advanced Networking', 'units': 3, 'year': 3, 'sem': 1, 'type': 'major'},
            {'code': 'IT303', 'title': 'Business Continuity', 'units': 3, 'year': 3, 'sem': 1, 'type': 'major'},

            # 3rd Year - 2nd Semester
            {'code': 'IT304', 'title': 'IT Governance', 'units': 3, 'year': 3, 'sem': 2, 'type': 'major'},
            {'code': 'IT305', 'title': 'Capstone Project I', 'units': 3, 'year': 3, 'sem': 2, 'type': 'major'},

            # 4th Year - 1st Semester
            {'code': 'IT401', 'title': 'IT Strategy & Planning', 'units': 3, 'year': 4, 'sem': 1, 'type': 'major'},
            {'code': 'IT402', 'title': 'Digital Transformation', 'units': 3, 'year': 4, 'sem': 1, 'type': 'major'},

            # 4th Year - 2nd Semester
            {'code': 'IT403', 'title': 'Capstone Project II', 'units': 3, 'year': 4, 'sem': 2, 'type': 'major'},
        ]

        return self._create_subjects(program, subjects_data, 'IT')

    def create_business_subjects(self, program):
        """Create Business subjects"""
        self.stdout.write('\n📚 Creating Business Administration subjects...')

        subjects_data = [
            # 1st Year - 1st Semester
            {'code': 'BUS101', 'title': 'Introduction to Business', 'units': 3, 'year': 1, 'sem': 1, 'type': 'major'},
            {'code': 'ECON101', 'title': 'Microeconomics', 'units': 3, 'year': 1, 'sem': 1, 'type': 'major'},
            {'code': 'ACCT101', 'title': 'Financial Accounting', 'units': 3, 'year': 1, 'sem': 1, 'type': 'major'},

            # 1st Year - 2nd Semester
            {'code': 'BUS102', 'title': 'Business Communication', 'units': 3, 'year': 1, 'sem': 2, 'type': 'major'},
            {'code': 'ECON102', 'title': 'Macroeconomics', 'units': 3, 'year': 1, 'sem': 2, 'type': 'major'},
            {'code': 'ACCT102', 'title': 'Managerial Accounting', 'units': 3, 'year': 1, 'sem': 2, 'type': 'major'},

            # 2nd Year - 1st Semester
            {'code': 'BUS201', 'title': 'Business Management', 'units': 3, 'year': 2, 'sem': 1, 'type': 'major'},
            {'code': 'MKTG201', 'title': 'Marketing Principles', 'units': 3, 'year': 2, 'sem': 1, 'type': 'major'},
            {'code': 'STAT201', 'title': 'Business Statistics', 'units': 3, 'year': 2, 'sem': 1, 'type': 'major'},

            # 2nd Year - 2nd Semester
            {'code': 'BUS202', 'title': 'Organizational Behavior', 'units': 3, 'year': 2, 'sem': 2, 'type': 'major'},
            {'code': 'MKTG202', 'title': 'Digital Marketing', 'units': 3, 'year': 2, 'sem': 2, 'type': 'major'},
            {'code': 'FIN201', 'title': 'Corporate Finance', 'units': 3, 'year': 2, 'sem': 2, 'type': 'major'},

            # 3rd Year - 1st Semester
            {'code': 'BUS301', 'title': 'Strategic Management', 'units': 3, 'year': 3, 'sem': 1, 'type': 'major'},
            {'code': 'MKTG301', 'title': 'Consumer Behavior', 'units': 3, 'year': 3, 'sem': 1, 'type': 'major'},
            {'code': 'HRM301', 'title': 'Human Resource Management', 'units': 3, 'year': 3, 'sem': 1, 'type': 'major'},

            # 3rd Year - 2nd Semester
            {'code': 'BUS302', 'title': 'Entrepreneurship', 'units': 3, 'year': 3, 'sem': 2, 'type': 'major'},
            {'code': 'BUS303', 'title': 'Business Ethics', 'units': 3, 'year': 3, 'sem': 2, 'type': 'major'},

            # 4th Year - 1st Semester
            {'code': 'BUS401', 'title': 'Business Capstone I', 'units': 3, 'year': 4, 'sem': 1, 'type': 'major'},
            {'code': 'BUS402', 'title': 'International Business', 'units': 3, 'year': 4, 'sem': 1, 'type': 'major'},

            # 4th Year - 2nd Semester
            {'code': 'BUS403', 'title': 'Business Capstone II', 'units': 3, 'year': 4, 'sem': 2, 'type': 'major'},
        ]

        return self._create_subjects(program, subjects_data, 'Business')

    def create_gen_ed_subjects(self, program):
        """Create General Education subjects"""
        self.stdout.write('\n📚 Creating General Education subjects...')

        subjects_data = [
            {'code': 'GEN101', 'title': 'Philippine History', 'units': 3, 'year': 1, 'sem': 1, 'type': 'minor'},
            {'code': 'GEN102', 'title': 'Social Science', 'units': 3, 'year': 1, 'sem': 2, 'type': 'minor'},
            {'code': 'GEN103', 'title': 'Philosophy', 'units': 3, 'year': 2, 'sem': 1, 'type': 'minor'},
            {'code': 'GEN104', 'title': 'Literature', 'units': 3, 'year': 2, 'sem': 2, 'type': 'minor'},
            {'code': 'GEN105', 'title': 'Science & Environment', 'units': 3, 'year': 1, 'sem': 1, 'type': 'minor'},
            {'code': 'GEN106', 'title': 'Mathematics for Life', 'units': 3, 'year': 1, 'sem': 2, 'type': 'minor'},
            {'code': 'GEN107', 'title': 'Physical Education 1', 'units': 2, 'year': 1, 'sem': 1, 'type': 'minor'},
            {'code': 'GEN108', 'title': 'Physical Education 2', 'units': 2, 'year': 1, 'sem': 2, 'type': 'minor'},
            {'code': 'GEN109', 'title': 'Values Education', 'units': 3, 'year': 3, 'sem': 1, 'type': 'minor'},
            {'code': 'GEN110', 'title': 'Oral Communication', 'units': 3, 'year': 1, 'sem': 1, 'type': 'minor'},
        ]

        return self._create_subjects(program, subjects_data, 'GenEd')

    def _create_subjects(self, program, subjects_data, prefix):
        """Helper to create subjects and return dict"""
        subjects = {}
        created = 0

        for data in subjects_data:
            code = data.pop('code')
            year = data.pop('year')
            sem = data.pop('sem')

            if not Subject.objects.filter(code=code).exists():
                subject = Subject.objects.create(
                    program=program,
                    code=code,
                    **data,
                    recommended_year=year,
                    recommended_sem=sem,
                    active=True,
                )
                subjects[code] = subject
                self.stdout.write(f"  ✓ {code}: {subject.title}")
                created += 1
            else:
                subject = Subject.objects.get(code=code)
                subjects[code] = subject
                self.stdout.write(f"  ℹ {code} already exists")

        self.stdout.write(self.style.SUCCESS(f"  Created {created} {prefix} subjects"))
        return subjects

    def create_all_prerequisites(self):
        """Create all prerequisite relationships"""
        self.stdout.write('\n🔗 Creating prerequisites...')

        prerequisites = [
            # CS Prerequisites
            ('CS103', 'CS102'), ('CS104', 'CS101'), ('CS201', 'CS103'), ('CS202', 'CS104'),
            ('CS203', 'CS103'), ('CS204', 'CS102'), ('CS205', 'CS202'), ('CS206', 'CS201'),
            ('CS301', 'CS204'), ('CS302', 'CS204'), ('CS303', 'CS102'), ('CS304', 'CS205'),
            ('CS305', 'CS203'), ('CS306', 'CS201'), ('CS307', 'CS205'), ('CS308', 'CS203'),
            ('CS401', 'CS206'), ('CS402', 'CS306'), ('CS403', 'CS201'), ('CS404', 'CS401'),

            # IT Prerequisites
            ('IT104', 'IT102'), ('IT105', 'IT103'), ('IT106', 'IT101'), ('IT201', 'IT102'),
            ('IT202', 'IT106'), ('IT203', 'IT102'), ('IT204', 'IT202'), ('IT205', 'IT201'),
            ('IT206', 'IT101'), ('IT301', 'IT203'), ('IT302', 'IT202'), ('IT303', 'IT204'),
            ('IT304', 'IT206'), ('IT305', 'IT205'), ('IT401', 'IT305'), ('IT402', 'IT301'),
            ('IT403', 'IT401'),

            # Business Prerequisites
            ('BUS102', 'BUS101'), ('ACCT102', 'ACCT101'), ('BUS201', 'BUS101'),
            ('MKTG201', 'BUS101'), ('BUS202', 'BUS201'), ('MKTG202', 'MKTG201'),
            ('FIN201', 'ACCT102'), ('BUS301', 'BUS201'), ('MKTG301', 'MKTG201'),
            ('HRM301', 'BUS202'), ('BUS302', 'BUS201'), ('BUS303', 'BUS101'),
            ('BUS401', 'BUS301'), ('BUS402', 'MKTG201'), ('BUS403', 'BUS401'),
        ]

        count = 0
        for subject_code, prereq_code in prerequisites:
            try:
                subject = Subject.objects.get(code=subject_code)
                prereq_subject = Subject.objects.get(code=prereq_code)

                if not Prereq.objects.filter(subject=subject, prereq_subject=prereq_subject).exists():
                    Prereq.objects.create(subject=subject, prereq_subject=prereq_subject)
                    count += 1
            except Subject.DoesNotExist:
                pass

        self.stdout.write(self.style.SUCCESS(f"  Created {count} prerequisite relationships"))

    def create_curricula(self, programs):
        """Create curricula for each program"""
        self.stdout.write('\n📖 Creating curricula...')

        curricula = {}
        created = 0

        for key, program in programs.items():
            version = 'CHED 2021 Revision'
            if not Curriculum.objects.filter(program=program, version=version).exists():
                curriculum = Curriculum.objects.create(
                    program=program,
                    version=version,
                    effective_sy='2024-2025',
                    active=True
                )
                curricula[key] = curriculum
                self.stdout.write(f"  ✓ {program.name} - {version}")
                created += 1
            else:
                curriculum = Curriculum.objects.get(program=program, version=version)
                curricula[key] = curriculum
                self.stdout.write(f"  ℹ {program.name} curriculum already exists")

        self.stdout.write(self.style.SUCCESS(f"  Created {created} curricula"))
        return curricula

    def add_subjects_to_curricula(self, curricula):
        """Add subjects to respective curricula"""
        self.stdout.write('\n📚 Adding subjects to curricula...')

        total_added = 0
        for key, curriculum in curricula.items():
            subjects = Subject.objects.filter(program=curriculum.program)
            count = 0

            for subject in subjects:
                year = subject.recommended_year or 1
                sem = subject.recommended_sem or 1

                if not CurriculumSubject.objects.filter(
                    curriculum=curriculum,
                    subject=subject,
                    year_level=year,
                    term_no=sem
                ).exists():
                    CurriculumSubject.objects.create(
                        curriculum=curriculum,
                        subject=subject,
                        year_level=year,
                        term_no=sem,
                        is_recommended=True
                    )
                    count += 1

            self.stdout.write(f"  ✓ Added {count} subjects to {curriculum.program.name} curriculum")
            total_added += count

        self.stdout.write(self.style.SUCCESS(f"  Total subjects added: {total_added}"))

    def create_terms(self):
        """Create academic terms"""
        self.stdout.write('\n📅 Creating academic terms...')

        terms_data = [
            {'name': '1st Semester 2024-2025', 'level': 'Bachelor', 'start': date(2024, 8, 15), 'end': date(2024, 12, 20), 'is_active': True},
            {'name': '2nd Semester 2024-2025', 'level': 'Bachelor', 'start': date(2025, 1, 15), 'end': date(2025, 5, 31), 'is_active': False},
            {'name': 'Summer 2025', 'level': 'Bachelor', 'start': date(2025, 6, 1), 'end': date(2025, 7, 31), 'is_active': False},
        ]

        created = 0
        for data in terms_data:
            if not Term.objects.filter(name=data['name'], level=data['level']).exists():
                Term.objects.create(
                    name=data['name'],
                    level=data['level'],
                    start_date=data['start'],
                    end_date=data['end'],
                    add_drop_deadline=data['start'] + timedelta(days=14),
                    grade_encoding_deadline=data['end'] + timedelta(days=7),
                    is_active=data['is_active'],
                )
                self.stdout.write(f"  ✓ {data['name']}")
                created += 1
            else:
                self.stdout.write(f"  ℹ {data['name']} already exists")

        self.stdout.write(self.style.SUCCESS(f"  Created {created} terms"))

    def create_sections(self, all_subjects):
        """Create sections for subjects"""
        self.stdout.write('\n🏫 Creating sections...')

        active_term = Term.objects.filter(is_active=True).first()
        if not active_term:
            self.stdout.write(self.style.WARNING('  ⚠ No active term found, skipping sections'))
            return

        professors = User.objects.filter(role='professor')
        if not professors.exists():
            self.stdout.write(self.style.WARNING('  ⚠ No professors found, skipping sections'))
            return

        created = 0
        subject_list = list(all_subjects.values())[:15]  # Create sections for first 15 subjects

        for i, subject in enumerate(subject_list):
            section_code = f"{subject.code}-{chr(65 + (i % 3))}"  # A, B, C sections

            if not Section.objects.filter(term=active_term, section_code=section_code).exists():
                section = Section.objects.create(
                    term=active_term,
                    section_code=section_code,
                    capacity=40,
                    status='open'
                )
                section.subjects.add(subject)
                section.professors.add(professors[i % len(professors)])
                self.stdout.write(f"  ✓ {section_code}")
                created += 1

        self.stdout.write(self.style.SUCCESS(f"  Created {created} sections"))

    def print_summary(self, programs, subjects, curricula):
        """Print summary statistics"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write('📊 SEEDING SUMMARY')
        self.stdout.write('='*60)

        self.stdout.write(f"\n🎓 Programs: {len(programs)}")
        for key, program in programs.items():
            subject_count = Subject.objects.filter(program=program).count()
            self.stdout.write(f"   • {program.name}: {subject_count} subjects")

        self.stdout.write(f"\n📚 Total Subjects: {len(subjects)}")
        self.stdout.write(f"📖 Curricula: {len(curricula)}")
        self.stdout.write(f"👨‍🏫 Professors: {User.objects.filter(role='professor').count()}")
        self.stdout.write(f"📅 Terms: {Term.objects.count()}")
        self.stdout.write(f"🏫 Sections: {Section.objects.count()}")
        self.stdout.write('='*60 + '\n')
