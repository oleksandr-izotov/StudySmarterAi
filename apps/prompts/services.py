from django.db import transaction
from .models import Prompt, Section
from django.conf import settings
import logging
import json
import time
from abc import ABC, abstractmethod
import google.generativeai as genai
from openai import OpenAI

logger = logging.getLogger(__name__)

class AIProvider(ABC):
    @abstractmethod
    def generate_content(self, system_instruction):
        pass

class GeminiProvider(AIProvider):
    def generate_content(self, system_instruction):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-flash-latest')
        try:
            response = model.generate_content(system_instruction)
            logger.info("Successfully generated content using GeminiProvider")
            return response.text
        except Exception as e:
            logger.error(f"Gemini Error: {e}")
            raise

class QwenProvider(AIProvider):
    def __init__(self):
        self.client = OpenAI(
            api_key=settings.QWEN_API_KEY,
            base_url=settings.QWEN_BASE_URL
        )

    def generate_content(self, system_instruction):
        try:
            response = self.client.chat.completions.create(
                model="qwen-turbo", # Switched to qwen-turbo to verify permissions.
                messages=[
                    {'role': 'system', 'content': 'You are a helpful study assistant.'},
                    {'role': 'user', 'content': system_instruction}
                ]
            )
            logger.info("Successfully generated content using QwenProvider")
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Qwen Error: {e}")
            raise

class AIService:
    def __init__(self):
        self.providers = []
        if settings.QWEN_API_KEY:
            self.providers.append(QwenProvider())
        if settings.GEMINI_API_KEY:
            self.providers.append(GeminiProvider())
            
        if not self.providers:
            logger.warning("No AI providers configured!")

    def generate(self, system_instruction):
        errors = []
        for provider in self.providers:
            try:
                return provider.generate_content(system_instruction)
            except Exception as e:
                errors.append(f"{provider.__class__.__name__}: {str(e)}")
                continue
        
        raise Exception(f"All providers failed: {'; '.join(errors)}")

def create_prompt(user, session_key, text, settings):
    """
    Creates a new Prompt instance.
    """
    prompt = Prompt.objects.create(
        user=user if user.is_authenticated else None,
        session_key=session_key if not user.is_authenticated else None,
        text=text,
        language=settings.get('language', 'ru'),
        tone=settings.get('tone', 'friendly'),
        depth=settings.get('depth', 'detailed'),
        format=settings.get('format', 'bullets'),
        goal=settings.get('goal', 'understand'),
        status='pending'
    )
    return prompt

def generate_content_with_providers(prompt):
    """
    Generates content using available AI providers (Qwen -> Gemini fallback).
    """
    service = AIService()
    
    # Construct System Prompt (Reusing logic)
    language_code = prompt.language
    language_name = prompt.get_language_display()
    
    system_instruction = f"""
    You are an expert study tutor.
    User request: "{prompt.text}"
    
    CONFIGURATION:
    - Target Language: {language_name} ({language_code}). YOU MUST ANSWER IN {language_name}.
    - Tone: {prompt.get_tone_display()}
    - Depth: {prompt.get_depth_display()}
    - Goal: {prompt.get_goal_display()}
    
    IMPORTANT INSTRUCTIONS:
    1. Language: All content (explanations, summaries, quiz) MUST be in {language_name}, regardless of the user's prompt language.
       - Exception: Standard scientific acronyms (e.g., ATP, DNA, RNA, NADP) can be used in English if that is standard in the target language's scientific community, but usually in Russian we use АТФ, ДНК, РНК, НАДФ. Use the most natural and professional terminology for the target language.
    2. Terminology: Use precise and correct academic terminology. Avoid clumsy translations.
    3. Math Formulas: ALWAYS wrap ALL mathematical expressions, variables, and formulas in LaTeX delimiters:
       - Use $...$ for inline math (e.g., $F = ma$, $v_0$, $\\frac{{1}}{{2}}gt^2$)
       - Use $$...$$ for display/block equations
       - This includes: variable names ($F_D$, $C_D$, $\\rho$), subscripts, superscripts, fractions, Greek letters
       - This includes: variable names ($F_D$, $C_D$, $\\rho$), subscripts, superscripts, fractions, Greek letters
       - NEVER write bare math like "F_D = ..." - ALWAYS use "$F_D = ...$"
    4. Code Blocks: ALWAYS format code snippets using HTML <pre> and <code> tags.
       - Use: <pre><code class="language-python">...</code></pre>
       - Do NOT use markdown code blocks (```python ... ```).
       - Ensure you escape HTML entities within the code (e.g., < becomes &lt;).
    
    CRITICAL OUTPUT FORMAT:
    You must output a VALID JSON object. Do not include markdown code blocks.
    The JSON must be a list of objects.
    
    IMPORTANT: JSON String Escaping
    - Since you are outputting code within a JSON string, you MUST escape all special characters.
    - All newlines inside the "content" string MUST be escaped as "\\n".
    - All double quotes inside the "content" string MUST be escaped as \" (or use single quotes for HTML attributes).
    - Do NOT include real line breaks inside the JSON strings.
    
    Required Sections:
    1. "explanation": A clear explanation of the topic. HTML allowed (p, ul, li, strong).
    2. "summary": A concise summary or cheat sheet. HTML allowed.
    3. "plan": A step-by-step study plan. HTML allowed.
    4. "quiz": A self-check quiz with at least 3 questions. Use HTML. For quiz, use <details> and <summary> for answers if possible, or just Q&A.
    
    Example JSON Structure:
    [
        {{ "type": "explanation", "content": "<p>...</p>" }},
        {{ "type": "summary", "content": "<ul>...</ul>" }},
        {{ "type": "plan", "content": "<div>...</div>" }},
        {{ "type": "quiz", "content": "<div>...</div>" }}
    ]
    
    Ensure the content is formatted nicely with Tailwind CSS classes where appropriate (e.g., class="mb-4", class="text-indigo-600").
    """
    
    try:
        response_text = service.generate(system_instruction)
        
        # Strip markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        response_text = response_text.strip()
        
        # Try to parse JSON
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError as json_err:
            import re
            fixed_text = re.sub(r'(?<!\\)\\(?!["\\/bfnrtu])', r'\\\\', response_text)
            try:
                data = json.loads(fixed_text)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse AI response: {json_err}")
                return []
        
        return data
    except Exception as e:
        logger.error(f"AI Service Error: {e}")
        return []

from celery import shared_task

@shared_task
def generate_sections_task(prompt_id: str) -> list[str]:
    """
    Celery task to generate sections asynchronously.
    Returns list of section types created.
    """
    try:
        prompt = Prompt.objects.get(id=prompt_id)
    except Prompt.DoesNotExist:
        logger.error(f"Prompt {prompt_id} not found in task")
        return []

    # Call AI
    try:
        sections_data = generate_content_with_providers(prompt)
    except Exception as e:
        logger.error(f"Critical error in generate_sections_task: {e}")
        prompt.status = 'failed'
        prompt.save()
        return []

    # If AI failed
    if not sections_data:
         prompt.status = 'failed'
         prompt.save()
         return []

    created_types = []
    with transaction.atomic():
        for data in sections_data:
            if data.get('type') not in dict(Section.TYPE_CHOICES):
                continue
                
            Section.objects.create(
                prompt=prompt,
                type=data.get('type'),
                content=data.get('content', '').strip(),
                status='done'
            )
            created_types.append(data.get('type'))
        
        prompt.status = 'done'
        prompt.save()
        
    return created_types

def generate_sections(prompt: Prompt) -> list[Section]:
    """
    Synchronous wrapper or legacy entry point. 
    If you want to trigger async, use generate_sections_task.delay(prompt.id).
    This function kept for backward compatibility or synchronous testing if needed.
    """
    # ... logic allows synchronous test execution if needed
    # For now, let's keep the synchronous logic here too or rely on the task?
    # To avoid duplication, let's make this call the task synchronously?
    # Or just duplicate logic for now to ensure I don't break tests that expect return values of objects?
    # The tests expect `list[Section]`. The task returns `list[str]`.
    # I will leave this function as is for synchronous usage (testing), 
    # and the task will be used by views.
    
    # Call AI
    try:
        sections_data = generate_content_with_providers(prompt)
    except Exception as e:
        logger.error(f"Critical error in generate_sections: {e}")
        prompt.status = 'failed'
        prompt.save()
        return []

    # If AI failed
    if not sections_data:
         prompt.status = 'failed'
         prompt.save()
         return []

    created_sections = []
    with transaction.atomic():
        for data in sections_data:
            if data.get('type') not in dict(Section.TYPE_CHOICES):
                continue
                
            section = Section.objects.create(
                prompt=prompt,
                type=data.get('type'),
                content=data.get('content', '').strip(),
                status='done'
            )
            created_sections.append(section)
        
        prompt.status = 'done'
        prompt.save()
        
    return created_sections

def generate_single_section_content(prompt, section_type, mode=None):
    """
    Generates content for a single section using available providers.
    """
    service = AIService()
    
    language_code = prompt.language
    language_name = prompt.get_language_display()
    
    type_instructions = {
        'explanation': "Provide a clear and concise explanation of the topic.",
        'summary': "Provide a structured summary or cheat sheet.",
        'plan': "Provide a step-by-step study plan with timing.",
        'quiz': "Provide 3-5 self-check questions. CRITICAL: Use HTML <details> and <summary> tags for answers. Format: <details class='mb-4 p-4 bg-yellow-50 rounded-xl cursor-pointer'><summary class='font-bold text-indigo-700 list-none'>Question...</summary><div class='mt-2 text-gray-700'>Answer...</div></details>"
    }
    
    specific_instruction = type_instructions.get(section_type, "Provide relevant content.")

    mode_instruction = ""
    if mode == 'simpler':
        mode_instruction = "EXPLAIN LIKE I'M 5. Use very simple language, analogies, and short sentences. Avoid complex jargon."
    elif mode == 'detailed':
        mode_instruction = "GO DEEP. Provide comprehensive details, advanced concepts, and thorough analysis. Use academic language."
    
    system_instruction = f"""
    You are an expert study tutor.
    User request: "{prompt.text}"
    Target Section: "{section_type}"
    
    CONFIGURATION:
    - Target Language: {language_name} ({language_code}). YOU MUST ANSWER IN {language_name}.
    - Tone: {prompt.get_tone_display()}
    
    TASK:
    {specific_instruction}
    
    MODIFICATIONS:
    {mode_instruction}
    
    IMPORTANT INSTRUCTIONS:
    1. Language: All content MUST be in {language_name}.
    2. Format: Return ONLY the HTML content for this section. Do NOT return JSON. Do NOT return markdown code blocks. Just the HTML.
    3. Styling: Use Tailwind CSS classes (e.g., class="mb-4 text-gray-700").
    """
    
    try:
        content = service.generate(system_instruction)
        
        if content.startswith("```html"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
            
        return content.strip()
    except Exception as e:
        logger.error(f"AI Service Error (Single Section): {e}")
        return None

def regenerate_section(section_id, user, mode=None):
    """
    Regenerates a specific section.
    """
    original_section = Section.objects.get(id=section_id)
    prompt = original_section.prompt
    
    # Calculate new version
    last_version = Section.objects.filter(prompt=prompt, type=original_section.type).order_by('-version').first()
    new_version = last_version.version + 1 if last_version else 1
    
    # Generate content
    content = generate_single_section_content(prompt, original_section.type, mode)
    
    if not content:
        raise Exception("Failed to generate content")
        
    # Create new section version
    new_section = Section.objects.create(
        prompt=prompt,
        type=original_section.type,
        content=content,
        status='done',
        version=new_version
    )
    
    return new_section
