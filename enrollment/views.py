from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from users.decorators import role_required
from .models import Term, Section, Student, StudentSubject
from users.models import User
from audit.models import AuditTrail
import json


@role_required('registrar')
def terms_list(request):
    """
    List all terms with active terms highlighted per level.
    """
    terms = Term.objects.all().order_by('level', '-start_date')

    # Get active terms for each level
    active_terms = {
        'SHS': Term.objects.filter(is_active=True, level='SHS').first(),
        'Bachelor': Term.objects.filter(is_active=True, level='Bachelor').first(),
        'Masteral': Term.objects.filter(is_active=True, level='Masteral').first(),
    }

    context = {
        'terms': terms,
        'active_terms': active_terms,
        'level_choices': Term.LEVEL_CHOICES,
    }
    return render(request, 'registrar/terms/terms_list.html', context)


@role_required('registrar')
def term_create(request):
    """
    Create a new term.
    """
    if request.method == 'POST':
        name = request.POST.get('name')
        level = request.POST.get('level', 'Bachelor')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        add_drop_deadline = request.POST.get('add_drop_deadline')
        grade_encoding_deadline = request.POST.get('grade_encoding_deadline')

        # Validation
        if not all([name, level, start_date, end_date]):
            messages.error(request, 'Name, Level, Start Date, and End Date are required.')
            return redirect('enrollment:terms_list')

        try:
            # Create term
            term = Term.objects.create(
                name=name,
                level=level,
                start_date=start_date,
                end_date=end_date,
                add_drop_deadline=add_drop_deadline or None,
                grade_encoding_deadline=grade_encoding_deadline or None,
                is_active=False,
            )

            # Audit trail
            AuditTrail.objects.create(
                actor=request.user,
                action='create',
                entity='Term',
                entity_id=term.id,
                new_value_json={
                    'name': term.name,
                    'level': term.level,
                    'start_date': str(term.start_date),
                    'end_date': str(term.end_date),
                    'add_drop_deadline': str(term.add_drop_deadline) if term.add_drop_deadline else None,
                    'grade_encoding_deadline': str(term.grade_encoding_deadline) if term.grade_encoding_deadline else None,
                }
            )

            messages.success(request, f'Term "{term.name}" for {term.get_level_display()} created successfully.')
            return redirect('enrollment:terms_list')

        except Exception as e:
            messages.error(request, f'Error creating term: {str(e)}')
            return redirect('enrollment:terms_list')

    context = {
        'level_choices': Term.LEVEL_CHOICES,
    }
    return render(request, 'registrar/terms/term_form.html', context)


@role_required('registrar')
def term_update(request, pk):
    """
    Update an existing term.
    """
    term = get_object_or_404(Term, pk=pk)

    if request.method == 'POST':
        old_values = {
            'name': term.name,
            'level': term.level,
            'start_date': str(term.start_date),
            'end_date': str(term.end_date),
            'add_drop_deadline': str(term.add_drop_deadline) if term.add_drop_deadline else None,
            'grade_encoding_deadline': str(term.grade_encoding_deadline) if term.grade_encoding_deadline else None,
        }

        # Update fields
        term.name = request.POST.get('name', term.name)
        term.level = request.POST.get('level', term.level)
        term.start_date = request.POST.get('start_date', term.start_date)
        term.end_date = request.POST.get('end_date', term.end_date)
        term.add_drop_deadline = request.POST.get('add_drop_deadline') or None
        term.grade_encoding_deadline = request.POST.get('grade_encoding_deadline') or None
        term.save()

        new_values = {
            'name': term.name,
            'level': term.level,
            'start_date': str(term.start_date),
            'end_date': str(term.end_date),
            'add_drop_deadline': str(term.add_drop_deadline) if term.add_drop_deadline else None,
            'grade_encoding_deadline': str(term.grade_encoding_deadline) if term.grade_encoding_deadline else None,
        }

        # Audit trail
        AuditTrail.objects.create(
            actor=request.user,
            action='update',
            entity='Term',
            entity_id=term.id,
            old_value_json=old_values,
            new_value_json=new_values,
        )

        messages.success(request, f'Term "{term.name}" updated successfully.')
        return redirect('enrollment:terms_list')

    context = {
        'term': term,
        'level_choices': Term.LEVEL_CHOICES,
    }
    return render(request, 'registrar/terms/term_form.html', context)


@role_required('registrar')
def term_activate(request, pk):
    """
    Activate a term. Only one term per level can be active at a time.
    """
    term = get_object_or_404(Term, pk=pk)

    if request.method == 'POST':
        with transaction.atomic():
            # Get currently active term for this level
            old_active_term = Term.objects.filter(is_active=True, level=term.level).first()

            # Deactivate all terms for this level only
            Term.objects.filter(level=term.level).update(is_active=False)

            # Activate selected term
            term.is_active = True
            term.save()

            # Audit trail for deactivation
            if old_active_term and old_active_term.id != term.id:
                AuditTrail.objects.create(
                    actor=request.user,
                    action='deactivate',
                    entity='Term',
                    entity_id=old_active_term.id,
                    old_value_json={'is_active': True, 'level': old_active_term.level},
                    new_value_json={'is_active': False, 'level': old_active_term.level},
                )

            # Audit trail for activation
            AuditTrail.objects.create(
                actor=request.user,
                action='activate',
                entity='Term',
                entity_id=term.id,
                old_value_json={'is_active': False},
                new_value_json={'is_active': True},
            )

        messages.success(request, f'Term "{term.name}" is now active.')
        return redirect('enrollment:terms_list')

    context = {
        'term': term,
    }
    return render(request, 'registrar/terms/term_activate_confirm.html', context)


@role_required('registrar')
def term_close(request, pk):
    """
    Close a term. Sets is_active to False and can trigger archiving.
    """
    term = get_object_or_404(Term, pk=pk)

    if request.method == 'POST':
        old_status = term.is_active

        # Close term
        term.is_active = False
        term.save()

        # Audit trail
        AuditTrail.objects.create(
            actor=request.user,
            action='close',
            entity='Term',
            entity_id=term.id,
            old_value_json={'is_active': old_status},
            new_value_json={'is_active': False},
        )

        messages.success(request, f'Term "{term.name}" has been closed.')
        return redirect('enrollment:terms_list')

    context = {
        'term': term,
    }
    return render(request, 'registrar/terms/term_close_confirm.html', context)


@role_required('registrar')
def term_delete(request, pk):
    """
    Delete a term (only if no sections are associated).
    """
    term = get_object_or_404(Term, pk=pk)

    if request.method == 'POST':
        # Check if term has sections
        if Section.objects.filter(term=term).exists():
            messages.error(request, f'Cannot delete term "{term.name}" because it has associated sections.')
            return redirect('enrollment:terms_list')

        # Store term info for audit
        term_name = term.name
        term_id = term.id

        # Audit trail
        AuditTrail.objects.create(
            actor=request.user,
            action='delete',
            entity='Term',
            entity_id=term_id,
            old_value_json={
                'name': term.name,
                'start_date': str(term.start_date),
                'end_date': str(term.end_date),
            },
        )

        # Delete term
        term.delete()

        messages.success(request, f'Term "{term_name}" deleted successfully.')
        return redirect('enrollment:terms_list')

    context = {
        'term': term,
    }
    return render(request, 'registrar/terms/term_delete_confirm.html', context)


# ==================== SECTION MANAGEMENT ====================

@role_required('registrar')
def sections_list(request):
    """
    List all sections with filtering by term and optimized queries for multi-select fields.
    """
    from academics.models import Subject

    # Get active term or allow selection
    active_term = Term.objects.filter(is_active=True).first()
    selected_term_id = request.GET.get('term', active_term.id if active_term else None)

    terms = Term.objects.all().order_by('-start_date')
    sections = Section.objects.all().prefetch_related('subjects', 'professors').select_related('term')

    if selected_term_id:
        sections = sections.filter(term_id=selected_term_id)

    sections = sections.order_by('-created_at')

    context = {
        'sections': sections,
        'terms': terms,
        'selected_term_id': int(selected_term_id) if selected_term_id else None,
        'active_term': active_term,
    }
    return render(request, 'registrar/sections/sections_list.html', context)


@role_required('registrar')
def section_create(request):
    """
    Create a new section with multiple subjects and professors.
    """
    from academics.models import Subject

    if request.method == 'POST':
        subject_ids = request.POST.getlist('subjects[]')
        term_id = request.POST.get('term_id')
        section_code = request.POST.get('section_code')
        capacity = request.POST.get('capacity', 40)
        professor_ids = request.POST.getlist('professors[]')

        # Validation
        if not all([subject_ids, term_id, section_code]):
            messages.error(request, 'Subjects, Term, and Section Code are required.')
            return redirect('enrollment:sections_list')

        try:
            term = Term.objects.get(pk=term_id)

            # Check for duplicate section code in term
            if Section.objects.filter(term=term, section_code=section_code).exists():
                messages.error(request, f'Section {section_code} already exists for {term.name}.')
                return redirect('enrollment:sections_list')

            # Create section
            section = Section.objects.create(
                term=term,
                section_code=section_code,
                capacity=capacity,
                status='open',
            )

            # Add subjects to section
            subjects = Subject.objects.filter(id__in=subject_ids)
            section.subjects.set(subjects)

            # Add professors to section
            if professor_ids:
                professors = User.objects.filter(id__in=professor_ids, role='professor')
                section.professors.set(professors)

            # Audit trail
            subject_codes = ', '.join([s.code for s in subjects])
            professor_names = ', '.join([p.get_full_name() or p.username for p in section.professors.all()])

            AuditTrail.objects.create(
                actor=request.user,
                action='create',
                entity='Section',
                entity_id=section.id,
                new_value_json={
                    'subjects': subject_codes,
                    'term': term.name,
                    'section_code': section_code,
                    'capacity': capacity,
                    'professors': professor_names or 'None',
                }
            )

            messages.success(request, f'Section {section_code} created successfully with {len(subjects)} subject(s).')
            return redirect('enrollment:sections_list')

        except Exception as e:
            messages.error(request, f'Error creating section: {str(e)}')
            return redirect('enrollment:sections_list')

    # GET request - show form
    terms = Term.objects.all().order_by('-start_date')
    active_term = Term.objects.filter(is_active=True).first()

    context = {
        'terms': terms,
        'active_term': active_term,
    }
    return render(request, 'registrar/sections/section_form.html', context)


@role_required('registrar')
def section_update(request, pk):
    """
    Update an existing section with multiple subjects and professors.
    """
    section = get_object_or_404(Section, pk=pk)

    if request.method == 'POST':
        old_subjects = ', '.join([s.code for s in section.subjects.all()])
        old_professors = ', '.join([p.get_full_name() or p.username for p in section.professors.all()])

        old_values = {
            'section_code': section.section_code,
            'capacity': section.capacity,
            'subjects': old_subjects,
            'professors': old_professors or 'None',
            'status': section.status,
        }

        # Update fields
        section.section_code = request.POST.get('section_code', section.section_code)
        section.capacity = request.POST.get('capacity', section.capacity)

        # Update subjects
        subject_ids = request.POST.getlist('subjects[]')
        if subject_ids:
            subjects = section.subjects.model.objects.filter(id__in=subject_ids)
            section.subjects.set(subjects)

        # Update professors
        professor_ids = request.POST.getlist('professors[]')
        section.professors.clear()
        if professor_ids:
            professors = User.objects.filter(id__in=professor_ids, role='professor')
            section.professors.set(professors)

        section.save()

        new_subjects = ', '.join([s.code for s in section.subjects.all()])
        new_professors = ', '.join([p.get_full_name() or p.username for p in section.professors.all()])

        new_values = {
            'section_code': section.section_code,
            'capacity': section.capacity,
            'subjects': new_subjects,
            'professors': new_professors or 'None',
            'status': section.status,
        }

        # Audit trail
        AuditTrail.objects.create(
            actor=request.user,
            action='update',
            entity='Section',
            entity_id=section.id,
            old_value_json=old_values,
            new_value_json=new_values,
        )

        messages.success(request, f'Section {section.section_code} updated successfully.')
        return redirect('enrollment:sections_list')

    # Get terms for the form
    terms = Term.objects.all().order_by('-start_date')

    context = {
        'section': section,
        'terms': terms,
    }
    return render(request, 'registrar/sections/section_form.html', context)


@role_required('registrar')
def section_delete(request, pk):
    """
    Delete a section (only if no students enrolled).
    """
    section = get_object_or_404(Section, pk=pk)

    if request.method == 'POST':
        # Check if section has enrolled students
        if StudentSubject.objects.filter(section=section).exists():
            messages.error(request, f'Cannot delete section {section.section_code} because students are enrolled.')
            return redirect('enrollment:sections_list')

        # Store section info for audit
        section_code = section.section_code
        section_id = section.id

        # Audit trail
        AuditTrail.objects.create(
            actor=request.user,
            action='delete',
            entity='Section',
            entity_id=section_id,
            old_value_json={
                'section_code': section.section_code,
                'subject': section.subject.code,
                'term': section.term.name,
            },
        )

        # Delete section
        section.delete()

        messages.success(request, f'Section {section_code} deleted successfully.')
        return redirect('enrollment:sections_list')

    context = {
        'section': section,
    }
    return render(request, 'registrar/sections/section_delete_confirm.html', context)


@role_required('registrar')
def section_change_status(request, pk):
    """
    Change section status (open, full, closed).
    """
    section = get_object_or_404(Section, pk=pk)

    if request.method == 'POST':
        new_status = request.POST.get('status')

        if new_status not in ['open', 'full', 'closed']:
            messages.error(request, 'Invalid status.')
            return redirect('enrollment:sections_list')

        old_status = section.status
        section.status = new_status
        section.save()

        # Audit trail
        AuditTrail.objects.create(
            actor=request.user,
            action='change_status',
            entity='Section',
            entity_id=section.id,
            old_value_json={'status': old_status},
            new_value_json={'status': new_status},
        )

        messages.success(request, f'Section {section.section_code} status changed to {new_status}.')
        return redirect('enrollment:sections_list')

    return redirect('enrollment:sections_list')


@role_required('registrar')
def sections_bulk_create(request):
    """
    Bulk create sections for a subject.
    """
    from academics.models import Subject

    if request.method == 'POST':
        subject_id = request.POST.get('subject_id')
        term_id = request.POST.get('term_id')
        num_sections = int(request.POST.get('num_sections', 1))
        capacity = int(request.POST.get('capacity', 40))
        professor_id = request.POST.get('professor_id')

        if not all([subject_id, term_id, num_sections]):
            messages.error(request, 'Subject, Term, and Number of Sections are required.')
            return redirect('enrollment:sections_list')

        try:
            subject = Subject.objects.get(pk=subject_id)
            term = Term.objects.get(pk=term_id)
            professor = User.objects.get(pk=professor_id, role='professor') if professor_id else None

            # Generate section codes (A, B, C, ...)
            import string
            letters = string.ascii_uppercase
            created_count = 0

            for i in range(num_sections):
                if i < len(letters):
                    section_code = f"{subject.code}-{letters[i]}"

                    # Check if exists
                    if Section.objects.filter(subject=subject, term=term, section_code=section_code).exists():
                        continue

                    # Create section
                    section = Section.objects.create(
                        subject=subject,
                        term=term,
                        section_code=section_code,
                        capacity=capacity,
                        professor=professor if professor else User.objects.filter(role='professor').first(),
                        status='open',
                    )

                    # Audit trail
                    AuditTrail.objects.create(
                        actor=request.user,
                        action='bulk_create',
                        entity='Section',
                        entity_id=section.id,
                        new_value_json={
                            'section_code': section_code,
                            'subject': subject.code,
                            'term': term.name,
                        }
                    )

                    created_count += 1

            messages.success(request, f'Created {created_count} sections for {subject.code}.')
            return redirect('enrollment:sections_list')

        except Exception as e:
            messages.error(request, f'Error creating sections: {str(e)}')
            return redirect('enrollment:sections_list')

    terms = Term.objects.all().order_by('-start_date')
    active_term = Term.objects.filter(is_active=True).first()

    context = {
        'terms': terms,
        'active_term': active_term,
    }
    return render(request, 'registrar/sections/bulk_create_form.html', context)


@role_required('registrar')
def professor_search(request):
    """
    AJAX endpoint for professor search.
    """
    query = request.GET.get('q', '').strip()

    if len(query) < 2:
        return JsonResponse({'results': []})

    # Search professors by name or username
    professors = User.objects.filter(
        role='professor'
    ).filter(
        models.Q(first_name__icontains=query) |
        models.Q(last_name__icontains=query) |
        models.Q(username__icontains=query)
    )[:10]

    results = [
        {
            'id': prof.id,
            'name': prof.get_full_name() or prof.username,
            'username': prof.username,
            'email': prof.email,
        }
        for prof in professors
    ]

    return JsonResponse({'results': results})


# ==================== ADMISSIONS (PLACEHOLDER) ====================

@role_required('registrar')
def admissions_list(request):
    """
    Placeholder for admissions management.
    """
    return render(request, 'registrar/admissions/admissions_list.html')
