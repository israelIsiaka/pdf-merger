"""
QSS stylesheet generator for PDF Merger.
Accepts a colors dict and font family string from ThemeManager
and returns the full application stylesheet as a string.
"""
from typing import Dict


def build_stylesheet(c: Dict[str, str], font_family: str) -> str:
    return f"""
    QMainWindow, QWidget {{
        background-color: {c['bg']};
        color: {c['fg']};
        font-family: "{font_family}";
        font-size: 13px;
    }}

    QLabel#appTitle {{
        font-size: 22px;
        font-weight: bold;
        color: {c['label_main']};
        padding-bottom: 4px;
    }}
    QLabel#fieldLabel {{
        font-size: 12px;
        font-weight: bold;
        color: {c['label_main']};
    }}
    QLabel#sectionTitle {{
        font-size: 14px;
        font-weight: bold;
        color: {c['label_main']};
    }}
    QLabel#descLabel {{
        font-size: 12px;
        color: {c['label_secondary']};
    }}
    QLabel#hintLabel {{
        font-size: 11px;
        color: {c['label_secondary']};
    }}
    QLabel#statusLabel {{
        font-size: 11px;
        color: {c['label_main']};
    }}
    QLabel#errorLabel {{
        font-size: 11px;
        color: {c['error']};
    }}
    QLabel#dialogPrompt {{
        font-size: 13px;
        color: {c['label_main']};
    }}

    /* Peep output info panel */
    QWidget#outPanel {{
        background-color: {c['tree_alt_bg']};
        border-radius: 8px;
    }}

    /* Tabs */
    QTabWidget#mainTabs::pane {{
        background-color: {c['bg']};
        border: none;
    }}
    QTabWidget#mainTabs QTabBar::tab {{
        background-color: {c['secondary_btn_bg']};
        color: {c['label_main']};
        padding: 10px 32px;
        border: none;
        border-radius: 6px 6px 0px 0px;
        margin-right: 2px;
        font-size: 12px;
        font-weight: bold;
        min-width: 100px;
    }}
    QTabWidget#mainTabs QTabBar::tab:selected {{
        background-color: {c['bg']};
        color: {c['button_bg']};
    }}
    QTabWidget#mainTabs QTabBar::tab:hover:!selected {{
        background-color: {c['secondary_btn_hover']};
    }}
    QWidget#tabPage {{
        background-color: {c['bg']};
    }}

    /* Primary action button (large CTA) */
    QPushButton#primaryBtn {{
        background-color: {c['button_bg']};
        color: {c['button_fg']};
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        font-size: 13px;
        font-weight: bold;
    }}
    QPushButton#primaryBtn:hover {{
        background-color: {c['button_hover']};
    }}
    QPushButton#primaryBtn:pressed {{
        background-color: {c['button_bg']};
    }}
    QPushButton#primaryBtn:disabled {{
        background-color: {c['border']};
        color: {c['label_secondary']};
    }}

    /* Action button (top-row coloured buttons) */
    QPushButton#actionBtn {{
        background-color: {c['button_bg']};
        color: {c['button_fg']};
        border: none;
        border-radius: 8px;
        padding: 8px 16px;
        font-size: 12px;
        font-weight: bold;
    }}
    QPushButton#actionBtn:hover {{
        background-color: {c['button_hover']};
    }}
    QPushButton#actionBtn:pressed {{
        background-color: {c['button_bg']};
    }}
    QPushButton#actionBtn:disabled {{
        background-color: {c['border']};
        color: {c['label_secondary']};
    }}

    /* Secondary button */
    QPushButton#secondaryBtn {{
        background-color: {c['secondary_btn_bg']};
        color: {c['secondary_btn_fg']};
        border: none;
        border-radius: 8px;
        padding: 8px 16px;
        font-size: 12px;
        font-weight: bold;
    }}
    QPushButton#secondaryBtn:hover {{
        background-color: {c['secondary_btn_hover']};
    }}
    QPushButton#secondaryBtn:pressed {{
        background-color: {c['secondary_btn_bg']};
    }}

    /* Input fields */
    QLineEdit#inputField {{
        background-color: {c['secondary_bg']};
        color: {c['fg']};
        border: 1px solid {c['border']};
        border-radius: 6px;
        padding: 8px 12px;
        font-size: 12px;
        selection-background-color: {c['button_bg']};
    }}
    QLineEdit#inputField:focus {{
        border: 2px solid {c['button_bg']};
        padding: 7px 11px;
    }}

    /* Spinbox */
    QSpinBox#spinBox {{
        background-color: {c['secondary_bg']};
        color: {c['fg']};
        border: 1px solid {c['border']};
        border-radius: 6px;
        padding: 6px 8px;
        font-size: 12px;
    }}
    QSpinBox#spinBox:focus {{
        border: 2px solid {c['button_bg']};
    }}
    QSpinBox#spinBox::up-button,
    QSpinBox#spinBox::down-button {{
        width: 18px;
        border: none;
        background: transparent;
    }}

    /* Sort combo */
    QComboBox#sortCombo {{
        background-color: {c['secondary_bg']};
        color: {c['fg']};
        border: 1px solid {c['border']};
        border-radius: 6px;
        padding: 5px 10px;
        font-size: 12px;
        min-width: 130px;
    }}
    QComboBox#sortCombo:focus {{
        border: 2px solid {c['button_bg']};
    }}
    QComboBox#sortCombo::drop-down {{
        border: none;
        width: 20px;
    }}
    QComboBox#sortCombo QAbstractItemView {{
        background-color: {c['listbox_bg']};
        color: {c['listbox_fg']};
        border: 1px solid {c['border']};
        selection-background-color: {c['listbox_select']};
        selection-color: #ffffff;
        outline: none;
    }}

    /* File list */
    QTreeWidget#fileList {{
        background-color: {c['listbox_bg']};
        alternate-background-color: {c['tree_alt_bg']};
        color: {c['listbox_fg']};
        border: none;
        border-radius: 10px;
        outline: none;
        font-size: 12px;
    }}
    QTreeWidget#fileList::item {{
        padding: 6px 4px;
        border: none;
    }}
    QTreeWidget#fileList::item:selected {{
        background-color: {c['listbox_select']};
        color: #ffffff;
        border-radius: 4px;
    }}
    QTreeWidget#fileList::indicator {{
        width: 15px;
        height: 15px;
        border: 2px solid {c['border']};
        border-radius: 3px;
        background-color: transparent;
    }}
    QTreeWidget#fileList::indicator:checked {{
        background-color: {c['button_bg']};
        border-color: {c['button_bg']};
    }}
    QTreeWidget#fileList::indicator:hover {{
        border-color: {c['button_hover']};
    }}
    QTreeWidget#fileList QHeaderView::section {{
        background-color: {c['tree_header_bg']};
        color: {c['tree_header_fg']};
        border: none;
        padding: 7px 8px;
        font-size: 11px;
        font-weight: bold;
    }}

    /* History list */
    QTreeWidget#historyList {{
        background-color: {c['listbox_bg']};
        alternate-background-color: {c['tree_alt_bg']};
        color: {c['listbox_fg']};
        border: none;
        border-radius: 10px;
        outline: none;
        font-size: 12px;
    }}
    QTreeWidget#historyList::item {{
        padding: 5px 4px;
        border: none;
    }}
    QTreeWidget#historyList::item:selected {{
        background-color: {c['listbox_select']};
        color: #ffffff;
    }}
    QTreeWidget#historyList QHeaderView::section {{
        background-color: {c['tree_header_bg']};
        color: {c['tree_header_fg']};
        border: none;
        padding: 7px 8px;
        font-size: 11px;
        font-weight: bold;
    }}

    /* Progress bars */
    QProgressBar#progressBar {{
        background-color: {c['secondary_bg']};
        border: none;
        border-radius: 3px;
    }}
    QProgressBar#progressBar::chunk {{
        background-color: {c['button_bg']};
        border-radius: 3px;
    }}

    /* Scrollbars */
    QScrollBar:vertical {{
        background-color: {c['bg']};
        width: 8px;
        border: none;
    }}
    QScrollBar::handle:vertical {{
        background-color: {c['border']};
        border-radius: 4px;
        min-height: 24px;
    }}
    QScrollBar::handle:vertical:hover {{
        background-color: {c['label_secondary']};
    }}
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{ height: 0px; }}
    QScrollBar:horizontal {{
        background-color: {c['bg']};
        height: 8px;
        border: none;
    }}
    QScrollBar::handle:horizontal {{
        background-color: {c['border']};
        border-radius: 4px;
        min-width: 24px;
    }}
    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {{ width: 0px; }}

    /* Help / FAQ tab */
    QLabel#helpSection {{
        font-size: 14px;
        font-weight: bold;
        color: {c['button_bg']};
        padding-bottom: 2px;
        border-bottom: 2px solid {c['button_bg']};
    }}
    QLabel#helpQ {{
        font-size: 12px;
        font-weight: bold;
        color: {c['label_main']};
    }}
    QLabel#helpA {{
        font-size: 12px;
        color: {c['label_secondary']};
        padding-left: 12px;
    }}
    QTreeWidget#helpTable {{
        background-color: {c['listbox_bg']};
        alternate-background-color: {c['tree_alt_bg']};
        color: {c['listbox_fg']};
        border: none;
        border-radius: 8px;
        outline: none;
        font-size: 12px;
    }}
    QTreeWidget#helpTable::item {{
        padding: 6px 4px;
        border: none;
    }}
    QTreeWidget#helpTable::item:selected {{
        background-color: transparent;
        color: {c['listbox_fg']};
    }}
    QTreeWidget#helpTable QHeaderView::section {{
        background-color: {c['tree_header_bg']};
        color: {c['button_bg']};
        border: none;
        padding: 7px 8px;
        font-size: 11px;
        font-weight: bold;
    }}
    QScrollArea#helpScroll {{
        background-color: {c['bg']};
        border: none;
    }}

    /* Password show/hide toggle */
    QPushButton#eyeBtn {{
        background-color: {c['secondary_btn_bg']};
        color: {c['label_secondary']};
        border: none;
        border-radius: 6px;
        padding: 0px 8px;
        font-size: 11px;
        font-weight: bold;
    }}
    QPushButton#eyeBtn:hover {{
        background-color: {c['secondary_btn_hover']};
        color: {c['label_main']};
    }}
    QPushButton#eyeBtn:checked {{
        background-color: {c['secondary_btn_hover']};
        color: {c['button_bg']};
    }}

    /* Dialogs */
    QDialog {{ background-color: {c['bg']}; }}
    QMessageBox {{ background-color: {c['bg']}; }}
    QMessageBox QPushButton {{
        background-color: {c['secondary_btn_bg']};
        color: {c['secondary_btn_fg']};
        border: none;
        border-radius: 6px;
        padding: 6px 20px;
        font-weight: bold;
        min-width: 80px;
    }}
    QMessageBox QPushButton:hover {{
        background-color: {c['secondary_btn_hover']};
    }}
    QMessageBox QPushButton:default {{
        background-color: {c['button_bg']};
        color: {c['button_fg']};
    }}
    QMessageBox QPushButton:default:hover {{
        background-color: {c['button_hover']};
    }}
    """
