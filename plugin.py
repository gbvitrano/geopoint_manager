# -*- coding: utf-8 -*-
"""
GeoPoint Manager - Classe principale del plugin QGIS
Gestisce: toolbar, voce di menu, provider Processing, caricamento/scaricamento
"""

import os
from qgis.PyQt.QtWidgets import QAction, QToolButton, QMenu
from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsApplication


class GeoPointManagerPlugin:
    """Classe principale del plugin GeoPoint Manager."""

    def __init__(self, iface):
        """
        Costruttore.

        :param iface: istanza QgsInterface fornita da QGIS all'avvio
        """
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.provider = None
        self.toolbar_action = None
        self.menu_action = None

    # ------------------------------------------------------------------
    # Ciclo di vita del plugin
    # ------------------------------------------------------------------

    def initGui(self):
        """Chiamata da QGIS al caricamento del plugin (al login / avvio)."""

        # Icona: usa icons/icon.svg se presente, altrimenti icona QGIS generica
        icon_path = os.path.join(self.plugin_dir, "icons", "icon.svg")
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
        else:
            icon = QgsApplication.getThemeIcon("/mActionAddOgrLayer.svg")

        # --- Azione principale ---
        self.toolbar_action = QAction(
            icon,
            "GeoPoint Manager",
            self.iface.mainWindow()
        )
        self.toolbar_action.setToolTip(
            "GeoPoint Manager v5.1 — Crea layer di punti da sorgenti coordinate"
        )
        self.toolbar_action.triggered.connect(self.run)

        # --- Voce nel menu Vettore > GeoPoint Manager ---
        self.iface.addPluginToVectorMenu("GeoPoint Manager", self.toolbar_action)

        # --- Pulsante nella toolbar principale ---
        self.iface.addToolBarIcon(self.toolbar_action)

        # --- Registra il provider Processing ---
        self._load_provider()

    def unload(self):
        """Chiamata da QGIS allo scaricamento del plugin."""

        # Rimuove voce menu e toolbar
        self.iface.removePluginVectorMenu("GeoPoint Manager", self.toolbar_action)
        self.iface.removeToolBarIcon(self.toolbar_action)

        # Rimuove il provider Processing
        self._unload_provider()

    # ------------------------------------------------------------------
    # Azioni
    # ------------------------------------------------------------------

    def run(self):
        """Apre la dialog principale di GeoPoint Manager."""
        from .geopoint_manager_dialog import GeoPointManagerDialog
        dialog = GeoPointManagerDialog(self.iface.mainWindow())
        dialog.exec()

    # ------------------------------------------------------------------
    # Processing provider
    # ------------------------------------------------------------------

    def _load_provider(self):
        """Registra il provider Processing di GeoPoint Manager."""
        try:
            from .geopoint_manager_dialog import GeoPointManagerProvider
            self.provider = GeoPointManagerProvider()
            QgsApplication.processingRegistry().addProvider(self.provider)
        except Exception as e:
            from qgis.core import QgsMessageLog, Qgis
            QgsMessageLog.logMessage(
                f"GeoPoint Manager: errore caricamento provider Processing: {e}",
                "GeoPoint Manager",
                Qgis.MessageLevel.Warning
            )

    def _unload_provider(self):
        """Rimuove il provider Processing dal registro."""
        if self.provider:
            try:
                QgsApplication.processingRegistry().removeProvider(self.provider)
            except Exception:
                pass
            self.provider = None
