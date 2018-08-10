# -*- coding: utf-8 -*-
"""
/***************************************************************************
 BulkVectorExport
                                 A QGIS plugin
 Export vector layers
                             -------------------
        begin                : 2015-07-10
        copyright            : (C) 2015 by Simon Oberhammer
        email                : simon@nekapuzer.at
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
from __future__ import absolute_import

def classFactory(iface):
    # load BulkVectorExport class from file BulkVectorExport
    from .bulkvectorexport import BulkVectorExport
    return BulkVectorExport(iface)
