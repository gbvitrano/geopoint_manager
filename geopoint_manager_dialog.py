#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script QGIS - GeoPoint Manager v5.1
Plugin per creare layer di punti da sorgenti dati con coordinate
NOVITÀ v5.1: Fix caricamento Google Sheets su QGIS 4 (download via urllib + salvataggio GeoPackage),
             aggiornamento manuale on-demand, compatibilità QGIS 3 (Qt5/PyQt5) e QGIS 4 (Qt6/PyQt6)
"""

import os
import sqlite3
import urllib.request
import urllib.error
import tempfile
from qgis.core import Qgis

# --- Rilevazione versione QGIS per compatibilità Qt5/Qt6 ---
_QGIS4 = Qgis.versionInt() >= 40000

if _QGIS4:
    from qgis.PyQt.QtCore import QMetaType, Qt, QSize, pyqtSignal, QMargins, QTimer
    _FIELD_INT    = QMetaType.Type.Int
    _FIELD_STRING = QMetaType.Type.QString
else:
    from qgis.PyQt.QtCore import QVariant, Qt, QSize, pyqtSignal, QMargins, QTimer
    _FIELD_INT    = QVariant.Int
    _FIELD_STRING = QVariant.String

from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QLineEdit, QTextEdit, QProgressBar,
    QTabWidget, QWidget, QFormLayout, QGroupBox, QGridLayout,
    QScrollArea, QMessageBox, QFileDialog, QRadioButton,
    QStyleOptionGroupBox, QStyle, QCheckBox, QTextBrowser,
    QListWidget, QListWidgetItem, QFrame, QSizePolicy
)
from qgis.PyQt.QtGui import QFont, QIcon, QCursor
from qgis.core import (
    QgsProcessing, QgsProcessingException, QgsProcessingAlgorithm,
    QgsProcessingProvider, QgsFeature, QgsFields, QgsField,
    QgsGeometry, QgsPointXY, QgsWkbTypes, QgsProject, QgsVectorLayer,
    QgsVectorFileWriter, QgsCoordinateReferenceSystem, QgsMessageLog,
    Qgis, QgsApplication
)
from qgis.gui import QgsProjectionSelectionWidget
from qgis.utils import iface

# _WRITER_OK definito dopo l'import di QgsVectorFileWriter
if _QGIS4:
    _WRITER_OK = QgsVectorFileWriter.WriterError.NoError
else:
    _WRITER_OK = QgsVectorFileWriter.NoError


class _Theme:
    """Palette adattiva per tema chiaro/scuro di QGIS.
    Chiamare _Theme.setup() prima di creare qualsiasi widget."""

    dark        = False
    # testo
    text_muted  = "#666666"
    text_subtle = "#888888"
    # accento/link
    accent      = "#2196F3"
    accent_dark = "#1976D2"
    # pulsanti icona (neutri)
    btn_bg      = "#f0f0f0"
    btn_hover   = "#e0e0e0"
    btn_pressed = "#d0d0d0"
    btn_border  = "#dddddd"
    # sfondi speciali
    code_bg     = "#f5f5f5"
    card_bg     = "#f8f9fa"
    card_border = "#dee2e6"
    # etichetta CRS
    crs_color   = "#1565C0"
    # titolo dialogo info
    info_title  = "#2196F3"
    # stato disabilitato
    disabled_bg = "#cccccc"
    disabled_fg = "#666666"

    @classmethod
    def setup(cls):
        from qgis.PyQt.QtWidgets import QApplication
        from qgis.PyQt.QtGui import QPalette
        app = QApplication.instance()
        if app:
            try:
                bg = app.palette().color(QPalette.ColorRole.Window)
            except AttributeError:
                bg = app.palette().color(QPalette.Window)
            cls.dark = bg.lightness() < 128
        if cls.dark:
            cls.text_muted  = "#aaaaaa"
            cls.text_subtle = "#909090"
            cls.accent      = "#64B5F6"
            cls.accent_dark = "#42A5F5"
            cls.btn_bg      = "#3a3a3a"
            cls.btn_hover   = "#484848"
            cls.btn_pressed = "#555555"
            cls.btn_border  = "#555555"
            cls.code_bg     = "#2a2a2a"
            cls.card_bg     = "#252525"
            cls.card_border = "#4a4a4a"
            cls.crs_color   = "#64B5F6"
            cls.info_title  = "#64B5F6"
            cls.disabled_bg = "#484848"
            cls.disabled_fg = "#888888"


_Theme.setup()


class CollapsibleGroupBox(QGroupBox):
    """GroupBox collassabile personalizzato con interfaccia migliorata"""
    
    # Segnale emesso quando lo stato cambia
    toggled = pyqtSignal(bool)
    
    def __init__(self, title="", parent=None):
        super().__init__(title, parent)
        
        # Rimuovi il checkbox - non più checkable
        self.setCheckable(False)
        
        # Stato iniziale: chiuso
        self._is_expanded = False
        
        # Salva il titolo base
        self.base_title = title
        
        # Imposta il cursore a mano per indicare che è cliccabile
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        # Aggiorna il titolo con icona iniziale (chiuso)
        self.update_title()
        
        # Stile: bordo rimosso, solo titolo cliccabile visibile
        self.setStyleSheet(f"""
            QGroupBox {{
                border: none;
                margin-top: 18px;
                padding-top: 0px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                font-weight: bold;
                color: {_Theme.accent};
                padding: 2px 4px;
            }}
            QGroupBox::title:hover {{
                color: {_Theme.accent_dark};
                text-decoration: underline;
            }}
        """)
        
        # Nascondi il contenuto inizialmente
        QTimer.singleShot(0, self._hide_content)
        
    def _hide_content(self):
        """Nasconde il contenuto dopo l'inizializzazione"""
        self.set_content_visible(False)
        
    def update_title(self):
        """Aggiorna il titolo con icona indicativa dello stato"""
        if self._is_expanded:
            # Aperto: usa simbolo "meno" o freccia verso il basso
            icon = "⌄"  # Alternativa più moderna: "−" o "▾"
        else:
            # Chiuso: usa simbolo "più" o freccia verso destra
            icon = "⏵"  # Alternativa più moderna: "+" o "▸"
            
        self.setTitle(f"{icon} {self.base_title}")
        
    def set_content_visible(self, visible):
        """Mostra/nasconde il contenuto del group box"""
        for child in self.findChildren(QWidget):
            # Nascondi solo i widget figli diretti
            if child.parent() == self:
                child.setVisible(visible)
                
    def mousePressEvent(self, event):
        """Gestisce il click sul titolo per aprire/chiudere"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Crea un'opzione di stile per il GroupBox
            option = QStyleOptionGroupBox()
            self.initStyleOption(option)

            # Ottieni il rettangolo del titolo usando l'opzione di stile corretta
            title_rect = self.style().subControlRect(
                QStyle.ComplexControl.CC_GroupBox,
                option,
                QStyle.SubControl.SC_GroupBoxLabel,
                self
            )
            
            # Aggiungi un margine per rendere l'area cliccabile più grande
            margins = QMargins(5, 5, 5, 5)
            if title_rect.marginsAdded(margins).contains(event.pos()):
                self.toggle_expanded()
            
        super().mousePressEvent(event)
        
    def toggle_expanded(self):
        """Cambia lo stato aperto/chiuso"""
        self._is_expanded = not self._is_expanded
        self.set_content_visible(self._is_expanded)
        self.update_title()
        
        # Emetti il segnale
        self.toggled.emit(self._is_expanded)
        
    def setExpanded(self, expanded):
        """Imposta lo stato aperto/chiuso programmaticamente"""
        if self._is_expanded != expanded:
            self._is_expanded = expanded
            self.set_content_visible(expanded)
            self.update_title()
            self.toggled.emit(expanded)
            
    def isExpanded(self):
        """Restituisce se è espanso"""
        return self._is_expanded
        
    def setChecked(self, checked):
        """Compatibilità con il codice esistente"""
        self.setExpanded(checked)
        
    def isChecked(self):
        """Compatibilità con il codice esistente"""
        return self.isExpanded()


class CoordinateFieldsDialog(QDialog):
    """Dialog per la selezione dei campi coordinate e delle colonne da caricare."""

    def __init__(self, available_fields, parent=None):
        super().__init__(parent)
        self.available_fields = available_fields
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Seleziona Campi Coordinate e Colonne")
        self.setMinimumSize(460, 420)
        self.resize(460, 520)

        layout = QVBoxLayout()

        # Titolo
        title = QLabel("Seleziona i campi per le coordinate:")
        title_font = QFont()
        title_font.setPointSize(11)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Info campi
        info_label = QLabel(
            f"Campi disponibili: {', '.join(self.available_fields[:5])}"
            f"{'...' if len(self.available_fields) > 5 else ''}"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet(f"color: {_Theme.text_muted}; font-size: 9pt; margin-bottom: 4px;")
        layout.addWidget(info_label)

        # Form: Lat / Lon
        form_layout = QFormLayout()
        self.lat_combo = QComboBox()
        self.lat_combo.addItems(self.available_fields)
        form_layout.addRow("Campo Latitudine (Y):", self.lat_combo)
        self.lon_combo = QComboBox()
        self.lon_combo.addItems(self.available_fields)
        form_layout.addRow("Campo Longitudine (X):", self.lon_combo)
        layout.addLayout(form_layout)

        note_label = QLabel("I valori devono essere coordinate decimali (es: 45.123, 12.456)")
        note_label.setWordWrap(True)
        note_label.setStyleSheet(f"color: {_Theme.text_subtle}; font-size: 8pt; font-style: italic; margin: 6px 0;")
        layout.addWidget(note_label)

        # Separatore
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine if _QGIS4 else QFrame.HLine)
        sep.setStyleSheet(f"color: {_Theme.card_border};")
        layout.addWidget(sep)

        # Sezione selezione colonne
        col_title = QLabel("Colonne da includere nel layer virtuale:")
        col_title_font = QFont()
        col_title_font.setBold(True)
        col_title.setFont(col_title_font)
        layout.addWidget(col_title)

        col_note = QLabel("Deseleziona le colonne che non ti servono. I campi coordinate sono sempre inclusi.")
        col_note.setWordWrap(True)
        col_note.setStyleSheet(f"color: {_Theme.text_muted}; font-size: 8pt; margin-bottom: 4px;")
        layout.addWidget(col_note)

        # "Seleziona tutte" checkbox
        self._select_all_cb = QCheckBox("Seleziona tutte")
        self._select_all_cb.setChecked(True)
        self._select_all_cb.stateChanged.connect(self._on_select_all_changed)
        layout.addWidget(self._select_all_cb)

        # Lista colonne con checkbox
        self._col_list = QListWidget()
        self._col_list.setMinimumHeight(140)
        self._col_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #aaaaaa;
                border-radius: 4px;
                background-color: #ffffff;
                color: #111111;
            }
            QListWidget::item {
                color: #111111;
                background-color: #ffffff;
                padding: 2px 4px;
            }
            QListWidget::item:hover {
                background-color: #e3f2fd;
                color: #111111;
            }
        """)
        for name in self.available_fields:
            item = QListWidgetItem(name)
            item.setFlags(item.flags() | _Qt_ItemUserCheckable | _Qt_ItemEnabled)
            item.setCheckState(_Qt_Checked)
            self._col_list.addItem(item)
        self._col_list.itemChanged.connect(self._on_col_item_changed)
        layout.addWidget(self._col_list)

        # Contatore
        self._col_count_label = QLabel(f"{len(self.available_fields)} colonne selezionate")
        self._col_count_label.setStyleSheet("font-size: 9pt; font-weight: bold;")
        layout.addWidget(self._col_count_label)

        # Pulsanti
        button_layout = QHBoxLayout()
        self.auto_btn = QPushButton("Auto-detect coordinate")
        self.auto_btn.clicked.connect(self.auto_detect_fields)
        button_layout.addWidget(self.auto_btn)
        button_layout.addStretch()
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self.accept)
        self.ok_btn.setDefault(True)
        button_layout.addWidget(self.ok_btn)
        self.cancel_btn = QPushButton("Annulla")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)
        self.auto_detect_fields()

    def _on_select_all_changed(self, state):
        checked = (state == _Qt_Checked)
        self._col_list.blockSignals(True)
        for i in range(self._col_list.count()):
            self._col_list.item(i).setCheckState(_Qt_Checked if checked else _Qt_Unchecked)
        self._col_list.blockSignals(False)
        self._update_col_count()

    def _on_col_item_changed(self, _item):
        self._col_list.blockSignals(True)
        n = sum(1 for i in range(self._col_list.count())
                if self._col_list.item(i).checkState() == _Qt_Checked)
        total = self._col_list.count()
        self._select_all_cb.blockSignals(True)
        self._select_all_cb.setCheckState(
            _Qt_Checked if n == total else
            _Qt_Unchecked if n == 0 else
            _Qt_PartiallyChecked
        )
        self._select_all_cb.blockSignals(False)
        self._col_list.blockSignals(False)
        self._update_col_count()

    def _update_col_count(self):
        n = sum(1 for i in range(self._col_list.count())
                if self._col_list.item(i).checkState() == _Qt_Checked)
        self._col_count_label.setText(f"{n} colonne selezionate")

    def auto_detect_fields(self):
        """Rileva automaticamente i campi coordinate."""
        lat_keywords = ['lat', 'latitude', 'y', 'northing', 'Lat']
        lon_keywords = ['lon', 'lng', 'longitude', 'x', 'easting', 'long', 'Long']
        lat_field = lon_field = None
        for field in self.available_fields:
            fl = field.lower()
            if not lat_field and any(k.lower() in fl for k in lat_keywords):
                lat_field = field
            if not lon_field and any(k.lower() in fl for k in lon_keywords):
                lon_field = field
            if lat_field and lon_field:
                break
        if lat_field:
            self.lat_combo.setCurrentIndex(self.available_fields.index(lat_field))
        if lon_field:
            self.lon_combo.setCurrentIndex(self.available_fields.index(lon_field))

    def get_selected_fields(self):
        """Restituisce (lat_field, lon_field)."""
        return self.lat_combo.currentText(), self.lon_combo.currentText()

    def get_selected_columns(self):
        """Restituisce la lista delle colonne selezionate (sempre include X/Y)."""
        selected = [self._col_list.item(i).text()
                    for i in range(self._col_list.count())
                    if self._col_list.item(i).checkState() == _Qt_Checked]
        # Garantisce che i campi coordinate ci siano sempre
        lat = self.lat_combo.currentText()
        lon = self.lon_combo.currentText()
        for f in (lat, lon):
            if f and f not in selected:
                selected.append(f)
        return selected if selected else None


class RefreshSourcesDialog(QDialog):
    """Dialog che mostra le sorgenti registrate nel GeoPackage e permette di aggiornarle."""

    def __init__(self, sources, parent=None):
        # sources: list of (layer_name, url, last_updated)
        super().__init__(parent)
        self.setWindowTitle("Aggiorna sorgenti Google Sheets")
        self.setMinimumWidth(600)
        self._checkboxes = []
        self._setup_ui(sources)

    def _setup_ui(self, sources):
        layout = QVBoxLayout()

        header = QLabel(f"<b>{len(sources)} sorgent{'e' if len(sources)==1 else 'i'} registrat{'a' if len(sources)==1 else 'e'} nel GeoPackage.</b><br>"
                        "Seleziona i layer da risincronizzare con Google Sheets:")
        header.setWordWrap(True)
        layout.addWidget(header)

        # Un checkbox per ogni sorgente
        for layer_name, url, last_updated in sources:
            short_url = url[:70] + "..." if len(url) > 70 else url
            cb = QCheckBox(f"  {layer_name}")
            cb.setChecked(True)
            cb.setToolTip(f"URL: {url}\nUltimo aggiornamento: {last_updated or 'n/d'}")
            # etichetta URL sotto il checkbox
            url_lbl = QLabel(f"    <span style='color:{_Theme.text_muted}; font-size:8pt;'>{short_url}</span>")
            url_lbl.setTextFormat(Qt.TextFormat.RichText)
            layout.addWidget(cb)
            layout.addWidget(url_lbl)
            self._checkboxes.append((cb, layer_name, url))

        layout.addSpacing(8)

        btn_layout = QHBoxLayout()
        select_all_btn = QPushButton("Seleziona tutti")
        select_all_btn.clicked.connect(lambda: [cb.setChecked(True) for cb, *_ in self._checkboxes])
        select_none_btn = QPushButton("Deseleziona tutti")
        select_none_btn.clicked.connect(lambda: [cb.setChecked(False) for cb, *_ in self._checkboxes])
        btn_layout.addWidget(select_all_btn)
        btn_layout.addWidget(select_none_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        layout.addSpacing(4)

        action_layout = QHBoxLayout()
        update_btn = QPushButton("↻  Aggiorna selezionati")
        update_btn.setStyleSheet(f"background-color:#FF9800; color:white; font-weight:bold; padding:6px 14px; border:none; border-radius:4px;")
        update_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Annulla")
        cancel_btn.clicked.connect(self.reject)
        action_layout.addStretch()
        action_layout.addWidget(update_btn)
        action_layout.addWidget(cancel_btn)
        layout.addLayout(action_layout)

        self.setLayout(layout)

    def get_selected(self):
        """Restituisce lista di (layer_name, url) per i checkbox selezionati."""
        return [(name, url) for cb, name, url in self._checkboxes if cb.isChecked()]


# Costanti Qt compatibili Qt5/Qt6
if _QGIS4:
    _Qt_Checked          = Qt.CheckState.Checked
    _Qt_Unchecked        = Qt.CheckState.Unchecked
    _Qt_PartiallyChecked = Qt.CheckState.PartiallyChecked
    _Qt_ItemUserCheckable = Qt.ItemFlag.ItemIsUserCheckable
    _Qt_ItemEnabled       = Qt.ItemFlag.ItemIsEnabled
else:
    _Qt_Checked          = Qt.Checked
    _Qt_Unchecked        = Qt.Unchecked
    _Qt_PartiallyChecked = Qt.PartiallyChecked
    _Qt_ItemUserCheckable = Qt.ItemIsUserCheckable
    _Qt_ItemEnabled       = Qt.ItemIsEnabled


class CheckableComboBox(QWidget):
    """Dropdown con checkbox per la selezione multipla di colonne.
    Mostra un popup con 'Seleziona tutte', lista colonne e barra di stato."""

    selectionChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Pulsante principale
        self._btn = QPushButton("0 colonne selezionate  ▾")
        _sp_exp   = QSizePolicy.Policy.Expanding if _QGIS4 else QSizePolicy.Expanding
        _sp_fixed = QSizePolicy.Policy.Fixed     if _QGIS4 else QSizePolicy.Fixed
        self._btn.setSizePolicy(_sp_exp, _sp_fixed)
        self._btn.setMinimumHeight(28)
        self._btn.clicked.connect(self._toggle_popup)
        layout.addWidget(self._btn)

        # Popup frameless
        self._popup = QFrame(None, Qt.WindowType.Popup if hasattr(Qt, 'WindowType') else Qt.Popup)
        self._popup.setFrameShape(QFrame.Shape.StyledPanel if _QGIS4 else QFrame.StyledPanel)
        self._popup.setMinimumWidth(220)
        popup_layout = QVBoxLayout(self._popup)
        popup_layout.setContentsMargins(4, 4, 4, 4)
        popup_layout.setSpacing(2)

        # "Seleziona tutte"
        self._select_all_cb = QCheckBox("Seleziona tutte")
        self._select_all_cb.setChecked(True)
        self._select_all_cb.stateChanged.connect(self._on_select_all_changed)
        popup_layout.addWidget(self._select_all_cb)

        # Lista colonne
        self._list = QListWidget()
        self._list.setMinimumHeight(150)
        self._list.setMaximumHeight(250)
        self._list.itemChanged.connect(self._on_item_changed)
        popup_layout.addWidget(self._list)

        # Barra di stato inferiore
        bar = QWidget()
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(0, 2, 0, 0)
        self._count_label = QLabel("0 Colonne selezionate")
        self._count_label.setStyleSheet("font-size: 9pt; font-weight: bold;")
        bar_layout.addWidget(self._count_label, 1)
        clear_btn = QPushButton("✕")
        clear_btn.setFixedSize(24, 24)
        clear_btn.setToolTip("Deseleziona tutte")
        clear_btn.clicked.connect(self._clear_all)
        bar_layout.addWidget(clear_btn)
        close_btn = QPushButton("▲")
        close_btn.setFixedSize(24, 24)
        close_btn.setToolTip("Chiudi")
        close_btn.clicked.connect(self._popup.hide)
        bar_layout.addWidget(close_btn)
        popup_layout.addWidget(bar)

        self._updating = False
        self._apply_theme()

    def _apply_theme(self):
        btn_fg = "#e0e0e0" if _Theme.dark else "#212121"
        self._btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {_Theme.btn_bg};
                color: {btn_fg};
                border: 1px solid {_Theme.btn_border};
                border-radius: 4px;
                padding: 4px 8px;
                text-align: left;
            }}
            QPushButton:hover {{ background-color: {_Theme.btn_hover}; }}
        """)
        self._popup.setStyleSheet("""
            QFrame { background-color: #ffffff; border: 1px solid #cccccc; border-radius: 4px; }
            QCheckBox { color: #212121; }
            QListWidget { border: none; background-color: #ffffff; color: #212121; }
            QListWidget::item { color: #212121; padding: 2px 4px; }
            QListWidget::item:hover { background-color: #e3f2fd; }
            QLabel { color: #212121; }
            QPushButton { color: #212121; }
        """)

    def setItems(self, field_names, checked=True):
        """Popola la lista con i nomi dei campi."""
        self._updating = True
        self._list.clear()
        for name in field_names:
            item = QListWidgetItem(name)
            item.setFlags(item.flags() | _Qt_ItemUserCheckable | _Qt_ItemEnabled)
            item.setCheckState(_Qt_Checked if checked else _Qt_Unchecked)
            self._list.addItem(item)
        self._select_all_cb.setChecked(checked)
        self._updating = False
        self._update_display()

    def checkedItems(self):
        """Restituisce la lista dei nomi colonne selezionate."""
        result = []
        for i in range(self._list.count()):
            item = self._list.item(i)
            if item.checkState() == _Qt_Checked:
                result.append(item.text())
        return result

    def _toggle_popup(self):
        if self._popup.isVisible():
            self._popup.hide()
        else:
            self._popup.adjustSize()
            pos = self.mapToGlobal(self._btn.rect().bottomLeft())
            self._popup.move(pos)
            self._popup.resize(max(self.width(), 260), self._popup.sizeHint().height())
            self._popup.show()

    def _on_select_all_changed(self, state):
        if self._updating:
            return
        self._updating = True
        checked = (state == _Qt_Checked)
        for i in range(self._list.count()):
            self._list.item(i).setCheckState(_Qt_Checked if checked else _Qt_Unchecked)
        self._updating = False
        self._update_display()
        self.selectionChanged.emit()

    def _on_item_changed(self, item):
        if self._updating:
            return
        self._updating = True
        total = self._list.count()
        n_checked = sum(
            1 for i in range(total) if self._list.item(i).checkState() == _Qt_Checked
        )
        self._select_all_cb.setCheckState(
            _Qt_Checked if n_checked == total else
            _Qt_Unchecked if n_checked == 0 else
            _Qt_PartiallyChecked
        )
        self._updating = False
        self._update_display()
        self.selectionChanged.emit()

    def _clear_all(self):
        self._updating = True
        for i in range(self._list.count()):
            self._list.item(i).setCheckState(_Qt_Unchecked)
        self._select_all_cb.setCheckState(_Qt_Unchecked)
        self._updating = False
        self._update_display()
        self.selectionChanged.emit()

    def _update_display(self):
        n = len(self.checkedItems())
        total = self._list.count()
        self._btn.setText(f"{n} colonne selezionate  ▾")
        self._count_label.setText(f"{n} Colonne selezionate")


class GeoPointManagerDialog(QDialog):
    """Dialog principale per GeoPoint Manager - versione semplificata"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("GeoPoint Manager - v5.1")
        self.setMinimumSize(640, 600)
        self.resize(800, 750)

        # Rimuove cornici inutili, lascia solo quella del tab attivo
        self.setStyleSheet("""
            QGroupBox {
                border: none;
                margin-top: 20px;
                padding-top: 4px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 2px;
                padding: 0 4px;
            }
            QScrollArea { border: none; background: transparent; }
            QScrollArea > QWidget > QWidget { background: transparent; }
        """)
        
        # Variabili
        self.source_layer = None
        self.points_layer = None
        self._selected_columns = None        # None = tutte le colonne
        self._available_fields_cache = []    # lista campi dell'ultimo layer caricato

        # Google Sheets → GeoPackage
        self._gs_url = None
        self._gs_gpkg_path = None
        self._gs_source_layer_id = None
        
        self.setup_ui()
        self.update_layer_list()
        
    def create_icon_button(self, text, icon_text, tooltip="", size=(40, 30)):
        """Crea un pulsante con icona"""
        btn = QPushButton()
        
        # Usa icone QGIS native quando possibile
        if icon_text == "refresh":
            icon = QIcon(":/images/themes/default/mActionRefresh.svg")
            if not icon.isNull():
                btn.setIcon(icon)
                btn.setIconSize(QSize(20, 20))
            else:
                btn.setText("↻")
                font = btn.font()
                font.setPointSize(12)
                btn.setFont(font)
        elif icon_text == "help":
            icon = QIcon(":/images/themes/default/mActionHelpContents.svg")
            if not icon.isNull():
                btn.setIcon(icon)
                btn.setIconSize(QSize(16, 16))
            else:
                btn.setText("?")
        else:
            btn.setText(icon_text)
            font = btn.font()
            font.setPointSize(12)
            font.setBold(True)
            btn.setFont(font)
        
        if text:
            btn.setText(f"{btn.text()} {text}".strip())
        
        btn.setMinimumSize(size[0], size[1])
        btn.setToolTip(tooltip)
        
        # Stile migliorato per pulsanti icona
        btn_fg = "#e0e0e0" if _Theme.dark else "#212121"
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {_Theme.btn_bg};
                color: {btn_fg};
                border: 2px solid {_Theme.btn_border};
                border-radius: 4px;
                padding: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {_Theme.btn_hover};
                color: {btn_fg};
                border-color: {_Theme.accent};
            }}
            QPushButton:pressed {{
                background-color: {_Theme.btn_pressed};
                color: {btn_fg};
                border-color: {_Theme.accent_dark};
            }}
        """)
        
        return btn
    
    def create_large_button(self, text, style_color="#4CAF50", font_size=10):
        """Crea un pulsante grande con stile"""
        btn = QPushButton(text)
        btn.setMinimumHeight(35)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {style_color};
                color: white;
                font-weight: bold;
                font-size: {font_size}pt;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {self.lighten_color(style_color)};
            }}
            QPushButton:pressed {{
                background-color: {self.darken_color(style_color)};
            }}
            QPushButton:disabled {{
                background-color: {_Theme.disabled_bg};
                color: {_Theme.disabled_fg};
            }}
        """)
        return btn
    
    def lighten_color(self, color):
        """Schiarisce un colore per l'hover"""
        color_map = {
            "#4CAF50": "#66BB6A",
            "#9C27B0": "#AB47BC", 
            "#2196F3": "#42A5F5",
            "#FF9800": "#FFB74D",
            "#F44336": "#EF5350",
            "#757575": "#9E9E9E"
        }
        return color_map.get(color, color)
    
    def darken_color(self, color):
        """Scurisce un colore per il press"""
        color_map = {
            "#4CAF50": "#388E3C",
            "#9C27B0": "#7B1FA2",
            "#2196F3": "#1976D2", 
            "#FF9800": "#F57C00",
            "#F44336": "#D32F2F",
            "#757575": "#616161"
        }
        return color_map.get(color, color)
        
    def setup_ui(self):
        """Crea l'interfaccia utente"""
        main_layout = QVBoxLayout()
        
        # Area scrollabile per il contenuto principale
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame if _QGIS4 else QFrame.NoFrame)
        
        # Widget contenitore per il contenuto scrollabile
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # === SEZIONE INPUT CON TAB ===
        input_group = QWidget()
        input_layout = QVBoxLayout()
        
        # Tab widget per diverse sorgenti
        self.source_tabs = QTabWidget()
        self.source_tabs.setMinimumHeight(280)
        
        # === TAB 1: DATI OGR/GDAL ONLINE (PRIMA SCHEDA) ===
        self.ogr_tab = QWidget()
        
        ogr_scroll = QScrollArea()
        ogr_scroll.setWidgetResizable(True)
        ogr_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        ogr_scroll.setMinimumHeight(320)
        ogr_scroll.setFrameShape(QFrame.Shape.NoFrame if _QGIS4 else QFrame.NoFrame)
        
        ogr_content = QWidget()
        ogr_layout = QVBoxLayout(ogr_content)
        
        ogr_layout.addWidget(QLabel("URL sorgente dati:"))
        self.ogr_url_edit = QLineEdit()
        self.ogr_url_edit.setPlaceholderText("Link tipo per Google Sheets - https://docs.google.com/spreadsheets/d/[ID_DEL_FILE]/export?format=csv&gid=[ID_DEL_FOGLIO]")
        ogr_layout.addWidget(self.ogr_url_edit)
        
        # Guida Google Sheets
        gs_help_layout = QHBoxLayout()
        self.gs_help_btn = self.create_icon_button("Google Sheets", "?", "Guida per Google Sheets CSV", (140, 30))
        self.gs_help_btn.clicked.connect(self.show_google_sheets_help)
        gs_help_layout.addWidget(self.gs_help_btn)
        gs_help_layout.addStretch()
        ogr_layout.addLayout(gs_help_layout)
        
        # Formato e Nome Layer layout
        format_name_layout = QHBoxLayout()
        format_name_layout.addWidget(QLabel("Formato:"))
        self.ogr_format_combo = QComboBox()
        self.ogr_format_combo.addItems([
            "Auto-detect", "GeoJSON", "WFS", "Shapefile (ZIP)", 
            "KML/KMZ", "GPX", "CSV", "Google Sheets", "Altri"
        ])
        format_name_layout.addWidget(self.ogr_format_combo)
        
        # NUOVO: Campo per nome layer personalizzato
        format_name_layout.addWidget(QLabel("Nome:"))
        self.ogr_layer_custom_name = QLineEdit()
        self.ogr_layer_custom_name.setPlaceholderText("Nome layer personalizzato")
        self.ogr_layer_custom_name.setToolTip("Nome personalizzato per il layer (opzionale)")
        format_name_layout.addWidget(self.ogr_layer_custom_name)
        
        format_name_layout.addStretch()
        ogr_layout.addLayout(format_name_layout)
        
        # Modalità di caricamento
        mode_group = QWidget()
        mode_layout = QHBoxLayout()

        self.table_only_radio = QRadioButton("Solo tabella dati")
        self.table_only_radio.setChecked(False)
        self.table_only_radio.setToolTip("Scarica i dati come layer tabellare senza mappatura automatica")

        self.direct_points_radio = QRadioButton("Aggiungi tabella dati e layer virtuale")
        self.direct_points_radio.setChecked(True)
        self.direct_points_radio.setToolTip("Crea automaticamente il layer di punti mappando i campi coordinate")

        mode_layout.addWidget(self.direct_points_radio)
        mode_layout.addWidget(self.table_only_radio)

        mode_group.setLayout(mode_layout)
        ogr_layout.addWidget(mode_group)
        
        # Opzioni avanzate (collassabile)
        self.ogr_options_group = QGroupBox("Opzioni Avanzate")

        ogr_options_layout = QGridLayout()

        ogr_options_layout.addWidget(QLabel("User:"), 0, 0)
        self.ogr_username = QLineEdit()
        ogr_options_layout.addWidget(self.ogr_username, 0, 1)

        ogr_options_layout.addWidget(QLabel("Pass:"), 0, 2)
        self.ogr_password = QLineEdit()
        self.ogr_password.setEchoMode(QLineEdit.EchoMode.Password)
        ogr_options_layout.addWidget(self.ogr_password, 0, 3)

        ogr_options_layout.addWidget(QLabel("Params:"), 1, 0)
        self.ogr_params = QLineEdit()
        self.ogr_params.setPlaceholderText("param1=value1&param2=value2")
        ogr_options_layout.addWidget(self.ogr_params, 1, 1, 1, 3)

        ogr_options_layout.addWidget(QLabel("Layer:"), 2, 0)
        self.ogr_layer_name_edit = QLineEdit()
        ogr_options_layout.addWidget(self.ogr_layer_name_edit, 2, 1)

        ogr_options_layout.addWidget(QLabel("CRS:"), 2, 2)
        self.ogr_crs_edit = QLineEdit()
        self.ogr_crs_edit.setPlaceholderText("EPSG:4326")
        ogr_options_layout.addWidget(self.ogr_crs_edit, 2, 3)

        self.ogr_options_group.setLayout(ogr_options_layout)
        ogr_layout.addWidget(self.ogr_options_group)
    
        # Salva come GeoPackage (per Google Sheets)
        gpkg_group = QWidget()
        gpkg_layout = QVBoxLayout()
        gpkg_layout.setContentsMargins(0, 0, 0, 0)
        gpkg_layout.setSpacing(2)
        gpkg_label = QLabel("Salva dati come GeoPackage (richiesto per Google Sheets):")
        gpkg_label.setStyleSheet(f"color: {_Theme.text_muted}; font-size: 9pt;")
        gpkg_layout.addWidget(gpkg_label)
        gpkg_row = QHBoxLayout()
        self.gpkg_path_edit = QLineEdit()
        self.gpkg_path_edit.setPlaceholderText("Percorso file .gpkg — lascia vuoto per scegliere al caricamento")
        self.gpkg_path_edit.setToolTip("Percorso GeoPackage in cui salvare i dati scaricati da Google Sheets")
        gpkg_row.addWidget(self.gpkg_path_edit)
        self.gpkg_browse_btn = QPushButton("Sfoglia...")
        self.gpkg_browse_btn.setFixedWidth(80)
        self.gpkg_browse_btn.clicked.connect(self._browse_gpkg_path)
        gpkg_row.addWidget(self.gpkg_browse_btn)
        gpkg_layout.addLayout(gpkg_row)
        gpkg_group.setLayout(gpkg_layout)
        ogr_layout.addWidget(gpkg_group)

        # Pulsante carica
        self.load_ogr_btn = self.create_large_button("Carica dati OGR/GDAL", "#9C27B0", 10)
        self.load_ogr_btn.clicked.connect(self.load_ogr_data)
        ogr_layout.addWidget(self.load_ogr_btn)

        # Riga: [ Sfoglia GeoPackage esistente ] [ ↻ Aggiorna dati da Google Sheets ]
        refresh_row = QHBoxLayout()

        self.gpkg_open_btn = self.create_large_button("📂  Apri GeoPackage esistente", "#757575", 10)
        self.gpkg_open_btn.setToolTip("Seleziona un GeoPackage già esistente per aggiornarne i layer")
        self.gpkg_open_btn.clicked.connect(self._open_existing_gpkg)
        refresh_row.addWidget(self.gpkg_open_btn)

        self.refresh_gs_btn = self.create_large_button("↻  Aggiorna da Google Sheets", "#FF9800", 10)
        self.refresh_gs_btn.clicked.connect(self._refresh_google_sheets_manual)
        self.refresh_gs_btn.setEnabled(False)
        self.refresh_gs_btn.setToolTip("Legge la registry dal GeoPackage e aggiorna i layer registrati")
        refresh_row.addWidget(self.refresh_gs_btn)

        ogr_layout.addLayout(refresh_row)
        self.gpkg_path_edit.textChanged.connect(
            lambda t: self.refresh_gs_btn.setEnabled(bool(t.strip()))
        )
        
        ogr_scroll.setWidget(ogr_content)
        
        ogr_tab_layout = QVBoxLayout(self.ogr_tab)
        ogr_tab_layout.addWidget(ogr_scroll)
        
        self.source_tabs.addTab(self.ogr_tab, "Dati OGR/GDAL")  # PRIMA SCHEDA
        
        # === TAB 2: LAYER QGIS (SECONDA SCHEDA) ===
        self.layer_tab = QWidget()
        layer_layout = QVBoxLayout()
        
        layer_layout.addWidget(QLabel("Seleziona un layer vettoriale dal progetto:"))
        self.layer_combo = QComboBox()
        layer_layout.addWidget(self.layer_combo)
        # fields_group verrà aggiunto qui sotto dopo la sua creazione
        self.layer_tab.setLayout(layer_layout)
        self.source_tabs.addTab(self.layer_tab, "Dati da layer QGIS")  # SECONDA SCHEDA

        # === TAB 3: INFO / ABOUT (TERZA SCHEDA) ===
        self.info_tab = QWidget()
        info_tab_layout = QVBoxLayout(self.info_tab)

        info_browser = QTextBrowser()
        info_browser.setOpenExternalLinks(True)
        info_browser.setHtml("""
<html><body style="font-family: sans-serif; font-size: 13px; padding: 8px;">

<h2 style="color:#2196F3;">GeoPoint Manager v5.1</h2>
<p>Plugin QGIS per creare <b>layer vettoriali di punti</b> a partire da sorgenti dati contenenti
campi di coordinate geografiche (latitudine/longitudine).</p>
<p><b>Compatibilità:</b> QGIS 3.16+ / 4.x &nbsp;|&nbsp; <b>Licenza:</b> GPL-2.0+<br>
<b>Autori:</b> @gbvitrano, Claude AI (Anthropic)</p>

<hr>
<h3>Sorgenti dati supportate</h3>
<table border="1" cellspacing="0" cellpadding="4" style="border-collapse:collapse; width:100%;">
  <tr style="background:#e3f2fd;"><th>Sorgente</th><th>Note</th></tr>
  <tr><td><b>Google Sheets</b></td><td>Download diretto via urllib, salvataggio in GeoPackage</td></tr>
  <tr><td><b>URL OGR/GDAL</b></td><td>Fonti online generiche</td></tr>
  <tr><td><b>WFS</b></td><td>Web Feature Services</td></tr>
  <tr><td><b>GeoJSON, Shapefile (ZIP), KML/KMZ, GPX, CSV</b></td><td>File locali o remoti</td></tr>
  <tr><td><b>Layer QGIS esistenti</b></td><td>Layer già caricati nel progetto corrente</td></tr>
</table>

<hr>
<h3>Funzionalità principali</h3>
<ol>
  <li><b>Rilevamento automatico coordinate</b> — individua i campi lat/lon tramite keyword matching
      (es. <code>lat</code>, <code>latitude</code>, <code>y</code>, <code>northing</code>,
      <code>lon</code>, <code>lng</code>, <code>x</code>, <code>easting</code>…)</li>
  <li><b>Virtual Layer dinamico</b> — crea layer virtuali QGIS con query SQL:<br>
      <code style="background:#f5f5f5; padding:2px 4px;">
      SELECT *, make_point(CAST(lon AS REAL), CAST(lat AS REAL)) as geometry
      FROM source WHERE lon IS NOT NULL AND lat IS NOT NULL
      </code></li>
  <li><b>Google Sheets integration</b> — salva i CSV scaricati in un GeoPackage locale,
      con registro persistente (<code>_geopoint_sources</code>) e refresh manuale on-demand.</li>
  <li><b>Gestione CRS flessibile</b> — auto-rilevamento o forzatura del sistema di riferimento
      (EPSG:4326, 3857, UTM e personalizzato).</li>
  <li><b>Export multiplo</b> — GeoPackage, Shapefile, GeoJSON, KML, CSV.</li>
  <li><b>Processing integration</b> — accessibile anche dal QGIS Processing Framework.</li>
</ol>

<hr>
<h3>Interfaccia utente</h3>
<table border="1" cellspacing="0" cellpadding="4" style="border-collapse:collapse; width:100%;">
  <tr style="background:#e3f2fd;"><th>Tab</th><th>Descrizione</th></tr>
  <tr><td><b>Tab 1 – Dati OGR/GDAL</b></td><td>Caricamento da URL (OGR/GDAL, Google Sheets, WFS…). Include Opzioni Avanzate (autenticazione, parametri, layer, CRS override) e salvataggio GeoPackage.</td></tr>
  <tr><td><b>Tab 2 – Dati da layer QGIS</b></td><td>Caricamento da layer già presenti nel progetto. Include la sezione <i>Configurazione campi e CRS</i> per selezione campi X/Y, CRS, nome layer virtuale e selezione colonne da includere.</td></tr>
  <tr><td><b>Tab 3 – Log</b></td><td>Storico delle operazioni con timestamp.</td></tr>
  <tr><td><b>Tab 4 – Info / About</b></td><td>Documentazione del plugin.</td></tr>
</table>
<p>La barra inferiore contiene: <b>Aggiungi layer virtuale di punti</b>, <b>Esporta Layer…</b>, <b>Salva GPKG</b> e <b>Chiudi</b>.</p>

<hr>
<h3>Workflow tipici</h3>
<h4>Flusso base</h4>
<ol>
  <li>Avvia il plugin (icona toolbar o menu Vettore).</li>
  <li>Seleziona la sorgente dati (tab <i>Dati OGR/GDAL</i> o <i>Dati da layer QGIS</i>).</li>
  <li>Inserisci l'URL o seleziona il layer.</li>
  <li>I campi coordinate vengono rilevati automaticamente oppure si apre il dialogo <i>Seleziona Campi Coordinate e Colonne</i> per scegliere lat/lon e le colonne da includere nel layer virtuale.</li>
  <li>Clicca <b>"Aggiungi layer virtuale di punti e la relativa tabella"</b>.</li>
  <li>Esporta se necessario.</li>
</ol>
<h4>Google Sheets</h4>
<ol>
  <li>Condividi il foglio Google pubblicamente e copia l'URL di esportazione CSV.</li>
  <li>Specifica il percorso del GeoPackage di destinazione.</li>
  <li>Carica i dati; il plugin li salva localmente.</li>
  <li>Per aggiornare: clicca <b>"↻ Aggiorna da Google Sheets"</b>.</li>
</ol>

<hr>
<h3>Novità v5.1</h3>
<ul>
  <li>Fix caricamento Google Sheets su QGIS 4 (<i>urllib</i> gestisce i redirect HTTP).</li>
  <li>Storage persistente basato su GeoPackage per i dati scaricati.</li>
  <li>Refresh manuale on-demand al posto dell'auto-fetch.</li>
  <li>Compatibilità Qt5/PyQt5 (QGIS 3) e Qt6/PyQt6 (QGIS 4) — fix enum <code>QSizePolicy</code>, <code>QFrame</code>, <code>Qt</code>.</li>
  <li>Nuova struttura a 4 tab: <i>Dati OGR/GDAL</i>, <i>Dati da layer QGIS</i>, <i>Log</i>, <i>Info / About</i>.</li>
  <li>Dialogo <i>Seleziona Campi Coordinate e Colonne</i>: permette di scegliere lat/lon <b>e</b> quali colonne includere nel layer virtuale, tutto in un unico passaggio.</li>
  <li>Sezione <i>Configurazione campi e CRS</i> integrata nel tab <i>Dati da layer QGIS</i>.</li>
  <li>Pulsanti <i>Esporta Layer</i> e <i>Salva GPKG</i> spostati nella barra inferiore, sempre visibili.</li>
  <li>Layout pulito: rimossi i frame ridondanti, lasciato solo il bordo del tab widget.</li>
  <li>Messaggi di errore e logging migliorati.</li>
</ul>

<hr>
<h3>Sviluppo tecnico</h3>
<p>Script Python per QGIS sviluppato attraverso una collaborazione <b>human-Claude AI (Anthropic)</b> e <b>chatbot Z.ai</b>,
che hanno supportato la progettazione dell'architettura modulare, l'ottimizzazione del codice e l'implementazione di funzionalità avanzate.</p>

<h4>v5.1 — Dettagli tecnici</h4>
<ul>
  <li>Download Google Sheets via <i>urllib</i> con gestione redirect HTTP (QGIS 4 compatibility).</li>
  <li>Dati salvati in <b>GeoPackage</b> scelto dall'utente, persistente tra le sessioni; registro sorgenti nella tabella <code>_geopoint_sources</code>.</li>
  <li>Aggiornamento <b>manuale on-demand</b>: il pulsante <i>↻ Aggiorna da Google Sheets</i> riscarica il foglio e sovrascrive il GeoPackage.</li>
  <li>Supporta entrambi i formati URL Google Sheets (<i>/pub?output=csv</i> e <i>/export?format=csv&amp;gid=…</i>).</li>
  <li>Selezione colonne tramite <code>CheckableComboBox</code> nel dialogo coordinate — le colonne X/Y sono sempre incluse.</li>
  <li>Fix Qt6: enum <code>QSizePolicy.Policy</code>, <code>QFrame.Shape</code>, <code>Qt.ItemFlag</code>, <code>Qt.CheckState</code>.</li>
</ul>

<p>by <a href="https://www.linkedin.com/in/gbvitrano/">@gbvitrano</a> —
<a href="https://opendatasicilia.it/">@opendatasicilia</a></p>
<p style="color:#888888; font-size:10px; font-style:italic;">Plugin QGIS per gestione punti geografici da sorgenti dati online — compatibile QGIS 3 e QGIS 4</p>

</body></html>
        """)
        info_tab_layout.addWidget(info_browser)
        # Aggiungi tab al layout
        input_layout.addWidget(self.source_tabs)
        input_group.setLayout(input_layout)
        scroll_layout.addWidget(input_group)

        # === SEZIONE COLLASSABILE: CONFIGURAZIONE CAMPI E CRS (CHIUSA DI DEFAULT) ===
        self.fields_group = QGroupBox("Configurazione campi e CRS")
        fields_layout = QGridLayout()
        
        fields_layout.addWidget(QLabel("X (Lon):"), 0, 0)
        self.x_field_combo = QComboBox()
        fields_layout.addWidget(self.x_field_combo, 0, 1)
        
        fields_layout.addWidget(QLabel("Y (Lat):"), 0, 2)
        self.y_field_combo = QComboBox()
        fields_layout.addWidget(self.y_field_combo, 0, 3)
        
        # Pulsante refresh campi
        self.refresh_fields_btn = self.create_icon_button("", "refresh", "Aggiorna campi", (50, 30))
        self.refresh_fields_btn.clicked.connect(self.refresh_fields)
        fields_layout.addWidget(self.refresh_fields_btn, 0, 4)
        
        fields_layout.addWidget(QLabel("CRS:"), 1, 0)
        self.crs_combo = QComboBox()
        self.setup_crs_combo()
        fields_layout.addWidget(self.crs_combo, 1, 1, 1, 2)
        
        self.crs_selector = QgsProjectionSelectionWidget()
        self.crs_selector.setCrs(QgsCoordinateReferenceSystem("EPSG:4326"))
        
        self.custom_crs_btn = self.create_icon_button("CRS...", "🌍", "Seleziona CRS personalizzato", (80, 30))
        self.custom_crs_btn.clicked.connect(self.select_custom_crs)
        fields_layout.addWidget(self.custom_crs_btn, 1, 3, 1, 2)
        
        self.current_crs_label = QLabel("CRS: EPSG:4326 - WGS 84")
        self.current_crs_label.setStyleSheet(f"color: {_Theme.crs_color}; font-size: 9pt;")
        fields_layout.addWidget(self.current_crs_label, 2, 0, 1, 5)
        
        fields_layout.addWidget(QLabel("Nome Layer virtuale:"), 3, 0)
        self.layer_name_edit = QLineEdit("Punti_virtuali")
        fields_layout.addWidget(self.layer_name_edit, 3, 1, 1, 4)

        fields_layout.addWidget(QLabel("Colonne:"), 4, 0)
        self.columns_btn = QPushButton("— nessun layer caricato —")
        self.columns_btn.setEnabled(False)
        self.columns_btn.setToolTip("Modifica le colonne incluse nel layer virtuale")
        self.columns_btn.clicked.connect(self._open_columns_dialog)
        fields_layout.addWidget(self.columns_btn, 4, 1, 1, 4)
        self._selected_columns = None   # None = tutte

        self.fields_group.setLayout(fields_layout)
        # Inserisce la sezione nel Tab 2 "Dati da layer QGIS"
        self.layer_tab.layout().addWidget(self.fields_group)
        self.layer_tab.layout().addStretch()
        
        # Pulsanti esportazione (creati qui, inseriti nella barra pulsanti in fondo)
        self.export_btn = self.create_large_button("Esporta Layer...", "#4CAF50", 10)
        self.export_btn.clicked.connect(self.export_layer_dialog)
        self.export_btn.setEnabled(False)
        self.export_btn.setToolTip("Apre il dialogo nativo di QGIS per esportare in tutti i formati supportati")

        self.quick_save_btn = self.create_large_button("Salva GPKG", "#FF9800", 10)
        self.quick_save_btn.clicked.connect(self.quick_save_geopackage)
        self.quick_save_btn.setEnabled(False)
        self.quick_save_btn.setToolTip("Salvataggio rapido come GeoPackage")


        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        scroll_layout.addWidget(self.progress_bar)

        # === TAB 4: LOG ===
        self.log_tab = QWidget()
        log_tab_layout = QVBoxLayout(self.log_tab)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setPlainText("GeoPoint Manager v5.1 pronto - Google Sheets → GeoPackage, aggiornamento manuale on-demand...")
        log_tab_layout.addWidget(self.log_text)

        self.source_tabs.addTab(self.log_tab, "Log")
        self.source_tabs.addTab(self.info_tab, "Info / About")
        
        # Imposta il widget scrollabile
        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area, 1)  # stretch=1: si espande con la finestra
        
        # === PULSANTI PRINCIPALI ===
        buttons_layout = QHBoxLayout()
        
        self.create_btn = self.create_large_button("Aggiungi layer vettoriale di punti", "#4CAF50", 11)
        self.create_btn.clicked.connect(self.create_points_layer)

        self.close_btn = self.create_large_button("Chiudi", "#757575", 10)
        self.close_btn.clicked.connect(self.close)

        buttons_layout.addWidget(self.create_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.export_btn)
        buttons_layout.addWidget(self.quick_save_btn)
        buttons_layout.addWidget(self.close_btn)

        main_layout.addLayout(buttons_layout)

        # Titolo centrato in fondo
        footer = QLabel("GeoPoint Manager - v5.1")
        footer_font = QFont()
        footer_font.setPointSize(8)
        footer.setFont(footer_font)
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet(f"color: {_Theme.text_muted}; padding: 2px 0;")
        main_layout.addWidget(footer)
        self.setLayout(main_layout)
        
        # Connetti eventi
        self.layer_combo.currentTextChanged.connect(self.on_layer_changed)
        self.crs_combo.currentTextChanged.connect(self.on_crs_combo_changed)
        self.source_tabs.currentChanged.connect(self.on_source_tab_changed)

    def show_google_sheets_help(self):
        """Mostra una finestra di aiuto per Google Sheets"""
        help_dialog = QDialog(self)
        help_dialog.setWindowTitle("Guida Google Sheets CSV")
        help_dialog.setFixedSize(500, 400)
        
        layout = QVBoxLayout()
        
        title = QLabel("Google Sheets -> URL tipo")
        title_font = QFont()
        title_font.setPointSize(11)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Scroll area per il contenuto
        scroll = QScrollArea()
        content = QWidget()
        content_layout = QVBoxLayout(content)
        
        example_label = QLabel("Esempio URL:")
        content_layout.addWidget(example_label)
        
        example_url = QLabel("https://docs.google.com/spreadsheets/d/[ID]/export?format=csv&gid=[SHEET_ID]")
        example_url.setWordWrap(True)
        code_fg = "#e0e0e0" if _Theme.dark else "#212121"
        example_url.setStyleSheet(f"background-color: {_Theme.code_bg}; color: {code_fg}; padding: 5px; font-family: monospace; font-size: 9pt;")
        content_layout.addWidget(example_url)
        
        steps_label = QLabel("Passi:")
        content_layout.addWidget(steps_label)
        
        steps_text = QLabel("""1. Condividi il foglio: "Chiunque con link possa visualizzare"
2. Sostituisci [ID] con l'ID del documento
3. Sostituisci [SHEET_ID] con l'ID del foglio (opzionale)
4. Il foglio deve avere colonne Lat/Long con coordinate decimali""")
        steps_text.setWordWrap(True)
        steps_text.setStyleSheet("font-size: 9pt;")
        content_layout.addWidget(steps_text)
        
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        ok_btn = self.create_large_button("OK", "#4CAF50", 10)
        ok_btn.clicked.connect(help_dialog.accept)
        layout.addWidget(ok_btn)
        
        help_dialog.setLayout(layout)
        help_dialog.exec()


    def export_layer_dialog(self):
        """Esporta il layer punti nel formato scelto dall'utente (QGIS 3 e 4)."""
        if not self.points_layer:
            QMessageBox.warning(self, "Errore", "Nessun layer da esportare!")
            return

        # Mappa estensione → driver OGR
        _FORMATS = [
            ("GeoPackage (*.gpkg)",        ".gpkg",  "GPKG"),
            ("Shapefile (*.shp)",          ".shp",   "ESRI Shapefile"),
            ("GeoJSON (*.geojson)",        ".geojson","GeoJSON"),
            ("KML (*.kml)",               ".kml",   "KML"),
            ("CSV (*.csv)",               ".csv",   "CSV"),
        ]
        filter_str = ";;".join(f[0] for f in _FORMATS)

        file_path, selected_filter = QFileDialog.getSaveFileName(
            self, "Esporta layer punti", self.points_layer.name(), filter_str
        )
        if not file_path:
            self.log("Esportazione annullata dall'utente")
            return

        # Determina il driver dall'estensione (o dal filtro selezionato)
        ext = os.path.splitext(file_path)[1].lower()
        driver = next((d for _, e, d in _FORMATS if e == ext), None)
        if driver is None:
            # fallback: prendi dal filtro scelto
            driver = next((d for f, _, d in _FORMATS if f == selected_filter), "GPKG")
            file_path += next((e for f, e, _ in _FORMATS if f == selected_filter), ".gpkg")

        try:
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName = driver
            error, msg, _, _ = QgsVectorFileWriter.writeAsVectorFormatV3(
                self.points_layer,
                file_path,
                QgsProject.instance().transformContext(),
                options
            )
            if error == _WRITER_OK:
                self.log(f"Esportato come {driver}: {os.path.basename(file_path)}")
                QMessageBox.information(
                    self, "Successo",
                    f"Layer esportato con successo!\n\n"
                    f"Formato: {driver}\n"
                    f"File: {os.path.basename(file_path)}"
                )
            else:
                raise RuntimeError(msg)
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore durante l'esportazione: {str(e)}")
            self.log(f"Errore esportazione: {str(e)}")

    def quick_save_geopackage(self):
        """Salvataggio rapido come GeoPackage"""
        if not self.points_layer:
            QMessageBox.warning(self, "Errore", "Nessun layer da salvare!")
            return
        
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_name = f"{self.points_layer.name()}_{timestamp}.gpkg"
            
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Salvataggio Rapido GeoPackage", default_name, "GeoPackage (*.gpkg)"
            )
            
            if not file_path:
                return
                
            if not file_path.endswith('.gpkg'):
                file_path += '.gpkg'
                
            # Salva utilizzando le API di QGIS
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName = "GPKG"
            options.fileEncoding = "UTF-8"
            
            error = QgsVectorFileWriter.writeAsVectorFormatV3(
                self.points_layer, file_path,
                QgsProject.instance().transformContext(),
                options
            )
            
            if error[0] == _WRITER_OK:
                self.log(f"Salvato come GeoPackage: {os.path.basename(file_path)}")
                
                QMessageBox.information(
                    self, "Successo", 
                    f"GeoPackage salvato con successo!\n\n"
                    f"File: {os.path.basename(file_path)}\n"
                    f"Percorso: {file_path}"
                )
            else:
                QMessageBox.critical(self, "Errore", f"Errore salvataggio: {error[1]}")
                self.log(f"Errore salvataggio GeoPackage: {error[1]}")
                
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore: {str(e)}")
            self.log(f"Errore salvataggio: {str(e)}")

    def _write_source_registry(self, gpkg_path, layer_name, url):
        """Scrive/aggiorna la riga (layer_name, url) nella tabella _geopoint_sources del GeoPackage."""
        conn = sqlite3.connect(gpkg_path)
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS _geopoint_sources (
                    layer_name  TEXT PRIMARY KEY,
                    url         TEXT NOT NULL,
                    last_updated TEXT
                )
            """)
            conn.execute("""
                INSERT OR REPLACE INTO _geopoint_sources (layer_name, url, last_updated)
                VALUES (?, ?, datetime('now','localtime'))
            """, (layer_name, url))
            conn.commit()
        finally:
            conn.close()

    def _read_source_registry(self, gpkg_path):
        """Legge tutte le sorgenti dalla tabella _geopoint_sources. Restituisce lista di tuple."""
        if not os.path.exists(gpkg_path):
            return []
        conn = sqlite3.connect(gpkg_path)
        try:
            cur = conn.execute("""
                SELECT layer_name, url, last_updated FROM _geopoint_sources
                ORDER BY layer_name
            """)
            return cur.fetchall()
        except sqlite3.OperationalError:
            return []   # tabella non ancora creata
        finally:
            conn.close()

    def _browse_gpkg_path(self):
        """Apre il dialogo Salva per scegliere il percorso del nuovo GeoPackage."""
        path, _ = QFileDialog.getSaveFileName(
            self, "Salva GeoPackage", "", "GeoPackage (*.gpkg)"
        )
        if path:
            if not path.lower().endswith('.gpkg'):
                path += '.gpkg'
            self.gpkg_path_edit.setText(path)

    def _open_existing_gpkg(self):
        """Apre il dialogo Apri per selezionare un GeoPackage esistente da aggiornare."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Apri GeoPackage esistente", "", "GeoPackage (*.gpkg)"
        )
        if path:
            self.gpkg_path_edit.setText(path)
            # Mostra subito quante sorgenti sono registrate
            sources = self._read_source_registry(path)
            if sources:
                nomi = ", ".join(s[0] for s in sources)
                self.log(f"GeoPackage aperto: {len(sources)} sorgent{'e' if len(sources)==1 else 'i'} registrat{'a' if len(sources)==1 else 'e'} → {nomi}")
            else:
                self.log("GeoPackage aperto — nessuna sorgente Google Sheets registrata")

    def _save_csv_to_geopackage(self, csv_path, gpkg_path, table_name):
        """Salva un CSV come tabella in un GeoPackage. Restituisce (ok, messaggio)."""
        csv_layer = QgsVectorLayer(csv_path, "csv_temp", "ogr")
        if not csv_layer.isValid():
            return False, "Impossibile leggere il CSV scaricato"

        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "GPKG"
        options.layerName = table_name
        # Se il file esiste già, sovrascrive solo il layer; altrimenti crea il file da zero.
        # CreateOrOverwriteLayer richiede che il file esista (apre in update mode).
        file_exists = os.path.exists(gpkg_path)
        if _QGIS4:
            options.actionOnExistingFile = (
                QgsVectorFileWriter.ActionOnExistingFile.CreateOrOverwriteLayer
                if file_exists else
                QgsVectorFileWriter.ActionOnExistingFile.CreateOrOverwriteFile
            )
        else:
            options.actionOnExistingFile = (
                QgsVectorFileWriter.CreateOrOverwriteLayer
                if file_exists else
                QgsVectorFileWriter.CreateOrOverwriteFile
            )

        error, msg, _, _ = QgsVectorFileWriter.writeAsVectorFormatV3(
            csv_layer,
            gpkg_path,
            QgsProject.instance().transformContext(),
            options
        )
        if error == _WRITER_OK:
            return True, ""
        return False, msg

    def _gpkg_feature_count(self, gpkg_path, table_name):
        """Restituisce il numero di righe di una tabella nel GeoPackage, o -1 se non esiste."""
        try:
            conn = sqlite3.connect(gpkg_path)
            cur = conn.execute(f'SELECT COUNT(*) FROM "{table_name}"')
            count = cur.fetchone()[0]
            conn.close()
            return count
        except Exception:
            return -1

    def _refresh_google_sheets_manual(self):
        """Legge la registry dal GeoPackage e aggiorna i layer selezionati dall'utente."""
        gpkg_path = self.gpkg_path_edit.text().strip()
        if not gpkg_path:
            QMessageBox.warning(self, "Errore", "Inserisci il percorso del GeoPackage nel campo apposito.")
            return

        sources = self._read_source_registry(gpkg_path)
        if not sources:
            QMessageBox.warning(self, "Nessuna sorgente",
                "Nessuna sorgente Google Sheets registrata in questo GeoPackage.\n"
                "Carica prima un Google Sheet per registrarlo.")
            return

        dlg = RefreshSourcesDialog(sources, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        selected = dlg.get_selected()
        if not selected:
            return

        results = []   # lista di dict per il report finale
        for layer_name, url in selected:
            entry = {"name": layer_name, "ok": False, "before": -1, "after": -1, "error": ""}
            try:
                self.log(f"Aggiornamento '{layer_name}'...")
                entry["before"] = self._gpkg_feature_count(gpkg_path, layer_name)

                temp_path = self._download_to_temp_csv(url)
                ok, msg = self._save_csv_to_geopackage(temp_path, gpkg_path, layer_name)
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

                if not ok:
                    entry["error"] = msg
                    results.append(entry)
                    continue

                entry["after"] = self._gpkg_feature_count(gpkg_path, layer_name)

                # Ricarica il layer nel progetto QGIS se presente
                for lyr in QgsProject.instance().mapLayers().values():
                    if lyr.name() == layer_name:
                        lyr.dataProvider().reloadData()
                        lyr.triggerRepaint()
                        break

                self._write_source_registry(gpkg_path, layer_name, url)
                entry["ok"] = True

            except Exception as e:
                entry["error"] = str(e)

            results.append(entry)

        # --- Costruisce il popup di notifica ---
        html_parts = ["<table width='100%' cellspacing='4'>"]
        html_parts.append(
            "<tr>"
            f"<th align='left'>Layer</th>"
            f"<th align='right'>Prima</th>"
            f"<th align='right'>Dopo</th>"
            f"<th align='right'>Variazione</th>"
            "</tr>"
        )
        log_lines = []
        for e in results:
            if e["ok"]:
                b, a = e["before"], e["after"]
                if b == -1:
                    delta_str = "nuovo"
                    color = _Theme.accent
                elif a > b:
                    delta_str = f"+{a - b}"
                    color = "#4CAF50"
                elif a < b:
                    delta_str = f"{a - b}"
                    color = "#F44336"
                else:
                    delta_str = "nessuna"
                    color = _Theme.text_muted
                before_str = str(b) if b >= 0 else "—"
                html_parts.append(
                    f"<tr>"
                    f"<td>✓ <b>{e['name']}</b></td>"
                    f"<td align='right'>{before_str}</td>"
                    f"<td align='right'>{a}</td>"
                    f"<td align='right'><b><span style='color:{color}'>{delta_str}</span></b></td>"
                    f"</tr>"
                )
                log_lines.append(f"✓ {e['name']}: {before_str} → {a} ({delta_str})")
            else:
                html_parts.append(
                    f"<tr>"
                    f"<td colspan='4'>✗ <b>{e['name']}</b>: "
                    f"<span style='color:#F44336'>{e['error']}</span></td>"
                    f"</tr>"
                )
                log_lines.append(f"✗ {e['name']}: {e['error']}")

        html_parts.append("</table>")

        self.log("Aggiornamento completato:\n" + "\n".join(log_lines))

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Aggiornamento completato")
        msg_box.setTextFormat(Qt.TextFormat.RichText)
        msg_box.setText("".join(html_parts))
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.exec()

    def _download_to_temp_csv(self, url):
        """Scarica un URL CSV in un file temporaneo e restituisce il percorso.
        Usato per Google Sheets che usa redirect HTTP non gestiti da GDAL in QGIS 4."""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/csv,text/plain,*/*',
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            content = response.read()
        tmp = tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False)
        tmp.write(content)
        tmp.close()
        return tmp.name

    def load_ogr_data(self):
        """Carica dati OGR/GDAL da URL"""
        url = self.ogr_url_edit.text().strip()
        
        if not url:
            QMessageBox.warning(self, "Errore", "Inserisci un URL valido!")
            return
            
        if not url.startswith(('http://', 'https://', 'ftp://')):
            QMessageBox.warning(self, "Errore", "L'URL deve iniziare con http://, https:// o ftp://")
            return
            
        try:
            self.log(f"Caricamento da: {url[:50]}...")
            
            # Usa il nome personalizzato se inserito, altrimenti genera automaticamente
            if self.ogr_layer_custom_name.text().strip():
                layer_name = self.ogr_layer_custom_name.text().strip()
            else:
                layer_name = f"OGR_{os.path.basename(url.split('?')[0])}"
                if not layer_name or layer_name == "OGR_":
                    layer_name = "OGR_Online_Data"
            
            # Prepara l'URL con eventuali parametri aggiuntivi
            ogr_url = url
            if self.ogr_params.text().strip():
                separator = "&" if "?" in url else "?"
                ogr_url = f"{url}{separator}{self.ogr_params.text().strip()}"

            # Per Google Sheets: scarica CSV → salva come GeoPackage → carica GeoPackage.
            # GDAL/OGR in QGIS 4 non segue i redirect HTTP 302/303 di Google;
            # urllib.request li gestisce correttamente.
            is_google_sheets = 'docs.google.com' in url
            actual_ogr_url = ogr_url
            gpkg_path_for_gs = None

            if is_google_sheets:
                # Determina il percorso GeoPackage
                gpkg_path_for_gs = self.gpkg_path_edit.text().strip()
                if not gpkg_path_for_gs:
                    gpkg_path_for_gs, _ = QFileDialog.getSaveFileName(
                        self, "Salva GeoPackage", f"{layer_name}.gpkg", "GeoPackage (*.gpkg)"
                    )
                    if not gpkg_path_for_gs:
                        self.log("Operazione annullata dall'utente")
                        return
                    if not gpkg_path_for_gs.lower().endswith('.gpkg'):
                        gpkg_path_for_gs += '.gpkg'
                    self.gpkg_path_edit.setText(gpkg_path_for_gs)

                self.log("Google Sheets rilevato - scarico CSV...")
                try:
                    temp_csv_path = self._download_to_temp_csv(ogr_url)
                    self.log("CSV scaricato, salvo nel GeoPackage...")
                    ok, msg = self._save_csv_to_geopackage(temp_csv_path, gpkg_path_for_gs, layer_name)
                    try:
                        os.remove(temp_csv_path)
                    except Exception:
                        pass
                    if not ok:
                        QMessageBox.critical(self, "Errore", f"Errore salvataggio GeoPackage: {msg}")
                        return
                    actual_ogr_url = gpkg_path_for_gs
                    self._write_source_registry(gpkg_path_for_gs, layer_name, ogr_url)
                    self.log(f"GeoPackage salvato: {gpkg_path_for_gs}")
                except urllib.error.URLError as dl_err:
                    QMessageBox.critical(self, "Errore", f"Download fallito: {dl_err}")
                    return
                except Exception as dl_err:
                    QMessageBox.critical(self, "Errore", f"Errore: {dl_err}")
                    return

            # Determina la modalità di caricamento
            direct_points_mode = self.direct_points_radio.isChecked()
            
            if direct_points_mode:
                # Modalità: crea direttamente il layer di punti
                self.log("Modalità: creazione diretta layer punti con OGR")

                # Carica il layer OGR (actual_ogr_url è già il file locale per Google Sheets)
                ogr_layer = QgsVectorLayer(actual_ogr_url, layer_name, "ogr")

                # Prova approcci alternativi se il primo tentativo fallisce
                if not ogr_layer.isValid():
                    self.log("Primo tentativo fallito, provo approcci alternativi...")

                    if url.lower().endswith('.zip'):
                        zip_url = f"/vsizip/vsicurl/{url}"
                        ogr_layer = QgsVectorLayer(zip_url, layer_name, "ogr")

                    if not ogr_layer.isValid():
                        curl_url = f"/vsicurl/{url}"
                        ogr_layer = QgsVectorLayer(curl_url, layer_name, "ogr")

                    if not ogr_layer.isValid() and self.ogr_layer_name_edit.text():
                        layer_specific_url = f"{actual_ogr_url}|layername={self.ogr_layer_name_edit.text()}"
                        ogr_layer = QgsVectorLayer(layer_specific_url, layer_name, "ogr")
                
                if not ogr_layer.isValid():
                    QMessageBox.critical(self, "Errore", "Impossibile caricare i dati dall'URL.")
                    return
                
                # Applica CRS forzato se specificato
                if self.ogr_crs_edit.text().strip():
                    try:
                        forced_crs = QgsCoordinateReferenceSystem(self.ogr_crs_edit.text().strip())
                        if forced_crs.isValid():
                            ogr_layer.setCrs(forced_crs)
                            self.log(f"CRS forzato applicato: {forced_crs.authid()}")
                    except:
                        self.log("CRS forzato non valido, uso quello del layer")
                
                # Ottieni i campi disponibili
                available_fields = [field.name() for field in ogr_layer.fields()]
                self.log(f"Campi disponibili: {', '.join(available_fields)}")
                
                # Mostra dialog per selezione campi coordinate
                coord_dialog = CoordinateFieldsDialog(available_fields, self)
                
                if coord_dialog.exec() != QDialog.DialogCode.Accepted:
                    self.log("Selezione campi annullata dall'utente")
                    return
                
                # Ottieni i campi selezionati
                lat_field, lon_field = coord_dialog.get_selected_fields()
                selected_cols_from_dialog = coord_dialog.get_selected_columns()
                
                if not lat_field or not lon_field:
                    QMessageBox.warning(self, "Errore", "Devi selezionare entrambi i campi di coordinate!")
                    return
                
                # Verifica che i campi selezionati esistano
                if lat_field not in available_fields or lon_field not in available_fields:
                    QMessageBox.warning(self, "Errore", "I campi selezionati non esistono nel dataset!")
                    return
                
                self.log(f"Campi coordinate selezionati - Lat: {lat_field}, Lon: {lon_field}")
                
                # Ottieni il CRS per il layer punti
                crs = self.get_selected_crs()

                # Se è stato specificato un CRS forzato, usalo anche per il layer punti
                if self.ogr_crs_edit.text().strip():
                    forced_crs = QgsCoordinateReferenceSystem(self.ogr_crs_edit.text().strip())
                    if forced_crs.isValid():
                        crs = forced_crs
                        self.log(f"CRS per layer punti: {forced_crs.authid()}")

                # Crea il layer di punti usando direttamente il layer OGR
                points_layer_name = f"Points_{layer_name}"

                # Aggiungi prima il layer OGR al progetto (necessario per il Virtual Layer)
                QgsProject.instance().addMapLayer(ogr_layer)
                self.source_layer = ogr_layer

                # Traccia sorgente Google Sheets per aggiornamento manuale
                if is_google_sheets:
                    self._gs_url = ogr_url
                    self._gs_gpkg_path = gpkg_path_for_gs
                    self._gs_source_layer_id = ogr_layer.id()
                    self.refresh_gs_btn.setEnabled(True)

                # Crea Virtual Layer collegato alla sorgente dati
                # Usa le colonne scelte nel dialog; fallback su tutte le colonne
                success = self._create_virtual_points_layer(
                    ogr_layer, lon_field, lat_field,
                    points_layer_name, crs,
                    selected_fields=selected_cols_from_dialog
                )

                if success:
                    # Aggiorna l'interfaccia
                    self.x_field_combo.clear()
                    self.y_field_combo.clear()
                    for field in available_fields:
                        self.x_field_combo.addItem(field)
                        self.y_field_combo.addItem(field)

                    self.x_field_combo.setCurrentText(lon_field)
                    self.y_field_combo.setCurrentText(lat_field)
                    # Aggiorna il pulsante colonne
                    self._selected_columns = selected_cols_from_dialog
                    self._available_fields_cache = available_fields
                    n = len(selected_cols_from_dialog) if selected_cols_from_dialog else len(available_fields)
                    self.columns_btn.setText(f"{n} / {len(available_fields)} colonne selezionate  ✎")
                    self.columns_btn.setEnabled(True)

                    # Abilita i controlli per esportazione
                    self.export_btn.setEnabled(True)
                    self.quick_save_btn.setEnabled(True)

                    # Passa alla scheda Layer QGIS
                    self.source_tabs.setCurrentIndex(1)

                    feature_count = self.points_layer.featureCount()
                    source_count = ogr_layer.featureCount()
                    gs_note = f"\nGeoPackage: {gpkg_path_for_gs}\n✓ Usa '↻ Aggiorna dati' per sincronizzare con Google Sheets." if is_google_sheets else ""

                    QMessageBox.information(
                        self, "Successo",
                        f"Dati caricati e mappati automaticamente!\n\n"
                        f"Layer punti: {points_layer_name}\n"
                        f"Layer origine: {layer_name}\n"
                        f"X (Lon): {lon_field}, Y (Lat): {lat_field}\n"
                        f"Features: {feature_count} / {source_count}\n"
                        f"CRS: {crs.authid()}{gs_note}"
                    )
                    return
                else:
                    QMessageBox.critical(self, "Errore", "Impossibile creare il layer di punti.")
                    self.log("Impossibile creare il layer di punti")
                    return
            else:
                # Modalità: scarica solo la tabella
                self.log("Modalità: scarica solo tabella")

                # Crea il layer vettoriale (actual_ogr_url è già il file locale per Google Sheets)
                ogr_layer = QgsVectorLayer(actual_ogr_url, layer_name, "ogr")

                # Prova approcci alternativi se il primo tentativo fallisce
                if not ogr_layer.isValid():
                    self.log("Primo tentativo fallito, provo approcci alternativi...")

                    if url.lower().endswith('.zip'):
                        zip_url = f"/vsizip/vsicurl/{url}"
                        ogr_layer = QgsVectorLayer(zip_url, layer_name, "ogr")

                    if not ogr_layer.isValid():
                        curl_url = f"/vsicurl/{url}"
                        ogr_layer = QgsVectorLayer(curl_url, layer_name, "ogr")

                    if not ogr_layer.isValid() and self.ogr_layer_name_edit.text():
                        layer_specific_url = f"{actual_ogr_url}|layername={self.ogr_layer_name_edit.text()}"
                        ogr_layer = QgsVectorLayer(layer_specific_url, layer_name, "ogr")
                
                if ogr_layer.isValid():
                    # Applica CRS forzato se specificato
                    if self.ogr_crs_edit.text().strip():
                        try:
                            forced_crs = QgsCoordinateReferenceSystem(self.ogr_crs_edit.text().strip())
                            if forced_crs.isValid():
                                ogr_layer.setCrs(forced_crs)
                                self.log(f"CRS forzato: {forced_crs.authid()}")
                        except:
                            self.log("CRS non valido, uso quello del layer")
                    
                    # Aggiungi il layer OGR al progetto
                    QgsProject.instance().addMapLayer(ogr_layer)
                    self.source_layer = ogr_layer

                    # Traccia sorgente Google Sheets per aggiornamento manuale
                    if is_google_sheets:
                        self._gs_url = ogr_url
                        self._gs_gpkg_path = gpkg_path_for_gs
                        self._gs_source_layer_id = ogr_layer.id()
                        self.refresh_gs_btn.setEnabled(True)

                    # Aggiorna la lista dei layer
                    self.update_layer_list()

                    # Seleziona il layer appena caricato
                    index = self.layer_combo.findText(layer_name)
                    if index >= 0:
                        self.layer_combo.setCurrentIndex(index)
                        self.force_update_field_combos(ogr_layer)

                    # Passa alla scheda Layer QGIS
                    self.source_tabs.setCurrentIndex(1)

                    feature_count = ogr_layer.featureCount()
                    geometry_type = QgsWkbTypes.displayString(ogr_layer.wkbType())
                    crs_info = ogr_layer.crs().authid()
                    gs_note = f"\nGeoPackage: {gpkg_path_for_gs}\n✓ Usa '↻ Aggiorna dati' per sincronizzare con Google Sheets." if is_google_sheets else ""

                    self.log(f"Layer tabellare caricato: {layer_name} ({feature_count} features)")

                    QMessageBox.information(
                        self, "Successo",
                        f"Layer caricato: {layer_name}\n\n"
                        f"Tipo: {geometry_type}\n"
                        f"CRS: {crs_info}\n"
                        f"Features: {feature_count}{gs_note}\n\n"
                        f"Usa la scheda 'Layer QGIS' per configurare la mappatura dei punti."
                    )
                else:
                    QMessageBox.critical(self, "Errore", "Impossibile caricare i dati dall'URL.")
                    self.log("Errore nel caricamento")
                    
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore: {str(e)}")
            self.log(f"Errore: {str(e)}")

    def _create_virtual_points_layer(self, source_layer, x_field, y_field, layer_name, crs,
                                      selected_fields=None):
        """Crea un Virtual Layer di punti che si aggiorna automaticamente con la sorgente"""
        try:
            # Ottieni l'ID del layer sorgente
            source_layer_id = source_layer.id()
            source_layer_name = source_layer.name()

            # Usa le colonne selezionate dall'utente, o tutte se non specificate
            all_field_names = [field.name() for field in source_layer.fields()]
            if selected_fields:
                # Mantieni sempre i campi X/Y anche se non selezionati esplicitamente
                field_names = list(dict.fromkeys(
                    [f for f in selected_fields if f in all_field_names] +
                    ([x_field] if x_field not in selected_fields else []) +
                    ([y_field] if y_field not in selected_fields else [])
                ))
            else:
                field_names = all_field_names
            fields_to_select = [f'"{name}"' for name in field_names]
            fields_str = ", ".join(fields_to_select)

            # Costruisci la query SQL per il Virtual Layer
            # Usa make_point per creare geometrie punto dalle coordinate
            query = f"""
            SELECT
                {fields_str},
                make_point(CAST("{x_field}" AS REAL), CAST("{y_field}" AS REAL)) as geometry
            FROM
                "{source_layer_id}"
            WHERE
                "{x_field}" IS NOT NULL
                AND "{y_field}" IS NOT NULL
                AND CAST("{x_field}" AS TEXT) != ''
                AND CAST("{y_field}" AS TEXT) != ''
            """

            # Crea l'URI per il Virtual Layer
            # Il Virtual Layer si aggiorna automaticamente quando cambia la sorgente
            # NON specificare uid - lascia che QGIS lo generi automaticamente
            uri = f"?query={query}&geometry=geometry:Point:{crs.postgisSrid()}"

            # Crea il Virtual Layer
            virtual_layer = QgsVectorLayer(uri, layer_name, "virtual")

            if not virtual_layer.isValid():
                self.log(f"Impossibile creare il Virtual Layer: {layer_name}")
                self.log(f"Query usata: {query}")
                return False

            # Imposta il CRS
            virtual_layer.setCrs(crs)

            # Aggiungi il layer al progetto
            QgsProject.instance().addMapLayer(virtual_layer)
            self.points_layer = virtual_layer

            feature_count = virtual_layer.featureCount()
            self.log(f"Virtual Layer creato: {layer_name} ({feature_count} features)")
            self.log(f"Il layer si aggiorna automaticamente con '{source_layer_name}'")

            return True

        except Exception as e:
            self.log(f"Errore creazione Virtual Layer: {str(e)}")
            return False

    def _create_points_layer(self, source_layer, x_field, y_field, layer_name, crs):
        """Crea un layer di punti da un layer con campi di coordinate"""
        try:
            # Crea un layer di punti in memoria
            points_layer = QgsVectorLayer(f"Point?crs={crs.authid()}", layer_name, "memory")

            if not points_layer.isValid():
                self.log(f"Impossibile creare il layer: {layer_name}")
                return False

            # Ottieni il provider del layer
            provider = points_layer.dataProvider()

            # Aggiungi tutti i campi del layer di origine più alcuni campi aggiuntivi
            fields = QgsFields()
            for field in source_layer.fields():
                fields.append(field)

            # Aggiungi campi aggiuntivi per tracciare la provenienza
            fields.append(QgsField("source_id", _FIELD_INT))
            fields.append(QgsField("crs_info", _FIELD_STRING))
            fields.append(QgsField("created_at", _FIELD_STRING))

            provider.addAttributes(fields)
            points_layer.updateFields()

            # Crea le feature per il layer di punti
            features = []
            create_time = self.get_timestamp()

            for feature in source_layer.getFeatures():
                try:
                    x_val = feature[x_field]
                    y_val = feature[y_field]

                    if x_val is not None and y_val is not None:
                        x = float(x_val)
                        y = float(y_val)

                        # Crea un punto
                        point = QgsPointXY(x, y)
                        geom = QgsGeometry.fromPointXY(point)

                        # Crea una nuova feature
                        new_feature = QgsFeature()
                        new_feature.setGeometry(geom)

                        # Copia gli attributi dalla feature originale
                        attributes = []
                        for field in source_layer.fields():
                            attributes.append(feature[field.name()])

                        # Aggiungi gli attributi aggiuntivi
                        attributes.append(feature.id())  # source_id
                        attributes.append(crs.authid())   # crs_info
                        attributes.append(create_time)   # created_at

                        new_feature.setAttributes(attributes)
                        features.append(new_feature)

                except Exception as e:
                    self.log(f"Errore elaborazione feature: {str(e)}")
                    continue

            # Aggiungi le feature al layer
            provider.addFeatures(features)
            points_layer.updateExtents()

            # Aggiungi il layer al progetto
            QgsProject.instance().addMapLayer(points_layer)
            self.points_layer = points_layer

            self.log(f"Layer punti creato: {layer_name} ({len(features)} features)")
            return True

        except Exception as e:
            self.log(f"Errore creazione layer punti: {str(e)}")
            return False

    def create_points_layer(self):
        """Crea il layer di punti dalla configurazione corrente"""
        if not self.source_layer:
            QMessageBox.warning(self, "Errore", "Nessun layer di origine selezionato!")
            return

        x_field = self.x_field_combo.currentText()
        y_field = self.y_field_combo.currentText()

        if not x_field or not y_field:
            QMessageBox.warning(self, "Errore", "Seleziona i campi X e Y!")
            return

        layer_name = self.layer_name_edit.text().strip()
        if not layer_name:
            layer_name = "Punti_Dinamici"

        crs = self.get_selected_crs()

        # Crea Virtual Layer collegato alla sorgente dati
        success = self._create_virtual_points_layer(
            self.source_layer, x_field, y_field, layer_name, crs,
            selected_fields=self._selected_columns
        )

        if success:
            self.export_btn.setEnabled(True)
            self.quick_save_btn.setEnabled(True)
            QMessageBox.information(
                self, "Successo",
                f"Layer punti creato con successo!\n\n"
                f"Nome: {layer_name}\n"
                f"Tipo: Virtual Layer (auto-update)\n"
                f"Features: {self.points_layer.featureCount()}\n"
                f"CRS: {crs.authid()}\n\n"
                f"✓ Il layer si aggiorna automaticamente con la sorgente!"
            )
        else:
            QMessageBox.critical(self, "Errore", "Impossibile creare il layer di punti.")

    def get_selected_crs(self):
        """Restituisce il CRS selezionato"""
        return self.crs_selector.crs()

    def setup_crs_combo(self):
        """Configura la combo dei CRS comuni"""
        common_crs = [
            "EPSG:4326 - WGS 84",
            "EPSG:3857 - WGS 84 / Pseudo-Mercator",
            "EPSG:32632 - WGS 84 / UTM zone 32N",
            "EPSG:32633 - WGS 84 / UTM zone 33N",
            "EPSG:3003 - Monte Mario / Gauss-Boaga fuso Est",
            "EPSG:32634 - WGS 84 / UTM zone 34N",
            "EPSG:4258 - ETRS89",
            "EPSG:23032 - ED50 / UTM zone 32N"
        ]
        
        self.crs_combo.addItems(common_crs)
        self.crs_combo.setCurrentIndex(0)

    def on_crs_combo_changed(self, text):
        """Gestisce il cambio di CRS nella combo"""
        if text:
            crs_authid = text.split(" - ")[0]
            crs = QgsCoordinateReferenceSystem(crs_authid)
            if crs.isValid():
                self.crs_selector.setCrs(crs)
                self.current_crs_label.setText(f"CRS: {crs.description()}")

    def select_custom_crs(self):
        """Apre il selettore di CRS personalizzato"""
        crs_dialog = QDialog(self)
        crs_dialog.setWindowTitle("Seleziona CRS")
        crs_dialog.setFixedSize(600, 400)
        
        layout = QVBoxLayout()
        
        # Widget di selezione CRS
        selector = QgsProjectionSelectionWidget()
        selector.setCrs(self.crs_selector.crs())
        layout.addWidget(selector)
        
        # Pulsanti
        btn_layout = QHBoxLayout()
        
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(lambda: self.accept_crs(selector, crs_dialog))
        btn_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("Annulla")
        cancel_btn.clicked.connect(crs_dialog.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        crs_dialog.setLayout(layout)
        crs_dialog.exec()

    def accept_crs(self, selector, dialog):
        """Accetta il CRS selezionato"""
        crs = selector.crs()
        if crs.isValid():
            self.crs_selector.setCrs(crs)
            self.current_crs_label.setText(f"CRS: {crs.description()}")
            dialog.accept()

    def update_layer_list(self):
        """Aggiorna la lista dei layer disponibili"""
        self.layer_combo.clear()
        
        layers = QgsProject.instance().mapLayers().values()
        vector_layers = [layer for layer in layers if isinstance(layer, QgsVectorLayer)]
        
        for layer in vector_layers:
            self.layer_combo.addItem(layer.name(), layer)

    def on_layer_changed(self, layer_name):
        """Gestisce il cambio di layer selezionato"""
        index = self.layer_combo.currentIndex()
        if index >= 0:
            layer = self.layer_combo.itemData(index)
            if layer and isinstance(layer, QgsVectorLayer):
                self.source_layer = layer
                self.force_update_field_combos(layer)

    def force_update_field_combos(self, layer):
        """Aggiorna forzatamente le combo dei campi"""
        self.x_field_combo.clear()
        self.y_field_combo.clear()

        fields = layer.fields()
        field_names = [fields.field(i).name() for i in range(fields.count())]
        for name in field_names:
            self.x_field_combo.addItem(name)
            self.y_field_combo.addItem(name)
        self._available_fields_cache = field_names
        self._selected_columns = None  # reset: tutte le colonne
        self.columns_btn.setText(f"{len(field_names)} / {len(field_names)} colonne selezionate  ✎")
        self.columns_btn.setEnabled(True)

        # Auto-seleziona campi coordinate se disponibili
        self.auto_select_coordinate_fields()

    def auto_select_coordinate_fields(self):
        """Seleziona automaticamente i campi coordinate"""
        lat_keywords = ['lat', 'latitude', 'y', 'northing', 'Lat']
        lon_keywords = ['lon', 'lng', 'longitude', 'x', 'easting', 'long', 'Long']
        
        lat_field = None
        lon_field = None
        
        # Cerca nei campi disponibili
        for i in range(self.x_field_combo.count()):
            field_name = self.x_field_combo.itemText(i)
            
            # Controlla latitudine
            if not lat_field:
                for keyword in lat_keywords:
                    if keyword.lower() in field_name.lower():
                        lat_field = field_name
                        self.y_field_combo.setCurrentIndex(i)
                        break
            
            # Controlla longitudine
            if not lon_field:
                for keyword in lon_keywords:
                    if keyword.lower() in field_name.lower():
                        lon_field = field_name
                        self.x_field_combo.setCurrentIndex(i)
                        break
            
            if lat_field and lon_field:
                break

    def _open_columns_dialog(self):
        """Apre il dialog per modificare la selezione delle colonne."""
        if not self._available_fields_cache:
            return
        dlg = CoordinateFieldsDialog(self._available_fields_cache, self)
        # Pre-seleziona lat/lon correnti
        dlg.lat_combo.setCurrentText(self.y_field_combo.currentText())
        dlg.lon_combo.setCurrentText(self.x_field_combo.currentText())
        # Pre-seleziona colonne già scelte
        if self._selected_columns is not None:
            dlg._col_list.blockSignals(True)
            for i in range(dlg._col_list.count()):
                item = dlg._col_list.item(i)
                item.setCheckState(
                    _Qt_Checked if item.text() in self._selected_columns else _Qt_Unchecked
                )
            dlg._col_list.blockSignals(False)
            dlg._update_col_count()
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._selected_columns = dlg.get_selected_columns()
            n = len(self._selected_columns) if self._selected_columns else len(self._available_fields_cache)
            self.columns_btn.setText(f"{n} / {len(self._available_fields_cache)} colonne selezionate  ✎")

    def refresh_fields(self):
        """Aggiorna i campi del layer corrente"""
        if self.source_layer:
            self.force_update_field_combos(self.source_layer)
            self.log("Campi aggiornati")

    def on_source_tab_changed(self, index):
        """Gestisce il cambio di scheda delle sorgenti"""
        if index == 0:  # Tab OGR
            self.log("Modalità: Caricamento dati da URL")
        elif index == 1:  # Tab Layer QGIS
            self.log("Modalità: Layer dal progetto QGIS")

    def log(self, message):
        """Aggiunge un messaggio al log"""
        timestamp = self.get_timestamp()
        self.log_text.append(f"[{timestamp}] {message}")
        
        # Auto-scroll alla fine
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def get_timestamp(self):
        """Restituisce un timestamp formattato"""
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")


# Classe per l'integrazione con Processing
class GeoPointManagerAlgorithm(QgsProcessingAlgorithm):
    """
    Algoritmo di processing per GeoPoint Manager
    """
    
    def __init__(self):
        super().__init__()
    
    def createInstance(self):
        return GeoPointManagerAlgorithm()
    
    def name(self):
        return 'geopointmanager'
    
    def displayName(self):
        return 'GeoPoint Manager - v5.1'
    
    def group(self):
        return 'GeoPoint Manager'
    
    def groupId(self):
        return 'GeoPoint Manager'
    
    def shortHelpString(self):
        return """
        <h3>GeoPoint Manager v5.1</h3>
        <p>Plugin per creare layer di punti da sorgenti dati con coordinate</p>
        <h4>Funzionalità:</h4>
        <ul>
            <li>Caricamento dati da URL (GeoJSON, WFS, CSV, Google Sheets, ecc.)</li>
            <li>Utilizzo layer QGIS esistenti nel progetto</li>
            <li>Creazione automatica layer punti da campi coordinate</li>
            <li>Virtual Layer collegato alla sorgente dati</li>
            <li><b>NUOVO v5.1:</b> Fix Google Sheets su QGIS 4 — download via urllib, salvataggio GeoPackage scelto dall'utente, aggiornamento manuale on-demand</li>
            <li>Esportazione in vari formati (GeoPackage, Shapefile, ecc.)</li>
        </ul>
        """
    
    def initAlgorithm(self, config=None):
        pass
    
    def processAlgorithm(self, parameters, context, feedback):
        # Mostra la dialog
        dialog = GeoPointManagerDialog()
        dialog.exec()
        
        return {}


# Provider per Processing
class GeoPointManagerProvider(QgsProcessingProvider):

    def __init__(self):
        super().__init__()

    def id(self):
        return 'geopointmanager'

    def name(self):
        return 'GeoPoint Manager'

    def longName(self):
        return 'GeoPoint Manager - Strumenti per la gestione di punti geografici'

    def loadAlgorithms(self):
        """Metodo astratto obbligatorio: registra gli algoritmi del provider."""
        self.addAlgorithm(GeoPointManagerAlgorithm())


# Funzione per avviare il plugin
def run_geopoint_manager():
    dialog = GeoPointManagerDialog()
    dialog.exec()


# Punto di ingresso per Processing
def instance():
    return GeoPointManagerProvider()


# Se eseguito come script standalone
if __name__ == '__main__':
    run_geopoint_manager()