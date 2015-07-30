# -*- coding: utf-8 -*-
"""
/***************************************************************************
 BulkVectorExport
                                 A QGIS plugin
 Export map contents to specified format and CRS
                              -------------------
        begin                : 2015-07-10
        copyright            : (C) 2015 by ORFON
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
"""
# Import the PyQt and QGIS libraries
from PyQt4 import QtCore, QtGui
from osgeo import ogr
from qgis.core import *
import qgis.utils
import os
# Initialize Qt resources from file resources.py
import resources_rc
# Import the code for the dialog
from bulkvectorexportdialog import BulkVectorExportDialog
import json
import zipfile

def bounds(layers):

    extent = None
    for layer in layers:
        if layer.type() == 0:
            transform = QgsCoordinateTransform(layer.crs(), QgsCoordinateReferenceSystem('EPSG:4326')) # WGS 84 / UTM zone 33N
            try:
                layerExtent = transform.transform(layer.extent())
            except QgsCsException:
                print "exception in transform layer srs"
                layerExtent = QgsRectangle(-20026376.39, -20048966.10, 20026376.39, 20048966.10)
            if extent is None:
                extent = layerExtent
            else:
                extent.combineExtentWith(layerExtent)

            print str([extent.xMinimum(), extent.yMinimum(), extent.xMaximum(), extent.yMaximum()])
    return (extent.xMinimum(), extent.yMinimum(), extent.xMaximum(), extent.yMaximum())


class BulkVectorExport:

    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = QtCore.QFileInfo(QgsApplication.qgisUserDbFilePath()).path() + "/python/plugins/bulkvectorexport"
        # initialize locale
        localePath = ""
        locale = QtCore.QSettings().value("locale/userLocale")[0:2]

        if QtCore.QFileInfo(self.plugin_dir).exists():
            localePath = self.plugin_dir + "/i18n/bulkvectorexport_" + \
                locale + ".qm"

        if QtCore.QFileInfo(localePath).exists():
            self.translator = QTranslator()
            self.translator.load(localePath)

            if qVersion() > '4.3.3':
                QtCore.QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = BulkVectorExportDialog()

    def initGui(self):
        # Create action that will start plugin configuration
        self.action = QtGui.QAction( \
            QtGui.QIcon(":/plugins/bulkvectorexport/icon.png"), \
            u"Bulk export vectory layers", \
            self.iface.mainWindow())
        # connect the action to the run method
        QtCore.QObject.connect(self.action, QtCore.SIGNAL("triggered()"), self.run)

        # Add toolbar button and menu item
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu(u"&Bulk vector export", self.action)

    def unload(self):
        # Remove the plugin menu item and icon
        self.iface.removePluginMenu(u"&Bulk vector export", self.action)
        self.iface.removeToolBarIcon(self.action)

    # run method that performs all the real work
    def run(self):
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result == 1:
            # get target directory
            dirName = self.dlg.ui.dirEdit.text()
            if dirName[len(dirName)-1] != "/":
                dirName = dirName + "/"
            if not QtCore.QFileInfo(dirName).isDir():
                QtGui.QMessageBox.critical(self.dlg, "BulkVectorExport", \
                    "No such directory : " + dirName)
                return
            ogr_driver_name = "GeoJSON"
            print"Driver ogr name: " + ogr_driver_name
            layers = qgis.utils.iface.mapCanvas().layers()
            project = QgsProject.instance()
            mapInfo = {"name": os.path.basename(project.fileName()), "layers": [], "bounds": []}
            fileNames = []
            for layer in reversed(layers):
                layerType = layer.type()
                if layerType == QgsMapLayer.VectorLayer:
                    print 'Writing:' + layer.name()
                    layer_filename = dirName + layer.name()
                    print 'Filename: ' + layer_filename
                    crs = QgsCoordinateReferenceSystem("EPSG:4326")
                    result2 = qgis.core.QgsVectorFileWriter.writeAsVectorFormat(layer, layer_filename, layer.dataProvider().encoding(), crs, ogr_driver_name)
                    print "Status: " + str(result2)
                    if result2 != 0:
                        QtGui.QMessageBox.warning(self.dlg, "BulkVectorExport",\
                            "Failed to export: " + layer.name() + \
                            " Status: " + str(result2))
                    sld_filename = os.path.splitext( unicode( layer_filename ) )[ 0 ] + '.sld'
                    print 'Filename: ' + sld_filename
                    result3 = False
                    layer.saveSldStyle(sld_filename)
                    hasPopups = True
                    try:
                        layer.getFeatures().next()['html_exp']
                    except KeyError:
                        hasPopups = False
                    mapInfo['layers'].append({
                        "title": str(layer.name()),
                        "geojson": os.path.basename(layer_filename) + '.geojson',
                        "sld": os.path.basename(sld_filename),
                        "hasPopups": hasPopups
                    })
                    fileNames.append(layer_filename + '.geojson')
                    fileNames.append(sld_filename)

            mapInfo['bounds'] = bounds(layers)
            mapInfo['maxZoom'] = 11;
            mapInfo['minZoom'] = 6;
            mapInfo['description'] = "";
            mapInfo['attribution'] = "";
            mapInfo['hasLayerControl'] = True
            mapInfo['hasZoomControl'] = True
            mapInfo['hasLayerLegend'] = True
            mapInfo['basemap'] = 'bmapgrau';
            map_filename = dirName + 'metadata.json'
            with open(map_filename, 'w') as outfile:
                json.dump(mapInfo, outfile)

            fileNames.append(map_filename)

            ## zip all
            zf = zipfile.ZipFile(dirName +  os.sep + os.path.basename(project.fileName()) + '.globus.zip', "w")

            for fileName in fileNames:
                zf.write(os.path.join(fileName), arcname=os.path.split(fileName)[1])
                os.remove(fileName)
            zf.close()