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
from __future__ import print_function
from __future__ import absolute_import
# Import the PyQt and QGIS libraries
from builtins import str
from builtins import range
from builtins import object
from qgis.PyQt import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import *
from qgis.core import Qgis, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsFeatureRequest, QgsVectorLayer, QgsRasterLayer,  QgsMapLayerProxyModel, QgsProject, QgsRasterProjector
from osgeo import ogr
from qgis.core import *
import qgis.utils
import os
# Initialize Qt resources from file resources.py
from . import resources_rc
# Import the code for the dialog
from .bulkvectorexportdialog import BulkVectorExportDialog
import json
import zipfile
import tempfile
import shutil
import glob
import uuid

def bounds(layers):

    extent = None
    for layer in layers:
        layerType = layer.type()
        if layerType == QgsMapLayer.RasterLayer:
            provider_r = layer.dataProvider()
            layerExtent_r = provider_r.extent()
            print("Bounds provider.extent: " + str(provider_r.extent()))
            print("Bounds provider.crs: " + str(provider_r.crs()))
            xmin = layerExtent_r.xMinimum()
            ymin = layerExtent_r.yMinimum()
            xmax = layerExtent_r.xMaximum()
            ymax = layerExtent_r.yMaximum()
            layerExtent_rn = QgsRectangle(xmin, ymin, xmax, ymax)
            print("layerExtent_rn: " + str(layerExtent_rn))
            transform_r = QgsCoordinateTransform(layer.crs(), QgsCoordinateReferenceSystem('EPSG:4326'), QgsProject.instance()) # WGS 84 / UTM zone 33N
            try:
               layerExtent = transform_r.transform(layerExtent_rn)
            except QgsCsException:
                print("exception in transform layer srs")
                layerExtent = QgsRectangle(-180, -90, 180, 90)
            if extent is None:
                extent = layerExtent
            else:
                extent.combineExtentWith(layerExtent)
        elif layerType == QgsMapLayer.VectorLayer:
            transform = QgsCoordinateTransform(layer.crs(), QgsCoordinateReferenceSystem('EPSG:4326'), QgsProject.instance()) # WGS 84 / UTM zone 33N
            try:
                layerExtent = transform.transform(layer.extent())
            except QgsCsException:
                print("exception in transform layer srs")
                layerExtent = QgsRectangle(-180, -90, 180, 90)
            if extent is None:
                extent = layerExtent
            else:
                extent.combineExtentWith(layerExtent)
        else:
            extent.combineExtentWith(layerExtent)

    return (extent.xMinimum(), extent.yMinimum(), extent.xMaximum(), extent.yMaximum())
    print("Bounds: " + str(bounds(layers)))

def copySymbols(symbol, tempPath, fileNames):
    for i in range(symbol.symbolLayerCount()):
        sl = symbol.symbolLayer(i)
        if isinstance(sl, QgsSvgMarkerSymbolLayer):
             symbolPath = sl.path();
             shutil.copy(symbolPath, tempPath)
             print("Copying " + str(sl.path()))
             fileNames.append(tempPath + os.sep + os.path.basename(symbolPath))
        # SVG im Projektverzeichnis abholen
        elif isinstance(sl, QgsLineSymbolLayer):
             projFile = QFileInfo(QgsProject.instance().fileName());
             symbolLinePath = projFile.absolutePath();
             for svgfile in glob.iglob(os.path.join(symbolLinePath, "*.svg")):
                shutil.copy(svgfile, tempPath)
                print("Copying")
                fileNames.append(svgfile)
        else:
            print("Ignoring " + str(sl))

class BulkVectorExport(object):

    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = QtCore.QFileInfo(QgsApplication.qgisUserDatabaseFilePath()).path() + "/python/plugins/bulkvectorexport"
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
        # Set CRS.
        self.epsg4326 = QgsCoordinateReferenceSystem("EPSG:4326")

    def initGui(self):
        # Create action that will start plugin configuration
        self.action = QtWidgets.QAction(
            QtGui.QIcon(':/plugins/bulkvectorexportwithstyle/icon.png'),
            u"Bulk export vector layers",
            self.iface.mainWindow())
        # connect the action to the run method
        self.action.triggered.connect(self.run)

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
            # Export path field empty? Raise warning and break with return.
            if dirName == "":
                QtWidgets.QMessageBox.critical(self.dlg, "BulkVectorExport", \
                    "Please input directory name")
                return
            # Check for valid directory path.
            if dirName[len(dirName)-1] != "/":
                dirName = dirName + "/"
            if not QtCore.QFileInfo(dirName).isDir():
                QtWidgets.QMessageBox.critical(self.dlg, "BulkVectorExport", \
                    "No such directory : " + dirName)
                return
            ogr_driver_name = "GeoJSON"
            ogr_driver_name_raster = "GTiff"
            print("Driver name: " + ogr_driver_name)
            layers = qgis.utils.iface.mapCanvas().layers()
            project = QgsProject.instance()
            mapInfo = {"name": os.path.basename(project.fileName()), "layers": [], "bounds": []}
            tempPath = tempfile.mkdtemp('bulkexport') + os.sep
            fileNames = []
            for layer in reversed(layers):
                layerType = layer.type()
                if layerType == QgsMapLayer.RasterLayer:
                    renderer = layer.renderer()
                    hasIcon = False
                    print('Writing: ' + str(layer.name()))
                    layer_filename_r = tempPath + str(uuid.uuid4()) + '.tif'
                    print('Filename: ' + layer_filename_r)
                    provider = layer.dataProvider()
                    file_writer = qgis.core.QgsRasterFileWriter(layer_filename_r)
                    pipe = QgsRasterPipe()
                    crs = QgsCoordinateReferenceSystem("EPSG:4326")
                    projector = QgsRasterProjector(provider.crs(), crs);
                    pipe.set(provider.clone())
                    pipe.insert(2, projector);
                    #pipe.set(renderer.clone())
                    result4 = file_writer.writeRaster(pipe, provider.xSize(), provider.ySize(), provider.extent(), crs)
                    print("Status: " + str(result4))
                    if result4 != 0:
                        QtWidgets.QMessageBox.warning(self.dlg, "BulkVectorExport",\
                            "Failed to export: " + layer.name() + \
                            "Status: " + str(result4))
                    result5 = False
                    mapInfo['layers'].append({
                        "title": str(layer.name()),
                        "geotiff": os.path.basename(layer_filename_r) # + '.tif'
                    })
                    fileNames.append(layer_filename_r)
                elif layerType == QgsMapLayer.VectorLayer:
                    renderer = layer.renderer()
                    hasIcon = False
                    if isinstance(renderer, QgsSingleSymbolRenderer):
                        copySymbols(renderer.symbol(), tempPath, fileNames)
                        hasIcon = True
                    print('Writing:' + str(layer.name()))
                    layer_filename = tempPath + str(uuid.uuid4())
                    print('Filename: ' + layer_filename)
                    crs = QgsCoordinateReferenceSystem("EPSG:4326")
                    result2 = qgis.core.QgsVectorFileWriter.writeAsVectorFormat(layer, layer_filename, "utf-8", crs, ogr_driver_name)
                    print("Status: " + str(result2))
                    if result2[0] != 0:
                        QtWidgets.QMessageBox.warning(self.dlg, "BulkVectorExport",\
                            "Failed to export: " + layer.name() + \
                            "Status: " + str(result2))
                    sld_filename = os.path.join(tempPath, os.path.basename(layer_filename) + '.sld')
                    print('Filename: ' + sld_filename)
                    result3 = False
                    layer.saveSldStyle(sld_filename)
                    mapInfo['layers'].append({
                        "title": str(layer.name()),
                        "geojson": os.path.basename(layer_filename) + '.geojson',
                        "sld": os.path.basename(sld_filename),
                        ## opacity value has to be rounded, otherwise python 3.6 writes 0.99 instead of 1.0
                        "opacity":  round(1 - (layer.opacity() / 100.0), 1),
                        "hasIcon": hasIcon
                    })
                    fileNames.append(layer_filename + '.geojson')
                    fileNames.append(sld_filename)
                    print(fileNames)

            ## initial bounding box is visible extent
            canvas = self.iface.mapCanvas()
            canvasExtent = canvas.extent()
            crsDest = QgsCoordinateReferenceSystem("EPSG:4326")
            try:
                crsSrc = canvas.mapSettings().destinationCrs()
            except:
                crsSrc = canvas.mapRenderer().destinationCrs()
            xform = QgsCoordinateTransform(crsSrc, crsDest, QgsProject.instance())
            canvasExtentTransformed = xform.transform(canvasExtent)

            initialBounds = [canvasExtentTransformed.xMinimum(), canvasExtentTransformed.yMinimum(),
                            canvasExtentTransformed.xMaximum(), canvasExtentTransformed.yMaximum()]

            mapInfo['bounds'] = bounds(layers)
            mapInfo['maxZoom'] = 11;
            mapInfo['minZoom'] = 6;
            mapInfo['description'] = "";
            mapInfo['attribution'] = "";
            mapInfo['popupTemplate'] = "";
            mapInfo['initialBounds'] = initialBounds;
            mapInfo['limitedInitialBounds'] = False
            mapInfo['popupLayerIndex'] = -1;
            mapInfo['hasLayerControl'] = True
            mapInfo['hasZoomControl'] = True
            mapInfo['hasLayerLegend'] = True
            mapInfo['basemap'] = 'bmapgrau';
            map_filename = tempPath + 'metadata.json'
            with open(map_filename, 'w') as outfile:
                json.dump(mapInfo, outfile)

            fileNames.append(map_filename)

            ## if .svg file present, add to packlist
            for svgfile in os.listdir(tempPath):
                if svgfile.endswith(".svg"):
                    fileNames.append(tempPath + svgfile)

            ## zip all
            zf = zipfile.ZipFile(dirName +  os.sep + os.path.basename(str(project.fileName())) + '.globus.zip', "w")

            for fileName in fileNames:
                zf.write(os.path.join(fileName), arcname=os.path.split(fileName)[1])
                os.remove(fileName)

            shutil.rmtree(tempPath, ignore_errors=True, onerror=None)
            zf.close()
