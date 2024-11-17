import os
import re
from qgis.PyQt.QtCore import Qt
from qgis.PyQt import uic, QtWidgets
from qgis.PyQt.QtWidgets import QDialog, QStackedWidget, QWidget
from qgis.PyQt.QtGui import QFont, QColor
from qgis.core import (QgsCoordinateReferenceSystem, QgsVectorLayer, QgsProject, QgsFeature, 
                        QgsGeometry, QgsPointXY, QgsWkbTypes, QgsField, QgsCoordinateTransform, 
                        QgsTextFormat, QgsTextBufferSettings, QgsPalLayerSettings, QgsVectorLayerSimpleLabeling)
from PyQt5.QtCore import QSettings, QTranslator, QVariant, QCoreApplication

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
        self.setWindowTitle("Transformar Coordenadas")
        self.setGeometry(100, 100, 400, 450)
        self.setFixedSize(400, 450)
        self.stacked_inputs = QStackedWidget(self)

        # Final Coords: 
        self.result_line_edit = QtWidgets.QLineEdit(self)
        self.result_line_edit.setReadOnly(True)

        self.help_button = QtWidgets.QPushButton("Instrucciones", self) # User will press for help
        self.huso_destino = QtWidgets.QLineEdit(self)
        self.huso_destino.setPlaceholderText("3S - 8N - 18S - 19S - 35N...")

        # If for whatever reason the user decides to use the UTM mode, here they will tell us the UTM zone
        self.huso_usuario_utm_instrucciones = QtWidgets.QLabel(self)
        self.huso_usuario_utm_edit = QtWidgets.QLineEdit(self)

        self.format_selector = QtWidgets.QComboBox(self)
        self.format_selector.addItems(["Decimal", "Grados/Minuto/Segundo", "UTM (xd)"])

        # Decimal Coords
        self.latitud_longitud = QtWidgets.QLineEdit(self)
        self.latitud_longitud.setPlaceholderText("Latitud,Longitud")

        # Degreee-Minute-Second
        self.lat_deg_input = QtWidgets.QLineEdit(self)
        self.lat_min_input = QtWidgets.QLineEdit(self)
        self.lat_sec_input = QtWidgets.QLineEdit(self)
        self.lon_deg_input = QtWidgets.QLineEdit(self)
        self.lon_min_input = QtWidgets.QLineEdit(self)
        self.lon_sec_input = QtWidgets.QLineEdit(self)

        # UTM 
        self.coordenadas_utm = QtWidgets.QLineEdit(self)
        self.coordenadas_utm.setPlaceholderText("Coordenadas Este,Norte")

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

        self.sur_checkbox = QtWidgets.QCheckBox("Sur y Oeste? (Chile)", self)
        self.create_point_checkbox = QtWidgets.QCheckBox("Crear punto en coordenadas ingresadas?", self)
        self.name_point_checkbox = QtWidgets.QCheckBox("Agregar punto con nombre?", self)


        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.help_button)
        layout.addWidget(QtWidgets.QLabel("Formato de coordenadas de entrada:"))
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
        layout.addWidget(QtWidgets.QLabel("Huso UTM al que será transformado:"))
        layout.addWidget(self.huso_destino)
        layout.addWidget(self.result_line_edit)
        layout.addWidget(self.button_box)

        self.point_name_input.setVisible(False)
        self.name_point_checkbox.setVisible(False)

        self.result_line_edit.setPlaceholderText(f"Acá estarán las coordenadas UTM resultantes")

        self.ejemplo.setText(f"Ejemplo (Decimal): -34.438,-71.07")   
        self.decimal.setText(f"Latitud y Longitud (Decimal):")
        self.dms.setText(f"Latitud y Longitud (Grado, Minuto, Segundo):")
        self.huso_usuario_utm_instrucciones.setText(f"¿En que huso UTM se encuentran esas coordenadas?")
        self.huso_usuario_utm_edit.setPlaceholderText(f"3S - 8N - 18S - 19S - 35N...")

        self.format_selector.currentIndexChanged.connect(self.update_input_visibility)
        self.create_point_checkbox.stateChanged.connect(self.toggle_name_options)
        self.help_button.clicked.connect(self.mostrar_instrucciones)


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
            # huso = self.huso_combo_box.currentText()
            huso = self.huso_destino.text()
            zona_transformar, hemisferio_transformar = self.validar_huso(huso) 
            self.epsg_transformar = self.obtener_epsg_desde_huso(zona_transformar, hemisferio_transformar) # QgsCoordinateReferenceSystem(EPSG:32719) etc

            if self.format_selector.currentText() == "Decimal":
                # Decimal input
                partes = self.latitud_longitud.text().split(",")
                if len(partes) != 2:
                    raise ValueError("Coordenadas deben estar separadas por una coma")
                latitud, longitud = map(float, partes)
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
                #primero este, luego norte
                partes = self.coordenadas_utm.text().split(",")
                if len(partes) != 2:
                    raise ValueError("Coordenadas deben estar separadas por una coma")
                x, y = map(float, partes)
                check = 1

            if check == 0:
                # Calls the transform function and gets the UTM coords
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
            self.result_line_edit.setText(f"[Transformacion] Coordenadas UTM: X: {x}, Y: {y}")

            if self.create_point_checkbox.isChecked(): #To create a Point in QGIS
                self.crear_punto_en_qgis(x, y, self.epsg_transformar, zona_punto, hemisferio_punto, check)

        except ValueError as e:
            self.result_line_edit.setText(f"Error (noob): {str(e)}")

    def crear_punto_en_qgis(self, x, y, epsg_destino, zona_punto, hemisferio_punto, check): # To create a point in QGIS

        if check == 1: # To make sure this is ONLY for UTM -> UTM
            epsg_punto = self.obtener_epsg_desde_huso(zona_punto, hemisferio_punto)
        
        layer = self.transform_coords.iface.activeLayer() # Active layer to add the point
        if not layer or not isinstance(layer, QgsVectorLayer) or layer.geometryType() != QgsWkbTypes.PointGeometry: # Or make a new layer
            layer = QgsVectorLayer(f"Point?crs={self.project_crs.authid()}", "Capa Temporal uwu", "memory")

            layer_data_provider = layer.dataProvider()
            layer_data_provider.addAttributes([QgsField("ID", QVariant.Int), QgsField("Nombre", QVariant.String)])

            label_settings = QgsPalLayerSettings()
            text_format = QgsTextFormat()
            buffer_settings = QgsTextBufferSettings()
            buffer_settings.setEnabled(True)
            buffer_settings.setSize(0.8)
            buffer_settings.setColor(QColor('white'))
            text_format.setBuffer(buffer_settings)
            label_settings.fieldName = "Nombre"
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
                QtWidgets.QMessageBox.warning(self, "Error", "La capa activa no está en un UTM reconocido.")
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

    def update_input_visibility(self): # Change the Window, depending on the selected format
        if self.format_selector.currentText() == "Decimal":
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
        elif self.format_selector.currentText() == "Grados/Minuto/Segundo":
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
        else:
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
            raise ValueError("Huso inválido. Número entre (1,60) seguido de 'N' o 'S'. Ejemplo: '18S'")

    # To obtain the EPSG from the UTM zone provided. 
    def obtener_epsg_desde_huso(self, zona, hemisferio):
        if hemisferio == 'N':
            epsg_code = 32600 + zona
        elif hemisferio == 'S':
            epsg_code = 32700 + zona
        else:
            raise ValueError("Hemisferio inválido. Debe ser 'N' o 'S'.")
        return QgsCoordinateReferenceSystem(f"EPSG:{epsg_code}")

    # To compare the UTM zone of the point (provided by {self.huso_usuario_utm_edit}) and the UTM zone of the active layer.
    def obtener_huso_de_capa(self, crs_capa):
        epsg_code = crs_capa.authid()
        if epsg_code.startswith("EPSG:326") or epsg_code.startswith("EPSG:327"):
            zona = int(epsg_code[-2:])
            hemisferio = 'N' if epsg_code.startswith("EPSG:326") else 'S'
            return zona, hemisferio
        else:
            raise ValueError("La capa activa no está en un CRS UTM reconocido.")

    def mostrar_instrucciones(self): # Instructions on how to use the PLUGIN
        dialog = InstruccionesDialog(self)
        dialog.exec_()


# Just the instructions. 
class InstruccionesDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(InstruccionesDialog, self).__init__(parent)
        self.setWindowTitle("Instrucciones UwU")
        self.setGeometry(100, 100, 610, 550)

        layout = QtWidgets.QVBoxLayout(self)

        # Agregar un QTextEdit o QLabel para mostrar el texto de las instrucciones
        instrucciones = ("""
        <h3>Instrucciones de uso:</h3>
    
        <p>
            <strong>Seleccionar formato de las coordenadas de entrada:</strong> (Decimal, Grado/Minuto/Segundo, UTM)
        </p>
        
        <ul>
            <li><strong>Decimal:</strong> Simplemente llena los dos campos requeridos. Esto convertirá esas coordenadas a UTM en el huso seleccionado.</li>
            
            <li><strong>Grado/Minuto/Segundo:</strong> 
                <ul>
                    <li>Llena los campos. Deben ser números enteros.</li>
                    <li>Es posible que solo haya 'Grados' y 'Minutos'. Si no hay 'Segundo', pon 0.</li>
                    <li>Esto convertirá las coordenadas a UTM en el huso seleccionado.</li>
                </ul>
            </li>
            <li><strong>UTM:</strong>
                <ul>
                    <li>Llena los campos. Pueden ser decimales, pero ten cuidado de usar '.' o ',' según corresponda.</li>
                    <li>Debes escribir el huso de las coordenadas que vas a ingresar.</li>
                    <li>
                        Dado que esto es UTM → UTM, la transformación será en el Huso. Por ejemplo:
                        <ul>
                            <li>Un punto con coordenadas de huso 18S se ubicará en otro lugar si enfocamos la capa o el mapa a huso 21S.</li>
                        </ul>
                    </li>
                </ul>
            </li>
        </ul>
        
        <h3>Opcionalmente, puedes crear un punto en el mapa y asignarle un nombre:</h3>
        <ul>
            <li>
                Si tienes una capa seleccionada en QGIS que admite puntos, el punto será creado en esa capa.
            </li>
            <li>
                De lo contrario, si no tienes una capa seleccionada o si la capa seleccionada no admite puntos, se creará una capa temporal.
            </li>
            <li>
                En esa capa temporal se agregará el punto creado. <strong>La capa temporal tendrá el mismo huso que el proyecto.</strong>
            </li>
        </ul>
        
        <p>
            Presiona <strong>'Transformar'</strong> para obtener las coordenadas transformadas y para crear el punto, si has seleccionado la opción.
        </p>
        
        <h4>Nota:</h4>
        <p>
            Al momento de crear un punto en el modo UTM, si las coordenadas ingresadas pertenecen a un huso diferente al de la capa activa, el complemento transformará las coordenadas para ajustarlas al huso de la capa activa. Por ejemplo:
        </p>
        <ul>
            <li>
                <em>Puntos UTM (80, 70) en Huso 18S:</em> 
                <ul>
                    <li>Si la capa a la que se agregarán los puntos está en 18S, todo bien, el punto será creado en su posición correcta.</li>
                    <li>
                        Si la capa está en otro huso, como 19S, los puntos (80, 70) serán transformados al huso de la capa para así estar ubicados en su posición correcta.
                    </li>
                </ul>
            </li>
        </ul>
        <p>
            Recuerda que para Chile: 17S = Islas, 18S = Sur, 19S = Centro/Norte (Y un pedacito de la Patagonia). 
        </p>
        """)
        instrucciones_label = QtWidgets.QLabel(instrucciones, self)
        instrucciones_label.setWordWrap(True)
        instrucciones_label.setTextFormat(Qt.RichText)
        instrucciones_label.setAlignment(Qt.AlignTop)

        close_button = QtWidgets.QPushButton("Cerrar", self)
        close_button.clicked.connect(self.accept)

        layout.addWidget(instrucciones_label)
        layout.addWidget(close_button)
