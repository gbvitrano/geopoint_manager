# -*- coding: utf-8 -*-
"""
GeoPoint Manager - Plugin QGIS
Crea layer di punti da sorgenti dati con coordinate

Funzione classFactory() richiesta da QGIS per caricare il plugin.
"""


def classFactory(iface):
    """
    Punto di ingresso obbligatorio per ogni plugin QGIS.
    
    :param iface: istanza di QgsInterface fornita da QGIS
    :type iface: QgsInterface
    :returns: istanza del plugin principale
    :rtype: GeoPointManagerPlugin
    """
    from .plugin import GeoPointManagerPlugin
    return GeoPointManagerPlugin(iface)
