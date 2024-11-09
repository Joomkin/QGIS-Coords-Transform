import os
from qgis.PyQt.QtCore import Qt
from qgis.PyQt import uic, QtWidgets
from qgis.PyQt.QtWidgets import QDialog, QStackedWidget, QWidget
from qgis.core import QgsVectorLayer, QgsProject, QgsFeature, QgsGeometry, QgsPointXY, QgsWkbTypes, QgsField

from PyQt5.QtCore import QSettings, QTranslator, QVariant, QCoreApplication



# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'Transform_Coordinates_dialog_base.ui'))


class TransformCoordsDialog(QDialog):
    def __init__(self, transform_coords, parent=None):
        super(TransformCoordsDialog, self).__init__(parent)
        self.transform_coords = transform_coords
        self.ui = FORM_CLASS()

        # Window setup
        self.setWindowTitle("Transformar Coordenadas")
        self.setGeometry(100, 100, 400, 450)
        self.setFixedSize(400, 450)
        self.stacked_inputs = QStackedWidget(self)

        # Final Coords: 
        self.result_line_edit = QtWidgets.QLineEdit(self)
        self.result_line_edit.setReadOnly(True)

        
        self.huso_combo_box = QtWidgets.QComboBox(self)
        self.huso_combo_box.addItems(["17S [islas]", "18S [sur]", "19S [centro/norte]"])


        self.format_selector = QtWidgets.QComboBox(self)
        self.format_selector.addItems(["Decimal", "Grados/Minuto/Segundo", "UTM (xd)"])

        # Decimal Coords
        self.lat_input = QtWidgets.QLineEdit(self)
        self.lon_input = QtWidgets.QLineEdit(self)

        self.lat_input.setPlaceholderText("Latitud")
        self.lon_input.setPlaceholderText("Longitud")

        # Degreee-Minute-Second
        self.lat_deg_input = QtWidgets.QLineEdit(self)
        self.lat_min_input = QtWidgets.QLineEdit(self)
        self.lat_sec_input = QtWidgets.QLineEdit(self)
        self.lon_deg_input = QtWidgets.QLineEdit(self)
        self.lon_min_input = QtWidgets.QLineEdit(self)
        self.lon_sec_input = QtWidgets.QLineEdit(self)

        # UTM 
        self.este = QtWidgets.QLineEdit(self)
        self.norte = QtWidgets.QLineEdit(self)

        self.este.setPlaceholderText("Coordenadas Norte")
        self.norte.setPlaceholderText("Coordenadas Este")

        # To name a Point
        self.point_name_input = QtWidgets.QLineEdit(self)
        self.point_name_input.setPlaceholderText("Nombre del punto")
        

        # Aceptar/Cancelar // Accept/Cancel
        self.button_box = QtWidgets.QDialogButtonBox(self)
        self.button_box.setStandardButtons(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)

        # Connects the Accept button
        self.button_box.accepted.connect(self.on_accept)
        self.button_box.rejected.connect(self.reject)

        self.button_box.button(QtWidgets.QDialogButtonBox.Ok).setText("Transformar")
        self.button_box.button(QtWidgets.QDialogButtonBox.Cancel).setText("Cerrar")

        self.ejemplo = QtWidgets.QLabel(self)

        self.decimal = QtWidgets.QLabel(self)
        self.dms = QtWidgets.QLabel(self)

        ##############
        ### LAYOUT ###
        ##############

        self.sur_checkbox = QtWidgets.QCheckBox("Sur y Oeste?", self)
        self.create_point_checkbox = QtWidgets.QCheckBox("Crear punto en coordenadas ingresadas?", self)
        self.name_point_checkbox = QtWidgets.QCheckBox("Agregar punto con nombre?", self)


        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel("Formato de coordenadas de entrada:"))
        layout.addWidget(self.format_selector) # Type of coordinate options
        layout.addWidget(self.decimal)
        layout.addWidget(self.ejemplo)
        layout.addWidget(self.lat_input) #Edit line of Latitude
        layout.addWidget(self.lon_input) #Edit line of Longitude
        layout.addWidget(self.sur_checkbox)
        layout.addWidget(self.dms)
        layout.addWidget(self.norte) # UTM
        layout.addWidget(self.este) # UTM
        layout.addWidget(self.lat_deg_input)   # Degreee-Minute-Second   
        layout.addWidget(self.lat_min_input)   # Degreee-Minute-Second  
        layout.addWidget(self.lat_sec_input)   # Degreee-Minute-Second  
        layout.addWidget(self.lon_deg_input)   # Degreee-Minute-Second  
        layout.addWidget(self.lon_min_input)   # Degreee-Minute-Second  
        layout.addWidget(self.lon_sec_input)   # Degreee-Minute-Second
        layout.addWidget(self.create_point_checkbox) 
        layout.addWidget(self.name_point_checkbox)
        layout.addWidget(self.point_name_input)
        layout.addWidget(QtWidgets.QLabel("Huso UTM al que será transformado:"))
        layout.addWidget(self.huso_combo_box) 
        layout.addWidget(self.result_line_edit)
        layout.addWidget(self.button_box)

        self.point_name_input.setVisible(False)
        self.name_point_checkbox.setVisible(False)

        self.result_line_edit.setPlaceholderText(f"Acá estarán las coordenadas UTM resultantes")

        self.ejemplo.setText(f"Ejemplo (Decimal): -34.438, -71.07")   
        self.decimal.setText(f"Latitud y Longitud (Decimal):")
        self.dms.setText(f"Latitud y Longitud (Grado, Minuto, Segundo):")

        self.format_selector.currentIndexChanged.connect(self.update_input_visibility)
        self.create_point_checkbox.stateChanged.connect(self.toggle_name_options)


        self.update_input_visibility()

        self.ejemplo.setTextInteractionFlags(Qt.TextSelectableByMouse)

        #################################################################
        ### Gives text to Degreee-Minute-Second for easier use

        self.lat_deg_input.setPlaceholderText(f"Latitud (grado)")   # coords Degreee-Minute-Second   
        self.lat_min_input.setPlaceholderText(f"Latitud (minuto)")   # coords Degreee-Minute-Second  
        self.lat_sec_input.setPlaceholderText(f"Latitud (segundo)")   # coords Degreee-Minute-Second  
        self.lon_deg_input.setPlaceholderText(f"Longitud (grado)")   # coords Degreee-Minute-Second  
        self.lon_min_input.setPlaceholderText(f"Longitud (minuto)")   # coords Degreee-Minute-Second  
        self.lon_sec_input.setPlaceholderText(f"Longitud (segundo)")   # coords Degreee-Minute-Second    

    def on_accept(self):    # When you press "Transformar" (Accept), this function is called
        check = 0
        try:
            huso = self.huso_combo_box.currentText()

            if self.format_selector.currentText() == "Decimal":
                # Decimal input
                latitud = float(self.lat_input.text())
                longitud = float(self.lon_input.text())
                if not (-90 <= latitud <= 90):
                    raise ValueError("La latitud debe estar entre -90 y 90.")
                if not (-180 <= longitud <= 180):
                    raise ValueError("La longitud debe estar entre -180 y 180.")
            elif self.format_selector.currentText() == "Grados/Minuto/Segundo":
                # DMS input, convert to decimal
                lat_deg = int(self.lat_deg_input.text())
                lat_min = int(self.lat_min_input.text())
                lat_sec = float(self.lat_sec_input.text())
                lon_deg = int(self.lon_deg_input.text())
                lon_min = int(self.lon_min_input.text())
                lon_sec = float(self.lon_sec_input.text())
                latitud = self.dms_to_decimal(lat_deg, lat_min, lat_sec)
                longitud = self.dms_to_decimal(lon_deg, lon_min, lon_sec)
                if not (-90 <= latitud <= 90):
                    raise ValueError("La latitud debe estar entre -90 y 90.")
                if not (-180 <= longitud <= 180):
                    raise ValueError("La longitud debe estar entre -180 y 180.")
            else: # UTM
                latitud = float(self.norte.text())
                longitud = float(self.este.text())
                check = 1



            if check == 0:
                # Calls the transform function and gets the UTM coords
                x, y = self.transform_coords.transformar_coordenadas(latitud, longitud, huso)

                x = float(x)
                y = float(y)
            elif check == 1:
                x = latitud
                y = longitud

            # Show results in a line
            self.result_line_edit.setText(f"Coordenadas UTM (3 decimales): X: {x}, Y: {y}")

            if self.create_point_checkbox.isChecked(): #To create a Point in QGIS
                self.crear_punto_en_qgis(x, y, huso)

        except ValueError as e:
            self.result_line_edit.setText(f"Error (tipo de error): {str(e)}")

    def crear_punto_en_qgis(self, x, y, huso): # To create a point in QGIS

        huso_epsg = {
            "17S [islas]": "32717",
            "18S [sur]": "32718",
            "19S [centro/norte]": "32719"
        }
        epsg_code = huso_epsg.get(huso)


        layer = self.transform_coords.iface.activeLayer() # Active layer to add the point
        if not layer or not isinstance(layer, QgsVectorLayer) or layer.geometryType() != QgsWkbTypes.PointGeometry: # Or make a new layer
            layer = QgsVectorLayer(f"Point?crs=EPSG:{epsg_code}", "Capa Temporal uwu", "memory")

            layer_data_provider = layer.dataProvider()
            layer_data_provider.addAttributes([QgsField("ID", QVariant.Int), QgsField("Nombre", QVariant.String)])
            layer.updateFields()

            QgsProject.instance().addMapLayer(layer)
        
        point = QgsPointXY(x, y)
        feature = QgsFeature()
        feature.setGeometry(QgsGeometry.fromPointXY(point))

        field_count = layer.fields().count()
        attributes = [None] * field_count

        if "ID" in layer.fields().names():
            attributes[layer.fields().indexFromName("ID")] = layer.featureCount() + 1
        elif "id" in layer.fields().names():
            attributes[layer.fields().indexFromName("id")] = layer.featureCount() + 1

        # To add a name to the created point:
        if self.create_point_checkbox.isChecked():  
            nombre = self.point_name_input.text()  
            if nombre:
                attributes[layer.fields().indexFromName("Nombre")] = nombre

        feature.setAttributes(attributes)

        if not layer.isEditable():
            layer.startEditing()

        if layer.addFeature(feature):
            layer.commitChanges()
        else:
            layer.rollBack()
            print("Error al añadir la característica.")



    def update_input_visibility(self): # Change the Window, depending on the selected format
        if self.format_selector.currentText() == "Decimal":
            self.ejemplo.show()
            self.decimal.show()
            self.lat_input.show()
            self.lon_input.show()
            self.sur_checkbox.hide()
            self.dms.hide()
            self.norte.hide()
            self.este.hide()
            self.lat_deg_input.hide()
            self.lat_min_input.hide()
            self.lat_sec_input.hide()
            self.lon_deg_input.hide()
            self.lon_min_input.hide()
            self.lon_sec_input.hide()
        elif self.format_selector.currentText() == "Grados/Minuto/Segundo":
            self.ejemplo.hide()
            self.decimal.hide()
            self.lat_input.hide()
            self.lon_input.hide()
            self.norte.hide()
            self.este.hide()
            self.sur_checkbox.show()
            self.dms.show()
            self.lat_deg_input.show()
            self.lat_min_input.show()
            self.lat_sec_input.show()
            self.lon_deg_input.show()
            self.lon_min_input.show()
            self.lon_sec_input.show()
        else:
            self.ejemplo.hide()
            self.decimal.hide()
            self.lat_input.hide()
            self.lon_input.hide()
            self.sur_checkbox.hide()
            self.norte.show()
            self.este.show()
            self.dms.hide()
            self.lat_deg_input.hide()
            self.lat_min_input.hide()
            self.lat_sec_input.hide()
            self.lon_deg_input.hide()
            self.lon_min_input.hide()
            self.lon_sec_input.hide()



    def dms_to_decimal(self, grados, minutos, segundos): # Transforms Degreee-Minute-Second to decimal
        decimal = grados + (minutos / 60) + (segundos / 3600)
        if self.sur_checkbox.isChecked():
            decimal *= -1
        return decimal


    def toggle_name_options(self, state):
        if state == Qt.Checked:
            self.name_point_checkbox.setVisible(True)
            self.name_point_checkbox.stateChanged.connect(self.toggle_name_input)
        else:
            self.name_point_checkbox.setVisible(False)
            self.name_point_checkbox.setChecked(False)
            self.point_name_input.setVisible(False)

    def toggle_name_input(self, state):
        self.point_name_input.setVisible(state == Qt.Checked)





