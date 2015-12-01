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
import tempfile
import shutil
import uuid

def bounds(layers):

    extent = None
    for layer in layers:
        if layer.type() == QgsMapLayer.VectorLayer or layer.type() == QgsMapLayer.RasterLayer:
            transform = QgsCoordinateTransform(layer.crs(), QgsCoordinateReferenceSystem('EPSG:4326')) # WGS 84 / UTM zone 33N
            try:
                layerExtent = transform.transform(layer.extent())
            except QgsCsException:
                print "exception in transform layer srs"
                layerExtent = QgsRectangle(-180, -90, 180, 90)
            if extent is None:
                extent = layerExtent
            else:
                extent.combineExtentWith(layerExtent)

    return (extent.xMinimum(), extent.yMinimum(), extent.xMaximum(), extent.yMaximum())

def copySymbols(symbol, tempPath, fileNames):
    for i in xrange(symbol.symbolLayerCount()):
        sl = symbol.symbolLayer(i)
        if isinstance(sl, QgsSvgMarkerSymbolLayerV2):
            symbolPath = sl.path();
            shutil.copy(symbolPath, tempPath)
            print "Copying " + str(sl.path())
            fileNames.append(tempPath + os.sep + os.path.basename(symbolPath))
        else:
            print "Ignoring " + str(sl)

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
            print "Driver ogr name: " + ogr_driver_name
            layers = qgis.utils.iface.mapCanvas().layers()
            project = QgsProject.instance()
            mapInfo = {"name": os.path.basename(project.fileName()), "layers": [], "bounds": []}
            tempPath = tempfile.mkdtemp('bulkexport') + os.sep
            fileNames = []
            crs = QgsCoordinateReferenceSystem("EPSG:4326")
            for layer in reversed(layers):
                print 'Writing:' + unicode(layer.name())
                layer_filename = tempPath + unicode(uuid.uuid4())
                print 'Filename: ' + layer_filename
                layerType = layer.type()
                if layerType == QgsMapLayer.VectorLayer:
                    print 'VectorLayer'
                    renderer = layer.rendererV2()
                    hasIcon = False
                    if isinstance(renderer, QgsSingleSymbolRendererV2):
                        copySymbols(renderer.symbol(), tempPath, fileNames)
                        hasIcon = True

                    result2 = qgis.core.QgsVectorFileWriter.writeAsVectorFormat(layer, layer_filename, "utf-8", crs, ogr_driver_name)
                    print "Status: " + str(result2)
                    if result2 != 0:
                        QtGui.QMessageBox.warning(self.dlg, "BulkVectorExport",\
                            "Failed to export: " + layer.name() + \
                            " Status: " + str(result2))
                    sld_filename = os.path.join(tempPath, os.path.basename(layer_filename) + '.sld')
                    print 'Filename: ' + sld_filename
                    layer.saveSldStyle(sld_filename)
                    mapInfo['layers'].append({
                        "title": unicode(layer.name()),
                        "geojson": os.path.basename(layer_filename) + '.geojson',
                        "sld": os.path.basename(sld_filename),
                        "opacity":  1 - (layer.layerTransparency() / 100.0),
                        "hasIcon": hasIcon
                    })
                    fileNames.append(layer_filename + '.geojson')
                    fileNames.append(sld_filename)
                elif layerType == QgsMapLayer.RasterLayer:
                    print 'RasterLayer'
                    pipe = qgis.core.QgsRasterPipe()
                    pipe.set(layer.dataProvider())
                    pipe.set(layer.renderer())
                    rasterWriter = qgis.core.QgsRasterFileWriter(layer_filename + '.tif')
                    width, height, extent = layer.width(), layer.height(), layer.extent()
                    print 'exporting width, height, extend' + str(width) + '/' + str(height) + '/' + str(extent)
                    resultWriter = rasterWriter.writeRaster(pipe, width, height, extent, crs)
                    if resultWriter != 0:
                        QtGui.QMessageBox.warning(self.dlg, "BulkVectorExport", "Failed to export: " + layer.name() + " Status: " + str(resultWriter));
                    mapInfo['layers'].append({
                        "title": unicode(layer.name()),
                        "tif": os.path.basename(layer_filename) + '.tif',
                        "opacity": 1
                    });
                    fileNames.append(layer_filename + '.tif');

            ## initial bounding box is visible extent
            canvas = self.iface.mapCanvas()
            canvasExtent = canvas.extent()
            crsDest = QgsCoordinateReferenceSystem('EPSG:4326')
            try:
                crsSrc = canvas.mapSettings().destinationCrs()
            except:
                crsSrc = canvas.mapRenderer().destinationCrs()
            xform = QgsCoordinateTransform(crsSrc, crsDest)
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
            mapInfo['limitedInitialBounds'] = True
            mapInfo['popupLayerIndex'] = -1;
            mapInfo['hasLayerControl'] = True
            mapInfo['hasZoomControl'] = True
            mapInfo['hasLayerLegend'] = True
            mapInfo['basemap'] = 'bmapgrau';
            map_filename = tempPath + 'metadata.json'
            with open(map_filename, 'w') as outfile:
                json.dump(mapInfo, outfile)

            fileNames.append(map_filename)

            ## zip all
            zf = zipfile.ZipFile(dirName +  os.sep + os.path.basename(unicode(project.fileName())) + '.globus.zip', "w")

            for fileName in fileNames:
                zf.write(os.path.join(fileName), arcname=os.path.split(fileName)[1])
                os.remove(fileName)
            os.rmdir(tempPath)
            zf.close()
