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


def init_addon():
    from core.engine import AIEngine

    mw.ai_engine = AIEngine()
    log.info("AIEngine created")

    def on_profile_open():
        mw.ai_engine.start()

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
    current_ui_lang = s.get("ui_lang", "vi")

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
    key_inputs = []
    key_statuses = []
    key_labels = []
    for idx, label_key in enumerate(["settings.primary_key", "settings.fallback2", "settings.fallback3"]):
        row = QHBoxLayout()
        lbl = QLabel(_add_i18n_key(label_key))
        row.addWidget(lbl)
        i18n_widgets.append((lbl, label_key))

        key_name = "api_key" if idx == 0 else f"api_key{idx+1}"
        inp = QLineEdit(s.get(key_name, ""))
        inp.setEchoMode(QLineEdit.EchoMode.Password)
        inp.setPlaceholderText(f"Gemini API key #{idx+1}")
        inp.textChanged.connect(lambda text, i=idx: key_statuses[i].setText(""))
        row.addWidget(inp, 1)

        status_label = QLabel("")
        status_label.setFixedWidth(20)
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

    # ===== Model =====
    _section("settings.model")
    model_row = QHBoxLayout()
    model_lbl = QLabel(_add_i18n_key("settings.model"))
    model_row.addWidget(model_lbl)
    i18n_widgets.append((model_lbl, "settings.model"))

    model_cb = QComboBox()
    model_cb.addItems(["auto", "gemini-flash-latest", "gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-1.5-flash", "gemini-1.5-pro"])
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

    ui_lang_cb = QComboBox()
    ui_lang_cb.addItems(["vi", "en"])
    ui_lang_cb.setCurrentText(current_ui_lang)
    lang_row.addWidget(ui_lang_cb)

    learn_lang_lbl = QLabel(_add_i18n_key("settings.learn_lang"))
    lang_row.addWidget(learn_lang_lbl)
    i18n_widgets.append((learn_lang_lbl, "settings.learn_lang"))

    learn_lang_cb = QComboBox()
    learn_lang_cb.addItems(["en", "zh"])
    learn_lang_cb.setCurrentText(s.get("learn_lang", "en"))
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
            text = strings.get(key, key)
            if isinstance(widget, QCheckBox):
                widget.setText(text)
            else:
                widget.setText(text)
        temp_spin.setToolTip(strings.get("settings.temperature_tip", "").replace("\\n", "\n"))
        dialog.setWindowTitle(strings.get("settings.title", "Settings"))

    ui_lang_cb.currentTextChanged.connect(_retranslate)

    # ===== Test Key =====
    def _test_key(key: str, status_label: QLabel = None):
        if not key:
            if status_label:
                status_label.setText("")
            showWarning("Enter an API key first.")
            return
        from core.api_client import GeminiClient
        client = GeminiClient([key], "auto")
        res = client.test_key(key)
        if res.get("ok"):
            status_label.setText("\u2713")
            status_label.setStyleSheet("color: green; font-size: 16px; font-weight: bold;")
            log.info(f"Key test OK: {GeminiClient.detect_key_type(key)} -> {res.get('model')}")
        else:
            status_label.setText("\u2717")
            status_label.setStyleSheet("color: red; font-size: 16px; font-weight: bold;")
            log.warn(f"Key test FAIL: {res.get('error')}")

    # ===== Accept =====
    def on_accept():
        keys = [inp.text().strip() for inp in key_inputs]
        s.set("api_key", keys[0])
        s.set("api_key2", keys[1])
        s.set("api_key3", keys[2])
        s.set("model", model_cb.currentText())
        s.set("temperature", temp_spin.value())
        s.set("ui_lang", ui_lang_cb.currentText())
        s.set("learn_lang", learn_lang_cb.currentText())
        mw.ai_engine._reset_api_client()
        log.info("Settings dialog accepted")
        dialog.accept()

    buttons.accepted.connect(on_accept)
    buttons.rejected.connect(lambda: log.debug("Settings dialog cancelled"))
    dialog.exec()


gui_hooks.main_window_did_init.append(init_addon)
