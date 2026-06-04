from django.test import TestCase
from unittest.mock import patch, MagicMock
from apps.prompts.services import AIService, QwenProvider, GeminiProvider

class AIServiceTests(TestCase):
    def setUp(self):
        # Ensure we have mock keys for testing
        self.qwen_key_patch = patch('django.conf.settings.QWEN_API_KEY', 'mock_qwen_key')
        self.gemini_key_patch = patch('django.conf.settings.GEMINI_API_KEY', 'mock_gemini_key')
        self.qwen_key_patch.start()
        self.gemini_key_patch.start()

    def tearDown(self):
        self.qwen_key_patch.stop()
        self.gemini_key_patch.stop()

    @patch('apps.prompts.services.OpenAI')
    def test_qwen_provider_success(self, mock_openai):
        # Setup mock response
        mock_client = MagicMock()
        mock_completion = MagicMock()
        mock_completion.choices[0].message.content = "Qwen Response"
        mock_client.chat.completions.create.return_value = mock_completion
        mock_openai.return_value = mock_client

        provider = QwenProvider()
        response = provider.generate_content("test")
        
        self.assertEqual(response, "Qwen Response")
        mock_client.chat.completions.create.assert_called_once()

    @patch('apps.prompts.services.genai')
    def test_gemini_provider_success(self, mock_genai):
        # New google-genai SDK: genai.Client(...).models.generate_content(...)
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Gemini Response"
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client

        provider = GeminiProvider()
        response = provider.generate_content("test")

        self.assertEqual(response, "Gemini Response")
        mock_client.models.generate_content.assert_called_once()

    @patch('apps.prompts.services.QwenProvider')
    @patch('apps.prompts.services.GeminiProvider')
    def test_ai_service_fallback(self, MockGemini, MockQwen):
        # Setup mocks
        mock_qwen_instance = MockQwen.return_value
        mock_gemini_instance = MockGemini.return_value
        
        # Qwen raises exception
        mock_qwen_instance.generate_content.side_effect = Exception("Qwen Error")
        # Gemini succeeds
        mock_gemini_instance.generate_content.return_value = "Gemini Fallback Response"

        service = AIService()
        # Ensure configuration adds both providers
        service.providers = [mock_qwen_instance, mock_gemini_instance]
        
        response = service.generate("test")
        
        self.assertEqual(response, "Gemini Fallback Response")
        # Verify both were called
        mock_qwen_instance.generate_content.assert_called_once()
        mock_gemini_instance.generate_content.assert_called_once()

    @patch('apps.prompts.services.QwenProvider')
    @patch('apps.prompts.services.GeminiProvider')
    def test_ai_service_all_fail(self, MockGemini, MockQwen):
        # Setup mocks
        mock_qwen_instance = MockQwen.return_value
        mock_gemini_instance = MockGemini.return_value
        
        # Both raise exception
        mock_qwen_instance.generate_content.side_effect = Exception("Qwen Error")
        mock_gemini_instance.generate_content.side_effect = Exception("Gemini Error")

        service = AIService()
        service.providers = [mock_qwen_instance, mock_gemini_instance]
        
        with self.assertRaises(Exception) as context:
            service.generate("test")
            
        self.assertIn("All providers failed", str(context.exception))
