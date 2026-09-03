import sys
from pathlib import Path
from PySide6.QtCore import Qt, Signal, QUrl, QSettings, QTimer
from PySide6.QtGui import QPixmap, QImage, QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QSplitter,
    QFrame,
    QCheckBox,
    QFileDialog,
    QMessageBox,
    QDialog,
    QLineEdit,
)

from worker import TranscriptionWorker

REVIEW = 0.82
CHECK = 0.92
STYLE = """
QMainWindow{background:#f5f7fb}
QWidget{font-family:Segoe UI;color:#172033}
QFrame#card{background:white;border:1px solid #dfe3ea;border-radius:12px}
QPushButton#primary{background:#2563eb;color:white;border:0;border-radius:8px;padding:10px 18px;font-weight:600}
QPushButton#secondary{background:white;border:1px solid #cfd6e0;border-radius:8px;padding:10px 18px}
QProgressBar{border:0;border-radius:7px;background:#e8edf5;height:14px}
QProgressBar::chunk{background:#2563eb;border-radius:7px}
QTableWidget{background:white;border:1px solid #dfe3ea;border-radius:10px}
QHeaderView::section{background:#f7f8fa;border:0;border-bottom:1px solid #dfe3ea;padding:8px;font-weight:600}
"""


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("API Configuration")
        self.setFixedSize(450, 150)

        self.settings = QSettings("MySoftwareCo", "Transcribbl")

        layout = QVBoxLayout(self)

        self.info_label = QLabel("Enter your Google Gemini API Key:")
        layout.addWidget(self.info_label)

        self.key_input = QLineEdit()
        self.key_input.setEchoMode(QLineEdit.Password)
        self.key_input.setPlaceholderText("AIzaSy...")

        saved_key = self.settings.value("api_key", "")
        if saved_key:
            self.key_input.setText(saved_key)

        layout.addWidget(self.key_input)

        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.cancel_btn = QPushButton("Cancel")

        self.save_btn.clicked.connect(self.save_key)
        self.cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)

    def save_key(self):
        key = self.key_input.text().strip()
        if not key:
            QMessageBox.warning(self, "Error", "API Key cannot be empty.")
            return

        self.settings.setValue("api_key", key)
        self.accept()


class Card(QFrame):
    def __init__(self, title):
        super().__init__()
        self.setObjectName("card")
        l = QVBoxLayout(self)
        t = QLabel(title)
        t.setStyleSheet("color:#667085;font-size:12px")
        self.v = QLabel("—")
        self.v.setStyleSheet("font-size:26px;font-weight:700")
        self.s = QLabel("No data")
        self.s.setStyleSheet("color:#667085;font-size:11px")
        l.addWidget(t)
        l.addWidget(self.v)
        l.addWidget(self.s)

    def set(self, v, s):
        self.v.setText(v)
        self.s.setText(s)


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Transcribbl")
        self.resize(1450, 900)
        self.setStyleSheet(STYLE)

        self.path = None
        self.results = []
        self.output = None
        self.worker = None

        w = QWidget()
        self.setCentralWidget(w)
        o = QVBoxLayout(w)
        o.setContentsMargins(28, 24, 28, 24)
        o.setSpacing(18)

        h = QHBoxLayout()
        box = QVBoxLayout()
        title = QLabel("Transcribbl - Servidyne's Environmental Form Transcriber")
        title.setStyleSheet("font-size:25px;font-weight:700")
        sub = QLabel("Cloud-Based handwriting recognition • fixed-form extraction • confidence review")
        sub.setStyleSheet("color:#667085")
        box.addWidget(title)
        box.addWidget(sub)
        h.addLayout(box)
        h.addStretch()

        self.settings_btn = QPushButton("⚙ Settings")
        self.settings_btn.setObjectName("secondary")
        self.settings_btn.clicked.connect(self.open_settings)

        self.pick = QPushButton("Select Handwritten PDF")
        self.pick.setObjectName("secondary")
        self.pick.clicked.connect(self.select)

        self.run = QPushButton("Transcribe Form")
        self.run.setObjectName("primary")
        self.run.setEnabled(False)
        self.run.clicked.connect(self.start)

        h.addWidget(self.settings_btn)
        h.addWidget(self.pick)
        h.addWidget(self.run)
        o.addLayout(h)

        fc = QFrame()
        fc.setObjectName("card")
        fl = QVBoxLayout(fc)
        self.fn = QLabel("No form selected")
        self.fn.setStyleSheet("font-weight:600;font-size:14px")
        self.fd = QLabel("Select a PDF or image to begin.")
        self.fd.setStyleSheet("color:#667085")
        fl.addWidget(self.fn)
        fl.addWidget(self.fd)
        o.addWidget(fc)

        pc = QFrame()
        pc.setObjectName("card")
        pl = QVBoxLayout(pc)
        ph = QHBoxLayout()
        self.status = QLabel("Waiting for a form")
        self.pct = QLabel("0%")
        ph.addWidget(self.status)
        ph.addStretch()
        ph.addWidget(self.pct)
        self.bar = QProgressBar()
        pl.addLayout(ph)
        pl.addWidget(self.bar)
        o.addWidget(pc)

        m = QGridLayout()
        self.over = Card("OVERALL CONFIDENCE")
        self.high = Card("HIGH CONFIDENCE")
        self.med = Card("CHECK RECOMMENDED")
        self.low = Card("MANUAL REVIEW")
        for i, c in enumerate([self.over, self.high, self.med, self.low]):
            m.addWidget(c, 0, i)
        o.addLayout(m)

        sp = QSplitter(Qt.Horizontal)
        lc = QFrame()
        lc.setObjectName("card")
        ll = QVBoxLayout(lc)
        ll.addWidget(QLabel("<b>Recognized Fields</b>"))
        self.filter = QCheckBox("Show only fields requiring manual review")
        self.filter.stateChanged.connect(self.refresh)
        ll.addWidget(self.filter)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([
            "Page", "Field", "Row", "Recognized Text", "Confidence", "Status"
        ])
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        ll.addWidget(self.table)

        rc = QFrame()
        rc.setObjectName("card")
        rl = QVBoxLayout(rc)
        rl.addWidget(QLabel("<b>Form Preview</b>"))
        self.preview = QLabel("Aligned form preview will appear here.")
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setStyleSheet("color:#667085;background:#f7f8fa;border-radius:8px")
        rl.addWidget(self.preview, 1)

        sp.addWidget(lc)
        sp.addWidget(rc)
        sp.setSizes([820, 580])
        o.addWidget(sp, 1)

        foot = QHBoxLayout()
        self.msg = QLabel("Results will appear here.")
        self.msg.setStyleSheet("color:#667085")
        self.open = QPushButton("Open Excel Output")
        self.open.setObjectName("primary")
        self.open.setEnabled(False)
        self.open.clicked.connect(self.open_excel)
        foot.addWidget(self.msg)
        foot.addStretch()
        foot.addWidget(self.open)
        o.addLayout(foot)

        settings = QSettings("MySoftwareCo", "Transcribbl")
        if not settings.value("api_key", ""):
            QTimer.singleShot(400, self.open_settings)

    def open_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec()

    def select(self):
        p, _ = QFileDialog.getOpenFileName(
            self,
            "Select Handwritten Form",
            "",
            "Form Files (*.pdf *.png *.jpg *.jpeg *.tif *.tiff)",
        )
        if not p:
            return
        self.path = p
        q = Path(p)
        self.fn.setText(q.name)
        self.fd.setText(
            f"{q.suffix.upper()[1:]} • {q.stat().st_size/1048576:.1f} MB • Ready for cloud transcription"
        )
        self.run.setEnabled(True)
        self.status.setText("Ready to transcribe")

    def start(self):
        settings = QSettings("MySoftwareCo", "Transcribbl")
        if not settings.value("api_key", ""):
            QMessageBox.warning(
                self,
                "API Key Missing",
                "Please configure your Google Gemini API Key in Settings before transcribing.",
            )
            self.open_settings()
            return

        self.output = str(Path(self.path).with_name(Path(self.path).stem + "_transcribed.xlsx"))
        self.run.setEnabled(False)
        self.pick.setEnabled(False)
        self.worker = TranscriptionWorker(self.path, self.output)
        self.worker.progress.connect(self.progress)
        self.worker.status.connect(self.status.setText)
        self.worker.preview_ready.connect(self.show_preview)
        self.worker.completed.connect(self.done)
        self.worker.failed.connect(self.fail)
        self.worker.start()

    def progress(self, n, msg):
        self.bar.setValue(n)
        self.pct.setText(f"{n}%")
        self.status.setText(msg)

    def show_preview(self, img):
        rgb = img[:, :, ::-1].copy()
        h, w, _ = rgb.shape
        qi = QImage(rgb.data, w, h, 3 * w, QImage.Format_RGB888)
        self.preview.setPixmap(
            QPixmap.fromImage(qi).scaled(
                self.preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
        )

    def done(self, results, review, output):
        self.results = results
        self.output = output
        cs = [x["confidence"] for x in results]
        avg = sum(cs) / len(cs) if cs else 0
        hi = sum(c >= CHECK for c in cs)
        med = sum(REVIEW <= c < CHECK for c in cs)
        low = sum(c < REVIEW for c in cs)

        self.over.set(f"{avg:.1%}", "Mean model confidence")
        self.high.set(str(hi), f"of {len(cs)} fields")
        self.med.set(str(med), "Worth a quick check")
        self.low.set(str(low), "Requires intervention")

        self.refresh()
        self.run.setEnabled(True)
        self.pick.setEnabled(True)
        self.open.setEnabled(True)
        self.msg.setText(f"Excel created • {len(review)} items flagged for review")
        self.status.setText("Transcription complete")
        self.bar.setValue(100)
        self.pct.setText("100%")

    def fail(self, e):
        self.run.setEnabled(True)
        self.pick.setEnabled(True)
        QMessageBox.critical(self, "Transcription Error", e)

    def refresh(self):
        rows = [
            x
            for x in self.results
            if not self.filter.isChecked() or x["confidence"] < REVIEW
        ]
        self.table.setRowCount(len(rows))
        for r, x in enumerate(rows):
            c = x["confidence"]
            status = "MANUAL REVIEW" if c < REVIEW else ("CHECK" if c < CHECK else "HIGH")
            vals = [
                str(x.get("page", "")),
                x["field"].replace("_", " ").title(),
                "—" if x.get("row") is None else str(x["row"] + 1),
                x.get("text") or "—",
                f"{c:.1%}",
                status,
            ]
            for col, v in enumerate(vals):
                self.table.setItem(r, col, QTableWidgetItem(v))

    def open_excel(self):
        if self.output:
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.output))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    x = Window()
    x.show()
    sys.exit(app.exec())