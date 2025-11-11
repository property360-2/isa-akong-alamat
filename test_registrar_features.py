"""
Comprehensive test script for all registrar features.
Tests CRUD operations, permissions, and special features.
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richwell_portal.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from academics.models import Program, Curriculum, Subject, Prereq, CurriculumSubject
from enrollment.models import Term, Section, Student
from settingsapp.models import Setting
from django.db import transaction

User = get_user_model()

# Test counters
tests_passed = 0
tests_failed = 0
test_results = []

def log_test(test_name, passed, message=""):
    global tests_passed, tests_failed
    if passed:
        tests_passed += 1
        status = "[PASS]"
    else:
        tests_failed += 1
        status = "[FAIL]"
    test_results.append(f"{status}: {test_name} {message}")
    print(f"{status}: {test_name} {message}")

def test_user_roles():
    """Test that users with different roles exist."""
    print("\n=== Testing User Roles ===")

    # Test registrar exists
    registrar = User.objects.filter(role='registrar').first()
    log_test("Registrar user exists", registrar is not None)

    # Test professor exists
    professor = User.objects.filter(role='professor').first()
    log_test("Professor user exists", professor is not None)

    # Test student exists
    student_user = User.objects.filter(role='student').first()
    log_test("Student user exists", student_user is not None)

    # Test student profile exists
    if student_user:
        student_profile = Student.objects.filter(user=student_user).first()
        log_test("Student profile exists", student_profile is not None)

    return registrar, professor, student_user

def test_authentication():
    """Test login and role-based access."""
    print("\n=== Testing Authentication & Authorization ===")

    client = Client()

    # Test login page accessible
    response = client.get('/login/')
    log_test("Login page accessible", response.status_code == 200)

    # Test login with registrar
    registrar = User.objects.filter(role='registrar').first()
    login_success = client.login(username=registrar.username, password='password123')
    log_test("Registrar can login", login_success)

    # Test registrar can access registrar dashboard
    response = client.get('/dashboard/registrar/')
    log_test("Registrar can access registrar dashboard", response.status_code == 200)

    # Test registrar can access academics index
    response = client.get('/registrar/academics/')
    log_test("Registrar can access academics module", response.status_code == 200)

    # Test registrar can access terms list
    response = client.get('/registrar/enrollment/terms/')
    log_test("Registrar can access terms module", response.status_code == 200)

    # Test registrar can access settings
    response = client.get('/registrar/settings/')
    log_test("Registrar can access settings module", response.status_code == 200)

    client.logout()

    # Test student cannot access registrar pages
    student = User.objects.filter(role='student').first()
    client.login(username=student.username, password='password123')
    response = client.get('/registrar/academics/')
    log_test("Student cannot access registrar pages", response.status_code == 403)

    client.logout()

def test_programs_crud():
    """Test Program CRUD operations."""
    print("\n=== Testing Programs CRUD ===")

    client = Client()
    registrar = User.objects.filter(role='registrar').first()
    client.login(username=registrar.username, password='password123')

    # Create program
    response = client.post('/registrar/academics/programs/create/', {
        'code': 'BSIT',
        'name': 'Bachelor of Science in Information Technology',
        'description': 'Four-year IT program',
        'duration_years': 4
    })
    log_test("Create program", response.status_code in [200, 302])

    # Check program was created
    program = Program.objects.filter(code='BSIT').first()
    log_test("Program exists in database", program is not None)

    if program:
        # Update program
        response = client.post(f'/registrar/academics/programs/{program.id}/update/', {
            'code': 'BSIT',
            'name': 'Bachelor of Science in Information Technology (Updated)',
            'description': 'Updated description',
            'duration_years': 4
        })
        log_test("Update program", response.status_code in [200, 302])

        # Verify update
        program.refresh_from_db()
        log_test("Program name updated", 'Updated' in program.name)

    client.logout()
    return program

def test_subjects_crud():
    """Test Subject CRUD operations."""
    print("\n=== Testing Subjects CRUD ===")

    client = Client()
    registrar = User.objects.filter(role='registrar').first()
    client.login(username=registrar.username, password='password123')

    # Create first subject
    response = client.post('/registrar/academics/subjects/create/', {
        'code': 'IT101',
        'title': 'Introduction to Programming',
        'description': 'Basic programming concepts',
        'units_lec': 2,
        'units_lab': 1
    })
    log_test("Create subject IT101", response.status_code in [200, 302])

    subject1 = Subject.objects.filter(code='IT101').first()
    log_test("Subject IT101 exists", subject1 is not None)

    # Create second subject
    response = client.post('/registrar/academics/subjects/create/', {
        'code': 'IT102',
        'title': 'Data Structures',
        'description': 'Advanced data structures',
        'units_lec': 2,
        'units_lab': 1
    })
    log_test("Create subject IT102", response.status_code in [200, 302])

    subject2 = Subject.objects.filter(code='IT102').first()
    log_test("Subject IT102 exists", subject2 is not None)

    # Test prerequisite creation
    if subject1 and subject2:
        response = client.post(f'/registrar/academics/subjects/{subject2.id}/prerequisites/add/', {
            'prerequisite_id': subject1.id
        })
        log_test("Add prerequisite", response.status_code in [200, 302])

        # Verify prerequisite
        prereq = Prereq.objects.filter(subject=subject2, prerequisite=subject1).first()
        log_test("Prerequisite exists", prereq is not None)

    client.logout()
    return subject1, subject2

def test_curricula_management(program, subject1, subject2):
    """Test Curriculum CRUD and special features."""
    print("\n=== Testing Curricula Management ===")

    client = Client()
    registrar = User.objects.filter(role='registrar').first()
    client.login(username=registrar.username, password='password123')

    if not program:
        log_test("Skip curriculum tests", False, "(No program available)")
        return None

    # Create curriculum
    response = client.post('/registrar/academics/curricula/create/', {
        'program': program.id,
        'version_year': 2024,
        'description': 'Test Curriculum 2024',
        'is_active': True
    })
    log_test("Create curriculum", response.status_code in [200, 302])

    curriculum = Curriculum.objects.filter(program=program, version_year=2024).first()
    log_test("Curriculum exists", curriculum is not None)

    if curriculum and subject1:
        # Add subject to curriculum
        cs = CurriculumSubject.objects.create(
            curriculum=curriculum,
            subject=subject1,
            year_level=1,
            term_no=1,
            is_recommended=True
        )
        log_test("Add subject to curriculum", cs is not None)

        # Test curriculum duplicate
        response = client.post(f'/registrar/academics/curricula/{curriculum.id}/duplicate/', {
            'version_year': 2025,
            'description': 'Duplicated Curriculum 2025'
        })
        log_test("Duplicate curriculum", response.status_code in [200, 302])

        # Verify duplicate
        dup_curriculum = Curriculum.objects.filter(program=program, version_year=2025).first()
        log_test("Duplicated curriculum exists", dup_curriculum is not None)

        if dup_curriculum:
            dup_subjects = CurriculumSubject.objects.filter(curriculum=dup_curriculum).count()
            log_test("Duplicated curriculum has subjects", dup_subjects > 0)

    client.logout()
    return curriculum

def test_term_management():
    """Test Term CRUD and activation."""
    print("\n=== Testing Term Management ===")

    client = Client()
    registrar = User.objects.filter(role='registrar').first()
    client.login(username=registrar.username, password='password123')

    # Create term
    response = client.post('/registrar/enrollment/terms/create/', {
        'name': '1st Semester 2024-2025',
        'start_date': '2024-08-01',
        'end_date': '2024-12-15',
        'add_drop_deadline': '2024-08-15',
        'grade_encoding_deadline': '2024-12-20'
    })
    log_test("Create term", response.status_code in [200, 302])

    term = Term.objects.filter(name='1st Semester 2024-2025').first()
    log_test("Term exists", term is not None)

    if term:
        # Test term activation
        response = client.post(f'/registrar/enrollment/terms/{term.id}/activate/')
        log_test("Activate term", response.status_code in [200, 302])

        # Verify term is active
        term.refresh_from_db()
        log_test("Term is active", term.is_active)

        # Create second term
        response = client.post('/registrar/enrollment/terms/create/', {
            'name': '2nd Semester 2024-2025',
            'start_date': '2025-01-01',
            'end_date': '2025-05-15',
            'add_drop_deadline': '2025-01-15',
            'grade_encoding_deadline': '2025-05-20'
        })
        term2 = Term.objects.filter(name='2nd Semester 2024-2025').first()

        if term2:
            # Activate second term
            response = client.post(f'/registrar/enrollment/terms/{term2.id}/activate/')
            log_test("Activate second term", response.status_code in [200, 302])

            # Verify only one active term
            active_count = Term.objects.filter(is_active=True).count()
            log_test("Only one active term", active_count == 1)

            # Verify first term deactivated
            term.refresh_from_db()
            log_test("First term deactivated", not term.is_active)

    client.logout()
    return term

def test_section_management(term, subject1):
    """Test Section CRUD operations."""
    print("\n=== Testing Section Management ===")

    client = Client()
    registrar = User.objects.filter(role='registrar').first()
    client.login(username=registrar.username, password='password123')

    if not term or not subject1:
        log_test("Skip section tests", False, "(No term or subject available)")
        return None

    professor = User.objects.filter(role='professor').first()
    if not professor:
        log_test("Skip section tests", False, "(No professor available)")
        return None

    # Create section
    response = client.post('/registrar/enrollment/sections/create/', {
        'section_code': 'IT101-A',
        'subject': subject1.id,
        'term': term.id,
        'professor': professor.id,
        'schedule': 'MWF 9:00-10:00 AM',
        'room': 'Room 201',
        'capacity': 30,
        'status': 'open'
    })
    log_test("Create section", response.status_code in [200, 302])

    section = Section.objects.filter(section_code='IT101-A').first()
    log_test("Section exists", section is not None)

    if section:
        # Update section
        response = client.post(f'/registrar/enrollment/sections/{section.id}/update/', {
            'section_code': 'IT101-A',
            'subject': subject1.id,
            'term': term.id,
            'professor': professor.id,
            'schedule': 'MWF 10:00-11:00 AM',  # Changed time
            'room': 'Room 202',  # Changed room
            'capacity': 35,  # Changed capacity
            'status': 'open'
        })
        log_test("Update section", response.status_code in [200, 302])

        # Verify update
        section.refresh_from_db()
        log_test("Section schedule updated", '10:00' in section.schedule)
        log_test("Section capacity updated", section.capacity == 35)

    client.logout()
    return section

def test_settings_management():
    """Test Settings CRUD and toggle."""
    print("\n=== Testing Settings Management ===")

    client = Client()
    registrar = User.objects.filter(role='registrar').first()
    client.login(username=registrar.username, password='password123')

    # Access settings page (creates enrollment_open if not exists)
    response = client.get('/registrar/settings/')
    log_test("Access settings page", response.status_code == 200)

    # Check enrollment_open setting exists
    enrollment_setting = Setting.objects.filter(key_name='enrollment_open').first()
    log_test("Enrollment setting exists", enrollment_setting is not None)

    if enrollment_setting:
        initial_value = enrollment_setting.value_text

        # Toggle enrollment setting
        response = client.post(f'/registrar/settings/toggle/enrollment_open/')
        log_test("Toggle enrollment setting", response.status_code in [200, 302])

        # Verify toggle
        enrollment_setting.refresh_from_db()
        toggled = enrollment_setting.value_text != initial_value
        log_test("Enrollment setting toggled", toggled)

        # Toggle back
        response = client.post(f'/registrar/settings/toggle/enrollment_open/')
        enrollment_setting.refresh_from_db()
        back_to_initial = enrollment_setting.value_text == initial_value
        log_test("Enrollment setting toggled back", back_to_initial)

    client.logout()

def test_ajax_endpoints():
    """Test AJAX endpoints."""
    print("\n=== Testing AJAX Endpoints ===")

    client = Client()
    registrar = User.objects.filter(role='registrar').first()
    client.login(username=registrar.username, password='password123')

    # Test professor search
    response = client.get('/registrar/enrollment/ajax/professor-search/', {'q': 'prof'})
    log_test("Professor search endpoint", response.status_code == 200)

    if response.status_code == 200:
        import json
        data = json.loads(response.content)
        log_test("Professor search returns results", 'results' in data)

    # Test subject search
    response = client.get('/registrar/academics/subjects/search/', {'q': 'IT'})
    log_test("Subject search endpoint", response.status_code == 200)

    if response.status_code == 200:
        import json
        data = json.loads(response.content)
        log_test("Subject search returns results", 'results' in data)

    client.logout()

def run_all_tests():
    """Run all test suites."""
    print("="*60)
    print("REGISTRAR MODULE TEST SUITE")
    print("="*60)

    # Test user roles
    registrar, professor, student = test_user_roles()

    # Test authentication
    test_authentication()

    # Test programs
    program = test_programs_crud()

    # Test subjects
    subject1, subject2 = test_subjects_crud()

    # Test curricula
    curriculum = test_curricula_management(program, subject1, subject2)

    # Test terms
    term = test_term_management()

    # Test sections
    section = test_section_management(term, subject1)

    # Test settings
    test_settings_management()

    # Test AJAX
    test_ajax_endpoints()

    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Total Tests: {tests_passed + tests_failed}")
    print(f"Passed: {tests_passed}")
    print(f"Failed: {tests_failed}")
    print(f"Success Rate: {(tests_passed/(tests_passed+tests_failed)*100):.1f}%")
    print("="*60)

    if tests_failed > 0:
        print("\nFailed Tests:")
        for result in test_results:
            if "[FAIL]" in result:
                print(result)

    return tests_passed, tests_failed

if __name__ == '__main__':
    try:
        passed, failed = run_all_tests()
        exit(0 if failed == 0 else 1)
    except Exception as e:
        print(f"\n[FATAL ERROR]: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
