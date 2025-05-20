import os
import re
from qgis.PyQt.QtCore import Qt
from qgis.PyQt import uic, QtWidgets
from qgis.PyQt.QtWidgets import QDialog, QStackedWidget, QWidget
from qgis.PyQt.QtGui import QFont, QColor
from qgis.core import (QgsCoordinateReferenceSystem, QgsVectorLayer, QgsProject, QgsFeature, 
                        QgsGeometry, QgsPointXY, QgsWkbTypes, QgsField, QgsCoordinateTransform, 
                        QgsTextFormat, QgsTextBufferSettings, QgsPalLayerSettings, QgsVectorLayerSimpleLabeling)
from PyQt5.QtCore import QSettings, QTranslator, QVariant, QCoreApplication, QLocale

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'Transform_Coordinates_dialog_base.ui'))


class TransformCoordsDialog(QDialog):
    def __init__(self, transform_coords, parent=None):
        super(TransformCoordsDialog, self).__init__(parent)
        self.transform_coords = transform_coords
        self.ui = FORM_CLASS()
        self.project_crs = QgsProject.instance().crs()

        self.debug = 0

        # Window setup
        self.setWindowTitle(self.tr("Transform Coordinates"))
        self.setGeometry(100, 100, 400, 450)
        self.setFixedSize(400, 450)
        self.stacked_inputs = QStackedWidget(self)

        # Final Coords: 
        self.result_line_edit = QtWidgets.QLineEdit(self)
        self.result_line_edit.setReadOnly(True)

        self.help_button = QtWidgets.QPushButton(self.tr("Instructions"), self) # User will press for help
        self.huso_destino = QtWidgets.QLineEdit(self)
        self.huso_destino.setPlaceholderText(self.tr("3S - 8N - 18S - 19S - 35N..."))

        # If for whatever reason the user decides to use the UTM mode, here they will tell us the UTM zone
        self.huso_usuario_utm_instrucciones = QtWidgets.QLabel(self)
        self.huso_usuario_utm_edit = QtWidgets.QLineEdit(self)

        self.format_selector = QtWidgets.QComboBox(self)
        self.format_selector.addItems([self.tr("Decimal"), self.tr("Degree/Minute/Second"), self.tr("UTM")])

        # Because of the Translation, here we will need to get the response of the previous ComboBox in terms of a variable:

        self.decimal_check = 0
        self.degree_check = 0
        self.utm_check = 0


        # Decimal Coords
        self.latitud_longitud = QtWidgets.QLineEdit(self)
        self.latitud_longitud.setPlaceholderText(self.tr("Latitude,Longitude"))

        # Degreee-Minute-Second
        self.lat_deg_input = QtWidgets.QLineEdit(self)
        self.lat_min_input = QtWidgets.QLineEdit(self)
        self.lat_sec_input = QtWidgets.QLineEdit(self)
        self.lon_deg_input = QtWidgets.QLineEdit(self)
        self.lon_min_input = QtWidgets.QLineEdit(self)
        self.lon_sec_input = QtWidgets.QLineEdit(self)

        # UTM 
        self.coordenadas_utm = QtWidgets.QLineEdit(self)
        self.coordenadas_utm.setPlaceholderText(self.tr("Coordinates East,North"))

        # To name a Point
        self.point_name_input = QtWidgets.QLineEdit(self)
        self.point_name_input.setPlaceholderText(self.tr("Point name"))
        

        # Aceptar/Cancelar // Accept/Cancel
        self.button_box = QtWidgets.QDialogButtonBox(self)
        self.button_box.setStandardButtons(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)

        # Connects the Accept button
        self.button_box.accepted.connect(self.on_accept)
        self.button_box.rejected.connect(self.reject)

        self.button_box.button(QtWidgets.QDialogButtonBox.Ok).setText(self.tr("Transform"))
        self.button_box.button(QtWidgets.QDialogButtonBox.Cancel).setText(self.tr("Close"))

        self.ejemplo = QtWidgets.QLabel(self)

        self.decimal = QtWidgets.QLabel(self)
        self.dms = QtWidgets.QLabel(self)

        ##############
        ### LAYOUT ###
        ##############

        self.sur_checkbox = QtWidgets.QCheckBox(self.tr("Is your UTM zone in the southern hemisphere? (S - W instead of N - E)"), self)
        self.create_point_checkbox = QtWidgets.QCheckBox(self.tr("Create a point at entered coordinates?"), self)
        self.name_point_checkbox = QtWidgets.QCheckBox(self.tr("Add a name to the created point?"), self)


        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.help_button)
        layout.addWidget(QtWidgets.QLabel(self.tr("Original coordinates format: ")))
        layout.addWidget(self.format_selector) # Type of coordinate options
        layout.addWidget(self.decimal)
        layout.addWidget(self.ejemplo)
        layout.addWidget(self.latitud_longitud) #Edit line of Latitude, Longitude
        layout.addWidget(self.sur_checkbox)
        layout.addWidget(self.dms)
        layout.addWidget(self.coordenadas_utm) # UTM
        layout.addWidget(self.lat_deg_input)   # Degreee-Minute-Second   
        layout.addWidget(self.lat_min_input)   # Degreee-Minute-Second  
        layout.addWidget(self.lat_sec_input)   # Degreee-Minute-Second  
        layout.addWidget(self.lon_deg_input)   # Degreee-Minute-Second  
        layout.addWidget(self.lon_min_input)   # Degreee-Minute-Second  
        layout.addWidget(self.lon_sec_input)   # Degreee-Minute-Second
        layout.addWidget(self.huso_usuario_utm_instrucciones)  # UTM instructions 
        layout.addWidget(self.huso_usuario_utm_edit)           # UTM instructions
        layout.addWidget(self.create_point_checkbox) 
        layout.addWidget(self.name_point_checkbox)
        layout.addWidget(self.point_name_input)
        layout.addWidget(QtWidgets.QLabel(self.tr("UTM zone to which it will be transformed: ")))
        layout.addWidget(self.huso_destino)
        layout.addWidget(self.result_line_edit)
        layout.addWidget(self.button_box)

        self.point_name_input.setVisible(False)
        self.name_point_checkbox.setVisible(False)

        self.result_line_edit.setPlaceholderText(self.tr("Resulting UTM coordinates will be here"))

        self.ejemplo.setText(self.tr("Example (Decimal): -34.438,-71.07"))
        self.decimal.setText(self.tr("Latitude and Longitude (Decimal):"))
        self.dms.setText(self.tr("Latitude and Longitude (Degree, Minute, Second):"))
        self.huso_usuario_utm_instrucciones.setText(self.tr("In which UTM zone are those coordinates from?"))
        self.huso_usuario_utm_edit.setPlaceholderText(f"3S - 8N - 18S - 19S - 35N...")

        self.format_selector.currentIndexChanged.connect(self.update_input_visibility)
        self.create_point_checkbox.stateChanged.connect(self.toggle_name_options)
        self.help_button.clicked.connect(self.mostrar_instrucciones)


        self.update_input_visibility()

        self.ejemplo.setTextInteractionFlags(Qt.TextSelectableByMouse)

        #################################################################
        ### Gives text to Degreee-Minute-Second for easier use

        self.lat_deg_input.setPlaceholderText(self.tr("Latitude (degree)"))   # coords Degreee-Minute-Second   
        self.lat_min_input.setPlaceholderText(self.tr("Latitude (minute)"))   # coords Degreee-Minute-Second  
        self.lat_sec_input.setPlaceholderText(self.tr("Latitude (second)"))   # coords Degreee-Minute-Second  
        self.lon_deg_input.setPlaceholderText(self.tr("Longitud (degree)"))   # coords Degreee-Minute-Second  
        self.lon_min_input.setPlaceholderText(self.tr("Longitud (minute)"))   # coords Degreee-Minute-Second  
        self.lon_sec_input.setPlaceholderText(self.tr("Longitud (second)"))   # coords Degreee-Minute-Second    

    def on_accept(self):    # When you press "Transformar" (Accept), this function is called
        check = 0 # If it's UTM, this will be 1
        print(f"UTM check es: {self.utm_check}")
        try:
            # huso = self.huso_combo_box.currentText()
            huso = self.huso_destino.text()
            zona_transformar, hemisferio_transformar = self.validar_huso(huso) 
            self.epsg_transformar = self.obtener_epsg_desde_huso(zona_transformar, hemisferio_transformar) # QgsCoordinateReferenceSystem(EPSG:32719) etc

            if self.decimal_check == 1: # If the user picked "Decimal"
                print("DECIMAL")
                partes = self.latitud_longitud.text().split(",")
                if len(partes) != 2:
                    raise ValueError(self.tr("Coordinates must be separated by a comma"))
                latitud, longitud = map(float, partes)
                if not (-90 <= latitud <= 90):
                    raise ValueError(self.tr("Latitude must be between -90 and 90"))
                if not (-180 <= longitud <= 180):
                    raise ValueError(self.tr("Longitude must be between -180 and 180"))
            elif self.degree_check == 1: # If the user picked "Degree, Minutes, Seconds"
                print("GRADOS")
                lat_deg = int(self.lat_deg_input.text())
                lat_min = int(self.lat_min_input.text())
                lat_sec = float(self.lat_sec_input.text())
                lon_deg = int(self.lon_deg_input.text())
                lon_min = int(self.lon_min_input.text())
                lon_sec = float(self.lon_sec_input.text())
                latitud = self.dms_to_decimal(lat_deg, lat_min, lat_sec)
                longitud = self.dms_to_decimal(lon_deg, lon_min, lon_sec)
                if not (-90 <= latitud <= 90):
                    raise ValueError(self.tr("Latitude must be between -90 and 90"))
                if not (-180 <= longitud <= 180):
                    raise ValueError(self.tr("Longitude must be between -180 and 180"))
            elif self.utm_check == 1: # If the user picked "UTM"
                print("UTM")
                # First East, then North
                partes = self.coordenadas_utm.text().split(",")
                if len(partes) != 2:
                    raise ValueError(self.tr("Coordinates must be separated by a comma"))
                x, y = map(float, partes)
                check = 1 

            if check == 0: # Calls the transform function and gets the UTM coords
                x, y = self.transform_coords.transformar_coordenadas(latitud, longitud, self.epsg_transformar)
                x = float(x)
                y = float(y)
                zona_punto = "non-UTM"
                hemisferio_punto = "non-UTM"
            elif check == 1: # UTM mode
                huso_punto = self.huso_usuario_utm_edit.text()
                zona_punto, hemisferio_punto = self.validar_huso(huso_punto) # We call this function to check if the UTM zone is ok
                                                                             # Like: zona_punto = 18, hemisferio_punto = S
                epsg_punto = self.obtener_epsg_desde_huso(zona_punto, hemisferio_punto)
                x, y = self.transform_coords.transformar_coordenadas(x, y, epsg_punto, self.epsg_transformar)

            # Show results in a line
            self.result_line_edit.setText(self.tr(f"[Transformation] Coordinates UTM: X: {x}, Y: {y}"))

            if self.create_point_checkbox.isChecked(): #To create a Point in QGIS
                self.crear_punto_en_qgis(x, y, self.epsg_transformar, zona_punto, hemisferio_punto, check)

        except ValueError as e:
            self.result_line_edit.setText(f"{self.tr('Error: ')} {str(e)}")

    def crear_punto_en_qgis(self, x, y, epsg_destino, zona_punto, hemisferio_punto, check): # To create a point in QGIS

        if check == 1: # To make sure this is ONLY for UTM -> UTM
            epsg_punto = self.obtener_epsg_desde_huso(zona_punto, hemisferio_punto)
        
        layer = self.transform_coords.iface.activeLayer() # Active layer to add the point
        if not layer or not isinstance(layer, QgsVectorLayer) or layer.geometryType() != QgsWkbTypes.PointGeometry: # Or make a new layer
            layer = QgsVectorLayer(f"Point?crs={self.project_crs.authid()}", self.tr("Temporal Layer"), "memory")

            layer_data_provider = layer.dataProvider()
            layer_data_provider.addAttributes([QgsField("ID", QVariant.Int), QgsField(self.tr("Name"), QVariant.String)])

            label_settings = QgsPalLayerSettings()
            text_format = QgsTextFormat()
            buffer_settings = QgsTextBufferSettings()
            buffer_settings.setEnabled(True)
            buffer_settings.setSize(0.8)
            buffer_settings.setColor(QColor('white'))
            text_format.setBuffer(buffer_settings)
            label_settings.fieldName = self.tr("Name")
            label_settings.setFormat(text_format)
            label_settings.enabled = True
            labeling = QgsVectorLayerSimpleLabeling(label_settings)
            layer.setLabeling(labeling)
            layer.setLabelsEnabled(True)
            layer.triggerRepaint()
            layer.updateFields()

            QgsProject.instance().addMapLayer(layer)
        else:
            crs_capa = layer.crs() # To get the Coordinate Reference System of the current layer
            try:
                zona_capa, hemisferio_capa = self.obtener_huso_de_capa(crs_capa)
            except ValueError: # In case the layer is not UTM: 
                QtWidgets.QMessageBox.warning(self, self.tr("Error"), self.tr("The active layer is not in a recognized UTM."))
                return
            # Here, we compare layer UTM zone with the point UTM zone (as written by the user)
            if check == 1:
                if (zona_punto, hemisferio_punto) != (zona_capa, hemisferio_capa):
                    # Here is where the good part happens: It transforms the coords of the point to the CRS of the layer
                    x, y = self.transform_coords.transformar_coordenadas(x, y, epsg_destino, crs_capa)
        
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
            name_field_check = 0
            # If there is no name given to the point by the user, it will just take a NULL value.
            nombre = self.point_name_input.text() 
            if nombre:
                name_variants = ["Nombre", "Name", "Nom", "Namn", "Nome", "Naam", "Namn", "Nimi", "名前", "이름 "]
                for field in layer.fields():
                    if field.name() in name_variants:
                        name_field = field.name()
                        name_field_check = 1
                        break
                if name_field_check == 1:
                    if name_field:
                        attributes[layer.fields().indexFromName(name_field)] = nombre
                else:
                    QtWidgets.QMessageBox.warning(self, self.tr("Error"), self.tr("The active layer doesn't have a text field to store the point name"))

        feature.setAttributes(attributes)
        if not layer.isEditable():
            layer.startEditing()

        if layer.addFeature(feature):
            layer.commitChanges()
        else:
            layer.rollBack()


    def update_input_visibility(self): # Change the Window, depending on the selected format
        if self.format_selector.currentIndex() == 0: # Decimal
            self.decimal_check = 1
            self.degree_check = 0
            self.utm_check = 0
        elif self.format_selector.currentIndex() == 1: # Degree/Minute/Second
            self.decimal_check = 0
            self.degree_check = 1
            self.utm_check = 0
        elif self.format_selector.currentIndex() == 2: # UTM
            self.decimal_check = 0
            self.degree_check = 0
            self.utm_check = 1
        if self.decimal_check == 1: # If they picked Decimal
            self.ejemplo.show()
            self.decimal.show()
            self.latitud_longitud.show()
            self.sur_checkbox.hide()
            self.huso_usuario_utm_instrucciones.hide()
            self.huso_usuario_utm_edit.hide()
            self.dms.hide()
            self.coordenadas_utm.hide()
            self.lat_deg_input.hide()
            self.lat_min_input.hide()
            self.lat_sec_input.hide()
            self.lon_deg_input.hide()
            self.lon_min_input.hide()
            self.lon_sec_input.hide()
        elif self.degree_check == 1: # If they picked Degree/Minutes/Seconds
            self.ejemplo.hide()
            self.decimal.hide()
            self.latitud_longitud.hide()
            self.huso_usuario_utm_instrucciones.hide()
            self.huso_usuario_utm_edit.hide()
            self.coordenadas_utm.hide()
            self.sur_checkbox.show()
            self.dms.show()
            self.lat_deg_input.show()
            self.lat_min_input.show()
            self.lat_sec_input.show()
            self.lon_deg_input.show()
            self.lon_min_input.show()
            self.lon_sec_input.show()
        else: # If they picked UTM
            self.ejemplo.hide()
            self.decimal.hide()
            self.latitud_longitud.hide()
            self.sur_checkbox.hide()
            self.coordenadas_utm.show()
            self.huso_usuario_utm_instrucciones.show()
            self.huso_usuario_utm_edit.show()
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

    # To check if the UTM zone provided in the {self.huso_usuario_utm_edit} is correct. 
    def validar_huso(self, huso):
        pattern = r'^[1-9]|[1-5][0-9]|60[NnSs]$'
        if re.match(pattern, huso):
            zona = int(huso[:-1])
            hemisferio = huso[-1].upper()
            return zona, hemisferio
        else:
            raise ValueError(self.tr("Invalid UTM zone. Number between (1,60) followed by 'N' o 'S'. Example: '18S'"))

    # To obtain the EPSG from the UTM zone provided. 
    def obtener_epsg_desde_huso(self, zona, hemisferio):
        if hemisferio == 'N':
            epsg_code = 32600 + zona
        elif hemisferio == 'S':
            epsg_code = 32700 + zona
        else:
            raise ValueError(self.tr("Invalid hemisphere. It must be 'N' o 'S'."))
        return QgsCoordinateReferenceSystem(f"EPSG:{epsg_code}")

    # To compare the UTM zone of the point (provided by {self.huso_usuario_utm_edit}) and the UTM zone of the active layer.
    def obtener_huso_de_capa(self, crs_capa):
        epsg_code = crs_capa.authid()
        if epsg_code.startswith("EPSG:326") or epsg_code.startswith("EPSG:327"):
            zona = int(epsg_code[-2:])
            hemisferio = 'N' if epsg_code.startswith("EPSG:326") else 'S'
            return zona, hemisferio
        else:
            raise ValueError(self.tr("The active layer is not in a valid UTM CRS."))

    def mostrar_instrucciones(self): # Instructions on how to use the PLUGIN
        dialog = InstruccionesDialog(self)
        dialog.exec_()


# Just the instructions. 
class InstruccionesDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(InstruccionesDialog, self).__init__(parent)
        self.setWindowTitle(self.tr("Instructions"))
        self.setGeometry(100, 100, 610, 550)

        layout = QtWidgets.QVBoxLayout(self)

        # Agregar un QTextEdit o QLabel para mostrar el texto de las instrucciones

        # WARNING lmao I was too lazy for this part so I just asked GPT to do it for me (the translation etc):

        instrucciones = ("""
        <h3>{}</h3>
    
        <p>
            <strong>{}</strong> {}
        </p>
        
        <ul>
            <li><strong>{}</strong> {}</li>
            
            <li><strong>{}</strong> 
                <ul>
                    <li>{}</li>
                    <li>{}</li>
                    <li>{} </li>
                </ul>
            </li>
            <li><strong>{}</strong>
                <ul>
                    <li>{}</li>
                    <li>{}</li>
                    <li>{}<ul> <li>{}</li> </ul></li>
                </ul>
            </li>
        </ul>
        
        <h3>{}</h3>
        <ul>
            <li>{}</li>
            <li>{}</li>
            <li>{}</li>
        </ul>
        
        <p>
            {}</p>
        
        <h4>{}</h4>
        <p>
            {}</p>
        <ul>
            <li>
                <em>{}</em> 
                <ul>
                    <li>{}</li>
                    <li>{}</li>
                </ul>
            </li>
        </ul>
        <p>
            </p>
        """).format(
            self.tr("Instructions:"), #1
            self.tr("Select format of entry coordinates:"),  
            self.tr("(Decimal, Degree/Minute/Second, UTM)"),
            self.tr("Decimal:"),  
            self.tr("Simply fill the required fields. This will convert those coordinates to UTM in the selected zone."), #5
            self.tr("Degree/Minute/Second:"), 
            self.tr("Fill the required fields. They must be integers."),
            self.tr("If only 'Degrees' and 'Minutes' are given, set 'Seconds' to 0. If only 'Degrees' are given, set both 'Minutes' and 'Seconds' to 0"),
            self.tr("This will convert the coordinates to the selected UTM zone."),
            self.tr("UTM:"), #10
            self.tr("Fill the required fields. Use '.' for decimals."),
            self.tr("You have to type the UTM zone of the coordinates you will input."),
            self.tr("Since this is UTM → UTM, the transformation will be in the zone. Example:"),
            self.tr("A point with UTM zone 18 will be placed somewhere else if the layer is UTM zone 21"),
            self.tr("Optionally, you may create a point in the map and give it a name:"), #15
            self.tr("If you have selected a layer in QGIS that allows points, it will be created there."),
            self.tr("Otherwise, if you don't have a selected layer, or if the layer doesn't allow points, a temporal layer will be created"),
            self.tr("The new point will be placed in this temporal layer, which will have the same UTM zone as your QGIS map."),
            self.tr("Press 'Transform' to obtain the new coordinates and create the point."),
            self.tr("Also:"), #20
            self.tr("Once you create a point in UTM mode, if the input coordinates belong to a different UTM zone than the active layer, they will be transformed to adjust them to the UTM zone of the active layer. Example:"),
            self.tr("UTM points (80, 70) in zone 18S:"), #22
            self.tr("If the layer that will receive the points is in 18S, all good, the point will be created in the right spot."),
            self.tr("If the layer that will receive the points is in another UTM zone, like 19S for this example, the points (80, 70) will be transformated to the UTM zone of the active layer, so they can be placed correctly."),
        )

        instrucciones_label = QtWidgets.QLabel(instrucciones, self)
        instrucciones_label.setWordWrap(True)
        instrucciones_label.setTextFormat(Qt.RichText)
        instrucciones_label.setAlignment(Qt.AlignTop)

        close_button = QtWidgets.QPushButton(self.tr("Close"), self)
        close_button.clicked.connect(self.accept)

        layout.addWidget(instrucciones_label)
        layout.addWidget(close_button)

