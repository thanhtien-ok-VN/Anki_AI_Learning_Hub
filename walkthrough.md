# API Error Handling Walkthrough

Gemini and bridge failures now resolve as structured errors rather than escaping Anki callbacks. The AI Hub displays one dismissible, non-modal status banner and does not offer automatic or inline retry actions for failed generation or grading requests. Successful bridge responses clear the banner.

Verification: `python -m unittest tests.test_api_client`, `python -m compileall -q core ui __init__.py`, `node --check web/js/app.js`, `node --check web/js/bridge.js`, and `git diff --check`.
