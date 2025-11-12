"""
Seed command to create comprehensive test data for enrollment testing.

This command creates students with different scenarios:
1. Fresh students (Year 1, Sem 1) - no completed subjects
2. Year 1 Sem 2 students - completed Year 1 Sem 1
3. Year 2 Sem 1 students - completed Year 1 (both semesters)
4. Year 2 Sem 1 with INC - has incomplete subjects from previous semester
5. Year 3 students with multiple INC subjects
6. Mixed scenarios with failed subjects needing repeat

Each scenario includes proper grade history and prerequisite setup.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from decimal import Decimal
from datetime import date
from users.models import User
from enrollment.models import Student, Term, Section, StudentSubject, Enrollment
from academics.models import Program, Curriculum, Subject, Prereq, CurriculumSubject
from grades.models import Grade


class Command(BaseCommand):
    help = 'Seed enrollment test data with various scenarios (INC, different year levels)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing test data before seeding',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Starting enrollment test data seeding...'))

        if options['clear']:
            self.clear_test_data()

        # Setup: Create or get program and curriculum
        program = self.setup_program()
        curriculum = self.setup_curriculum(program)
        subjects = self.setup_subjects(program, curriculum)
        self.setup_prerequisites(subjects)
        terms = self.setup_terms()
        professors = self.setup_professors()
        sections = self.setup_sections(terms, subjects, professors)

        # Create test students with various scenarios
        self.create_test_students(program, curriculum, subjects, terms, professors)

        self.stdout.write(self.style.SUCCESS('\n' + '=' * 70))
        self.stdout.write(self.style.SUCCESS('ENROLLMENT TEST DATA SEEDING COMPLETE'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.print_test_scenarios()

    def clear_test_data(self):
        """Clear test data while preserving system data"""
        self.stdout.write(self.style.WARNING('Clearing test data...'))

        # Delete StudentSubject records first (has FK to Student)
        StudentSubject.objects.filter(student__user__username__startswith='test_student').delete()

        # Delete Enrollment records
        Enrollment.objects.filter(student__user__username__startswith='test_student').delete()

        # Delete Student profiles
        Student.objects.filter(user__username__startswith='test_student').delete()

        # Delete test users
        User.objects.filter(username__startswith='test_student').delete()

        self.stdout.write(self.style.SUCCESS('Test data cleared'))

    def setup_program(self):
        """Get or create test program"""
        program, created = Program.objects.get_or_create(
            name='Bachelor of Science in Computer Science',
            defaults={
                'level': 'Bachelor',
                'passing_grade': Decimal('2.00'),
            }
        )
        if created:
            self.stdout.write(f'Created program: {program.name}')
        return program

    def setup_curriculum(self, program):
        """Get or create test curriculum"""
        curriculum, created = Curriculum.objects.get_or_create(
            program=program,
            version='CHED 2021',
            defaults={
                'effective_sy': 'AY 2024-2025',
                'active': True,
            }
        )
        if created:
            self.stdout.write(f'Created curriculum: {curriculum}')
        return curriculum

    def setup_subjects(self, program, curriculum):
        """Create subjects with proper curriculum mapping"""
        subjects_data = [
            # Year 1, Semester 1
            {'code': 'CS101', 'title': 'Introduction to CS', 'units': 3, 'year': 1, 'sem': 1},
            {'code': 'CS102', 'title': 'Programming Fundamentals', 'units': 3, 'year': 1, 'sem': 1},
            {'code': 'MATH101', 'title': 'Discrete Mathematics', 'units': 3, 'year': 1, 'sem': 1},
            {'code': 'ENG101', 'title': 'English Composition', 'units': 3, 'year': 1, 'sem': 1},

            # Year 1, Semester 2
            {'code': 'CS103', 'title': 'Data Structures', 'units': 3, 'year': 1, 'sem': 2},
            {'code': 'CS104', 'title': 'Logic Design', 'units': 3, 'year': 1, 'sem': 2},
            {'code': 'MATH102', 'title': 'Calculus I', 'units': 4, 'year': 1, 'sem': 2},
            {'code': 'PE101', 'title': 'Physical Education', 'units': 2, 'year': 1, 'sem': 2},

            # Year 2, Semester 1
            {'code': 'CS201', 'title': 'Algorithms & Analysis', 'units': 3, 'year': 2, 'sem': 1},
            {'code': 'CS202', 'title': 'Computer Architecture', 'units': 3, 'year': 2, 'sem': 1},
            {'code': 'CS203', 'title': 'Database Management Systems', 'units': 3, 'year': 2, 'sem': 1},
            {'code': 'MATH201', 'title': 'Calculus II', 'units': 4, 'year': 2, 'sem': 1},

            # Year 2, Semester 2
            {'code': 'CS204', 'title': 'Object Oriented Programming', 'units': 3, 'year': 2, 'sem': 2},
            {'code': 'CS205', 'title': 'Web Development I', 'units': 3, 'year': 2, 'sem': 2},
            {'code': 'CS206', 'title': 'Software Engineering', 'units': 3, 'year': 2, 'sem': 2},

            # Year 3, Semester 1
            {'code': 'CS301', 'title': 'Web Development II', 'units': 3, 'year': 3, 'sem': 1},
            {'code': 'CS302', 'title': 'Databases II', 'units': 3, 'year': 3, 'sem': 1},
            {'code': 'CS303', 'title': 'Networking', 'units': 3, 'year': 3, 'sem': 1},
        ]

        subjects = {}
        for subj_data in subjects_data:
            subject, created = Subject.objects.get_or_create(
                code=subj_data['code'],
                defaults={
                    'program': program,
                    'title': subj_data['title'],
                    'units': Decimal(str(subj_data['units'])),
                    'type': 'major',
                    'recommended_year': subj_data['year'],
                    'recommended_sem': subj_data['sem'],
                    'active': True,
                }
            )

            # Create curriculum mapping
            CurriculumSubject.objects.get_or_create(
                curriculum=curriculum,
                subject=subject,
                defaults={
                    'year_level': subj_data['year'],
                    'term_no': subj_data['sem'],
                    'is_recommended': True,
                }
            )

            subjects[subj_data['code']] = subject

        self.stdout.write(f'Created/verified {len(subjects)} subjects')
        return subjects

    def setup_prerequisites(self, subjects):
        """Setup prerequisite relationships"""
        prerequisites = [
            # Year 1 Sem 2 prerequisites
            ('CS103', 'CS102'),  # Data Structures requires Programming
            ('CS104', 'CS101'),  # Logic Design requires Intro to CS

            # Year 2 Sem 1 prerequisites
            ('CS201', 'CS103'),  # Algorithms requires Data Structures
            ('CS202', 'CS104'),  # Computer Architecture requires Logic Design
            ('CS203', 'CS103'),  # Database requires Data Structures
            ('MATH201', 'MATH102'),  # Calculus II requires Calculus I

            # Year 2 Sem 2 prerequisites
            ('CS204', 'CS102'),  # OOP requires Programming
            ('CS205', 'CS103'),  # Web Dev I requires Data Structures
            ('CS206', 'CS201'),  # Software Engineering requires Algorithms

            # Year 3 Sem 1 prerequisites
            ('CS301', 'CS205'),  # Web Dev II requires Web Dev I
            ('CS302', 'CS203'),  # Databases II requires Database I
            ('CS303', 'CS202'),  # Networking requires Computer Architecture
        ]

        created_count = 0
        for subject_code, prereq_code in prerequisites:
            subject = subjects[subject_code]
            prereq = subjects[prereq_code]

            _, created = Prereq.objects.get_or_create(
                subject=subject,
                prereq_subject=prereq,
            )
            if created:
                created_count += 1

        self.stdout.write(f'Created {created_count} prerequisite relationships')

    def setup_terms(self):
        """Create test terms"""
        terms_data = [
            {
                'name': '2nd Semester 2023-2024',
                'level': 'Bachelor',
                'start_date': date(2024, 1, 15),
                'end_date': date(2024, 5, 31),
                'add_drop_deadline': date(2024, 1, 29),
                'grade_encoding_deadline': date(2024, 6, 7),
                'is_active': False,
                'archived': True,
            },
            {
                'name': '1st Semester 2024-2025',
                'level': 'Bachelor',
                'start_date': date(2024, 8, 15),
                'end_date': date(2024, 12, 20),
                'add_drop_deadline': date(2024, 8, 29),
                'grade_encoding_deadline': date(2024, 12, 27),
                'is_active': True,
            },
            {
                'name': '2nd Semester 2024-2025',
                'level': 'Bachelor',
                'start_date': date(2025, 1, 15),
                'end_date': date(2025, 5, 31),
                'add_drop_deadline': date(2025, 1, 29),
                'grade_encoding_deadline': date(2025, 6, 7),
                'is_active': False,
            },
        ]

        terms = {}
        for term_data in terms_data:
            term, created = Term.objects.get_or_create(
                name=term_data['name'],
                level=term_data['level'],
                defaults=term_data,
            )
            terms[term_data['name']] = term
            if created:
                self.stdout.write(f'Created term: {term.name}')

        return terms

    def setup_professors(self):
        """Create or get test professors"""
        professor_data = [
            {'username': 'test_prof1', 'name': 'Dr. Michael Garcia'},
            {'username': 'test_prof2', 'name': 'Dr. Sarah Reyes'},
            {'username': 'test_prof3', 'name': 'Dr. David Gonzales'},
        ]

        professors = {}
        for prof_data in professor_data:
            prof, created = User.objects.get_or_create(
                username=prof_data['username'],
                defaults={
                    'email': f"{prof_data['username']}@richwell.edu",
                    'first_name': prof_data['name'].split()[1],
                    'last_name': prof_data['name'].split()[2],
                    'role': 'professor',
                    'password': make_password('password123'),
                }
            )
            professors[prof_data['username']] = prof

        self.stdout.write(f'Created/verified {len(professors)} test professors')
        return professors

    def setup_sections(self, terms, subjects, professors):
        """Create sections for test subjects"""
        term = terms['1st Semester 2024-2025']
        prof1 = professors['test_prof1']
        prof2 = professors['test_prof2']

        section_data = [
            {'code': 'CS101-A', 'subject_codes': ['CS101'], 'prof': prof1},
            {'code': 'CS102-A', 'subject_codes': ['CS102'], 'prof': prof1},
            {'code': 'MATH101-A', 'subject_codes': ['MATH101'], 'prof': prof2},
            {'code': 'ENG101-A', 'subject_codes': ['ENG101'], 'prof': prof2},
        ]

        sections = {}
        for sec_data in section_data:
            section, created = Section.objects.get_or_create(
                term=term,
                section_code=sec_data['code'],
                defaults={
                    'capacity': 40,
                    'status': 'open',
                }
            )

            # Add subjects to section
            for subj_code in sec_data['subject_codes']:
                section.subjects.add(subjects[subj_code])

            # Add professor
            section.professors.add(sec_data['prof'])

            sections[sec_data['code']] = section

        self.stdout.write(f'Created sections for term: {term.name}')
        return sections

    def create_test_students(self, program, curriculum, subjects, terms, professors):
        """Create students with different enrollment scenarios"""

        active_term = terms['1st Semester 2024-2025']
        past_term = terms['2nd Semester 2023-2024']
        prof = professors['test_prof1']

        # Scenario 1: Fresh student (Year 1, Sem 1) - no history
        self.create_fresh_student(
            program, curriculum, subjects, active_term, prof,
            'test_student_fresh_y1s1',
            'Juan', 'Dela Cruz'
        )

        # Scenario 2: Year 1 Sem 2 student - completed Y1S1 with passing grades
        self.create_year1_sem2_student(
            program, curriculum, subjects, terms, past_term, prof,
            'test_student_y1s2_pass',
            'Maria', 'Rodriguez'
        )

        # Scenario 3: Year 2 Sem 1 student - completed full Year 1
        self.create_year2_sem1_student(
            program, curriculum, subjects, terms, past_term, prof,
            'test_student_y2s1_pass',
            'Pedro', 'Martinez'
        )

        # Scenario 4: Year 2 Sem 1 with ONE INC subject - can still proceed
        self.create_year2_student_with_inc(
            program, curriculum, subjects, terms, past_term, prof,
            'test_student_y2s1_with_inc',
            'Ana', 'Lopez'
        )

        # Scenario 5: Year 3 student with MULTIPLE INC subjects
        self.create_year3_student_with_multiple_inc(
            program, curriculum, subjects, terms, past_term, prof,
            'test_student_y3_multi_inc',
            'Carlos', 'Hernandez'
        )

        # Scenario 6: Year 2 Sem 2 student - completed Y2S1
        self.create_year2_sem2_student(
            program, curriculum, subjects, terms, past_term, prof,
            'test_student_y2s2_pass',
            'Sofia', 'Gonzalez'
        )

    def create_fresh_student(self, program, curriculum, subjects, active_term, prof, username, first_name, last_name):
        """Create a fresh Year 1 Sem 1 student with no enrollment history"""
        user, _ = User.objects.get_or_create(
            username=username,
            defaults={
                'email': f'{username}@richwell.edu',
                'first_name': first_name,
                'last_name': last_name,
                'role': 'student',
                'password': make_password('password123'),
            }
        )

        student, _ = Student.objects.get_or_create(
            user=user,
            defaults={
                'program': program,
                'curriculum': curriculum,
                'status': 'active',
            }
        )

        # Enroll in Year 1 Sem 1 subjects but don't complete them
        # This student has no prior completed subjects
        self.stdout.write(f'[OK] Created fresh student: {username} (Year 1, Sem 1)')

    def create_year1_sem2_student(self, program, curriculum, subjects, terms, past_term, prof, username, first_name, last_name):
        """Year 1 Sem 2 student - completed Y1S1 with passing grades"""

        # Create user and student
        user, _ = User.objects.get_or_create(
            username=username,
            defaults={
                'email': f'{username}@richwell.edu',
                'first_name': first_name,
                'last_name': last_name,
                'role': 'student',
                'password': make_password('password123'),
            }
        )

        student, _ = Student.objects.get_or_create(
            user=user,
            defaults={
                'program': program,
                'curriculum': curriculum,
                'status': 'active',
            }
        )

        # Mark Y1S1 subjects as completed with passing grades
        y1s1_subjects = [subjects['CS101'], subjects['CS102'], subjects['MATH101'], subjects['ENG101']]

        grades = ['2.5', '2.75', '2.0', '3.0']

        for i, subject in enumerate(y1s1_subjects):
            ss, _ = StudentSubject.objects.get_or_create(
                student=student,
                subject=subject,
                term=past_term,
                defaults={
                    'status': 'completed',
                    'professor': prof,
                }
            )

            # Create grade record
            Grade.objects.get_or_create(
                student_subject=ss,
                subject=subject,
                professor=prof,
                defaults={
                    'grade': grades[i],
                }
            )

        # Create enrollment for the completed term
        Enrollment.objects.get_or_create(
            student=student,
            term=past_term,
            defaults={
                'total_units': 12,
                'status': 'completed',
            }
        )

        self.stdout.write(f'[OK] Created Y1S2 student: {username} (completed Y1S1)')

    def create_year2_sem1_student(self, program, curriculum, subjects, terms, past_term, prof, username, first_name, last_name):
        """Year 2 Sem 1 student - completed full Year 1 (both semesters)"""

        user, _ = User.objects.get_or_create(
            username=username,
            defaults={
                'email': f'{username}@richwell.edu',
                'first_name': first_name,
                'last_name': last_name,
                'role': 'student',
                'password': make_password('password123'),
            }
        )

        student, _ = Student.objects.get_or_create(
            user=user,
            defaults={
                'program': program,
                'curriculum': curriculum,
                'status': 'active',
            }
        )

        # Complete Y1S1 subjects
        y1s1_subjects = [
            (subjects['CS101'], '2.5'),
            (subjects['CS102'], '2.75'),
            (subjects['MATH101'], '2.0'),
            (subjects['ENG101'], '3.0'),
        ]

        for subject, grade_val in y1s1_subjects:
            ss = StudentSubject.objects.create(
                student=student,
                subject=subject,
                term=past_term,
                status='completed',
                professor=prof,
            )
            Grade.objects.create(
                student_subject=ss,
                subject=subject,
                professor=prof,
                grade=grade_val,
            )

        # Complete Y1S2 subjects
        y1s2_subjects = [
            (subjects['CS103'], '2.5'),
            (subjects['CS104'], '2.75'),
            (subjects['MATH102'], '2.0'),
            (subjects['PE101'], '3.0'),
        ]

        for subject, grade_val in y1s2_subjects:
            ss = StudentSubject.objects.create(
                student=student,
                subject=subject,
                term=past_term,
                status='completed',
                professor=prof,
            )
            Grade.objects.create(
                student_subject=ss,
                subject=subject,
                professor=prof,
                grade=grade_val,
            )

        # Create past enrollments
        Enrollment.objects.get_or_create(
            student=student,
            term=past_term,
            defaults={
                'total_units': 24,
                'status': 'completed',
            }
        )

        self.stdout.write(f'[OK] Created Y2S1 student: {username} (completed full Year 1)')

    def create_year2_student_with_inc(self, program, curriculum, subjects, terms, past_term, prof, username, first_name, last_name):
        """Year 2 Sem 1 student WITH ONE INC subject from Y1S2"""

        user, _ = User.objects.get_or_create(
            username=username,
            defaults={
                'email': f'{username}@richwell.edu',
                'first_name': first_name,
                'last_name': last_name,
                'role': 'student',
                'password': make_password('password123'),
            }
        )

        student, _ = Student.objects.get_or_create(
            user=user,
            defaults={
                'program': program,
                'curriculum': curriculum,
                'status': 'active',
            }
        )

        # Complete Y1S1 subjects
        y1s1_subjects = [
            (subjects['CS101'], '2.5'),
            (subjects['CS102'], '2.75'),
            (subjects['MATH101'], '2.0'),
            (subjects['ENG101'], '3.0'),
        ]

        for subject, grade_val in y1s1_subjects:
            ss = StudentSubject.objects.create(
                student=student,
                subject=subject,
                term=past_term,
                status='completed',
                professor=prof,
            )
            Grade.objects.create(
                student_subject=ss,
                subject=subject,
                professor=prof,
                grade=grade_val,
            )

        # Y1S2: CS103 and CS104 completed, BUT CS103 is INCOMPLETE (INC)
        # Even with INC, grade is 2.5 which >= passing_grade 2.0
        ss = StudentSubject.objects.create(
            student=student,
            subject=subjects['CS103'],
            term=past_term,
            status='inc',
            professor=prof,
        )
        Grade.objects.create(
            student_subject=ss,
            subject=subjects['CS103'],
            professor=prof,
            grade='2.5',  # Passing grade despite being incomplete
        )

        # CS104 completed normally
        ss = StudentSubject.objects.create(
            student=student,
            subject=subjects['CS104'],
            term=past_term,
            status='completed',
            professor=prof,
        )
        Grade.objects.create(
            student_subject=ss,
            subject=subjects['CS104'],
            professor=prof,
            grade='2.75',
        )

        # Other Y1S2 subjects completed
        ss = StudentSubject.objects.create(
            student=student,
            subject=subjects['MATH102'],
            term=past_term,
            status='completed',
            professor=prof,
        )
        Grade.objects.create(
            student_subject=ss,
            subject=subjects['MATH102'],
            professor=prof,
            grade='2.0',
        )

        ss = StudentSubject.objects.create(
            student=student,
            subject=subjects['PE101'],
            term=past_term,
            status='completed',
            professor=prof,
        )
        Grade.objects.create(
            student_subject=ss,
            subject=subjects['PE101'],
            professor=prof,
            grade='3.0',
        )

        # Create enrollment
        Enrollment.objects.get_or_create(
            student=student,
            term=past_term,
            defaults={
                'total_units': 24,
                'status': 'completed',
            }
        )

        self.stdout.write(f'[OK] Created Y2S1 student with INC: {username} (CS103 is INC but passing)')

    def create_year3_student_with_multiple_inc(self, program, curriculum, subjects, terms, past_term, prof, username, first_name, last_name):
        """Year 3 student with MULTIPLE INC subjects from earlier years"""

        user, _ = User.objects.get_or_create(
            username=username,
            defaults={
                'email': f'{username}@richwell.edu',
                'first_name': first_name,
                'last_name': last_name,
                'role': 'student',
                'password': make_password('password123'),
            }
        )

        student, _ = Student.objects.get_or_create(
            user=user,
            defaults={
                'program': program,
                'curriculum': curriculum,
                'status': 'active',
            }
        )

        # Y1S1: Complete some, mark one as INC
        y1s1_data = [
            (subjects['CS101'], 'completed', '2.5'),
            (subjects['CS102'], 'inc', '2.5'),  # INC but passing
            (subjects['MATH101'], 'completed', '2.0'),
            (subjects['ENG101'], 'completed', '3.0'),
        ]

        for subject, status, grade_val in y1s1_data:
            ss = StudentSubject.objects.create(
                student=student,
                subject=subject,
                term=past_term,
                status=status,
                professor=prof,
            )
            Grade.objects.create(
                student_subject=ss,
                subject=subject,
                professor=prof,
                grade=grade_val,
            )

        # Y1S2: Complete some, mark CS103 as INC (depends on CS102 which is INC)
        y1s2_data = [
            (subjects['CS103'], 'inc', '2.25'),  # Depends on CS102 (INC but passing)
            (subjects['CS104'], 'completed', '2.75'),
            (subjects['MATH102'], 'completed', '2.0'),
            (subjects['PE101'], 'completed', '3.0'),
        ]

        for subject, status, grade_val in y1s2_data:
            ss = StudentSubject.objects.create(
                student=student,
                subject=subject,
                term=past_term,
                status=status,
                professor=prof,
            )
            Grade.objects.create(
                student_subject=ss,
                subject=subject,
                professor=prof,
                grade=grade_val,
            )

        # Y2S1: Complete some Y2S1 subjects despite prior INC subjects
        y2s1_data = [
            (subjects['CS201'], 'completed', '2.5'),  # Depends on CS103 (INC)
            (subjects['CS202'], 'completed', '2.75'),  # Depends on CS104
            (subjects['CS203'], 'completed', '2.0'),  # Depends on CS103 (INC)
        ]

        for subject, status, grade_val in y2s1_data:
            ss = StudentSubject.objects.create(
                student=student,
                subject=subject,
                term=past_term,
                status=status,
                professor=prof,
            )
            Grade.objects.create(
                student_subject=ss,
                subject=subject,
                professor=prof,
                grade=grade_val,
            )

        # Create enrollments
        Enrollment.objects.get_or_create(
            student=student,
            term=past_term,
            defaults={
                'total_units': 40,
                'status': 'completed',
            }
        )

        self.stdout.write(f'[OK] Created Y3 student with multiple INC: {username} (CS102, CS103 are INC)')

    def create_year2_sem2_student(self, program, curriculum, subjects, terms, past_term, prof, username, first_name, last_name):
        """Year 2 Sem 2 student - completed Y2S1"""

        user, _ = User.objects.get_or_create(
            username=username,
            defaults={
                'email': f'{username}@richwell.edu',
                'first_name': first_name,
                'last_name': last_name,
                'role': 'student',
                'password': make_password('password123'),
            }
        )

        student, _ = Student.objects.get_or_create(
            user=user,
            defaults={
                'program': program,
                'curriculum': curriculum,
                'status': 'active',
            }
        )

        # Complete full Year 1
        y1_subjects = [
            (subjects['CS101'], '2.5'),
            (subjects['CS102'], '2.75'),
            (subjects['MATH101'], '2.0'),
            (subjects['ENG101'], '3.0'),
            (subjects['CS103'], '2.5'),
            (subjects['CS104'], '2.75'),
            (subjects['MATH102'], '2.0'),
            (subjects['PE101'], '3.0'),
        ]

        for subject, grade_val in y1_subjects:
            ss = StudentSubject.objects.create(
                student=student,
                subject=subject,
                term=past_term,
                status='completed',
                professor=prof,
            )
            Grade.objects.create(
                student_subject=ss,
                subject=subject,
                professor=prof,
                grade=grade_val,
            )

        # Complete Y2S1
        y2s1_subjects = [
            (subjects['CS201'], '2.5'),
            (subjects['CS202'], '2.75'),
            (subjects['CS203'], '2.0'),
            (subjects['MATH201'], '2.5'),
        ]

        for subject, grade_val in y2s1_subjects:
            ss = StudentSubject.objects.create(
                student=student,
                subject=subject,
                term=past_term,
                status='completed',
                professor=prof,
            )
            Grade.objects.create(
                student_subject=ss,
                subject=subject,
                professor=prof,
                grade=grade_val,
            )

        # Create enrollment
        Enrollment.objects.get_or_create(
            student=student,
            term=past_term,
            defaults={
                'total_units': 36,
                'status': 'completed',
            }
        )

        self.stdout.write(f'[OK] Created Y2S2 student: {username} (completed Y2S1)')

    def print_test_scenarios(self):
        """Print detailed information about all test scenarios"""
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 70))
        self.stdout.write(self.style.WARNING('TEST STUDENT SCENARIOS:'))
        self.stdout.write(self.style.SUCCESS('=' * 70))

        scenarios = [
            {
                'username': 'test_student_fresh_y1s1',
                'name': 'Fresh Student (Year 1, Sem 1)',
                'description': 'No enrollment history. Can only take Year 1 Sem 1 subjects.',
                'enrollment_level': '1st Semester 2024-2025',
                'completed_subjects': 'None',
                'inc_subjects': 'None',
            },
            {
                'username': 'test_student_y1s2_pass',
                'name': 'Year 1 Sem 2 Student',
                'description': 'Completed Year 1 Sem 1 with all passing grades (2.0-3.0).',
                'enrollment_level': '2nd Semester 2024-2025',
                'completed_subjects': 'CS101, CS102, MATH101, ENG101',
                'inc_subjects': 'None',
            },
            {
                'username': 'test_student_y2s1_pass',
                'name': 'Year 2 Sem 1 Student',
                'description': 'Completed full Year 1 (both semesters) with passing grades.',
                'enrollment_level': '1st Semester 2024-2025',
                'completed_subjects': 'All Year 1 subjects (8 subjects, 12 units)',
                'inc_subjects': 'None',
            },
            {
                'username': 'test_student_y2s1_with_inc',
                'name': 'Year 2 Student with 1 INC',
                'description': 'Completed Year 1 BUT CS103 is marked INCOMPLETE (INC) with grade 2.5.',
                'enrollment_level': '1st Semester 2024-2025',
                'completed_subjects': 'CS101, CS102, MATH101, ENG101, CS104, MATH102, PE101',
                'inc_subjects': 'CS103 (grade: 2.5 - PASSING but still INCOMPLETE)',
                'test_case': 'CANNOT enroll in CS201/CS203 (requires CS103) - blocked until INC is resolved',
            },
            {
                'username': 'test_student_y3_multi_inc',
                'name': 'Year 3 Student with Multiple INC',
                'description': 'Advanced student with multiple incomplete subjects from earlier years.',
                'enrollment_level': '1st Semester 2024-2025',
                'completed_subjects': 'CS101, MATH101, ENG101, CS104, MATH102, PE101, CS201, CS202, CS203',
                'inc_subjects': 'CS102 (grade: 2.5), CS103 (grade: 2.25)',
                'test_case': 'CANNOT enroll in Y3S1 subjects if they require CS102/CS103 - blocked by INC',
            },
            {
                'username': 'test_student_y2s2_pass',
                'name': 'Year 2 Sem 2 Student',
                'description': 'Completed Year 1 and Year 2 Sem 1 with all passing grades.',
                'enrollment_level': '2nd Semester 2024-2025',
                'completed_subjects': 'All Year 1 + Year 2 Sem 1 subjects (12 subjects, 24 units)',
                'inc_subjects': 'None',
            },
        ]

        for scenario in scenarios:
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS(f">> {scenario['name']}"))
            self.stdout.write(f"  Username: {self.style.WARNING(scenario['username'])}")
            self.stdout.write(f"  Description: {scenario['description']}")
            self.stdout.write(f"  Completed: {scenario['completed_subjects']}")
            self.stdout.write(f"  INC subjects: {scenario['inc_subjects']}")
            if 'test_case' in scenario:
                self.stdout.write(f"  TEST CASE: {self.style.WARNING(scenario['test_case'])}")

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('All test students use password: password123'))
        self.stdout.write('')
