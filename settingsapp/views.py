from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from users.decorators import role_required
from .models import Setting
from audit.models import AuditTrail


@role_required('registrar', 'admin')
def settings_list(request):
    """
    List all system settings.
    """
    settings = Setting.objects.all().order_by('key_name')

    # Get or create enrollment_open setting if it doesn't exist
    enrollment_open, created = Setting.objects.get_or_create(
        key_name='enrollment_open',
        defaults={
            'value_text': 'false',
            'description': 'Toggle to enable or disable student enrollment',
            'updated_by': request.user,
        }
    )

    context = {
        'settings': settings,
        'enrollment_open': enrollment_open,
    }
    return render(request, 'registrar/settings/settings_list.html', context)


@role_required('registrar', 'admin')
def setting_update(request, pk):
    """
    Update a setting value.
    """
    setting = get_object_or_404(Setting, pk=pk)

    if request.method == 'POST':
        old_value = setting.value_text

        # Update value
        setting.value_text = request.POST.get('value_text', setting.value_text)
        setting.description = request.POST.get('description', setting.description)
        setting.updated_by = request.user
        setting.save()

        # Audit trail
        AuditTrail.objects.create(
            actor=request.user,
            action='update',
            entity='Setting',
            entity_id=setting.id,
            old_value_json={'value_text': old_value, 'key_name': setting.key_name},
            new_value_json={'value_text': setting.value_text, 'key_name': setting.key_name},
        )

        messages.success(request, f'Setting "{setting.key_name}" updated successfully.')
        return redirect('settingsapp:settings_list')

    context = {
        'setting': setting,
    }
    return render(request, 'registrar/settings/setting_form.html', context)


@role_required('registrar', 'admin')
def setting_toggle(request, key):
    """
    Toggle a boolean setting (for AJAX requests).
    """
    if request.method == 'POST':
        setting = get_object_or_404(Setting, key_name=key)
        old_value = setting.value_text

        # Toggle value
        if setting.value_text.lower() == 'true':
            setting.value_text = 'false'
        else:
            setting.value_text = 'true'

        setting.updated_by = request.user
        setting.save()

        # Audit trail
        AuditTrail.objects.create(
            actor=request.user,
            action='toggle',
            entity='Setting',
            entity_id=setting.id,
            old_value_json={'value_text': old_value, 'key_name': key},
            new_value_json={'value_text': setting.value_text, 'key_name': key},
        )

        messages.success(request, f'Enrollment is now {"enabled" if setting.value_text == "true" else "disabled"}.')

        if request.headers.get('HX-Request'):
            return JsonResponse({
                'success': True,
                'value': setting.value_text,
                'message': f'Enrollment is now {"enabled" if setting.value_text == "true" else "disabled"}.'
            })

        return redirect('settingsapp:settings_list')

    return redirect('settingsapp:settings_list')
