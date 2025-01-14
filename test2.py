from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QMainWindow, QDialog, QMessageBox, QApplication
from PyQt5.QtCore import QTimer, QTime, QDate
import json
import os
import sys
import random

# Login Window Class
class LoginWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('login.ui', self)
        
        # Load user data from JSON
        self.users = self.load_users()
        
        # Connect login button
        self.loginButton.clicked.connect(self.check_login)
        self.label_5.setText("")
        
        # Reset patient data on startup
        self.reset_patient_data()
        
        # Reset alarm values to default
        self.reset_alarm_values()

    def reset_patient_data(self):
        """Reset patient data to empty values"""
        empty_data = {
            'nama': '',
            'nrm': '',
            'umur': '',
            'gender': 'Laki-laki'
        }
        with open('patient_data.json', 'w') as file:
            json.dump(empty_data, file)

    def reset_alarm_values(self):
        """Reset alarm values to default"""
        default_values = {
            'HRlow': 60,
            'HRhigh': 100,
            'diasLow': 40,
            'diasHigh': 100,
            'sysLow': 60,
            'sysHigh': 190,
            'etco2low': 35,
            'etco2High': 47,
            'spO2low': 90,
            'spO2high': 100,
            'tempLow': 36.0,
            'tempHigh': 37.5
        }
        with open('alarm_values.json', 'w') as file:
            json.dump(default_values, file)

    def load_users(self):
        """Load users from users.json"""
        try:
            with open('users.json', 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            print("Error: users.json not found!")
            return []

    def check_login(self):
        """Validate username and password"""
        username = self.usernameInput.text()
        password = self.passwordInput.text()
        
        for user in self.users:
            if user['username'] == username and user['password'] == password:
                self.label_5.setText("")
                self.open_alldata()
                return
        
        self.label_5.setText("Wrong Username or Password!")
        self.label_5.setStyleSheet("color: red;")

    def open_alldata(self):
        """Open the main application window"""
        self.main_window = MainWindow()
        self.main_window.show()
        self.close()

class AlarmDialog(QDialog):
    def __init__(self):
        super(AlarmDialog, self).__init__()
        try:
            uic.loadUi('alarm.ui', self)
            self.load_alarm_values()
            # Connect the OK button to save values
            self.buttonBox.accepted.connect(self.save_alarm_values)
        except Exception as e:
            print("Error loading alarm UI:", e)

    def load_alarm_values(self):
        """Load saved alarm values or use defaults"""
        try:
            with open('alarm_values.json', 'r') as file:
                values = json.load(file)
                
                # Set values to spinboxes
                self.HRlow.setValue(values['HRlow'])
                self.HRhigh.setValue(values['HRhigh'])
                self.diasLow.setValue(values['diasLow'])
                self.diasHigh.setValue(values['diasHigh'])
                self.sysLow.setValue(values['sysLow'])
                self.sysHigh.setValue(values['sysHigh'])
                self.etco2low.setValue(values['etco2low'])
                self.etco2High.setValue(values['etco2High'])
                self.spO2low.setValue(values['spO2low'])
                self.spO2high.setValue(values['spO2high'])
                self.tempLow.setValue(values['tempLow'])
                self.tempHigh.setValue(values['tempHigh'])
        except FileNotFoundError:
            # Use default values if file doesn't exist
            self.set_default_values()

    def save_alarm_values(self):
        """Save current alarm values to file"""
        values = {
            'HRlow': self.HRlow.value(),
            'HRhigh': self.HRhigh.value(),
            'diasLow': self.diasLow.value(),
            'diasHigh': self.diasHigh.value(),
            'sysLow': self.sysLow.value(),
            'sysHigh': self.sysHigh.value(),
            'etco2low': self.etco2low.value(),
            'etco2High': self.etco2High.value(),
            'spO2low': self.spO2low.value(),
            'spO2high': self.spO2high.value(),
            'tempLow': self.tempLow.value(),
            'tempHigh': self.tempHigh.value()
        }
        with open('alarm_values.json', 'w') as file:
            json.dump(values, file)

    def set_default_values(self):
        """Set default values for all fields"""
        self.HRlow.setValue(60)
        self.HRhigh.setValue(100)
        self.diasLow.setValue(40)
        self.diasHigh.setValue(100)
        self.sysLow.setValue(60)
        self.sysHigh.setValue(190)
        self.etco2low.setValue(35)
        self.etco2High.setValue(47)
        self.spO2low.setValue(90)
        self.spO2high.setValue(100)
        self.tempLow.setValue(36.0)
        self.tempHigh.setValue(37.5)

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi('alldata.ui', self)

        # Real-time date and time display
        self.datetime_timer = QTimer()
        self.datetime_timer.timeout.connect(self.update_datetime)
        self.datetime_timer.start(1000)

        # Sensor data simulation
        self.sensor_timer = QTimer()
        self.sensor_timer.timeout.connect(self.update_sensor_values)
        self.sensor_timer.start(1000)

        # Connect menu buttons
        self.alarmButton.clicked.connect(self.show_alarm_dialog)
        self.exitButton.clicked.connect(self.exit_to_login)
        self.patientButton.clicked.connect(self.show_patient_dialog)
        self.nibpButton.clicked.connect(self.toggle_nibp)

        # Initialize NIBP status
        self.nibp_running = False
        self.last_nibp_value = "--/--"

    def exit_to_login(self):
        """Exit to login screen and reset patient data"""
        login_window = LoginWindow()
        login_window.show()
        self.close()

    # ... (rest of the MainWindow methods remain the same)

class PatientDialog(QDialog):
    def __init__(self):
        super(PatientDialog, self).__init__()
        uic.loadUi('patient.ui', self)
        self.buttonBox.accepted.connect(self.save_data)
        self.load_data()
    
    def save_data(self):
        """Save patient data to file"""
        patient_data = {
            'nama': self.nameInput.text(),
            'nrm': self.nrmInput.text(),
            'umur': self.ageInput.text(),
            'gender': self.genderInput.currentText()
        }
        with open('patient_data.json', 'w') as file:
            json.dump(patient_data, file)
    
    def load_data(self):
        """Load patient data from file"""
        try:
            with open('patient_data.json', 'r') as file:
                patient_data = json.load(file)
                
                self.nameInput.setText(patient_data.get('nama', ''))
                self.nrmInput.setText(patient_data.get('nrm', ''))
                self.ageInput.setText(patient_data.get('umur', ''))

                gender = patient_data.get('gender', 'Laki-laki')
                index = self.genderInput.findText(gender)
                if index >= 0:
                    self.genderInput.setCurrentIndex(index)
        except FileNotFoundError:
            # If file doesn't exist, leave fields empty
            pass

def main():
    app = QApplication(sys.argv)
    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()