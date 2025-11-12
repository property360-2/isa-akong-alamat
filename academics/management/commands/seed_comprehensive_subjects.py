"""
Django management command to seed comprehensive subject data for all programs.

This command creates detailed subject data including:
- Core CS/IT subjects with prerequisites
- General Education subjects
- Electives
- Lab courses
- Capstone/Thesis courses
- Realistic unit counts (1-4 units typical)
- Proper curriculum placement (year and semester)
- Prerequisite chains

Usage: python manage.py seed_comprehensive_subjects
"""

from django.core.management.base import BaseCommand
from decimal import Decimal

from academics.models import Program, Subject, Curriculum, CurriculumSubject, Prereq


class Command(BaseCommand):
    help = 'Seed comprehensive subject data for all programs'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting comprehensive subject seeding...'))

        # Get all programs
        programs = Program.objects.all()
        if not programs.exists():
            self.stdout.write(self.style.ERROR('No programs found. Run seed_registrar_data first.'))
            return

        # Seed subjects by program
        self.seed_cs_subjects(programs)
        self.seed_it_subjects(programs)
        self.seed_business_subjects(programs)
        self.seed_gen_ed_subjects(programs)

        self.stdout.write(self.style.SUCCESS('✓ Comprehensive subject seeding completed!'))

    def seed_cs_subjects(self, programs):
        """Seed Computer Science subjects"""
        self.stdout.write('\n📚 Creating Computer Science subjects...')

        cs_program = programs.filter(name__icontains='Computer Science').first()
        if not cs_program:
            self.stdout.write(self.style.WARNING('  ℹ Computer Science program not found, skipping...'))
            return

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

        created_count = 0
        for data in subjects_data:
            code = data.pop('code')
            year = data.pop('year')
            sem = data.pop('sem')

            if not Subject.objects.filter(code=code).exists():
                subject = Subject.objects.create(
                    program=cs_program,
                    code=code,
                    **data,
                    recommended_year=year,
                    recommended_sem=sem,
                    active=True,
                )
                created_count += 1
                self.stdout.write(f'  ✓ {code}: {subject.title}')
            else:
                self.stdout.write(f'  ℹ {code} already exists')

        # Add prerequisites for CS subjects
        self.add_cs_prerequisites()

        # Add to curriculum
        self.add_subjects_to_curriculum(cs_program)

        self.stdout.write(self.style.SUCCESS(f'  Created {created_count} CS subjects'))

    def seed_it_subjects(self, programs):
        """Seed Information Technology subjects"""
        self.stdout.write('\n📚 Creating Information Technology subjects...')

        it_program = programs.filter(name__icontains='Information Technology').first()
        if not it_program:
            self.stdout.write(self.style.WARNING('  ℹ IT program not found, skipping...'))
            return

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

        created_count = 0
        for data in subjects_data:
            code = data.pop('code')
            year = data.pop('year')
            sem = data.pop('sem')

            if not Subject.objects.filter(code=code).exists():
                subject = Subject.objects.create(
                    program=it_program,
                    code=code,
                    **data,
                    recommended_year=year,
                    recommended_sem=sem,
                    active=True,
                )
                created_count += 1
                self.stdout.write(f'  ✓ {code}: {subject.title}')
            else:
                self.stdout.write(f'  ℹ {code} already exists')

        # Add prerequisites for IT subjects
        self.add_it_prerequisites()

        # Add to curriculum
        self.add_subjects_to_curriculum(it_program)

        self.stdout.write(self.style.SUCCESS(f'  Created {created_count} IT subjects'))

    def seed_business_subjects(self, programs):
        """Seed Business Administration subjects"""
        self.stdout.write('\n📚 Creating Business Administration subjects...')

        business_program = programs.filter(name__icontains='Business').first()
        if not business_program:
            self.stdout.write(self.style.WARNING('  ℹ Business program not found, skipping...'))
            return

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

        created_count = 0
        for data in subjects_data:
            code = data.pop('code')
            year = data.pop('year')
            sem = data.pop('sem')

            if not Subject.objects.filter(code=code).exists():
                subject = Subject.objects.create(
                    program=business_program,
                    code=code,
                    **data,
                    recommended_year=year,
                    recommended_sem=sem,
                    active=True,
                )
                created_count += 1
                self.stdout.write(f'  ✓ {code}: {subject.title}')
            else:
                self.stdout.write(f'  ℹ {code} already exists')

        # Add prerequisites for Business subjects
        self.add_business_prerequisites()

        # Add to curriculum
        self.add_subjects_to_curriculum(business_program)

        self.stdout.write(self.style.SUCCESS(f'  Created {created_count} Business subjects'))

    def seed_gen_ed_subjects(self, programs):
        """Seed General Education subjects available to all programs"""
        self.stdout.write('\n📚 Creating General Education subjects...')

        # General Ed subjects should be available to all programs
        gen_ed_subjects = [
            {'code': 'GEN101', 'title': 'Philippine History', 'units': 3, 'year': 1, 'sem': 1},
            {'code': 'GEN102', 'title': 'Social Science', 'units': 3, 'year': 1, 'sem': 2},
            {'code': 'GEN103', 'title': 'Philosophy', 'units': 3, 'year': 2, 'sem': 1},
            {'code': 'GEN104', 'title': 'Literature', 'units': 3, 'year': 2, 'sem': 2},
            {'code': 'GEN105', 'title': 'Science & Environment', 'units': 3, 'year': 1, 'sem': 1},
            {'code': 'GEN106', 'title': 'Mathematics for Life', 'units': 3, 'year': 1, 'sem': 2},
            {'code': 'GEN107', 'title': 'Physical Education 1', 'units': 2, 'year': 1, 'sem': 1},
            {'code': 'GEN108', 'title': 'Physical Education 2', 'units': 2, 'year': 1, 'sem': 2},
            {'code': 'GEN109', 'title': 'Values Education', 'units': 3, 'year': 3, 'sem': 1},
            {'code': 'GEN110', 'title': 'Oral Communication', 'units': 3, 'year': 1, 'sem': 1},
        ]

        created_count = 0
        # Get a default program for Gen Ed (or pick first program)
        default_program = programs.first()

        for data in gen_ed_subjects:
            code = data['code']
            year = data.pop('year', 1)
            sem = data.pop('sem', 1)

            if not Subject.objects.filter(code=code).exists():
                subject = Subject.objects.create(
                    program=default_program,
                    **data,
                    type='minor',
                    recommended_year=year,
                    recommended_sem=sem,
                    active=True,
                )
                created_count += 1
                self.stdout.write(f'  ✓ {code}: {subject.title}')
            else:
                self.stdout.write(f'  ℹ {code} already exists')

        self.stdout.write(self.style.SUCCESS(f'  Created {created_count} Gen Ed subjects'))

    def add_cs_prerequisites(self):
        """Add prerequisite relationships for CS subjects"""
        self.stdout.write('  Adding CS prerequisites...')

        prerequisites = [
            ('CS103', 'CS102'),  # Data Structures requires Programming
            ('CS104', 'CS101'),  # Logic Design requires Intro to CS
            ('CS201', 'CS103'),  # Algorithms requires Data Structures
            ('CS202', 'CS104'),  # Computer Architecture requires Logic Design
            ('CS203', 'CS103'),  # DBMS requires Data Structures
            ('CS204', 'CS102'),  # OOP requires Programming Fundamentals
            ('CS205', 'CS202'),  # OS requires Computer Architecture
            ('CS206', 'CS201'),  # Software Engineering requires Algorithms
            ('CS301', 'CS204'),  # Web Dev requires OOP
            ('CS302', 'CS204'),  # Mobile App requires OOP
            ('CS303', 'CS102'),  # Networks requires Programming
            ('CS304', 'CS205'),  # Cybersecurity requires OS
            ('CS305', 'CS203'),  # Data Mining requires DBMS
            ('CS306', 'CS201'),  # AI requires Algorithms
            ('CS307', 'CS205'),  # Cloud Computing requires OS
            ('CS308', 'CS203'),  # Advanced DB requires DBMS
            ('CS401', 'CS206'),  # Capstone I requires Software Engineering
            ('CS402', 'CS306'),  # Machine Learning requires AI
            ('CS403', 'CS201'),  # Advanced Algorithms requires Algorithms
            ('CS404', 'CS401'),  # Capstone II requires Capstone I
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

        self.stdout.write(f'  ✓ Added {count} CS prerequisites')

    def add_it_prerequisites(self):
        """Add prerequisite relationships for IT subjects"""
        self.stdout.write('  Adding IT prerequisites...')

        prerequisites = [
            ('IT104', 'IT102'),  # Business Apps requires Programming
            ('IT105', 'IT103'),  # Systems Admin requires Hardware
            ('IT106', 'IT101'),  # Networking requires Fundamentals
            ('IT201', 'IT102'),  # Database Admin requires Programming
            ('IT202', 'IT106'),  # Network Admin requires Networking Basics
            ('IT203', 'IT102'),  # Web Tech requires Programming
            ('IT204', 'IT202'),  # Systems Security requires Network Admin
            ('IT205', 'IT201'),  # Enterprise Systems requires Database Admin
            ('IT206', 'IT101'),  # IT Project Management requires Fundamentals
            ('IT301', 'IT203'),  # Cloud Architecture requires Web Tech
            ('IT302', 'IT202'),  # Advanced Networking requires Network Admin
            ('IT303', 'IT204'),  # Business Continuity requires Systems Security
            ('IT304', 'IT206'),  # IT Governance requires Project Management
            ('IT305', 'IT205'),  # Capstone I requires Enterprise Systems
            ('IT401', 'IT305'),  # IT Strategy requires Capstone
            ('IT402', 'IT301'),  # Digital Transformation requires Cloud
            ('IT403', 'IT401'),  # Capstone II requires IT Strategy
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

        self.stdout.write(f'  ✓ Added {count} IT prerequisites')

    def add_business_prerequisites(self):
        """Add prerequisite relationships for Business subjects"""
        self.stdout.write('  Adding Business prerequisites...')

        prerequisites = [
            ('BUS102', 'BUS101'),  # Business Communication requires Intro to Business
            ('ACCT102', 'ACCT101'),  # Managerial Accounting requires Financial Accounting
            ('BUS201', 'BUS101'),  # Management requires Intro to Business
            ('MKTG201', 'BUS101'),  # Marketing requires Intro to Business
            ('BUS202', 'BUS201'),  # Org Behavior requires Management
            ('MKTG202', 'MKTG201'),  # Digital Marketing requires Marketing Principles
            ('FIN201', 'ACCT102'),  # Corporate Finance requires Managerial Accounting
            ('BUS301', 'BUS201'),  # Strategic Management requires Management
            ('MKTG301', 'MKTG201'),  # Consumer Behavior requires Marketing
            ('HRM301', 'BUS202'),  # HRM requires Org Behavior
            ('BUS302', 'BUS201'),  # Entrepreneurship requires Management
            ('BUS303', 'BUS101'),  # Business Ethics requires Intro to Business
            ('BUS401', 'BUS301'),  # Capstone I requires Strategic Management
            ('BUS402', 'MKTG201'),  # International Business requires Marketing
            ('BUS403', 'BUS401'),  # Capstone II requires Capstone I
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

        self.stdout.write(f'  ✓ Added {count} Business prerequisites')

    def add_subjects_to_curriculum(self, program):
        """Add subjects to the program's active curriculum"""
        self.stdout.write(f'  Adding subjects to {program.name} curriculum...')

        # Get active curriculum for this program
        curriculum = program.curricula.filter(active=True).first()
        if not curriculum:
            self.stdout.write(f'  ⚠ No active curriculum for {program.name}')
            return

        # Get all subjects for this program
        subjects = Subject.objects.filter(program=program)

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

        self.stdout.write(f'  ✓ Added {count} subjects to {program.name} curriculum')
