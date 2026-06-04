import bleach
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name='sanitize_html')
def sanitize_html(value):
    """
    Sanitizes HTML content using bleach, allowing only a specific set of tags and attributes.
    This is used to prevent XSS attacks while allowing rich text formatting from AI.
    """
    if not value:
        return ""

    # Allowed tags (rich text, tables, code blocks)
    allowed_tags = [
        'p', 'br', 'hr',
        'b', 'i', 'strong', 'em', 'u', 's', 'strike',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'ul', 'ol', 'li',
        'blockquote', 'pre', 'code',
        'a', 'img',
        'table', 'thead', 'tbody', 'tfoot', 'tr', 'th', 'td',
        'div', 'span', # Generic containers
        'sup', 'sub',
    ]

    # Allowed attributes. 'target' is intentionally NOT allowed on <a>: it
    # would enable reverse-tabnabbing (window.opener) on AI-generated links.
    allowed_attributes = {
        '*': ['class', 'title', 'id'], # Global attributes (removed style for safety)
        'a': ['href', 'rel'],
        'img': ['src', 'alt', 'title', 'width', 'height'],
        'code': ['class'], # For syntax highlighting
        'pre': ['class'],
        'th': ['colspan', 'rowspan', 'scope'],
        'td': ['colspan', 'rowspan'],
    }

    # Restrict URL schemes so AI output can't smuggle javascript:/data: URIs
    # into href or img src.
    allowed_protocols = ['http', 'https', 'mailto']

    # Clean the HTML
    cleaned_html = bleach.clean(
        value,
        tags=allowed_tags,
        attributes=allowed_attributes,
        protocols=allowed_protocols,
        strip=True, # Strip disallowed tags instead of escaping them (cleaner output)
        strip_comments=True
    )

    return mark_safe(cleaned_html)
