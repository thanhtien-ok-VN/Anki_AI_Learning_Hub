import json
import os
import platform
import sys
from typing import Optional

from aqt import mw
from aqt.qt import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QPlainTextEdit,
    QMessageBox,
    QApplication,
    QDesktopServices,
    QUrl,
    QFont,
)
from core.logger import log, read_flow_logs, clear_all_logs, LOG_PATH, FLOW_LOG_PATH, ADDON_PATH
from core.i18n import t


class LogViewerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent or mw)
        self.s = mw.ai_engine.settings if hasattr(mw, "ai_engine") and mw.ai_engine else None
        self.current_ui_lang = self.s.get("ui_lang", "en") if self.s else "en"
        self._init_ui()
        self._load_logs()

    def _init_ui(self):
        self.setWindowTitle(t("logs.title", self.current_ui_lang))
        self.resize(880, 580)
        layout = QVBoxLayout()
        layout.setSpacing(8)

        # Toolbar Lọc
        filter_row = QHBoxLayout()

        filter_row.addWidget(QLabel("Source:"))
        self.source_cb = QComboBox()
        self.source_cb.addItems([
            t("logs.source_flow", self.current_ui_lang),
            t("logs.source_main", self.current_ui_lang),
        ])
        filter_row.addWidget(self.source_cb)

        filter_row.addWidget(QLabel("Level:"))
        self.level_cb = QComboBox()
        self.level_cb.addItems(["ALL", "INFO", "WARN", "ERROR", "DEBUG", "FATAL"])
        filter_row.addWidget(self.level_cb)

        filter_row.addWidget(QLabel("Phase:"))
        self.phase_cb = QComboBox()
        self.phase_cb.addItems(["ALL", "CONNECT", "SYSTEM", "AI", "RENDER", "EVENT"])
        filter_row.addWidget(self.phase_cb)

        filter_row.addStretch()

        self.refresh_btn = QPushButton("🔄 Refresh")
        filter_row.addWidget(self.refresh_btn)

        layout.addLayout(filter_row)

        # Content Area Monospace
        self.text_edit = QPlainTextEdit()
        self.text_edit.setReadOnly(True)
        mono_font = QFont("Courier New" if platform.system() == "Windows" else "Monospace", 9)
        self.text_edit.setFont(mono_font)
        layout.addWidget(self.text_edit, 1)

        # Action Buttons
        btn_row = QHBoxLayout()

        self.copy_btn = QPushButton(t("logs.copy_report", self.current_ui_lang))
        self.copy_btn.setStyleSheet("font-weight: bold;")
        btn_row.addWidget(self.copy_btn)

        self.open_folder_btn = QPushButton(t("logs.open_folder", self.current_ui_lang))
        btn_row.addWidget(self.open_folder_btn)

        self.delete_btn = QPushButton(t("logs.delete", self.current_ui_lang))
        self.delete_btn.setStyleSheet("color: red;")
        btn_row.addWidget(self.delete_btn)

        btn_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)
        self.setLayout(layout)

        # Connect signals
        self.source_cb.currentIndexChanged.connect(self._load_logs)
        self.level_cb.currentIndexChanged.connect(self._load_logs)
        self.phase_cb.currentIndexChanged.connect(self._load_logs)
        self.refresh_btn.clicked.connect(self._load_logs)
        self.copy_btn.clicked.connect(self._copy_bug_report)
        self.open_folder_btn.clicked.connect(self._open_log_folder)
        self.delete_btn.clicked.connect(self._delete_logs)

    def _load_logs(self):
        source_idx = self.source_cb.currentIndex()
        level = self.level_cb.currentText()
        phase = self.phase_cb.currentText()

        if source_idx == 0:  # JSONL Flow Logs
            entries = read_flow_logs(limit=250, level=level, phase=phase)
            lines = []
            for e in entries:
                ts = e.get("ts", "")[:19].replace("T", " ")
                lvl = e.get("level", "INFO").ljust(5)
                phs = e.get("phase", "").ljust(7)
                gm = f"[{e.get('gamemode')}] " if e.get("gamemode") else ""
                dur = f" ({e.get('duration_ms')}ms)" if e.get("duration_ms") is not None else ""
                msg = e.get("message", "")
                extra = json.dumps(e.get("extra", {}), ensure_ascii=False) if e.get("extra") else ""
                lines.append(f"{ts} | {lvl} | {phs} | {gm}{msg}{dur} {extra}")
            self.text_edit.setPlainText("\n".join(lines) or "No flow logs recorded.")
        else:  # Text Log
            if not os.path.isfile(LOG_PATH):
                self.text_edit.setPlainText("No log file found.")
                return
            try:
                with open(LOG_PATH, "r", encoding="utf-8") as f:
                    content = f.read()
                self.text_edit.setPlainText(content[-50000:] or "Log file is empty.")
            except Exception as e:
                self.text_edit.setPlainText(f"Failed to read log file: {e}")

        # Scroll to bottom
        sb = self.text_edit.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _copy_bug_report(self):
        sys_info = {
            "OS": f"{platform.system()} {platform.release()} ({platform.machine()})",
            "Python": sys.version.split()[0],
            "Anki": getattr(mw, "ankiVersion", "Unknown"),
            "UI_Lang": self.current_ui_lang,
            "Learn_Lang": self.s.get("learn_lang") if self.s else "Unknown",
            "Model": self.s.get("model") if self.s else "auto",
            "Masked_Keys": self.s.get_masked_api_keys() if self.s else [],
        }

        recent_logs = read_flow_logs(limit=100)
        report = {
            "Diagnose_Report": "Anki AI Learning Hub System Diagnostics",
            "System_Info": sys_info,
            "Recent_Flow_Logs": recent_logs,
        }

        text = json.dumps(report, indent=2, ensure_ascii=False)
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        QMessageBox.information(
            self,
            "Report Copied",
            t("logs.copied", self.current_ui_lang),
        )

    def _open_log_folder(self):
        folder = os.path.join(ADDON_PATH, "user_files")
        os.makedirs(folder, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(folder))

    def _delete_logs(self):
        reply = QMessageBox.question(
            self,
            t("logs.delete", self.current_ui_lang),
            t("logs.confirm_delete", self.current_ui_lang),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            clear_all_logs()
            self._load_logs()
            QMessageBox.information(self, "Deleted", "All log files cleared successfully.")
