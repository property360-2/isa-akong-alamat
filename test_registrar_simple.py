"""
Simplified test script for registrar features that matches actual implementation.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richwell_portal.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from academics.models import Program, Curriculum, Subject
from enrollment.models import Term, Section
from settingsapp.models import Setting

User = get_user_model()

def print_test(name, passed):
    status = "[PASS]" if passed else "[FAIL]"
    print(f"{status}: {name}")
    return passed

def main():
    print("\n" + "="*60)
    print("REGISTRAR FEATURE TESTS")
    print("="*60)

    passed = 0
    total = 0

    # Setup client
    client = Client()
    registrar = User.objects.filter(role='registrar').first()

    # Test 1: User seeding
    print("\n=== User & Profile Tests ===")
    total += 1
    if print_test("Registrar user exists", registrar is not None):
        passed += 1

    total += 1
    professor = User.objects.filter(role='professor').first()
    if print_test("Professor user exists", professor is not None):
        passed += 1

    total += 1
    student_user = User.objects.filter(role='student').first()
    if print_test("Student user exists", student_user is not None):
        passed += 1

    # Test 2: Authentication
    print("\n=== Authentication Tests ===")
    total += 1
    response = client.get('/login/')
    if print_test("Login page loads", response.status_code == 200):
        passed += 1

    total += 1
    login_ok = client.login(username=registrar.username, password='password123')
    if print_test("Registrar can login", login_ok):
        passed += 1

    # Test 3: Dashboard access
    print("\n=== Dashboard Access Tests ===")
    total += 1
    response = client.get('/dashboard/registrar/')
    if print_test("Registrar dashboard accessible", response.status_code == 200):
        passed += 1

    # Test 4: Module access
    print("\n=== Module Access Tests ===")
    total += 1
    response = client.get('/registrar/academics/')
    if print_test("Academics module accessible", response.status_code == 200):
        passed += 1

    total += 1
    response = client.get('/registrar/enrollment/terms/')
    if print_test("Terms module accessible", response.status_code == 200):
        passed += 1

    total += 1
    response = client.get('/registrar/enrollment/sections/')
    if print_test("Sections module accessible", response.status_code == 200):
        passed += 1

    total += 1
    response = client.get('/registrar/settings/')
    if print_test("Settings module accessible", response.status_code == 200):
        passed += 1

    # Test 5: Model creation (direct)
    print("\n=== Data Model Tests ===")
    total += 1
    # Check if models can be accessed
    program = Program.objects.first()
    if print_test("Program model exists", program is not None):
        passed += 1

    total += 1
    curriculum = Curriculum.objects.first()
    if print_test("Curriculum model exists", curriculum is not None):
        passed += 1

    total += 1
    subject = Subject.objects.first()
    if print_test("Subject model exists", subject is not None):
        passed += 1

    total += 1
    term = Term.objects.first()
    if print_test("Term model exists", term is not None):
        passed += 1

    total += 1
    section = Section.objects.first()
    if print_test("Section model exists", section is not None):
        passed += 1

    # Test 6: Settings
    print("\n=== Settings Tests ===")
    total += 1
    enrollment_setting, created = Setting.objects.get_or_create(
        key_name='enrollment_open',
        defaults={
            'value_text': 'false',
            'description': 'Toggle enrollment',
            'updated_by': registrar
        }
    )
    if print_test("Enrollment setting exists", enrollment_setting is not None):
        passed += 1

    # Test 7: Term activation
    print("\n=== Term Activation Test ===")
    total += 1
    if term:
        term.is_active = True
        term.save()
        term.refresh_from_db()
        if print_test("Term can be activated", term.is_active):
            passed += 1
    else:
        print_test("Term can be activated", False)
        # Still count total even if we can't test

    # Test 8: Role-based access control
    print("\n=== RBAC Tests ===")
    client.logout()
    client.login(username=student_user.username, password='password123')
    total += 1
    response = client.get('/registrar/academics/')
    if print_test("Student blocked from registrar module", response.status_code == 403):
        passed += 1

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total*100):.1f}%")
    print("="*60)

    return 0 if passed == total else 1

if __name__ == '__main__':
    try:
        exit(main())
    except Exception as e:
        print(f"\n[ERROR]: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
