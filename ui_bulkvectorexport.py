# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_bulkvectorexport.ui'
#
# Created: Wed Jul 29 15:23:48 2015
#      by: PyQt4 UI code generator 4.10.4
#
# WARNING! All changes made in this file will be lost!

from builtins import object
from qgis.PyQt import QtCore, QtGui, QtWidgets

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtWidgets.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context, text, disambig)

class Ui_BulkVectorExportDialog(object):
    def setupUi(self, BulkVectorExportDialog):
        BulkVectorExportDialog.setObjectName(_fromUtf8("BulkVectorExportDialog"))
        BulkVectorExportDialog.resize(392, 141)
        self.buttonBox = QtWidgets.QDialogButtonBox(BulkVectorExportDialog)
        self.buttonBox.setGeometry(QtCore.QRect(220, 100, 161, 32))
        self.buttonBox.setWhatsThis(_fromUtf8(""))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(True)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.dirEdit = QtWidgets.QLineEdit(BulkVectorExportDialog)
        self.dirEdit.setGeometry(QtCore.QRect(120, 40, 231, 20))
        self.dirEdit.setObjectName(_fromUtf8("dirEdit"))
        self.label = QtWidgets.QLabel(BulkVectorExportDialog)
        self.label.setGeometry(QtCore.QRect(10, 40, 71, 16))
        self.label.setObjectName(_fromUtf8("label"))
        self.dirButton = QtWidgets.QPushButton(BulkVectorExportDialog)
        self.dirButton.setGeometry(QtCore.QRect(360, 40, 31, 21))
        self.dirButton.setObjectName(_fromUtf8("dirButton"))

        self.retranslateUi(BulkVectorExportDialog)
        self.buttonBox.accepted.connect(BulkVectorExportDialog.accept)
        self.buttonBox.rejected.connect(BulkVectorExportDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(BulkVectorExportDialog)

    def retranslateUi(self, BulkVectorExportDialog):
        BulkVectorExportDialog.setWindowTitle(_translate("BulkVectorExportDialog", "Export", None))
        self.label.setText(_translate("BulkVectorExportDialog", "Export to:", None))
        self.dirButton.setText(_translate("BulkVectorExportDialog", "...", None))

