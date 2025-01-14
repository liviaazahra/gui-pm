import sys
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QLabel, QSpinBox, QDoubleSpinBox, QComboBox, QWidget, QGridLayout, QHBoxLayout, QApplication
from PyQt5.QtCore import QCoreApplication, QRect, QMetaObject, Qt

class Ui_AlarmSettingsDialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(400, 300)

        # Button box setup
        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setGeometry(QRect(30, 240, 341, 32))
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)

        # Grid layout setup
        self.gridLayoutWidget = QWidget(Dialog)
        self.gridLayoutWidget.setObjectName(u"gridLayoutWidget")
        self.gridLayoutWidget.setGeometry(QRect(10, 10, 381, 181))
        self.gridLayout = QGridLayout(self.gridLayoutWidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(0, 0, 0, 0)

        # Labels for various parameters
        self.label = QLabel(self.gridLayoutWidget)
        self.label.setObjectName(u"label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)

        self.HRlow = QSpinBox(self.gridLayoutWidget)
        self.HRlow.setObjectName(u"HRlow")
        self.gridLayout.addWidget(self.HRlow, 0, 1, 1, 1)

        self.HRhigh = QSpinBox(self.gridLayoutWidget)
        self.HRhigh.setObjectName(u"HRhigh")
        self.gridLayout.addWidget(self.HRhigh, 0, 2, 1, 1)

        self.label_2 = QLabel(self.gridLayoutWidget)
        self.label_2.setObjectName(u"label_2")
        self.gridLayout.addWidget(self.label_2, 2, 0, 1, 1)

        self.spO2low = QSpinBox(self.gridLayoutWidget)
        self.spO2low.setObjectName(u"spO2low")
        self.gridLayout.addWidget(self.spO2low, 2, 1, 1, 1)

        self.spO2high = QSpinBox(self.gridLayoutWidget)
        self.spO2high.setObjectName(u"spO2high")
        self.gridLayout.addWidget(self.spO2high, 2, 2, 1, 1)

        self.label_3 = QLabel(self.gridLayoutWidget)
        self.label_3.setObjectName(u"label_3")
        self.gridLayout.addWidget(self.label_3, 4, 0, 1, 1)

        self.sysLow = QSpinBox(self.gridLayoutWidget)
        self.sysLow.setObjectName(u"sysLow")
        self.gridLayout.addWidget(self.sysLow, 4, 1, 1, 1)

        self.sysHigh = QSpinBox(self.gridLayoutWidget)
        self.sysHigh.setObjectName(u"sysHigh")
        self.gridLayout.addWidget(self.sysHigh, 4, 2, 1, 1)

        self.diasLow = QSpinBox(self.gridLayoutWidget)
        self.diasLow.setObjectName(u"diasLow")
        self.gridLayout.addWidget(self.diasLow, 5, 1, 1, 1)

        self.diasHigh = QSpinBox(self.gridLayoutWidget)
        self.diasHigh.setObjectName(u"diasHigh")
        self.gridLayout.addWidget(self.diasHigh, 5, 2, 1, 1)

        self.label_6 = QLabel(self.gridLayoutWidget)
        self.label_6.setObjectName(u"label_6")
        self.gridLayout.addWidget(self.label_6, 5, 0, 1, 1)

        self.label_4 = QLabel(self.gridLayoutWidget)
        self.label_4.setObjectName(u"label_4")
        self.gridLayout.addWidget(self.label_4, 6, 0, 1, 1)

        # Body temperature settings
        self.tempLow = QDoubleSpinBox(self.gridLayoutWidget)
        self.tempLow.setObjectName(u"tempLow")
        self.gridLayout.addWidget(self.tempLow, 6, 1, 1, 1)

        self.tempHigh = QDoubleSpinBox(self.gridLayoutWidget)
        self.tempHigh.setObjectName(u"tempHigh")
        self.gridLayout.addWidget(self.tempHigh, 6, 2, 1, 1)

        self.label_5 = QLabel(self.gridLayoutWidget)
        self.label_5.setObjectName(u"label_5")
        self.gridLayout.addWidget(self.label_5, 7, 0, 1, 1)

        self.etco2low = QSpinBox(self.gridLayoutWidget)
        self.etco2low.setObjectName(u"etco2low")
        self.gridLayout.addWidget(self.etco2low, 7, 1, 1, 1)

        self.etco2High = QSpinBox(self.gridLayoutWidget)
        self.etco2High.setObjectName(u"etco2High")
        self.gridLayout.addWidget(self.etco2High, 7, 2, 1, 1)

        # Alarm sensitivity selection
        self.horizontalLayoutWidget = QWidget(Dialog)
        self.horizontalLayoutWidget.setObjectName(u"horizontalLayoutWidget")
        self.horizontalLayoutWidget.setGeometry(QRect(10, 200, 381, 31))
        self.horizontalLayout = QHBoxLayout(self.horizontalLayoutWidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)

        self.label_8 = QLabel(self.horizontalLayoutWidget)
        self.label_8.setObjectName(u"label_8")
        self.horizontalLayout.addWidget(self.label_8)

        self.comboBox = QComboBox(self.horizontalLayoutWidget)
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.setObjectName(u"comboBox")
        self.horizontalLayout.addWidget(self.comboBox)

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)
        QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Alarm Settings", None))
        self.label.setText(QCoreApplication.translate("Dialog", u"Heart Rate", None))
        self.label_2.setText(QCoreApplication.translate("Dialog", u"SpO2", None))
        self.label_3.setText(QCoreApplication.translate("Dialog", u"Systolic Blood Pressure", None))
        self.label_6.setText(QCoreApplication.translate("Dialog", u"Diastolic Blood Pressure", None))
        self.label_4.setText(QCoreApplication.translate("Dialog", u"Body Temperature", None))
        self.label_5.setText(QCoreApplication.translate("Dialog", u"EtCO2", None))
        self.label_8.setText(QCoreApplication.translate("Dialog", u"Alarm Sensitivity", None))
        self.comboBox.setItemText(0, QCoreApplication.translate("Dialog", u"High", None))
        self.comboBox.setItemText(1, QCoreApplication.translate("Dialog", u"Low", None))
        self.comboBox.setItemText(2, QCoreApplication.translate("Dialog", u"Medium", None))

class AlarmDialog(QDialog):
    def __init__(self, parent=None):
        super(AlarmDialog, self).__init__(parent)
        self.ui = Ui_AlarmSettingsDialog()
        self.ui.setupUi(self)

    def accept(self):
        # Process and save the input values here if needed
        super(AlarmDialog, self).accept()

# Main application setup
if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = AlarmDialog()
    dialog.exec_()  # Show the dialog
    sys.exit(app.exec_())


class AlarmDialog(QDialog):
    def __init__(self, parent=None):
        super(AlarmDialog, self).__init__(parent)
        self.ui = Ui_AlarmSettingsDialog()
        self.ui.setupUi(self)

    def accept(self):
        # Process and save the input values here if needed
        super(AlarmDialog, self).accept()

# Main application setup
if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = AlarmDialog()
    dialog.exec_()  # Show the dialog
    sys.exit(app.exec_())
