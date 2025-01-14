from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QMainWindow, QDialog, QMessageBox, QApplication, QVBoxLayout
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtCore import QTimer, QTime, QDate
from PyQt5.QtGui import QPainter
import numpy as np
import time
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

        # Inisialisasi data untuk grafik
        self.data_points = 100
        self.charts_data = {
            'ecg1': [0] * self.data_points,
            'ecg2': [0] * self.data_points,
            'ecg5': [0] * self.data_points,
            'pleth': [0] * self.data_points,
            'resp': [0] * self.data_points,
            'co2': [0] * self.data_points
        }
        self.time_data = list(range(self.data_points))
        
        # Setup grafik
        self.setup_all_charts()
        
        # Timer untuk update grafik
        self.chart_timer = QTimer()
        self.chart_timer.timeout.connect(self.update_all_charts)
        self.chart_timer.start(50)  # Update setiap 50ms

    def setup_chart(self, widget, title, y_range=(-1.5, 1.5), y_label=''):
        # Buat figure dan axis matplotlib dengan background hitam
        figure = plt.Figure(figsize=(4, 2), facecolor='black')
        canvas = FigureCanvas(figure)
        ax = figure.add_subplot(111)
        
        # Set warna background plot menjadi hitam
        ax.set_facecolor('black')
        
        # Setup judul dan label
        ax.set_title(plt.title, color='white', pad=10)
        ax.set_xlabel('Waktu (detik)', color='white')
        ax.set_ylabel(plt.ylabel, color='white')
        
        # Setup range dan grid
        ax.set_ylim(range)
        ax.grid(True, color='gray', alpha=0.3)
        
        # Ubah warna ticks
        ax.tick_params(axis='x', colors='white')
        ax.tick_params(axis='y', colors='white')
        
        # Ubah warna spines (garis tepi plot)
        for spine in ax.spines.values():
            spine.set_color('white')
        
        # Plot line dengan warna yang sesuai
        line, = ax.plot(self.time_data, [0] * self.data_points, color='lime')
        
        # Tambahkan ke widget
        layout = QVBoxLayout()
        layout.addWidget(canvas)
        widget.setLayout(layout)
        
        return line, canvas

    def setup_all_charts(self):
        # Dictionary untuk menyimpan line dan canvas setiap grafik
        self.lines = {}
        self.canvases = {}
        
        # Setup setiap grafik dengan label yang sesuai
        self.lines['ecg1'], self.canvases['ecg1'] = self.setup_chart(
            self.ecg1, 
            "ECG Lead I", 
            (-1.5, 1.5), 
            'Amplitudo (mV)'
        )
        
        self.lines['ecg2'], self.canvases['ecg2'] = self.setup_chart(
            self.ecg2, 
            "ECG Lead II", 
            (-1.5, 1.5), 
            'Amplitudo (mV)'
        )
        
        self.lines['ecg5'], self.canvases['ecg5'] = self.setup_chart(
            self.ecg5, 
            "ECG Lead V", 
            (-1.5, 1.5), 
            'Amplitudo (mV)'
        )
        
        self.lines['pleth'], self.canvases['pleth'] = self.setup_chart(
            self.pleth, 
            "Plethysmograph", 
            (-1.0, 1.0), 
            'Amplitudo (AU)'
        )
        
        self.lines['resp'], self.canvases['resp'] = self.setup_chart(
            self.resp, 
            "Respiratory", 
            (-1.0, 1.0), 
            'Amplitudo (AU)'
        )
        
        self.lines['co2'], self.canvases['co2'] = self.setup_chart(
            self.co2, 
            "Capnograph", 
            (0, 50), 
            'CO2 (mmHg)'
        )

    def generate_signal(self, signal_type):
        t = time.time() * 10
        if signal_type.startswith('ecg'):
            # Sinyal ECG dengan spike periodik
            base = np.sin(t) * 0.3
            if t % 1 < 0.1:
                base += 1.0
            return base
        elif signal_type == 'pleth':
            # Sinyal pleth lebih smooth
            return np.sin(t) * 0.5
        elif signal_type == 'resp':
            # Sinyal respiratory lebih lambat
            return np.sin(t/4) * 0.5
        elif signal_type == 'co2':
            # Sinyal CO2 dengan baseline lebih tinggi
            return 35 + np.sin(t/2) * 5

    def update_all_charts(self):
        # Update data dan grafik
        for signal_type, line in self.lines.items():
            new_value = self.generate_signal(signal_type)
            self.charts_data[signal_type] = self.charts_data[signal_type][1:] + [new_value]
            
            # Update data grafik
            line.set_ydata(self.charts_data[signal_type])
            self.canvases[signal_type].draw()

    def update_datetime(self):
        current_time = QTime.currentTime()
        current_date = QDate.currentDate()
        self.date.setText(current_date.toString('dd/MM/yyyy'))
        self.time.setText(current_time.toString('HH:mm:ss'))

    def update_sensor_values(self):
        # ECG (BPM: 60-100)
        self.ecgInput.setText(str(random.randint(60, 100)))

        # NIBP
        if self.nibp_running:
            sys = random.randint(90, 140)
            dias = random.randint(60, 90)
            self.last_nibp_value = f"{sys}/{dias}"
            self.nibpInput.setText(self.last_nibp_value)
        else:
            self.nibpInput.setText(self.last_nibp_value)

        # Other sensor values
        self.nibpvolInput.setText(str(random.randint(80, 120)))
        self.spo2Input.setText(str(random.randint(95, 100)))
        self.awrrInput.setText(str(random.randint(12, 20)))
        self.insInput.setText(str(random.randint(15, 25)))
        self.co2Input.setText(str(random.randint(35, 45)))
        self.respInput.setText(str(random.randint(12, 20)))
        self.tempInput.setText(f"{round(random.uniform(36.5, 37.5), 1)}")


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

    def exit_to_login(self):
        self.close()
        self.login_window = LoginWindow()
        self.login_window.show()


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


# Main Application
def main():
    app = QApplication(sys.argv)
    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec_())

# Run the application
if __name__ == '__main__':
    main()

