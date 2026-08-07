from aqt import mw
from aqt.qt import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QCheckBox,
    QPushButton,
    QComboBox,
    QDoubleSpinBox,
    QDialogButtonBox,
    QScrollArea,
    QWidget
)
from core.logger import log
from core.i18n import t, load_strings
from core.languages import SUPPORTED_LANGUAGES, UI_LANGUAGES


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent or mw)
        self.s = mw.ai_engine.settings if hasattr(mw, "ai_engine") and mw.ai_engine else None
        self.current_ui_lang = self.s.get("ui_lang", "en") if self.s else "en"
        self.i18n_widgets = []
        self._init_ui()

    def _add_i18n_key(self, key: str) -> str:
        return load_strings(self.current_ui_lang).get(key, key)

    def _section(self, layout, text_key):
        lbl = QLabel(self._add_i18n_key(text_key))
        lbl.setStyleSheet("font-weight:600;font-size:13px;padding-top:6px;")
        layout.addWidget(lbl)
        self.i18n_widgets.append((lbl, text_key))
        return lbl

    def _init_ui(self):
        s = self.s
        self.setWindowTitle(t("settings.title", self.current_ui_lang))
        self.setMinimumWidth(620)
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # ===== API Keys =====
        self._section(layout, "settings.api_keys")

        keys_scroll = QScrollArea()
        keys_scroll.setWidgetResizable(True)
        keys_scroll.setMaximumHeight(350)
        keys_container = QWidget()
        keys_layout = QVBoxLayout(keys_container)

        self.key_inputs = []
        self.key_statuses = []

        stored_keys = s.get_api_keys() if s else [""] * 10

        for idx in range(10):
            row = QHBoxLayout()
            label_key = ("settings.key_n", idx + 1)
            lbl_text = self._add_i18n_key("settings.key_n").replace("{0}", str(idx + 1))
            lbl = QLabel(lbl_text)
            row.addWidget(lbl)
            self.i18n_widgets.append((lbl, label_key))

            inp = QLineEdit(stored_keys[idx])
            inp.setEchoMode(QLineEdit.EchoMode.Password)
            inp.setPlaceholderText(f"Gemini API key #{idx+1}")
            inp.textChanged.connect(lambda text, i=idx: self.key_statuses[i].setText(""))
            row.addWidget(inp, 1)

            status_label = QLabel("")
            status_label.setFixedWidth(45)
            row.addWidget(status_label)
            self.key_statuses.append(status_label)

            show_btn = QCheckBox(self._add_i18n_key("settings.show"))
            self.i18n_widgets.append((show_btn, "settings.show"))
            show_btn.toggled.connect(
                lambda checked, e=inp: e.setEchoMode(
                    QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
                )
            )
            row.addWidget(show_btn)

            test_btn = QPushButton(self._add_i18n_key("settings.test"))
            self.i18n_widgets.append((test_btn, "settings.test"))
            test_btn.setFixedWidth(50)
            test_btn.clicked.connect(
                lambda checked, k=inp, st=status_label: self._test_key(k.text().strip(), st)
            )
            row.addWidget(test_btn)

            keys_layout.addLayout(row)
            self.key_inputs.append(inp)

        keys_scroll.setWidget(keys_container)
        layout.addWidget(keys_scroll)

        # ===== Model =====
        self._section(layout, "settings.model")
        model_row = QHBoxLayout()
        model_lbl = QLabel(self._add_i18n_key("settings.model"))
        model_row.addWidget(model_lbl)
        self.i18n_widgets.append((model_lbl, "settings.model"))

        self.model_cb = QComboBox()
        self.model_cb.addItems(
            ["auto", "gemini-flash-latest", "gemini-3.6-flash", "gemma-4-31b-it", "gemini-3.1-flash-lite"]
        )
        if s:
            m_idx = self.model_cb.findText(s.get("model", "auto"))
            if m_idx >= 0:
                self.model_cb.setCurrentIndex(m_idx)
        model_row.addWidget(self.model_cb)

        temp_lbl = QLabel(self._add_i18n_key("settings.temperature"))
        model_row.addWidget(temp_lbl)
        self.i18n_widgets.append((temp_lbl, "settings.temperature"))

        self.temp_spin = QDoubleSpinBox()
        self.temp_spin.setRange(0.0, 1.0)
        self.temp_spin.setSingleStep(0.1)
        self.temp_spin.setValue(s.get("temperature", 0.7) if s else 0.7)
        self.temp_spin.setToolTip(self._add_i18n_key("settings.temperature_tip"))
        model_row.addWidget(self.temp_spin)
        layout.addLayout(model_row)

        # ===== Language =====
        self._section(layout, "settings.ui_lang")
        lang_row = QHBoxLayout()
        ui_lang_lbl = QLabel(self._add_i18n_key("settings.ui_lang"))
        lang_row.addWidget(ui_lang_lbl)
        self.i18n_widgets.append((ui_lang_lbl, "settings.ui_lang"))

        self.ui_lang_cb = QComboBox()
        self.ui_lang_cb.addItems(UI_LANGUAGES)
        self.ui_lang_cb.setCurrentText(self.current_ui_lang)
        lang_row.addWidget(self.ui_lang_cb)

        learn_lang_lbl = QLabel(self._add_i18n_key("settings.learn_lang"))
        lang_row.addWidget(learn_lang_lbl)
        self.i18n_widgets.append((learn_lang_lbl, "settings.learn_lang"))

        self.learn_lang_cb = QComboBox()
        for lang in SUPPORTED_LANGUAGES:
            name = f"{lang['native']} ({lang['names'].get(self.current_ui_lang, lang['native'])})"
            self.learn_lang_cb.addItem(name, lang["code"])

        if s:
            l_idx = self.learn_lang_cb.findData(s.get("learn_lang", "en"))
            if l_idx != -1:
                self.learn_lang_cb.setCurrentIndex(l_idx)
        lang_row.addWidget(self.learn_lang_cb)
        layout.addLayout(lang_row)

        # ===== Logs & Observability =====
        self._section(layout, "logs.title")
        log_row = QHBoxLayout()
        view_logs_btn = QPushButton(self._add_i18n_key("logs.view"))
        self.i18n_widgets.append((view_logs_btn, "logs.view"))
        view_logs_btn.clicked.connect(self._open_log_viewer)
        log_row.addWidget(view_logs_btn)
        log_row.addStretch()
        layout.addLayout(log_row)

        layout.addStretch()
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.ui_lang_cb.currentTextChanged.connect(self._retranslate)
        self.setLayout(layout)

    def _retranslate(self, lang_code: str):
        strings = load_strings(lang_code)
        for widget, key in self.i18n_widgets:
            if isinstance(key, tuple):
                text = strings.get(key[0], key[0]).replace("{0}", str(key[1]))
            else:
                text = strings.get(key, key)
            widget.setText(text)

        self.temp_spin.setToolTip(strings.get("settings.temperature_tip", "").replace("\\n", "\n"))
        self.setWindowTitle(strings.get("settings.title", "Settings"))
        selected = self.learn_lang_cb.currentData()
        self.learn_lang_cb.blockSignals(True)
        self.learn_lang_cb.clear()
        for item in SUPPORTED_LANGUAGES:
            label = f"{item['native']} ({item['names'].get(lang_code, item['native'])})"
            self.learn_lang_cb.addItem(label, item["code"])
        self.learn_lang_cb.setCurrentIndex(max(0, self.learn_lang_cb.findData(selected)))
        self.learn_lang_cb.blockSignals(False)

    def _test_key(self, key: str, status_label: QLabel = None):
        if not key:
            if status_label:
                status_label.setText("Empty")
                status_label.setStyleSheet("color: orange; font-weight: bold;")
            return

        if status_label:
            status_label.setText("...")
            status_label.setStyleSheet("color: gray; font-weight: bold;")

        selected_model = self.model_cb.currentText()

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

    def _on_accept(self):
        s = self.s
        if s:
            try:
                payload = {}
                for i in range(10):
                    payload[f"api_key{i+1}"] = self.key_inputs[i].text().strip()
                payload["model"] = self.model_cb.currentText()
                payload["temperature"] = self.temp_spin.value()
                payload["ui_lang"] = self.ui_lang_cb.currentText()
                payload["learn_lang"] = self.learn_lang_cb.currentData()

                result = s.set_many(payload)
                if not result.get("ok"):
                    from aqt.utils import showWarning
                    showWarning(f"Error saving settings: {result.get('message', 'Unknown error')}")
                    return

                changed = result.get("changed_keys", [])
                if hasattr(mw, "ai_engine") and mw.ai_engine:
                    if any(k.startswith("api_key") or k == "model" for k in changed):
                        mw.ai_engine._reset_api_client()
                        mw.ai_engine._gamemode_cache.clear()
                    elif any(k in ("temperature", "learn_lang") for k in changed):
                        mw.ai_engine._gamemode_cache.clear()
                log.info("Settings dialog accepted")
            except Exception as e:
                log.error(f"Error saving settings: {e}")

        self.accept()

    def _open_log_viewer(self):
        from ui.log_viewer import LogViewerDialog
        dialog = LogViewerDialog(self)
        dialog.exec()
