#!/usr/bin/env python
"""
Test script for the complete freshman enrollment flow.
Tests all steps: credentials → course selection → confirmation → completion
"""

import os
import django
import requests
from django.test import Client
from django.contrib.auth import get_user_model

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richwell_portal.settings')
django.setup()

from enrollment.models import Student, Program, Term
from django.urls import reverse

User = get_user_model()

def test_freshman_flow():
    """Test the complete freshman enrollment flow"""

    client = Client()
    BASE_URL = 'http://localhost:8000'

    print("=" * 70)
    print("FRESHMAN ENROLLMENT FLOW TEST")
    print("=" * 70)

    # Step 1: Test Landing Page
    print("\n[1] Testing Landing Page...")
    response = client.get('/freshman/')
    assert response.status_code == 200, f"Landing page failed: {response.status_code}"
    assert 'Start Enrollment' in response.content.decode(), "Start Enrollment button not found"
    print("✓ Landing page loads successfully")

    # Step 2: Test Credentials Creation
    print("\n[2] Testing Credentials Creation...")
    credentials_data = {
        'first_name': 'Juan',
        'middle_name': 'Carlos',
        'surname': 'DelaCruz',
        'suffix': 'Jr.',
        'email': 'juan.carlos.delacruz@example.com',
        'mobile': '+63 9123456789',
        'password': 'SecurePassword123!',
        'confirm_password': 'SecurePassword123!',
        'is_freshman': 'on'
    }

    response = client.post('/freshman/create-credentials/', credentials_data, follow=True)
    assert response.status_code == 200, f"Create credentials failed: {response.status_code}"

    # Check if user was created with correct username
    expected_username = 'delacruzjuancarlos'  # surname + firstname + middlename
    try:
        user = User.objects.get(username=expected_username)
        assert user.email == credentials_data['email'], "Email mismatch"
        assert user.first_name == 'Juan', "First name mismatch"
        assert user.last_name == 'DelaCruz', "Last name mismatch"
        print(f"✓ User created with username: {expected_username}")
    except User.DoesNotExist:
        print(f"✗ User not created with expected username: {expected_username}")
        return False

    # Check if student record was created
    try:
        student = Student.objects.get(user=user)
        print(f"  Student status: {student.status}, onboarding_complete: {student.onboarding_complete}")
        assert student.status == 'inactive', f"Student should be inactive but is {student.status}"
        assert not student.onboarding_complete, "Onboarding should not be complete"
        print(f"✓ Student record created (status: inactive)")
    except Student.DoesNotExist:
        print("✗ Student record not created")
        return False

    # Step 3: Test Course Selection
    print("\n[3] Testing Course Selection...")

    # Get a program for testing
    try:
        program = Program.objects.first()
        assert program is not None, "No programs in database"
        print(f"  Selected program: {program.name}")
    except Exception as e:
        print(f"✗ Program selection failed: {e}")
        return False

    # Log in the user and select course
    client.login(username=expected_username, password='SecurePassword123!')

    course_data = {
        'program_id': program.id
    }

    response = client.post('/freshman/select-course/', course_data, follow=True)
    assert response.status_code == 200, f"Course selection failed: {response.status_code}"

    # Verify student was updated with program and curriculum
    student.refresh_from_db()
    assert student.program is not None, "Program not assigned to student"
    assert student.curriculum is not None, "Curriculum not assigned to student"
    print(f"✓ Program assigned: {student.program.name}")
    print(f"✓ Curriculum assigned: {student.curriculum.version}")

    # Step 4: Test Credential Confirmation
    print("\n[4] Testing Credential Confirmation...")

    response = client.post('/freshman/confirm-credentials/', {}, follow=True)
    assert response.status_code == 200, f"Confirmation failed: {response.status_code}"

    # Verify student onboarding is complete
    student.refresh_from_db()
    assert student.onboarding_complete, "Onboarding should be complete"
    assert student.status == 'active', "Student should be active"
    print("✓ Onboarding marked as complete")
    print("✓ Student status changed to active")

    # Step 5: Test Enrollment Complete Page
    print("\n[5] Testing Enrollment Complete Page...")

    response = client.get('/freshman/complete/')
    assert response.status_code == 200, f"Enrollment complete page failed: {response.status_code}"
    assert 'Enrollment Successful' in response.content.decode(), "Success message not found"
    assert expected_username in response.content.decode(), "Username not displayed"
    print("✓ Enrollment complete page loads correctly")

    # Summary
    print("\n" + "=" * 70)
    print("ALL TESTS PASSED!")
    print("=" * 70)
    print(f"\nEnrolled Student Summary:")
    print(f"  Username: {user.username}")
    print(f"  Full Name: {user.first_name} {user.last_name}")
    print(f"  Email: {user.email}")
    print(f"  Program: {student.program.name}")
    print(f"  Curriculum: {student.curriculum.version}")
    print(f"  Status: {student.status}")
    print(f"  Onboarding Complete: {student.onboarding_complete}")
    print("=" * 70)

    return True

if __name__ == '__main__':
    try:
        test_freshman_flow()
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
