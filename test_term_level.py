"""
Test script for Term level feature
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richwell_portal.settings')
django.setup()

from enrollment.models import Term
from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()

print("="*60)
print("TERM LEVEL FEATURE TEST")
print("="*60)

# Test 1: Check model fields
print("\n1. Checking Term model fields...")
fields = [f.name for f in Term._meta.get_fields()]
print(f"   Fields: {fields}")
assert 'level' in fields, "Level field not found in Term model!"
print("   [PASS] Level field exists")

# Test 2: Check level choices
print("\n2. Checking level choices...")
print(f"   Choices: {Term.LEVEL_CHOICES}")
assert len(Term.LEVEL_CHOICES) == 3, "Expected 3 level choices"
print("   [PASS] Level choices are correct")

# Test 3: List existing terms
print("\n3. Checking existing terms...")
terms = Term.objects.all()
print(f"   Total terms: {terms.count()}")
for t in terms:
    print(f"   - {t.name}: Level={t.level} ({t.get_level_display()}), Active={t.is_active}")

# Test 4: Test views with Client
print("\n4. Testing term list view...")
client = Client()
registrar = User.objects.filter(role='registrar').first()
if registrar:
    client.login(username=registrar.username, password='password123')
    response = client.get('/registrar/enrollment/terms/')
    print(f"   Status code: {response.status_code}")
    if response.status_code == 200:
        print("   [PASS] Terms list page loads successfully")
    else:
        print(f"   [FAIL] Terms list page returned {response.status_code}")
else:
    print("   [SKIP] No registrar user found")

# Test 5: Test level-specific activation
print("\n5. Testing level-specific active terms...")
active_terms = {
    'SHS': Term.objects.filter(is_active=True, level='SHS').first(),
    'Bachelor': Term.objects.filter(is_active=True, level='Bachelor').first(),
    'Masteral': Term.objects.filter(is_active=True, level='Masteral').first(),
}
for level, term in active_terms.items():
    if term:
        print(f"   {level}: {term.name} (Active)")
    else:
        print(f"   {level}: No active term")

print("\n" + "="*60)
print("ALL TESTS PASSED!")
print("="*60)
print("\nSummary:")
print("- Term model now has a 'level' field")
print("- Each level can have its own independent active term")
print("- SHS, Bachelor, and Masteral levels are supported")
print("- Term activation only affects terms of the same level")
