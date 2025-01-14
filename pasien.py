import sys
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QDialog

class PatientInfo(QDialog):
    def __init__(self):
        super(PatientInfo, self).__init__()
        
        # Load UI file
        uic.loadUi('patient.ui', self)
        self.show()

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = PatientInfo()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()