import os
import sys

ADDON_NAME = "AI Learning Hub"
ADDON_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ADDON_PATH)

from aqt import mw, gui_hooks
from aqt.qt import *
from aqt.utils import showInfo, showWarning

from core.logger import log
from core.i18n import t, load_strings

mw.addonManager.setWebExports(__name__, r"web/.*")

log.info(f"Add-on loaded: {ADDON_NAME} v2.0")

def open_hub():
    try:
        if hasattr(mw, "ai_hub_view") and mw.ai_hub_view is not None and not mw.ai_hub_view.is_closed():
            mw.ai_hub_view.focus()
            return

        from ui.main_window import AIHubView

        if not hasattr(mw, "ai_engine") or mw.ai_engine is None:
            from core.engine import AIEngine
            mw.ai_engine = AIEngine()
            mw.ai_engine.start()

        mw.ai_hub_view = AIHubView(mw.ai_engine)
        mw.ai_hub_view.embed()
        log.info("Hub view embedded")
    except Exception as e:
        log.error(f"Error opening AI Hub: {e}")


def init_addon():
    from core.engine import AIEngine

    try:
        mw.ai_engine = AIEngine()
        log.info("AIEngine created")
    except Exception as e:
        log.error(f"Error initializing AIEngine: {e}")

    def on_profile_open():
        try:
            mw.ai_engine.start()
        except Exception as e:
            log.error(f"Error starting AIEngine on profile open: {e}")

    gui_hooks.profile_did_open.append(on_profile_open)

    menu = mw.form.menuTools
    action = QAction(f"{ADDON_NAME}...", mw)
    action.triggered.connect(open_hub)
    menu.addAction(action)

    settings_action = QAction(f"{ADDON_NAME} Settings...", mw)
    settings_action.triggered.connect(open_settings)
    menu.addAction(settings_action)

    log.info("Menu items added")


def open_settings():
    if not hasattr(mw, "ai_engine") or mw.ai_engine is None:
        from core.engine import AIEngine
        mw.ai_engine = AIEngine()
        mw.ai_engine.start()

    s = mw.ai_engine.settings
    current_ui_lang = s.get("ui_lang", "en")

    dialog = QDialog(mw)
    dialog.setWindowTitle(t("settings.title", current_ui_lang))
    dialog.setMinimumWidth(620)
    layout = QVBoxLayout()
    layout.setSpacing(10)

    # Widget references for retranslation
    i18n_widgets = []

    def _add_i18n_key(key: str) -> str:
        return load_strings(current_ui_lang).get(key, key)

    def _section(text_key):
        lbl = QLabel(_add_i18n_key(text_key))
        lbl.setStyleSheet("font-weight:600;font-size:13px;padding-top:6px;")
        layout.addWidget(lbl)
        i18n_widgets.append((lbl, text_key))
        return lbl

    # ===== API Keys =====
    _section("settings.api_keys")

    # API key count spinbox
    count_row = QHBoxLayout()
    count_lbl = QLabel(_add_i18n_key("settings.api_key_count"))
    count_row.addWidget(count_lbl)
    i18n_widgets.append((count_lbl, "settings.api_key_count"))

    # Determine dynamic count
    active_keys_count = len([k for k in s.get_api_keys() if k])
    default_count = max(1, min(10, active_keys_count))
    if default_count < 3 and not s.get("api_key_count"):
        default_count = 3
    api_key_count = s.get("api_key_count", default_count)

    num_keys_spin = QSpinBox()
    num_keys_spin.setRange(1, 10)
    num_keys_spin.setValue(api_key_count)
    num_keys_spin.setFixedWidth(50)
    count_row.addWidget(num_keys_spin)
    count_row.addStretch()
    layout.addLayout(count_row)

    key_inputs = []
    key_statuses = []
    key_labels = []
    key_rows = []

    stored_keys = s.get_api_keys()  # length 10

    for idx in range(10):
        row = QHBoxLayout()
        label_key = "settings.primary_key" if idx == 0 else ("settings.key_n", idx + 1)
        
        lbl_text = _add_i18n_key("settings.primary_key") if idx == 0 else _add_i18n_key("settings.key_n").replace("{0}", str(idx + 1))
        lbl = QLabel(lbl_text)
        row.addWidget(lbl)
        i18n_widgets.append((lbl, label_key))

        inp = QLineEdit(stored_keys[idx])
        inp.setEchoMode(QLineEdit.EchoMode.Password)
        inp.setPlaceholderText(f"Gemini API key #{idx+1}")
        inp.textChanged.connect(lambda text, i=idx: key_statuses[i].setText(""))
        row.addWidget(inp, 1)

        status_label = QLabel("")
        status_label.setFixedWidth(45)
        row.addWidget(status_label)
        key_statuses.append(status_label)

        show_btn = QCheckBox(_add_i18n_key("settings.show"))
        i18n_widgets.append((show_btn, "settings.show"))
        show_btn.toggled.connect(
            lambda checked, e=inp: e.setEchoMode(
                QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
            )
        )
        row.addWidget(show_btn)

        test_btn = QPushButton(_add_i18n_key("settings.test"))
        i18n_widgets.append((test_btn, "settings.test"))
        test_btn.setFixedWidth(50)
        test_btn.clicked.connect(lambda checked, k=inp, st=status_label: _test_key(k.text().strip(), st))
        row.addWidget(test_btn)
        
        layout.addLayout(row)
        key_inputs.append(inp)
        key_labels.append(lbl)
        key_rows.append((lbl, inp, status_label, show_btn, test_btn))

    def update_key_visibility():
        count = num_keys_spin.value()
        for i, (lbl, inp, status_lbl, show_btn, test_btn) in enumerate(key_rows):
            visible = i < count
            lbl.setVisible(visible)
            inp.setVisible(visible)
            status_lbl.setVisible(visible)
            show_btn.setVisible(visible)
            test_btn.setVisible(visible)

    num_keys_spin.valueChanged.connect(update_key_visibility)
    update_key_visibility()

    # ===== Model =====
    _section("settings.model")
    model_row = QHBoxLayout()
    model_lbl = QLabel(_add_i18n_key("settings.model"))
    model_row.addWidget(model_lbl)
    i18n_widgets.append((model_lbl, "settings.model"))

    model_cb = QComboBox()
    model_cb.addItems(["auto", "gemini-flash-latest", "gemini-3.6-flash", "gemma-4-31b-it", "gemini-3.1-flash-lite"])
    idx = model_cb.findText(s.get("model", "auto"))
    if idx >= 0:
        model_cb.setCurrentIndex(idx)
    model_row.addWidget(model_cb)

    temp_lbl = QLabel(_add_i18n_key("settings.temperature"))
    model_row.addWidget(temp_lbl)
    i18n_widgets.append((temp_lbl, "settings.temperature"))

    temp_spin = QDoubleSpinBox()
    temp_spin.setRange(0.0, 1.0)
    temp_spin.setSingleStep(0.1)
    temp_spin.setValue(s.get("temperature", 0.7))
    tip = _add_i18n_key("settings.temperature_tip")
    temp_spin.setToolTip(tip)
    model_row.addWidget(temp_spin)
    layout.addLayout(model_row)

    # ===== Language =====
    lang_lbl = _section("settings.ui_lang")
    lang_row = QHBoxLayout()
    ui_lang_lbl = QLabel(_add_i18n_key("settings.ui_lang"))
    lang_row.addWidget(ui_lang_lbl)
    i18n_widgets.append((ui_lang_lbl, "settings.ui_lang"))

    from core.languages import SUPPORTED_LANGUAGES, UI_LANGUAGES
    ui_lang_cb = QComboBox()
    ui_lang_cb.addItems(UI_LANGUAGES)
    ui_lang_cb.setCurrentText(current_ui_lang)
    lang_row.addWidget(ui_lang_cb)

    learn_lang_lbl = QLabel(_add_i18n_key("settings.learn_lang"))
    lang_row.addWidget(learn_lang_lbl)
    i18n_widgets.append((learn_lang_lbl, "settings.learn_lang"))

    learn_lang_cb = QComboBox()
    for lang in SUPPORTED_LANGUAGES:
        name = f"{lang['native']} ({lang['names'].get(current_ui_lang, lang['native'])})"
        learn_lang_cb.addItem(name, lang["code"])
    
    idx = learn_lang_cb.findData(s.get("learn_lang", "en"))
    if idx != -1:
        learn_lang_cb.setCurrentIndex(idx)
    lang_row.addWidget(learn_lang_cb)
    layout.addLayout(lang_row)

    layout.addStretch()
    buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
    layout.addWidget(buttons)
    dialog.setLayout(layout)

    # ===== Retranslation =====
    def _retranslate(lang_code: str):
        strings = load_strings(lang_code)
        for widget, key in i18n_widgets:
            if isinstance(key, tuple):
                text = strings.get(key[0], key[0]).replace("{0}", str(key[1]))
            else:
                text = strings.get(key, key)
            if isinstance(widget, QCheckBox):
                widget.setText(text)
            else:
                widget.setText(text)
        temp_spin.setToolTip(strings.get("settings.temperature_tip", "").replace("\\n", "\n"))
        dialog.setWindowTitle(strings.get("settings.title", "Settings"))
        selected = learn_lang_cb.currentData()
        learn_lang_cb.blockSignals(True)
        learn_lang_cb.clear()
        for item in SUPPORTED_LANGUAGES:
            label = f"{item['native']} ({item['names'].get(lang_code, item['native'])})"
            learn_lang_cb.addItem(label, item["code"])
        learn_lang_cb.setCurrentIndex(max(0, learn_lang_cb.findData(selected)))
        learn_lang_cb.blockSignals(False)

    ui_lang_cb.currentTextChanged.connect(_retranslate)

    # ===== Test Key =====
    def _test_key(key: str, status_label: QLabel = None):
        if not key:
            if status_label:
                status_label.setText("Empty")
                status_label.setStyleSheet("color: orange; font-weight: bold;")
            return
        
        if status_label:
            status_label.setText("...")
            status_label.setStyleSheet("color: gray; font-weight: bold;")

        selected_model = model_cb.currentText()
        def run_test():
            from core.api_client import GeminiClient
            client = GeminiClient([key], selected_model)
            return client.test_key(key)

        def on_done(future):
            try:
                res = future.result()
                if status_label and not status_label.isHidden():
                    if res.get("ok"):
                        status_label.setText("OK")
                        status_label.setStyleSheet("color: green; font-weight: bold;")
                        log.info(f"Key test OK: {res.get('model')}")
                    else:
                        status_label.setText("Fail")
                        status_label.setStyleSheet("color: red; font-weight: bold;")
                        log.warn(f"Key test FAIL: {res.get('error')}")
            except Exception as e:
                log.error(f"Key test exception: {e}")
                try:
                    if status_label and not status_label.isHidden():
                        status_label.setText("Error")
                        status_label.setStyleSheet("color: red; font-weight: bold;")
                except Exception:
                    pass

        mw.taskman.run_in_background(run_test, on_done)

    # ===== Accept =====
    def on_accept():
        try:
            count = num_keys_spin.value()
            s.set("api_key_count", count)
            # Save visible keys, clear hidden keys
            for i in range(10):
                val = key_inputs[i].text().strip() if i < count else ""
                s.set(f"api_key{i+1}", val)
            # Backward compatibility
            s.set("api_key", key_inputs[0].text().strip() if count > 0 else "")
            
            s.set("model", model_cb.currentText())
            s.set("temperature", temp_spin.value())
            s.set("ui_lang", ui_lang_cb.currentText())
            s.set("learn_lang", learn_lang_cb.currentData())
            try:
                mw.ai_engine._reset_api_client()
            except Exception as ex:
                log.error(f"Error resetting API client on accept: {ex}")
            log.info("Settings dialog accepted")
        except Exception as e:
            log.error(f"Error saving settings: {e}")
        
        try:
            dialog.accept()
        except Exception:
            pass

    buttons.accepted.connect(on_accept)
    buttons.rejected.connect(dialog.reject)
    dialog.exec()


gui_hooks.main_window_did_init.append(init_addon)
