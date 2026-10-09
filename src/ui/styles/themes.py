"""
OptiCleaner v4.0 - Themes & Modern QSS Engine
Cyberpunk HUD, OLED Black, and Nord Slate stylesheets with neon accents and matte surfaces.
"""

CYBERPUNK_THEME = """
QMainWindow, QWidget#centralWidget {
    background-color: #0A0D14;
    color: #E2E8F0;
    font-family: 'Segoe UI', 'Inter', sans-serif;
}

QFrame#sidebarFrame {
    background-color: #0F1420;
    border-right: 1px solid #1E293B;
}

QPushButton.nav-btn {
    background-color: transparent;
    color: #94A3B8;
    border: none;
    border-radius: 8px;
    padding: 10px 16px;
    font-size: 13px;
    font-weight: 600;
    text-align: left;
}

QPushButton.nav-btn:hover {
    background-color: #1E293B;
    color: #00E5FF;
}

QPushButton.nav-btn:checked {
    background-color: #16243A;
    color: #00E5FF;
    border-left: 3px solid #00E5FF;
}

QPushButton.primary-btn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00E5FF, stop:1 #0091EA);
    color: #0A0D14;
    font-weight: 800;
    font-size: 13px;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
}

QPushButton.primary-btn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #33ECFF, stop:1 #29B6F6);
}

QPushButton.danger-btn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #F43F5E, stop:1 #E11D48);
    color: #FFFFFF;
    font-weight: 700;
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
}

QFrame.card {
    background-color: #131927;
    border: 1px solid #1E293B;
    border-radius: 12px;
}

QProgressBar {
    background-color: #1E293B;
    border: none;
    border-radius: 4px;
    height: 8px;
    text-align: center;
}

QProgressBar::chunk {
    background-color: #00E5FF;
    border-radius: 4px;
}

QTableWidget {
    background-color: #131927;
    gridline-color: #1E293B;
    border: 1px solid #1E293B;
    border-radius: 8px;
    color: #E2E8F0;
    selection-background-color: #1E3A5F;
}

QHeaderView::section {
    background-color: #0F1420;
    color: #94A3B8;
    padding: 8px;
    border: none;
    border-bottom: 1px solid #1E293B;
    font-weight: 700;
}
"""
