import pytest
from django.template import Context, Template
from apps.core.templatetags.core_extras import sanitize_html

class TestSanitizeHtml:
    def test_basic_text_preservation(self):
        """Test that plain text is preserved."""
        text = "Hello, world!"
        assert sanitize_html(text) == text

    def test_allowed_tags_preservation(self):
        """Test that allowed tags are preserved."""
        html = "<p>Paragraph</p><b>Bold</b><ul><li>Item</li></ul>"
        assert sanitize_html(html) == html

    def test_script_tag_removal(self):
        """Test that script tags are removed (content remains as harmless text)."""
        html = "<script>alert('XSS')</script>"
        # Bleach strip=True removes tags but keeps content. This is safe (no execution).
        assert sanitize_html(html) == "alert('XSS')"
        
        html = "Safe<script>alert('XSS')</script>Text"
        assert sanitize_html(html) == "Safealert('XSS')Text"

    def test_event_handler_removal(self):
        """Test that event handlers are removed from attributes."""
        html = '<a href="#" onclick="alert(\'XSS\')">Link</a>'
        sanitized = sanitize_html(html)
        assert 'onclick' not in sanitized
        assert 'href' in sanitized
        assert 'Link' in sanitized

    def test_iframe_removal(self):
        """Test that iframes are removed."""
        html = '<iframe src="javascript:alert(1)"></iframe>'
        assert sanitize_html(html) == ""

    def test_style_attribute_removal(self):
        """Test that style attributes are removed (we decided to not allow inline styles)."""
        html = '<div style="color: red">Red Text</div>'
        sanitized = sanitize_html(html)
        assert 'style' not in sanitized
        assert 'Red Text' in sanitized

    def test_class_attribute_preservation(self):
        """Test that class attributes are preserved (important for Tailwind)."""
        html = '<div class="text-red-500 p-4">Content</div>'
        sanitized = sanitize_html(html)
        assert 'class="text-red-500 p-4"' in sanitized

    def test_javascript_href_scheme_removed(self):
        """javascript: URLs must be stripped from links (protocol allowlist)."""
        html = '<a href="javascript:alert(1)">Click</a>'
        sanitized = sanitize_html(html)
        assert 'javascript:' not in sanitized
        assert 'Click' in sanitized

    def test_data_uri_image_removed(self):
        """data: URIs must be stripped from img src (protocol allowlist)."""
        html = '<img src="data:text/html;base64,PHNjcmlwdD4=" alt="x">'
        sanitized = sanitize_html(html)
        assert 'data:' not in sanitized

    def test_link_target_blank_removed(self):
        """target is not allowed on <a> (reverse-tabnabbing protection)."""
        html = '<a href="https://example.com" target="_blank">Ext</a>'
        sanitized = sanitize_html(html)
        assert 'target' not in sanitized
        assert 'href="https://example.com"' in sanitized

    def test_safe_link_scheme_preserved(self):
        """http/https/mailto links survive."""
        for href in ['https://example.com', 'http://example.com', 'mailto:a@b.com']:
            sanitized = sanitize_html(f'<a href="{href}">x</a>')
            assert href in sanitized

    def test_complex_nesting(self):
        """Test complex nested structures."""
        html = '''
        <div class="prose">
            <h1>Title</h1>
            <p>Text with <b>bold</b> and <a href="https://example.com">link</a>.</p>
            <script>bad()</script>
        </div>
        '''
        sanitized = sanitize_html(html)
        assert '<h1>Title</h1>' in sanitized
        assert '<b>bold</b>' in sanitized
        assert '<a href="https://example.com">' in sanitized
        assert '<script>' not in sanitized
