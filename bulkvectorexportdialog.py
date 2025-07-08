# -*- coding: utf-8 -*-
"""
/***************************************************************************
 BulkVectorExportDialog
 
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

from builtins import str
from qgis.PyQt import QtCore, QtGui, QtWidgets
from .ui_bulkvectorexport import Ui_BulkVectorExportDialog
from osgeo import ogr


class BulkVectorExportDialog(QtWidgets.QDialog):
    def __init__(self):
        QtWidgets.QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.ui = Ui_BulkVectorExportDialog()
        self.ui.setupUi(self)
        # dir button push event
        self.ui.dirButton.clicked.connect(self.getDir)
        self.unsupportedDriverList = ['Memory', 'PostgreSQL', 'MySQL', 'ODBC', \
            'S57']
        self.ui.compression_no.toggled.connect(self.update_compression)
        self.ui.compression_lzw.toggled.connect(self.update_compression)
        self.ui.compression_jpeg.toggled.connect(self.update_compression)
        
    def getDir(self):
        dirName = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory"))
        self.ui.dirEdit.setText(dirName)
        
    def update_compression(self, checked):
        if not checked:
            return
        if self.ui.compression_no.isChecked():
            tiffCompression = 'COMPRESS=NONE'
            print(tiffCompression)
            return tiffCompression
        if self.ui.compression_lzw.isChecked():
            tiffCompression = 'COMPRESS=DEFLATE'
            print(tiffCompression)
            return tiffCompression
        if self.ui.compression_jpeg.isChecked():
            tiffCompression = 'COMPRESS=JPEG'
            print(tiffCompression)
            return tiffCompression
            
