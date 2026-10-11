"""
RogueByte GeoForensics Intelligence - Qt Styling
===============================================
Dark modern forensic cybersecurity theme for PySide6.
"""

DARK_THEME_QSS = """
QMainWindow {
    background-color: #0b0f19;
    color: #e2e8f0;
}

QWidget {
    background-color: #0b0f19;
    color: #e2e8f0;
    font-family: 'Segoe UI', Tahoma, Arial, sans-serif;
    font-size: 13px;
}

QTabWidget::pane {
    border: 1px solid #1e293b;
    background-color: #0f172a;
    border-radius: 6px;
    top: -1px;
}

QTabBar::tab {
    background: #111827;
    color: #94a3b8;
    padding: 10px 18px;
    margin-right: 4px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    border: 1px solid #1e293b;
    border-bottom: none;
    font-weight: 600;
}

QTabBar::tab:selected {
    background: #0f172a;
    color: #38bdf8;
    border-top: 2px solid #0ea5e9;
}

QTabBar::tab:hover {
    color: #f1f5f9;
}

QPushButton {
    background-color: #0284c7;
    color: #ffffff;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #0369a1;
}

QPushButton:pressed {
    background-color: #075985;
}

QPushButton#btn-danger {
    background-color: #dc2626;
}

QPushButton#btn-danger:hover {
    background-color: #b91c1c;
}

QPushButton#btn-success {
    background-color: #16a34a;
}

QPushButton#btn-success:hover {
    background-color: #15803d;
}

QPushButton#btn-secondary {
    background-color: #1e293b;
    color: #cbd5e1;
    border: 1px solid #334155;
}

QPushButton#btn-secondary:hover {
    background-color: #334155;
}

QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateTimeEdit {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 4px;
    padding: 6px 10px;
    color: #f8fafc;
    selection-background-color: #0ea5e9;
}

QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
    border: 1px solid #38bdf8;
}

QTableWidget, QTableView {
    background-color: #111827;
    alternate-background-color: #0f172a;
    border: 1px solid #1e293b;
    gridline-color: #1e293b;
    color: #f1f5f9;
    border-radius: 4px;
}

QHeaderView::section {
    background-color: #1e293b;
    color: #38bdf8;
    padding: 8px;
    border: 1px solid #0f172a;
    font-weight: bold;
    font-size: 12px;
}

QScrollBar:vertical {
    border: none;
    background: #0f172a;
    width: 10px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #334155;
    min-height: 20px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background: #475569;
}

QGroupBox {
    border: 1px solid #1e293b;
    border-radius: 6px;
    margin-top: 24px;
    padding-top: 15px;
    font-weight: bold;
    color: #38bdf8;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top right;
    padding: 0 10px;
    color: #38bdf8;
}

QStatusBar {
    background-color: #090d16;
    color: #64748b;
    border-top: 1px solid #1e293b;
}
"""
