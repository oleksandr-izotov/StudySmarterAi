from django.http import HttpRequest
from typing import Any, Dict

def ensure_session(request: HttpRequest) -> None:
    if not request.session.session_key:
        request.session.create()


def get_owner_filter(request: HttpRequest) -> Dict[str, Any]:
    if request.user.is_authenticated:
        return {'user': request.user}
    ensure_session(request)
    return {'session_key': request.session.session_key}


def check_ownership(request: HttpRequest, obj: Any) -> bool:
    if request.user.is_authenticated:
        return obj.user == request.user
    return obj.session_key == request.session.session_key


def get_user_settings(request: HttpRequest) -> Dict[str, str]:
    defaults = {'language': 'ru', 'tone': 'friendly', 'depth': 'detailed'}
    if request.user.is_authenticated:
        try:
            profile = request.user.profile
            return {
                'language': profile.language,
                'tone': profile.tone,
                'depth': profile.depth,
            }
        except Exception:
            pass
    return {k: request.session.get(k, v) for k, v in defaults.items()}
