from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon, QFont, QColor
from qgis.PyQt import QtWidgets
from qgis.PyQt.QtWidgets import QAction
from qgis.core import (QgsCoordinateReferenceSystem, QgsVectorLayer, QgsFeature, QgsGeometry, QgsCoordinateTransform, 
                        QgsProject, QgsPointXY, QgsWkbTypes, QgsField, QgsTextFormat, QgsTextBufferSettings, 
                        QgsPalLayerSettings, QgsVectorLayerSimpleLabeling)


# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .Transform_Coordinates_dialog import TransformCoordsDialog
import os.path


class TransformCoords:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        self.iface = iface
        self.actions = []
        self.first_start = True
        self.dlg = None
        self.load_translation()

    def load_translation(self):
        path_to_i18n = os.path.join(os.path.dirname(__file__), 'i18n')
        translator = QTranslator()
        qm_file = os.path.join(path_to_i18n, 'plugin_es.qm')
        if translator.load('plugin_es.qm', path_to_i18n):
            QCoreApplication.installTranslator(translator)


    def initGui(self):
        # Create the menu entries and toolbar icons inside the QGIS GUI
        icon_path = ':/plugins/Transform_Coordinates/icono2.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Transform Coordinates'),
            callback=self.run,
            parent=self.iface.mainWindow())

    def add_action(self, icon_path, text, callback, enabled_flag=True, add_to_menu=True, add_to_toolbar=True, status_tip=None, whats_this=None, parent=None):
        # Add a toolbar icon to the toolbar
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToVectorMenu(self.tr(u'&Transform Coords'), action)

        self.actions.append(action)
        return action

    def run(self):
        # Run method that performs all the real work
        if self.first_start:
            self.first_start = False
            self.dlg = TransformCoordsDialog(self)

        self.dlg.show()
        result = self.dlg.exec_()

    def transformar_coordenadas(self, latitud, longitud, huso, huso_destino=0): # This is the method that will transform the coords
        if huso_destino == 0: # Decimales or Grado//Minuto//Segundo
            crs_wgs84 = QgsCoordinateReferenceSystem("EPSG:4326")

            transformacion = QgsCoordinateTransform(crs_wgs84, huso, QgsProject.instance())
            punto_origen = QgsPointXY(longitud, latitud)
            punto_transformado = transformacion.transform(punto_origen)
        else: # Para UTM
            epsg_origen = (huso) # Huso = EPSG en este caso. Ejemplo: "EPSG:32719"
            epsg_destino = (huso_destino)
            transformacion = QgsCoordinateTransform(epsg_origen, epsg_destino, QgsProject.instance())
            punto_origen = QgsPointXY((latitud), (longitud))
            punto_transformado = transformacion.transform(punto_origen)
        x_decimales = int(punto_transformado.x())
        y_decimales = int(punto_transformado.y())
        return x_decimales, y_decimales

    def tr(self, message):
        # Get the translation for a string using Qt translation API
        return QCoreApplication.translate('TransformCoords', message)

    def unload(self): # Remove from GUI
        for action in self.actions:
            # Remove from menu
            self.iface.removePluginVectorMenu(self.tr(u'&Transform Coords'), action)
            # Remove from bar
            self.iface.removeToolBarIcon(action)

