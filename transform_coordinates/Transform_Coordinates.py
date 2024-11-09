from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt import QtWidgets
from qgis.PyQt.QtWidgets import QAction
from qgis.core import QgsCoordinateReferenceSystem, QgsVectorLayer, QgsFeature, QgsGeometry, QgsCoordinateTransform, QgsProject, QgsPointXY, QgsWkbTypes, QgsField


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

    def initGui(self):
        # Create the menu entries and toolbar icons inside the QGIS GUI
        icon_path = ':/plugins/Transform_Coordinates/icono.png'
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
        if result:
            try:
                latitud = float(self.dlg.lat_input.text())
                longitud = float(self.dlg.lon_input.text())
                huso = self.dlg.huso_combo_box.currentText()

                # Calls the transform function
                x, y = self.transformar_coordenadas(latitud, longitud, huso)

                # Show results 
                self.dlg.result_line_edit.setText(f"Coordenadas UTM: X: {x}, Y: {y}")

            except ValueError as e:
                self.dlg.result_label.setText(str(e))

    def transformar_coordenadas(self, latitud, longitud, huso): # This is the method that will transform the coords
        crs_wgs84 = QgsCoordinateReferenceSystem("EPSG:4326")
        crs_destino = { 
            '17S [islas]': QgsCoordinateReferenceSystem("EPSG:32717"),
            '18S [sur]': QgsCoordinateReferenceSystem("EPSG:32718"),
            '19S [centro/norte]': QgsCoordinateReferenceSystem("EPSG:32719"),
        }.get(huso)

        if not crs_destino:
            raise ValueError("Huso no válido. Elige 17S, 18S o 19S.")

        transformacion = QgsCoordinateTransform(crs_wgs84, crs_destino, QgsProject.instance())
        punto_origen = QgsPointXY(longitud, latitud)
        punto_destino = transformacion.transform(punto_origen)

        x_decimales = '%.3f'%(punto_destino.x())
        y_decimales = '%.3f'%(punto_destino.y())
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

