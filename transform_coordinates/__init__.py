# -*- coding: utf-8 -*-
"""
/***************************************************************************
 TransformCoords
                                 A QGIS plugin
 To transform coordinates to UTM and make a point in the layer. 
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2024-11-03
        copyright            : (C) 2024 by Joomkin
        email                : vicente.rivas@uc.cl
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""

from .resources import *


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load TransformCoords class from file TransformCoords.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .Transform_Coordinates import TransformCoords
    return TransformCoords(iface)
