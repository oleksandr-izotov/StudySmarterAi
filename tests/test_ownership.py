"""Cross-user authorization tests — a user must never reach another user's
prompts/sections (the ownership checks in prompts/history views)."""
import pytest
from django.urls import reverse

from apps.prompts.models import Prompt
from tests.factories import UserFactory, PromptFactory, SectionFactory


def make_user():
    """UserFactory uses skip_postgeneration_save, so the set_password hash is
    never persisted — that makes the session auth-hash mismatch on the next
    request and silently logs the client out. Persist a real password so
    force_login sticks."""
    u = UserFactory()
    u.set_password('testpass123')
    u.save()
    return u


@pytest.mark.django_db
class TestCrossUserOwnership:
    def test_cannot_view_others_prompt(self, client):
        owner, other = make_user(), make_user()
        prompt = PromptFactory(user=owner)
        client.force_login(other)
        resp = client.get(reverse('prompt_detail', args=[prompt.id]))
        assert resp.status_code == 403

    def test_owner_can_view_own_prompt(self, client):
        owner = make_user()
        prompt = PromptFactory(user=owner)
        client.force_login(owner)
        resp = client.get(reverse('prompt_detail', args=[prompt.id]))
        assert resp.status_code == 200

    def test_cannot_delete_others_prompt(self, client):
        owner, other = make_user(), make_user()
        prompt = PromptFactory(user=owner)
        client.force_login(other)
        resp = client.delete(reverse('history:delete', args=[prompt.id]))
        assert resp.status_code == 403
        assert Prompt.objects.filter(id=prompt.id).exists()

    def test_cannot_rerun_others_prompt(self, client):
        owner, other = make_user(), make_user()
        prompt = PromptFactory(user=owner)
        client.force_login(other)
        resp = client.post(reverse('history:rerun', args=[prompt.id]))
        assert resp.status_code == 403

    def test_cannot_regenerate_others_section(self, client):
        owner, other = make_user(), make_user()
        prompt = PromptFactory(user=owner)
        SectionFactory(prompt=prompt, type='explanation')
        client.force_login(other)
        resp = client.post(reverse('section_regenerate', args=[prompt.id, 'explanation']))
        assert resp.status_code == 403

    def test_history_list_shows_only_own_prompts(self, client):
        owner, other = make_user(), make_user()
        PromptFactory(user=owner, text='OWNER_ONLY_SECRET')
        PromptFactory(user=other, text='OTHER_USER_SECRET')
        client.force_login(owner)
        resp = client.get(reverse('history:list'))
        body = resp.content.decode()
        assert 'OWNER_ONLY_SECRET' in body
        assert 'OTHER_USER_SECRET' not in body
