import http.server
import json
import os
import shutil
import socketserver
import threading
import time
import unittest
from playwright.sync_api import sync_playwright

from gamemodes import list_manifests

ARTIFACT_DIR = r"C:\Users\Admin\.gemini\antigravity\brain\7a6ecc02-3c76-4b77-a38f-6a9ebaa06e32"
WEB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web")
SCREENSHOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")


class QuietHTTPHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def log_message(self, format, *args):
        pass  # suppress request logging to keep test output clean


class PlaywrightE2ETest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        # Start local HTTP server on an available port
        cls.server = socketserver.TCPServer(("127.0.0.1", 0), QuietHTTPHandler)
        cls.port = cls.server.server_address[1]
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_frontend_full_game_lifecycle(self):
        console_errors = []
        page_errors = []

        with open("lang/vi.json", encoding="utf-8") as f:
            vi_json = f.read()
        with open("lang/en.json", encoding="utf-8") as f:
            en_json = f.read()

        manifests_json = json.dumps(list_manifests())

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 1280, "height": 850})
            page = context.new_page()

            # Track console errors and exceptions
            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
            page.on("pageerror", lambda err: page_errors.append(str(err)))

            # Mock pycmd bridge communication
            mock_bridge_script = """
            let mockUiLang = 'vi';
            const viCatalog = __VI_JSON__;
            const enCatalog = __EN_JSON__;

            window.pycmd = function(rawMessage, callback) {
                let msg = typeof rawMessage === 'string' ? JSON.parse(rawMessage) : rawMessage;
                let action = msg.action;
                let data = msg.data || {};
                let res = { success: true, data: {} };

                if (action === 'get_gamemodes') {
                    res.data = { gamemodes: __MANIFESTS_PLACEHOLDER__ };
                } else if (action === 'get_ui_strings') {
                    res.data = { strings: (mockUiLang === 'vi' ? viCatalog : enCatalog), lang: mockUiLang };
                } else if (action === 'set_ui_lang') {
                    mockUiLang = data.lang || 'vi';
                    res.data = { lang: mockUiLang, ui_lang: mockUiLang };
                } else if (action === 'get_settings') {
                    res.data = { ui_lang: mockUiLang, learn_lang: 'en', model: 'auto', keys: ['AIzaSyDummyKey'] };
                } else if (action === 'load_prefs') {
                    res.data = {
                        sample_limit: 20,
                        level: 'intermediate',
                        topic: 'general',
                        pairs: [
                            { id: 'p1', term: 'apple', definition: 'quả táo', key: 'apple\\0quả táo' },
                            { id: 'p2', term: 'banana', definition: 'quả chuối', key: 'banana\\0quả chuối' },
                            { id: 'p3', term: 'orange', definition: 'quả cam', key: 'orange\\0quả cam' },
                            { id: 'p4', term: 'grape', definition: 'quả nho', key: 'grape\\0quả nho' },
                            { id: 'p5', term: 'mango', definition: 'quả xoài', key: 'mango\\0quả xoài' },
                            { id: 'p6', term: 'peach', definition: 'quả đào', key: 'peach\\0quả đào' }
                        ]
                    };
                } else if (action === 'get_supported_languages') {
                    res.data = {
                        learn_languages: [
                            { code: 'en', native: 'English', names: { vi: 'Tiếng Anh', en: 'English' } },
                            { code: 'zh', native: '中文', names: { vi: 'Tiếng Trung', en: 'Chinese' } }
                        ],
                        ui_languages: ['vi', 'en']
                    };
                } else if (action === 'list_decks') {
                    res.data = {
                        decks: [
                            { id: 1, name: 'Default', level: 0 },
                            { id: 2, name: 'English::Vocab', level: 1 }
                        ]
                    };
                } else if (action === 'list_source_models' || action === 'get_source_models') {
                    res.data = {
                        models: [
                            { id: 10, name: 'Basic' },
                            { id: 11, name: 'Cloze' }
                        ]
                    };
                } else if (action === 'list_source_fields' || action === 'get_source_fields') {
                    res.data = { fields: ['Front', 'Back'] };
                } else if (action === 'sample_vocab_pairs') {
                    res.data = {
                        pairs: [
                            { id: 101, term: 'apple', definition: 'quả táo', key: 'apple\\0quả táo' },
                            { id: 102, term: 'banana', definition: 'quả chuối', key: 'banana\\0quả chuối' },
                            { id: 103, term: 'orange', definition: 'quả cam', key: 'orange\\0quả cam' },
                            { id: 104, term: 'grape', definition: 'quả nho', key: 'grape\\0quả nho' },
                            { id: 105, term: 'mango', definition: 'quả xoài', key: 'mango\\0quả xoài' },
                            { id: 106, term: 'peach', definition: 'quả đào', key: 'peach\\0quả đào' }
                        ],
                        total: 6,
                        limit: 20
                    };
                } else if (action === 'generate') {
                    let gm = data.gamemode || 'fill_blank';
                    if (gm === 'matching') {
                        res.data = {
                            game_id: 'matching-123',
                            pairs: [
                                { id: 'p1', term: 'apple', definition: 'quả táo' },
                                { id: 'p2', term: 'banana', definition: 'quả chuối' },
                                { id: 'p3', term: 'orange', definition: 'quả cam' },
                                { id: 'p4', term: 'grape', definition: 'quả nho' },
                                { id: 'p5', term: 'mango', definition: 'quả xoài' }
                            ]
                        };
                    } else if (gm === 'cloze') {
                        res.data = {
                            paragraph: 'Every morning, she drinks a cup of [BLANK_1] and eats a red [BLANK_2] for health.',
                            blanks: [
                                { id: 'BLANK_1', answer: 'coffee', meaning: 'cà phê', distractors: ['tea', 'milk'], explanation: 'Coffee là cà phê.' },
                                { id: 'BLANK_2', answer: 'apple', meaning: 'quả táo', distractors: ['orange', 'banana'], explanation: 'Apple là quả táo.' }
                            ],
                            full_solution_text: 'Every morning, she drinks a cup of coffee and eats a red apple for health.',
                            story_translation: 'Mỗi buổi sáng, cô ấy uống một tách cà phê và ăn một quả táo đỏ vì sức khỏe.'
                        };
                    } else if (gm === 'translation') {
                        res.data = {
                            source_sentence: 'Tôi thích ăn hoa quả tươi vào mỗi buổi sáng.',
                            target_language: 'en',
                            reference_translation: 'I like eating fresh fruit every morning.',
                            grading_rubric: 'Check accuracy and natural vocabulary.'
                        };
                    } else if (gm === 'unscramble') {
                        res.data = {
                            questions: [
                                { original: 'She likes eating fresh fruit.', words: ['eating', 'She', 'likes', 'fresh', 'fruit'], translation: 'Cô ấy thích ăn hoa quả tươi.' }
                            ]
                        };
                    } else if (gm === 'sentence_transform') {
                        res.data = {
                            questions: [
                                {
                                    original: 'People speak English all over the world.',
                                    instruction: 'Chuyển sang câu bị động (Passive voice).',
                                    expected_answer: 'English is spoken all over the world.'
                                }
                            ]
                        };
                    } else if (gm === 'taboo') {
                        res.data = {
                            rounds: [
                                {
                                    target_word: 'Apple',
                                    taboo_words: ['Fruit', 'Red', 'Tree', 'Eat', 'Pie'],
                                    clue: 'A round sweet produce of a tree with crisp flesh.'
                                }
                            ]
                        };
                    } else if (gm === 'story') {
                        res.data = {
                            story: {
                                title: 'The Golden Orchard',
                                content: 'Once upon a time in a sunny valley, there was a quiet orchard. Every autumn, ripe apples covered the trees, attracting animals from near and far.',
                                full_translation: 'Ngày xửa ngày xưa ở một thung lũng đầy nắng...'
                            },
                            questions: [
                                {
                                    question: 'What covered the trees every autumn?',
                                    options: [
                                        { text: 'Ripe apples', is_correct: true },
                                        { text: 'Yellow bananas', is_correct: false },
                                        { text: 'Sweet oranges', is_correct: false }
                                    ],
                                    correct_index: 0,
                                    explanation: 'The passage explicitly says: ripe apples covered the trees.'
                                }
                            ]
                        };
                    } else {
                        res.data = {
                            questions: [
                                {
                                    sentence: 'She peeled an ___ for breakfast.',
                                    target_word: 'apple',
                                    meaning: 'quả táo',
                                    options: [
                                        { word: 'apple', is_correct: true, type: 'correct' },
                                        { word: 'banana', is_correct: false, type: 'wrong' },
                                        { word: 'orange', is_correct: false, type: 'wrong' },
                                        { word: 'grape', is_correct: false, type: 'wrong' }
                                    ],
                                    explanation: 'Apple (quả táo) là đáp án chính xác.'
                                }
                            ]
                        };
                    }
                } else if (action === 'check_answer') {
                    res.data = {
                        correct: true,
                        score: 10,
                        feedback: 'Chính xác! Làm tốt lắm.'
                    };
                } else if (action === 'test_all_keys') {
                    res.data = {
                        results: [{ key: 'Slot 1', ok: true, status: 'OK', model: 'gemini-3.5-flash-lite' }]
                    };
                } else if (action === 'log_event') {
                    res.data = { status: 'logged' };
                } else if (action === 'save_prefs') {
                    res.data = { success: true };
                }

                if (typeof callback === 'function') {
                    setTimeout(() => callback(res), 5);
                }
            };
            """.replace("__MANIFESTS_PLACEHOLDER__", manifests_json).replace("__VI_JSON__", vi_json).replace("__EN_JSON__", en_json)
            page.add_init_script(mock_bridge_script)

            # 1. Navigate to web application
            url = f"http://127.0.0.1:{self.port}/index.html"
            page.goto(url, wait_until="networkidle")

            # 2. Verify boot-overlay disappears and game grid renders
            page.wait_for_selector(".game-grid", timeout=5000)
            self.assertFalse(page.is_visible("#boot-overlay"))

            # 3. Verify all 8 game cards are rendered
            game_cards = page.query_selector_all(".game-card")
            self.assertEqual(len(game_cards), 8, "Expected 8 game mode cards on dashboard")

            # Click Test Keys to verify API status badge
            page.click("#test-keys")
            page.wait_for_selector(".badge-status-ok", timeout=5000)

            # Capture dashboard screenshot with API test status
            shot1 = os.path.join(SCREENSHOT_DIR, "hub_dashboard.png")
            page.screenshot(path=shot1, full_page=True)
            if os.path.isdir(ARTIFACT_DIR):
                shutil.copy2(shot1, os.path.join(ARTIFACT_DIR, "hub_dashboard.png"))

            # 4. Cloze mode (Config, Vocabulary Sampling & Gameplay)
            page.click('[data-game="cloze"]')
            page.wait_for_selector(".config-panel", timeout=3000)
            self.assertIsNotNone(page.query_selector("#num_blanks"), "Cloze custom control #num_blanks should be rendered")

            # Check Vietnamese button label
            gen_btn_text = page.text_content("#generate").strip()
            self.assertEqual(gen_btn_text, "Tạo bài", f"Expected 'Tạo bài' in Vietnamese UI, got: {gen_btn_text}")

            # Test Vocabulary Sampling: clicking #sample before selecting deck gives validation warning
            page.click("#sample")
            page.wait_for_selector("#status-banner", timeout=3000)
            banner_msg = page.text_content("#status-banner-message").strip()
            self.assertIn("Hãy chọn deck", banner_msg, f"Expected select fields warning, got: {banner_msg}")

            # Now select deck, model, term and definition fields
            page.select_option("#deck", value="1")
            page.evaluate("document.querySelector('#deck').dispatchEvent(new Event('change'))")
            page.wait_for_selector("#model option[value='10']", state="attached", timeout=3000)
            page.select_option("#model", value="10")
            page.evaluate("document.querySelector('#model').dispatchEvent(new Event('change'))")
            page.wait_for_selector("#term option[value='Front']", state="attached", timeout=3000)
            page.select_option("#term", value="Front")
            page.select_option("#definition", value="Back")

            # Sample vocabulary with valid fields
            page.click("#sample")
            page.wait_for_selector("#source-status", timeout=3000)
            time.sleep(0.3)
            status_text = page.text_content("#source-status").strip()
            self.assertIn("Đã lấy 6 cặp", status_text, f"Expected 6 pairs loaded, got: {status_text}")

            page.evaluate("window.scrollTo(0, 0)")
            time.sleep(0.15)
            shot_sample = os.path.join(SCREENSHOT_DIR, "hub_sampling_success.png")
            page.screenshot(path=shot_sample, full_page=True)
            if os.path.isdir(ARTIFACT_DIR):
                shutil.copy2(shot_sample, os.path.join(ARTIFACT_DIR, "hub_sampling_success.png"))

            # Test UI Language Switcher toggle
            page.click("#toggle-ui-lang")
            time.sleep(0.3)
            page.wait_for_selector("#generate", timeout=3000)
            gen_btn_en = page.text_content("#generate").strip()
            self.assertEqual(gen_btn_en, "Generate", f"Expected 'Generate' in English UI, got: {gen_btn_en}")
            page.evaluate("window.scrollTo(0, 0)")
            time.sleep(0.15)
            shot_en = os.path.join(SCREENSHOT_DIR, "hub_english_parity.png")
            page.screenshot(path=shot_en, full_page=True)
            if os.path.isdir(ARTIFACT_DIR):
                shutil.copy2(shot_en, os.path.join(ARTIFACT_DIR, "hub_english_parity.png"))

            # Switch back to Vietnamese
            page.click("#toggle-ui-lang")
            time.sleep(0.3)
            page.wait_for_selector("#generate", timeout=3000)
            gen_btn_vi = page.text_content("#generate").strip()
            self.assertEqual(gen_btn_vi, "Tạo bài", f"Expected 'Tạo bài' in Vietnamese UI, got: {gen_btn_vi}")
            page.evaluate("window.scrollTo(0, 0)")
            time.sleep(0.15)
            shot_vi = os.path.join(SCREENSHOT_DIR, "hub_vietnamese_parity.png")
            page.screenshot(path=shot_vi, full_page=True)
            if os.path.isdir(ARTIFACT_DIR):
                shutil.copy2(shot_vi, os.path.join(ARTIFACT_DIR, "hub_vietnamese_parity.png"))

            shot_cloze = os.path.join(SCREENSHOT_DIR, "hub_cloze_config.png")
            page.screenshot(path=shot_cloze, full_page=True)
            if os.path.isdir(ARTIFACT_DIR):
                shutil.copy2(shot_cloze, os.path.join(ARTIFACT_DIR, "hub_cloze_config.png"))

            page.click("#generate")
            page.wait_for_selector(".word-bank-box", timeout=5000)
            time.sleep(0.35)
            page.evaluate("document.querySelector('#play').scrollIntoView({behavior: 'instant', block: 'center'})")
            time.sleep(0.1)
            shot_cloze_game = os.path.join(SCREENSHOT_DIR, "hub_cloze_game.png")
            page.screenshot(path=shot_cloze_game)
            if os.path.isdir(ARTIFACT_DIR):
                shutil.copy2(shot_cloze_game, os.path.join(ARTIFACT_DIR, "hub_cloze_game.png"))

            # Back to hub
            page.click("#back")
            page.wait_for_selector(".game-grid", timeout=3000)

            # 5. Navigate into Sentence Transform mode to verify custom control 'focus' and gameplay
            page.click('[data-game="sentence_transform"]')
            page.wait_for_selector(".config-panel", timeout=3000)
            focus_select = page.query_selector("#focus")
            self.assertIsNotNone(focus_select, "Sentence transform custom control #focus should be rendered")
            shot_st = os.path.join(SCREENSHOT_DIR, "hub_sentence_transform_config.png")
            page.screenshot(path=shot_st, full_page=True)
            if os.path.isdir(ARTIFACT_DIR):
                shutil.copy2(shot_st, os.path.join(ARTIFACT_DIR, "hub_sentence_transform_config.png"))

            page.click("#generate")
            page.wait_for_selector("#answer", timeout=5000)
            time.sleep(0.35)
            page.evaluate("document.querySelector('#play').scrollIntoView({behavior: 'instant', block: 'center'})")
            time.sleep(0.1)
            shot_st_game = os.path.join(SCREENSHOT_DIR, "hub_sentence_transform_game.png")
            page.screenshot(path=shot_st_game)
            if os.path.isdir(ARTIFACT_DIR):
                shutil.copy2(shot_st_game, os.path.join(ARTIFACT_DIR, "hub_sentence_transform_game.png"))

            # Back to hub
            page.click("#back")
            page.wait_for_selector(".game-grid", timeout=3000)

            # 6. Navigate into Fill in the Blank mode and play
            page.click('[data-game="fill_blank"]')
            page.wait_for_selector(".config-panel", timeout=3000)

            # Click generate to produce questions
            page.click("#generate")
            page.wait_for_selector(".option-btn, .opt-btn, .choice-btn, button[data-choice]", timeout=5000)
            time.sleep(0.35)
            page.evaluate("document.querySelector('#play').scrollIntoView({behavior: 'instant', block: 'center'})")
            time.sleep(0.1)
            shot2 = os.path.join(SCREENSHOT_DIR, "hub_fill_blank_game.png")
            page.screenshot(path=shot2)
            if os.path.isdir(ARTIFACT_DIR):
                shutil.copy2(shot2, os.path.join(ARTIFACT_DIR, "hub_fill_blank_game.png"))

            # 7. Return to Hub
            page.click("#back")
            page.wait_for_selector(".game-grid", timeout=3000)

            # 8. Navigate into Word Matching mode
            page.click('[data-game="matching"]')
            page.wait_for_selector(".config-panel", timeout=3000)

            # Click generate to start Word Matching
            page.click("#generate")
            page.wait_for_selector(".match-board", timeout=5000)
            time.sleep(0.35)

            # Check that match-card elements exist and are 5 on left, 5 on right
            cards_left = page.query_selector_all('.match-card[data-col="left"]')
            cards_right = page.query_selector_all('.match-card[data-col="right"]')
            self.assertEqual(len(cards_left), 5, "Expected 5 cards on left column")
            self.assertEqual(len(cards_right), 5, "Expected 5 cards on right column")

            # Click a card to trigger selection
            cards_left[0].click()
            time.sleep(0.1)

            page.evaluate("window.scrollTo(0, 0)")
            time.sleep(0.1)

            shot3 = os.path.join(SCREENSHOT_DIR, "hub_matching_board.png")
            page.screenshot(path=shot3, full_page=True)
            if os.path.isdir(ARTIFACT_DIR):
                shutil.copy2(shot3, os.path.join(ARTIFACT_DIR, "hub_matching_board.png"))

            # Open matching stats modal and wait for fadeIn animation
            page.click("#open-history-btn")
            page.wait_for_selector("#history-modal:not([hidden])", timeout=3000)
            time.sleep(0.35)
            shot_stats = os.path.join(SCREENSHOT_DIR, "hub_matching_stats_modal.png")
            page.screenshot(path=shot_stats, full_page=True)
            if os.path.isdir(ARTIFACT_DIR):
                shutil.copy2(shot_stats, os.path.join(ARTIFACT_DIR, "hub_matching_stats_modal.png"))

            # Close modal
            page.click("#close-history-modal")

            # Back to hub
            page.click("#back")
            page.wait_for_selector(".game-grid", timeout=3000)

            # 9. Translation mode
            page.click('[data-game="translation"]')
            page.wait_for_selector(".config-panel", timeout=3000)
            page.click("#generate")
            page.wait_for_selector("#answer", timeout=5000)
            time.sleep(0.35)
            page.evaluate("document.querySelector('#play').scrollIntoView({behavior: 'instant', block: 'center'})")
            time.sleep(0.1)
            shot_trans = os.path.join(SCREENSHOT_DIR, "hub_translation_game.png")
            page.screenshot(path=shot_trans)
            if os.path.isdir(ARTIFACT_DIR):
                shutil.copy2(shot_trans, os.path.join(ARTIFACT_DIR, "hub_translation_game.png"))

            page.click("#back")
            page.wait_for_selector(".game-grid", timeout=3000)

            # 10. Word Unscramble mode
            page.click('[data-game="unscramble"]')
            page.wait_for_selector(".config-panel", timeout=3000)
            page.click("#generate")
            page.wait_for_selector(".unscramble-card", timeout=5000)
            time.sleep(0.35)
            page.evaluate("document.querySelector('#play').scrollIntoView({behavior: 'instant', block: 'center'})")
            time.sleep(0.1)
            shot_unscramble = os.path.join(SCREENSHOT_DIR, "hub_unscramble_game.png")
            page.screenshot(path=shot_unscramble)
            if os.path.isdir(ARTIFACT_DIR):
                shutil.copy2(shot_unscramble, os.path.join(ARTIFACT_DIR, "hub_unscramble_game.png"))

            page.click("#back")
            page.wait_for_selector(".game-grid", timeout=3000)

            # 11. Story mode
            page.click('[data-game="story"]')
            page.wait_for_selector(".config-panel", timeout=3000)
            page.click("#generate")
            page.wait_for_selector(".story-passage-card", timeout=5000)
            time.sleep(0.35)
            page.evaluate("document.querySelector('#play').scrollIntoView({behavior: 'instant', block: 'center'})")
            time.sleep(0.1)
            shot_story = os.path.join(SCREENSHOT_DIR, "hub_story_game.png")
            page.screenshot(path=shot_story)
            if os.path.isdir(ARTIFACT_DIR):
                shutil.copy2(shot_story, os.path.join(ARTIFACT_DIR, "hub_story_game.png"))

            page.click("#back")
            page.wait_for_selector(".game-grid", timeout=3000)

            # 12. Taboo mode
            page.click('[data-game="taboo"]')
            page.wait_for_selector(".config-panel", timeout=3000)
            page.click("#generate")
            page.wait_for_selector(".taboo-card", timeout=5000)
            time.sleep(0.35)
            page.evaluate("document.querySelector('#play').scrollIntoView({behavior: 'instant', block: 'center'})")
            time.sleep(0.1)
            shot_taboo = os.path.join(SCREENSHOT_DIR, "hub_taboo_game.png")
            page.screenshot(path=shot_taboo)
            if os.path.isdir(ARTIFACT_DIR):
                shutil.copy2(shot_taboo, os.path.join(ARTIFACT_DIR, "hub_taboo_game.png"))

            taboo_placeholder = page.get_attribute("#answer", "placeholder") or ""
            self.assertIn("Tiếng Anh", taboo_placeholder, f"Expected 'Tiếng Anh' in taboo placeholder, got: {taboo_placeholder}")
            self.assertNotIn("bằng en...", taboo_placeholder, "Taboo placeholder should not contain raw 'en' code")
            page.evaluate("document.querySelector('.taboo-card').scrollIntoView({behavior: 'instant', block: 'start'})")
            time.sleep(0.15)
            shot_taboo_loc = os.path.join(SCREENSHOT_DIR, "hub_taboo_localized.png")
            page.screenshot(path=shot_taboo_loc)
            if os.path.isdir(ARTIFACT_DIR):
                shutil.copy2(shot_taboo_loc, os.path.join(ARTIFACT_DIR, "hub_taboo_localized.png"))

            # Check for unhandled exceptions or console errors
            self.assertEqual(len(page_errors), 0, f"Detected unhandled page errors: {page_errors}")

            browser.close()


if __name__ == "__main__":
    unittest.main()
