import unittest
from unittest.mock import MagicMock
import core.schema_registry as sr
from core.services.generation_service import GenerationService


class TestGenerationService(unittest.TestCase):
    def setUp(self):
        self.mock_api_client = MagicMock()
        self.mock_prompt_mgr = MagicMock()
        self.mock_settings = MagicMock()
        self.mock_resolver = MagicMock(return_value=None)

        self.mock_prompt_mgr.get_prompt.return_value = 'Test prompt'
        self.mock_settings.get.side_effect = lambda k, default=None: {
            'ui_lang': 'vi',
            'learn_lang': 'en'
        }.get(k, default)

        self.service = GenerationService()

    def test_generate_game_succeeds_when_pydantic_missing(self):
        orig_registry = sr.REGISTRY
        try:
            sr.REGISTRY = {}
            self.mock_api_client.generate_structured.return_value = {
                'questions': [{
                    'sentence': 'The dog ___ loudly.',
                    'target_word': 'barked',
                    'meaning': 'sủa',
                    'options': [
                        {'word': 'barked', 'is_correct': True, 'type': 'correct'},
                        {'word': 'slept', 'is_correct': False, 'type': 'wrong'},
                        {'word': 'ate', 'is_correct': False, 'type': 'wrong'},
                        {'word': 'ran', 'is_correct': False, 'type': 'wrong'}
                    ],
                    'explanation': 'barked is correct'
                }]
            }

            result = self.service.generate(
                data={
                    'gamemode': 'fill_blank',
                    'learn_lang': 'en',
                    'level': 'intermediate',
                    'topic': 'general',
                    'count': 1,
                    'vocab_pairs': []
                },
                api_client=self.mock_api_client,
                prompt_mgr=self.mock_prompt_mgr,
                gamemode_resolver=self.mock_resolver,
                settings=self.mock_settings
            )

            self.assertFalse(result.get('error', False), f'Expected no error, got: {result}')
            self.assertIn('questions', result)
            call_kwargs = self.mock_api_client.generate_structured.call_args[1]
            self.assertIn('response_schema', call_kwargs)
            self.assertIsInstance(call_kwargs['response_schema'], dict)
            self.assertEqual(call_kwargs['response_schema']['type'], 'OBJECT')
        finally:
            sr.REGISTRY = orig_registry

    def test_generate_game_all_gamemodes_have_valid_schema(self):
        ai_modes = ['fill_blank', 'cloze', 'translation', 'taboo', 'story', 'unscramble', 'sentence_transform']
        orig_registry = sr.REGISTRY
        try:
            sr.REGISTRY = {}
            self.mock_api_client.generate_structured.return_value = {}
            for gm in ai_modes:
                result = self.service.generate(
                    data={
                        'gamemode': gm,
                        'learn_lang': 'en',
                        'level': 'intermediate',
                        'topic': 'general',
                        'count': 3,
                        'vocab_pairs': []
                    },
                    api_client=self.mock_api_client,
                    prompt_mgr=self.mock_prompt_mgr,
                    gamemode_resolver=self.mock_resolver,
                    settings=self.mock_settings
                )
                self.assertNotEqual(result.get('error_code'), 'E_NO_SCHEMA', f'Game mode {gm} failed with E_NO_SCHEMA')
        finally:
            sr.REGISTRY = orig_registry


if __name__ == '__main__':
    unittest.main()
