"""
Tests for prompts and sections functionality.
Covers: prompt creation, section creation, regeneration.
"""
import pytest
from django.urls import reverse
from django.contrib.auth.models import User

from apps.prompts.models import Prompt, Section
from tests.factories import PromptFactory, SectionFactory, UserFactory, UserProfileFactory


# =============================================================================
# Prompt Model Tests
# =============================================================================

@pytest.mark.django_db
class TestPromptModel:
    
    def test_prompt_creation_authenticated(self, user):
        """Test prompt is created with correct user association."""
        prompt = PromptFactory(user=user)
        
        assert prompt.user == user
        assert prompt.session_key is None
        assert prompt.status == 'done'
        assert len(prompt.text) > 0
    
    def test_prompt_creation_guest(self, db, guest_session_key):
        """Test prompt is created with session key for guests."""
        prompt = PromptFactory(user=None, session_key=guest_session_key)
        
        assert prompt.user is None
        assert prompt.session_key == guest_session_key
    
    def test_prompt_settings_applied(self, user):
        """Test prompt stores specified settings."""
        prompt = PromptFactory(
            user=user,
            language='en',
            tone='strict',
            depth='short',
            format='paragraphs',
            goal='exam'
        )
        
        assert prompt.language == 'en'
        assert prompt.tone == 'strict'
        assert prompt.depth == 'short'
        assert prompt.format == 'paragraphs'
        assert prompt.goal == 'exam'
    
    def test_prompt_status_choices(self, user):
        """Test prompt can have different statuses."""
        pending = PromptFactory(user=user, status='pending')
        done = PromptFactory(user=user, status='done')
        failed = PromptFactory(user=user, status='failed')
        
        assert pending.status == 'pending'
        assert done.status == 'done'
        assert failed.status == 'failed'
    
    def test_prompt_str_representation(self, user):
        """Test prompt string representation."""
        prompt = PromptFactory(user=user)
        assert str(prompt.id) in str(prompt)
        assert prompt.status in str(prompt)


# =============================================================================
# Section Model Tests
# =============================================================================

@pytest.mark.django_db
class TestSectionModel:
    
    def test_section_creation(self, prompt):
        """Test section is created with correct associations."""
        section = SectionFactory(prompt=prompt, type='explanation')
        
        assert section.prompt == prompt
        assert section.type == 'explanation'
        assert section.status == 'done'
        assert section.version == 1
    
    def test_all_section_types(self, prompt):
        """Test all section types can be created."""
        types = ['explanation', 'summary', 'plan', 'quiz']
        
        for section_type in types:
            section = SectionFactory(prompt=prompt, type=section_type)
            assert section.type == section_type
    
    def test_section_versioning(self, prompt):
        """Test sections can have multiple versions."""
        v1 = SectionFactory(prompt=prompt, type='explanation', version=1)
        v2 = SectionFactory(prompt=prompt, type='explanation', version=2)
        
        assert v1.version == 1
        assert v2.version == 2
        
        # Both should belong to same prompt
        sections = Section.objects.filter(prompt=prompt, type='explanation')
        assert sections.count() == 2
    
    def test_section_unique_together(self, prompt):
        """Test unique_together constraint on prompt, type, version."""
        SectionFactory(prompt=prompt, type='summary', version=1)
        
        # Creating same combination should raise error
        with pytest.raises(Exception):
            Section.objects.create(
                prompt=prompt,
                type='summary',
                version=1,
                content='duplicate'
            )


# =============================================================================
# Prompt with Sections Tests
# =============================================================================

@pytest.mark.django_db
class TestPromptWithSections:
    
    def test_prompt_sections_relationship(self, prompt_with_sections):
        """Test prompt has related sections."""
        prompt, sections = prompt_with_sections
        
        assert prompt.sections.count() == 4
        
        section_types = set(s.type for s in prompt.sections.all())
        assert section_types == {'explanation', 'summary', 'plan', 'quiz'}
    
    def test_prompt_delete_cascades_sections(self, prompt_with_sections):
        """Test deleting prompt deletes all sections."""
        prompt, sections = prompt_with_sections
        prompt_id = prompt.id
        
        # Get section ids before delete
        section_ids = [s.id for s in sections]
        
        prompt.delete()
        
        # Sections should be deleted too
        assert not Section.objects.filter(id__in=section_ids).exists()


# =============================================================================
# Prompt Query Tests
# =============================================================================

@pytest.mark.django_db
class TestPromptQueries:
    
    def test_filter_prompts_by_user(self, db):
        """Test filtering prompts by user."""
        user1 = UserFactory()
        user2 = UserFactory()
        
        UserProfileFactory(user=user1)
        UserProfileFactory(user=user2)
        
        PromptFactory.create_batch(3, user=user1)
        PromptFactory.create_batch(2, user=user2)
        
        assert Prompt.objects.filter(user=user1).count() == 3
        assert Prompt.objects.filter(user=user2).count() == 2
    
    def test_filter_prompts_by_session(self, db, guest_session_key):
        """Test filtering prompts by session key."""
        PromptFactory.create_batch(2, user=None, session_key=guest_session_key)
        PromptFactory.create_batch(1, user=None, session_key='other_session')
        
        assert Prompt.objects.filter(session_key=guest_session_key).count() == 2
    
    def test_prompts_ordered_by_created_at(self, user):
        """Test prompts are ordered by creation date."""
        PromptFactory.create_batch(3, user=user)
        
        prompts = list(Prompt.objects.filter(user=user).order_by('-created_at'))
        
        # Each prompt should be newer than the next
        for i in range(len(prompts) - 1):
            assert prompts[i].created_at >= prompts[i + 1].created_at
