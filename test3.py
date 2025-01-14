from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QTableWidgetItem, QMainWindow, QDialog, QMessageBox, QApplication, QVBoxLayout, QTableWidget
from PyQt5.QtCore import QTimer, QTime, QDate, Qt 
from datetime import datetime
import json
import os
import sys
import random
import sqlite3

# Create SQLite database and table
conn = sqlite3.connect('patient_vitals.db')
c = conn.cursor()
c.execute("""CREATE TABLE IF NOT EXISTS patient_vitals (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              timestamp DATETIME NOT NULL,
              ecg INTEGER,
              nibp TEXT,
              spo2 INTEGER,
              co2 INTEGER,
              resp INTEGER,
              temp DECIMAL(3,1)
           )""")
conn.commit()

# Login Window Class
class LoginWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('login.ui', self)

        # Store main window as instance variable
        self.main_window = None

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
            'tempHigh': 37.5,
            'sens': 'Med'
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

        # Check credentials in user list
        for user in self.users:
            if user['username'] == username and user['password'] == password:
                self.label_5.setText("")
                self.open_alldata()  # Open alldata on successful login
                return

        # If no match is found
        self.label_5.setText("Wrong Username or Password!")
        self.label_5.setStyleSheet("color: red;")

    def open_alldata(self):
        """Open the main application window"""
        self.main_window = MainWindow()
        self.main_window.show()
        self.close()


# Main Monitoring Window Class
class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi('alldata.ui', self)

        # Store dialog references
        self.table_dialog = None

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
        self.tableButton.clicked.connect(self.show_table_dialog) 

        # Initialize NIBP status
        self.nibp_running = False
        self.last_nibp_value = "--/--"  # Initialize with default "--/--"

    def update_datetime(self):
        current_time = QTime.currentTime()
        current_date = QDate.currentDate()
        self.date.setText(current_date.toString('dd/MM/yyyy'))
        self.time.setText(current_time.toString('HH:mm:ss'))

    def update_sensor_values(self):
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Get ECG value
        ecg = random.randint(60, 100)
        self.ecgInput.setText(str(ecg))

        # Get NIBP values
        if self.nibp_running:
            sys = random.randint(90, 140)
            dias = random.randint(60, 90)
            self.last_nibp_value = f"{sys}/{dias}"
            self.nibpInput.setText(self.last_nibp_value)
        else:
            sys, dias = map(str, self.last_nibp_value.split('/'))

        # Get other values
        spo2 = random.randint(95, 100)
        co2 = random.randint(35, 45)
        resp = random.randint(12, 20)
        temp = round(random.uniform(36.5, 37.5), 1)
        awrr = random.randint(12, 20)
        ins = random.randint(15, 25)
        nibpvol = random.randint(80, 120)

        # Update display
        self.spo2Input.setText(str(spo2))
        self.co2Input.setText(str(co2))
        self.respInput.setText(str(resp))
        self.tempInput.setText(f"{temp}")
        self.awrrInput.setText(str(awrr))
        self.insInput.setText(str(ins))
        self.nibpvolInput.setText(str(nibpvol))

        # Store data in database
        c.execute("""
            INSERT INTO patient_vitals 
            (timestamp, ecg, nibp, spo2, co2, resp, temp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (current_time, ecg, self.last_nibp_value, spo2, co2, resp, temp))
        conn.commit()
    

    def set_modes_off(self):
        self.pvcsmode.setText("OFF")
        self.st1mode.setText("OFF")
        self.st2mode.setText("OFF")

    def show_alarm_dialog(self):
        dialog = AlarmDialog()
        dialog.exec_()

    def show_patient_dialog(self):
        dialog = PatientDialog()
        dialog.exec_()

    def toggle_nibp(self):
        self.nibp_running = not self.nibp_running
        self.nibpButton.setText("Stop NIBP" if self.nibp_running else "Start NIBP")

    def show_table_dialog(self):
        if self.table_dialog is None or not self.table_dialog.isVisible():
            self.table_dialog = TableDialog(self)
        self.table_dialog.show()
        self.table_dialog.raise_()
        self.table_dialog.activateWindow()

    def closeEvent(self, event):
        """Clean up database connection when closing"""
        conn.close()
        super().closeEvent(event)

    def closeEvent(self, event):
        # Cleanup
        self.datetime_timer.stop()
        self.sensor_timer.stop()
        if self.table_dialog is not None:
            self.table_dialog.close()
        conn.close()
        super().closeEvent(event)


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
                # Set sensInput value
                sens_index = self.sensInput.findText(values['sens'])
                if sens_index >= 0:
                    self.sensInput.setCurrentIndex(sens_index)
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
            'tempHigh': self.tempHigh.value(),
            'sens': self.sensInput.currentText()
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
        # Set default value for sensInput to Med
        sens_index = self.sensInput.findText('Med')
        if sens_index >= 0:
            self.sensInput.setCurrentIndex(sens_index)


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


class TableDialog(QDialog):
    def __init__(self, parent=None):
        super(TableDialog, self).__init__(parent)
        self.setWindowTitle("Patient Vitals Data")
        self.setMinimumSize(800, 400)
        
        # Create and set layout
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        # Create table widget
        self.tableWidget = QTableWidget(self)
        self.tableWidget.setColumnCount(7)
        self.tableWidget.setHorizontalHeaderLabels([
            'Timestamp', 'ECG', 'NIBP (Sys/Dias)', 
            'SPO2', 'CO2', 'RESP', 'TEMP'
        ])
        
        # Set table properties
        self.tableWidget.setAlternatingRowColors(True)
        self.tableWidget.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        self.tableWidget.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents)
        
        # Add table to layout
        self.layout.addWidget(self.tableWidget)
        
        # Setup update timer
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_table)
        self.update_timer.start(1000)

    def update_table(self):
        try:
            c.execute("""
                SELECT timestamp, ecg, nibp, spo2, co2, resp, temp 
                FROM patient_vitals 
                WHERE timestamp >= datetime('now', '-60 seconds') 
                ORDER BY timestamp DESC
            """)
            data = c.fetchall()
            
            self.tableWidget.setRowCount(len(data))
            for row, record in enumerate(data):
                for col, value in enumerate(record):
                    item = QtWidgets.QTableWidgetItem(str(value))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.tableWidget.setItem(row, col, item)
        except Exception as e:
            print(f"Error updating table: {e}")

    def closeEvent(self, event):
        self.update_timer.stop()
        super().closeEvent(event)


# Main Application
def main():
    app = QApplication(sys.argv)
    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec_())

# Run the application
if __name__ == '__main__':
    main()

