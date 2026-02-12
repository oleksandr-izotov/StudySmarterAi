from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden, HttpRequest
from django.urls import reverse
from django.template.loader import render_to_string
from .models import Prompt
from . import services
from apps.core.utils import ensure_session, get_owner_filter, check_ownership, get_user_settings
from apps.subscriptions.decorators import check_rate_limit
from apps.subscriptions.services import UsageService



@check_rate_limit
def prompt_create_view(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        text = request.POST.get('text')
        
        saved = get_user_settings(request)
        language = request.POST.get('language') or saved['language']
        tone = request.POST.get('tone') or saved['tone']
        depth = request.POST.get('depth') or saved['depth']

        settings = {
            'language': language,
            'tone': tone,
            'depth': depth,
        }
        
        ensure_session(request)
            
        prompt = services.create_prompt(
            user=request.user,
            session_key=request.session.session_key,
            text=text,
            settings=settings
        )
        
        # Async generation
        services.generate_sections_task.delay(prompt.id)
        
        UsageService.record_usage(
            request.user,
            request.session.session_key,
            prompt
        )
        
        # Return polling UI
        detail_url = reverse('prompt_detail', args=[prompt.id])
        
        # Render standardized skeleton loader
        skeleton_html = render_to_string('partials/skeleton.html', request=request)
        
        polling_html = f'''
        <div hx-get="{detail_url}" 
             hx-trigger="load delay:2s, every 2s" 
             hx-swap="outerHTML">
             {skeleton_html}
        </div>
        '''
        
        prompts = Prompt.objects.filter(**get_owner_filter(request)).order_by('-created_at')
        if not request.user.is_authenticated:
            prompts = prompts[:10]

        history_html = render_to_string('partials/history_list.html', {'prompts': prompts}, request=request)
        
        history_oob = f'<div id="history-list" hx-swap-oob="innerHTML">{history_html}</div>'

        response = HttpResponse(polling_html + history_oob)
        response['HX-Trigger'] = 'usage-updated'
        return response
        
    return HttpResponse(status=405)


def get_latest_sections(prompt):
    """Helper to get only the latest version of each section type."""
    all_sections = prompt.sections.order_by('version')
    latest_sections = {}
    for section in all_sections:
        latest_sections[section.type] = section
    
    # Return as a list sorted by type order
    order = ['explanation', 'summary', 'plan', 'quiz']
    result = []
    for type_name in order:
        if type_name in latest_sections:
            result.append(latest_sections[type_name])
            
    return result

def prompt_detail_view(request, id):
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Prompt detail requested for ID: {id}, User: {request.user}, Session: {request.session.session_key}")

    # Verify ownership (basic check)
    prompt = get_object_or_404(Prompt, id=id)
    
    if not check_ownership(request, prompt):
        logger.warning(f"Access denied for prompt {id}")
        return HttpResponseForbidden()

    sections = get_latest_sections(prompt)
    logger.info(f"Found {len(sections)} sections for prompt {id}")
    
    return render(request, 'partials/result.html', {
        'prompt': prompt,
        'sections': sections
    })

def section_detail_view(request, id, type):
    return HttpResponse(f"Section {type} for Prompt {id}")

def section_regenerate_view(request, id, type):
    prompt = get_object_or_404(Prompt, id=id)
    
    if not check_ownership(request, prompt):
        return HttpResponseForbidden()
    
    from decimal import Decimal
    from apps.subscriptions.services import UsageService
    
    session_key = request.session.session_key
    regeneration_cost = Decimal('0.5')
    
    if not UsageService.can_make_request(request.user, session_key, cost=regeneration_cost):
        if request.headers.get('HX-Request'):
            from django.template.loader import render_to_string
            from apps.subscriptions.services import SubscriptionService
            plan = SubscriptionService.get_user_plan(request.user, session_key)
            html = render_to_string('partials/rate_limit_exceeded.html', {
                'is_guest': not request.user.is_authenticated,
                'plan': plan,
                'stats': UsageService.get_usage_stats(request.user, session_key),
            }, request=request)
            return HttpResponse(html, status=429)
        return HttpResponse("Rate limit exceeded", status=429)
            
    mode = request.GET.get('mode')
    
    last_section = prompt.sections.filter(type=type).order_by('-version').first()
    
    if not last_section:
        return HttpResponse("Section not found", status=404)

    try:
        new_section = services.regenerate_section(last_section.id, request.user, mode)
        
        UsageService.record_regeneration(request.user, session_key, prompt)
        
        response = render(request, 'partials/section.html', {
            'section': new_section,
            'prompt': prompt
        })
        response['HX-Trigger'] = 'usage-updated'
        return response
    except Exception as e:
        print(f"Error regenerating: {e}")
        return HttpResponse(f"Error regenerating: {e}", status=500)
