from django import template

register = template.Library()

@register.simple_tag
def check_match(current_value, expected_value):
    """
    Returns 'checked' if current_value equals expected_value, otherwise empty string.
    Usage: {% check_match settings.language 'ru' %}
    """
    if str(current_value) == str(expected_value):
        return 'checked'
    return ''
