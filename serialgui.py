import sys
import os
import random
import json
import csv
from datetime import datetime, timedelta
import sqlite3
import numpy as np
import neurokit2 as nk

# PyQt5 imports
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QMainWindow, QApplication, QMessageBox,
    QComboBox, QPushButton, QFileDialog
)
from PyQt5.QtCore import QTimer, QTime, QDate, QObject, pyqtSignal
from PyQt5 import QtWidgets, uic

# Matplotlib imports
import pyqtgraph as pg
from pyqtgraph import PlotWidget

# Threading
from threading import Thread

import serial
from PyQt5.QtCore import QThread, pyqtSignal



def save_login_time():
    """Simpan waktu login terpisah"""
    with open('login_time.json', 'w') as f:
        json.dump({'last_login': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}, f)

def get_login_time():
    """Ambil waktu login dari file terpisah"""
    try:
        with open('login_time.json', 'r') as f:
            return json.load(f).get('last_login', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    except (FileNotFoundError, json.JSONDecodeError):
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

class SerialReaderThread(QThread):
    data_received = pyqtSignal(dict)

    def __init__(self, port='COM10', baudrate=115200):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.running = True

    def run(self):
        try:
            with serial.Serial(self.port, self.baudrate, timeout=1) as ser:
                while self.running:
                    line = ser.readline().decode().strip()
                    if line.startswith("{") and line.endswith("}"):
                        try:
                            data = json.loads(line)
                            self.data_received.emit(data)
                        except json.JSONDecodeError:
                            continue
        except serial.SerialException as e:
            print(f"[ERROR] Serial connection failed: {e}")

    def stop(self):
        self.running = False
        self.wait()


# Login Window Class
class LoginWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('login.ui', self)
        self.showMaximized()
        # Load user data from JSON
        self.users = self.load_users()
        # Connect login button
        self.loginButton.clicked.connect(self.check_login)
        # Reset patient data and alarm values
        self.reset_patient_data()
        self.reset_alarm_values()

    def check_login(self):
        username = self.usernameInput.text()
        password = self.passwordInput.text()

        for user in self.users:
            if user['username'] == username and user['password'] == password:
                save_login_time()  # <-- Simpan waktu login ke file terpisah
                self.open_alldata()
                return

        self.label_5.setText("Wrong Username or Password!")
        self.label_5.setStyleSheet("color: red;")

    def load_users(self):
        """Load users from users.json"""
        try:
            with open('users.json', 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            print("Error: users.json not found!")
            return []

    def open_alldata(self):
        """Open the main application window"""
        self.main_window = MainWindow()
        self.main_window.show()
        self.close()

    def reset_patient_data(self):
        """Reset patient data to empty/default values"""
        empty_data = {
            'nama': '',
            'nrm': '',
            'tanggal_lahir': '2000-01-01',
            'umur': 0,
            'gender': 'Laki-laki',
            'nomor_kamar': '',
            'dokter': '',
            'diagnosis': '',
            'alergi': '',
            'tanggal_masuk': '2000-01-01'
        }
        with open('patient_data.json', 'w') as file:
            json.dump(empty_data, file)


    def reset_alarm_values(self):
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
            'respLow': 12,  # TAMBAHKAN INI
            'respHigh': 20, # TAMBAHKAN INI
            'sens': 'Med'
        }
        with open('alarm_values.json', 'w') as file:
            json.dump(default_values, file)     


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi('alldata.ui', self)
        self.showMaximized()

        # Inisialisasi Serial Reader
        self.serial_thread = SerialReaderThread(port='COM10', baudrate=9600)  # Sesuaikan port
        self.serial_thread.data_received.connect(self.update_from_serial)
        self.serial_thread.start()


        self.table_trend = TableTrendWidget()

        # Real-time date and time display
        self.datetime_timer = QTimer()
        self.datetime_timer.timeout.connect(self.update_datetime)
        self.datetime_timer.start(1000)

        # Sensor data simulation
        self.sensor_timer = QTimer()
        self.sensor_timer.timeout.connect(self.update_sensor_values)
        self.sensor_timer.start(1000)

        # Connect menu buttons
        self.alarmButton.clicked.connect(self.show_alarm_window)
        self.exitButton.clicked.connect(self.exit_to_login)
        self.patientButton.clicked.connect(self.show_patient_window)
        self.nibpButton.clicked.connect(self.toggle_nibp)
        self.table_trend = TableTrendWidget()
        self.pushButton.clicked.connect(self.show_table_trend)

        # Initialize NIBP status
        self.nibp_running = False
        self.last_nibp_value = "--/--"

        # Initialize for ECG Chart
        self.data_points = 500
        self.charts_data = {
            'ecg1': [0] * self.data_points,
            'ecg2': [0] * self.data_points,
            'ecg3': [0] * self.data_points,
        }
        self.time_data = np.linspace(-2, 0, self.data_points)  # 2 sec

        # Setup grafik dengan PyQtGraph
        self.setup_all_charts()
        self.setup_ecg_signals() 
        
        # Timer untuk update grafik
        self.chart_timer = QTimer()
        self.chart_timer.timeout.connect(self.update_all_charts)
        self.chart_timer.start(33)  # Update setiap 50ms

    def setup_chart(self, widget, title, y_range=(-1.0, 1.5)):
        # Create a PlotWidget
        plot_widget = PlotWidget()
        
        # Customize the appearance
        plot_widget.setBackground('black')
        plot_widget.setTitle(title, color='white', size='10pt')
        plot_widget.setYRange(*y_range)
        plot_widget.showGrid(x=True, y=True, alpha=0.3)
        
        # Customize axis colors
        styles = {'color': 'white', 'font-size': '8pt'}
        plot_widget.setLabel('left', 'Amplitude', **styles)
        plot_widget.setLabel('bottom', 'Time', **styles)
        
        # Get the plot item to customize axes
        plot_item = plot_widget.getPlotItem()
        
        # Customize axis pens
        axis_pen = pg.mkPen(color='white', width=1)
        plot_item.getAxis('left').setPen(axis_pen)
        plot_item.getAxis('bottom').setPen(axis_pen)
        
        # Customize axis text
        plot_item.getAxis('left').setTextPen(axis_pen)
        plot_item.getAxis('bottom').setTextPen(axis_pen)
        
        # Plot initial data
        line = plot_widget.plot(self.time_data, [0] * self.data_points, pen='cyan')
        
        # Add to widget
        layout = QVBoxLayout()
        layout.addWidget(plot_widget)
        widget.setLayout(layout)
        
        return line, plot_widget

    def setup_all_charts(self):
        # Dictionary untuk menyimpan line dan widget setiap grafik
        self.lines = {}
        self.plot_widgets = {}
        
        # Setup setiap grafik
        self.lines['ecg1'], self.plot_widgets['ecg1'] = self.setup_chart(
            self.ecg1, "ECG Lead I", (-1.5, 1.5))
        self.lines['ecg2'], self.plot_widgets['ecg2'] = self.setup_chart(
            self.ecg2, "ECG Lead II", (-1.5, 1.5))
        self.lines['ecg3'], self.plot_widgets['ecg3'] = self.setup_chart(
            self.ecg3, "ECG Lead III", (-1.5, 1.5))

    def setup_ecg_signals(self):
        """Initialize parameter ECG signals"""
        duration = 60  
        sampling_rate = 250  # Sampling frequency(Hz)
        heart_rate = 72  # Heart Rate (bpm)
        
        self.ecg_data = {
            'ecg1': nk.ecg_simulate(duration, sampling_rate, heart_rate, method="ecgsyn", noise=0.03, random_state=np.random.RandomState(42)),
            'ecg2': nk.ecg_simulate(duration, sampling_rate, heart_rate, method="ecgsyn", noise=0.01, random_state=np.random.RandomState(42)),
            'ecg3': nk.ecg_simulate(duration, sampling_rate, heart_rate, method="ecgsyn", noise=0.02, random_state=np.random.RandomState(42))
        }
        self.ecg_pointers = {key: 0 for key in self.ecg_data.keys()}
        self.ecg_length = len(self.ecg_data['ecg1'])

    def generate_signal(self, signal_type):
        """Generate realistic ECG signal using neurokit2"""
        if signal_type in self.ecg_data:
            # Get current position in ECG data
            idx = self.ecg_pointers[signal_type]
            
            # Get the value and move pointer
            value = self.ecg_data[signal_type][idx]
            self.ecg_pointers[signal_type] = (idx + 1) % self.ecg_length
            
            return value
        return 0
        
    def update_all_charts(self):
        # Update data dan grafik
        for signal_type, line in self.lines.items():
            new_value = self.generate_signal(signal_type)
            self.charts_data[signal_type] = self.charts_data[signal_type][1:] + [new_value]
            
            # Update data grafik
            line.setData(self.time_data, self.charts_data[signal_type])

    def update_datetime(self):
        current_time = QTime.currentTime()
        current_date = QDate.currentDate()
        self.date.setText(current_date.toString('dd/MM/yyyy'))
        self.time.setText(current_time.toString('HH:mm:ss'))

    def load_alarm_values(self):
        """Load alarm threshold values from file"""
        try:
            with open('alarm_values.json', 'r') as file:
                self.alarm_values = json.load(file)
        except FileNotFoundError:
            # Default values if file doesn't exist
            self.alarm_values = {
                'HRlow': 60, 'HRhigh': 100,
                'diasLow': 40, 'diasHigh': 100,
                'sysLow': 60, 'sysHigh': 190,
                'etco2low': 35, 'etco2High': 47,
                'spO2low': 90, 'spO2high': 100,
                'tempLow': 36.0, 'tempHigh': 37.5,
                'respLow': 12, 'respHigh': 20,
                'alarm_status': 'ON' 
            }

    def update_sensor_values(self):
        """Update sensor values using pure serial data"""
        # Initialize with default 0 values
        ecg = 0
        spo2 = 0
        temp = 0.0
        co2 = 0
        
        # Use Serial data for HR, temp, spo2, etco2
        if hasattr(self, 'last_serial_data'):
            serial_data = self.last_serial_data
            ecg = serial_data.get('hr', 0)
            spo2 = serial_data.get('spo2', 0)
            temp = serial_data.get('temp', 0.0)
            co2 = serial_data.get('etco2', 0)

        
        # Update GUI with the values
        self.ecgInput.setText(str(ecg))
        self.spo2Input.setText(str(spo2))
        self.tempInput.setText(f"{temp:.1f}")
        self.co2Input.setText(str(co2))

        # NIBP (Systolic/Diastolic) - always from random generator
        sys, dias = 120, 80  # Default
        if self.nibp_running:
            sys = random.randint(90, 140)
            dias = random.randint(60, 90)
            self.last_nibp_value = f"{sys}/{dias}"
            self.nibpInput.setText(self.last_nibp_value)
        else:
            self.nibpInput.setText(self.last_nibp_value)

        # Respiratory rate - always from random generator
        resp = random.randint(5, 25)
        self.respInput.setText(str(resp))

        # Save values to trend table
        self.table_trend.store_current_values(
            ecg=ecg,
            spo2=spo2,
            nibp=self.last_nibp_value,
            resp=resp,
            temp=temp,
            co2=co2
        )

        # Load alarm values (termasuk sensitivity setting)
        self.load_alarm_values()
        # Check if alarms are enabled
        if self.alarm_values.get('alarm_status', 'ON') == 'OFF':
            self.alert1.setText("Alarm OFF")
            self.alert1.setStyleSheet("color: black;")
            self.alert2.setStyleSheet("background-color: white; border: 0px; color: black;")
            return
        # Check warning/critical conditions
        alert_text = []
        critical_alerts = []

        # Heart Rate
        if 0 <= ecg < 40:
            critical_alerts.append("CRITICAL: Heart Rate <40 bpm!")
        elif 40 <= ecg < self.alarm_values['HRlow']:
            alert_text.append(f"Heart Rate Low! ({ecg} < {self.alarm_values['HRlow']})")
        elif self.alarm_values['HRhigh'] < ecg <= 140:
            alert_text.append(f"Heart Rate High! ({ecg} > {self.alarm_values['HRhigh']})")
        elif ecg > 140:
            critical_alerts.append("CRITICAL: Heart Rate >140 bpm!")

        # SpO2
        if 0 <= spo2 <= 90:
            critical_alerts.append("CRITICAL: SpO₂ ≤90%!")
        elif 90 < spo2 < self.alarm_values['spO2low']:
            alert_text.append(f"Warning: SpO₂ Low ({spo2} < {self.alarm_values['spO2low']})")
        elif spo2 >= self.alarm_values['spO2high']:
            alert_text.append(f"SpO₂ High ({spo2} > {self.alarm_values['spO2high']})")

        # NIBP - Systolic
        if 0 <= sys < 70:
            critical_alerts.append("CRITICAL: Systolic BP <70 mmHg!")
        elif 70 <= sys < self.alarm_values['sysLow']:
            alert_text.append(f"Warning: Systolic BP Low ({sys} < {self.alarm_values['sysLow']})")
        elif self.alarm_values['sysHigh'] < sys < 180:
            alert_text.append(f"Warning: Systolic BP High ({sys} > {self.alarm_values['sysHigh']})")
        elif sys >= 180:
            critical_alerts.append("CRITICAL: Systolic BP ≥180 mmHg!")

        # NIBP - Diastolic
        if 0 <= dias < 40:
            critical_alerts.append("CRITICAL: Diastolic BP <40 mmHg!")
        elif 70 <= dias < self.alarm_values['diasLow']:
            alert_text.append(f"Warning: Diastolic BP Low ({dias} < {self.alarm_values['diasLow']})")
        elif self.alarm_values['diasHigh'] < dias < 110:
            alert_text.append(f"Warning: Diastolic BP High ({dias} > {self.alarm_values['diasHigh']})")
        elif dias >= 110:
            critical_alerts.append("CRITICAL: Diastolic BP ≥110 mmHg!")

        # Temperature
        if 0 <= temp < 35.0:
            critical_alerts.append("CRITICAL: Temperature <35°C!")
        elif 35.0 <= temp < self.alarm_values['tempLow']:
            alert_text.append(f"Warning: Temperature Low ({temp} < {self.alarm_values['tempLow']})")
        elif self.alarm_values['tempHigh'] < temp < 40:
            alert_text.append(f"Warning: Temperature High ({temp} > {self.alarm_values['tempHigh']})")
        elif temp >= 40:
            critical_alerts.append("CRITICAL: Temperature >40°C!")

        # ETCO2
        if 0 <= co2 <= 30:
            critical_alerts.append("CRITICAL: ETCO₂ <30 mmHg!")
        elif 30 < co2 < self.alarm_values['etco2low']:
            alert_text.append(f"Warning: ETCO₂ Low ({co2} < {self.alarm_values['etco2low']})")
        elif self.alarm_values['etco2High'] < co2 <= 50:
            alert_text.append(f"Warning: ETCO₂ High ({co2} > {self.alarm_values['etco2High']})")
        elif co2 > 50:
            critical_alerts.append("CRITICAL: ETCO₂ >50 mmHg!")

        # Respiratory Rate
        if resp < 6:
            critical_alerts.append("CRITICAL: Respiratory Rate <6/min!")
        elif 6 <= resp < self.alarm_values['respLow']:
            alert_text.append(f"Respiratory Rate Low ({resp} < {self.alarm_values['respLow']})")
        elif self.alarm_values['respHigh'] < resp <= 30:
            alert_text.append(f"Respiratory Rate High ({resp} > {self.alarm_values['respHigh']})")
        elif resp > 30:
            critical_alerts.append("CRITICAL: Respiratory Rate >30/min!")

        # Update UI based on alerts
        if critical_alerts:
            # self.show_critical_warning("\n".join(critical_alerts))
            self.alert1.setText(", ".join(critical_alerts))
            self.alert1.setStyleSheet("color: black; font-weight: bold;")
            self.alert2.setStyleSheet("background-color: red; border: 0px; color: white;")
        elif alert_text:
            self.alert1.setText(", ".join(alert_text))
            self.alert1.setStyleSheet("color: orange; font-weight: bold;")
            self.alert2.setStyleSheet("background-color: yellow; border: 0px; color: black;")
        else:
            self.alert1.setText("Normal")
            self.alert1.setStyleSheet("color: black;")
            self.alert2.setStyleSheet("background-color: green; color: black;")

    def update_from_serial(self, data):
        """Update dari data serial"""
        try:
            print("[GUI] Received from serial:", data)  # Debug log

            self.last_serial_data = {  # GANTI dari last_mqtt_data ke last_serial_data
                'hr': float(data.get('hr', 0)),
                'spo2': float(data.get('spo2', 0)),
                'temp': float(data.get('temp', 0.0)),  # Gunakan default jika belum dikirim
                'etco2': float(data.get('etco2', 0))
            }

            self.update_sensor_values()
        except Exception as e:
            print(f"Error parsing serial data: {e}")


    def show_critical_warning(self, message):
            # Close previous alert if exists and is valid
            if hasattr(self, "current_alert_box") and self.current_alert_box is not None:
                try:
                    self.current_alert_box.close()
                except:
                    pass  # Skip if close fails
                finally:
                    self.current_alert_box = None  # Clean up

              # Create new alert
            self.current_alert_box = QMessageBox()
            self.current_alert_box.setIcon(QMessageBox.Critical)
            self.current_alert_box.setWindowTitle("CRITICAL ALARM")
            self.current_alert_box.setText(message)
            self.current_alert_box.setStandardButtons(QMessageBox.Ok)
            
            # Configure to be non-blocking
            self.current_alert_box.setModal(False)  # Allows interaction with other windows
            self.current_alert_box.show()
            
            # Force cleanup when dialog is closed
            self.current_alert_box.finished.connect(lambda: setattr(self, 'current_alert_box', None))


    def verify_password(self):
        """Verifikasi password sebelum membuka window tertentu"""
        password, ok = QtWidgets.QInputDialog.getText(
            self, 'Password Required', 'Enter your password:', 
            QtWidgets.QLineEdit.Password
        )
        
        if ok:
            # Cek password di users.json
            try:
                with open('users.json', 'r') as file:
                    users = json.load(file)
                    for user in users:
                        if user['password'] == password:
                            return True
            except FileNotFoundError:
                pass
                
            QtWidgets.QMessageBox.warning(self, 'Error', 'Wrong password!')
        return False


    def show_alarm_window(self):
        if self.verify_password():
            self.alarm_window = AlarmWindow()
            self.alarm_window.show()

    def show_patient_window(self):
        if self.verify_password():
            self.patient_window = PatientWindow()
            self.patient_window.show()


    def toggle_nibp(self):
        self.nibp_running = not self.nibp_running
        self.nibpButton.setText("Stop NIBP" if self.nibp_running else "Start NIBP")

    def show_table_trend(self):
        self.table_trend.show()

    def exit_to_login(self):
        # Stop semua timer yang aktif
        self.sensor_timer.stop()
        self.datetime_timer.stop()
        self.chart_timer.stop()
        
        # Hentikan koneksi MQTT jika ada
        if hasattr(self, 'serial_thread'):
            self.serial_thread.stop()

        
        # Reset data
        self.table_trend.clear_database()
        
        # Tutup window saat ini
        self.close()
        
        # Tampilkan login window
        self.login_window = LoginWindow()
        self.login_window.show()
        
        # Hapus referensi untuk membantu garbage collection
        del self

    def __del__(self):
        try:
            self.sensor_timer.stop()
            self.datetime_timer.stop()
            self.chart_timer.stop()
            if hasattr(self, 'serial_thread'):
                self.serial_thread.stop()

        except:
            pass

class AlarmWindow(QMainWindow):
    def __init__(self):
        super(AlarmWindow, self).__init__()
        try:
            uic.loadUi('alarm.ui', self)
            self.load_alarm_values()
  
            # Connect the OK button to save values
            self.buttonBox.accepted.connect(self.on_accept)
        except Exception as e:
            print("Error loading alarm UI:", e)

    def on_accept(self):
        self.save_alarm_values()
        
        # Jika MainWindow sedang aktif, reload alarm values
        if hasattr(self, 'main_window_ref'):  # Anda bisa pass reference dari MainWindow
            self.main_window_ref.load_alarm_values()
        
        self.close()

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
                self.respHigh.setValue(values['respHigh'])
                self.respLow.setValue(values['respLow'])
                # Set alarm status (ON/OFF)
                self.alarmInput.setCurrentText(values.get('alarm_status', 'ON'))
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
            'respLow': self.respLow.value(),
            'respHigh': self.respHigh.value(),
            'alarm_status': self.alarmInput.currentText()
        }
        with open('alarm_values.json', 'w') as file:
            json.dump(values, file)
            file.flush()
            os.fsync(file.fileno())  # Pakai ini biar bener-bener ke-save ke disk sebelum close

class PatientWindow(QMainWindow):
    def __init__(self):
        super(PatientWindow, self).__init__()
        uic.loadUi('patient.ui', self)
        self.buttonBox.accepted.connect(self.on_accept)
        self.load_data()

    def on_accept(self):
        self.save_data()
        self.close()

    def save_data(self):
        """Save patient data to file"""
        patient_data = {
            'nama': self.nameInput.text(),
            'nrm': self.nrmInput.text(),
            'tanggal_lahir': self.birthDateInput.date().toString("yyyy-MM-dd"),
            'umur': self.ageInput.value(),
            'gender': self.genderInput.currentText(),
            'nomor_kamar': self.roomInput.text(),
            'dokter': self.doctorInput.text(),
            'diagnosis': self.diagnosisInput.text(),
            'alergi': self.allergyInput.text(),
            'tanggal_masuk': self.admitDateInput.date().toString("yyyy-MM-dd")
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
                self.birthDateInput.setDate(
                    QDate.fromString(patient_data.get('tanggal_lahir', '2000-01-01'), "yyyy-MM-dd")
                )
                self.ageInput.setValue(patient_data.get('umur', 0))

                gender = patient_data.get('gender', 'Laki-laki')
                index = self.genderInput.findText(gender)
                if index >= 0:
                    self.genderInput.setCurrentIndex(index)

                self.roomInput.setText(patient_data.get('nomor_kamar', ''))
                self.doctorInput.setText(patient_data.get('dokter', ''))
                self.diagnosisInput.setText(patient_data.get('diagnosis', ''))
                self.allergyInput.setText(patient_data.get('alergi', ''))

                self.admitDateInput.setDate(
                    QDate.fromString(patient_data.get('tanggal_masuk', '2000-01-01'), "yyyy-MM-dd")
                )
        except FileNotFoundError:
            pass

class TableTrendWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_db()
        self.load_alarm_values()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # ComboBox untuk memilih rentang waktu
        self.time_range_combo = QComboBox()
        self.time_range_combo.addItems(['1 jam', '6 jam', '12 jam'])
        self.time_range_combo.currentIndexChanged.connect(self.update_table)
        layout.addWidget(self.time_range_combo)

        # Buat tabel
        self.table = QTableWidget()
        layout.addWidget(self.table)

        # Set kolom sesuai vital signs dari GUI utama
        headers = ['Waktu', 'ECG (BPM)', 'SpO2', 'NIBP', 'RESP', 'Temp', 'EtCO2', 'Condition']
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)

        # Atur lebar kolom
        header = self.table.horizontalHeader()
        for i in range(len(headers)):
            header.setSectionResizeMode(i, QHeaderView.Stretch)

        # Update tabel setiap 1 detik
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_table)
        self.timer.start(1000)

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.close)
        layout.addWidget(self.ok_button)

        # Tombol Save As
        self.save_button = QPushButton("Save As CSV")
        self.save_button.clicked.connect(self.save_as_csv)
        layout.addWidget(self.save_button)


    def setup_db(self):
        conn = sqlite3.connect('patient_data.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vital_signs (
                timestamp TEXT,
                ecg INTEGER,
                spo2 INTEGER,
                nibp TEXT,
                resp INTEGER,
                temp REAL,
                co2 INTEGER
            )
        ''')
        conn.commit()
        conn.close()

    def load_alarm_values(self):
        """Load alarm threshold values from file"""
        try:
            with open('alarm_values.json', 'r') as file:
                self.alarm_values = json.load(file)
        except FileNotFoundError:
            self.alarm_values = {
                'HRlow': 60, 'HRhigh': 100,
                'diasLow': 40, 'diasHigh': 100,
                'sysLow': 60, 'sysHigh': 190,
                'etco2low': 35, 'etco2High': 47,
                'spO2low': 90, 'spO2high': 100,
                'tempLow': 36.0, 'tempHigh': 37.5,
                'respLow': 12, 'respHigh': 20,
                'alarm_status': 'ON'  # Default to ON
            }

    def get_condition(self, ecg, spo2, nibp, resp, temp, co2):
        """Determine condition based on thresholds"""
        conditions = []
        
        # Parse NIBP if available (format: "120/80")
        sys, dias = (0, 0)  # Default values if parsing fails
        if nibp and isinstance(nibp, str) and "/" in nibp:
            try:
                sys, dias = map(int, nibp.split("/"))
            except (ValueError, AttributeError):
                pass
        
        # Check if alarms are enabled
        if self.alarm_values.get('alarm_status', 'ON') == 'OFF':
            return "Alarm OFF"
        
        # Heart Rate conditions
        if 0 <= ecg < 40:
            conditions.append("Critical Low HR")
        elif 40 <= ecg < self.alarm_values['HRlow']:
            conditions.append("Low HR")
        elif self.alarm_values['HRhigh'] < ecg <= 140:
            conditions.append("High HR")
        elif ecg > 140:
            conditions.append("Critical High HR")
        
        # SpO2 conditions
        if 0 <= spo2 <= 90:
            conditions.append("Critical Low SpO2")
        elif 90 < spo2 < self.alarm_values['spO2low']:
            conditions.append("Low SpO2")
        elif spo2 >= self.alarm_values['spO2high']:
            conditions.append("High SpO2")
        
        # NIBP (Systolic) conditions
        if 0 <= sys < 70:
            conditions.append("Critical Low NIBP")
        elif 70 <= sys < self.alarm_values['sysLow']:
            conditions.append("Low NIBP")
        elif self.alarm_values['sysHigh'] < sys < 180:
            conditions.append("High NIBP")
        elif sys >= 180:
            conditions.append("Critical High NIBP")
        
        # Temperature conditions
        if 0 <= temp < 35.0:
            conditions.append("Critical Low Temp")
        elif 35.0 <= temp < self.alarm_values['tempLow']:
            conditions.append("Low Temp")
        elif self.alarm_values['tempHigh'] < temp < 40:
            conditions.append("High Temp")
        elif temp >= 40:
            conditions.append("Critical High Temp")
        
        # ETCO2 conditions
        if 0 <= co2 <= 30:
            conditions.append("Critical Low CO2")
        elif 30 < co2 < self.alarm_values['etco2low']:
            conditions.append("Low CO2")
        elif self.alarm_values['etco2High'] < co2 <= 50:
            conditions.append("High CO2")
        elif co2 > 50:
            conditions.append("Critical High CO2")
        
        # Respiratory Rate conditions
        if resp < 6:
            conditions.append("Critical Low Resp")
        elif 6 <= resp < self.alarm_values['respLow']:
            conditions.append("Low Resp")
        elif self.alarm_values['respHigh'] < resp <= 30:
            conditions.append("High Resp")
        elif resp > 30:
            conditions.append("Critical High Resp")
        
        return ", ".join(conditions) if conditions else "Normal"

    def update_table(self):
        """Update isi tabel dengan data dari database"""
        try:
            # Buka koneksi database
            conn = sqlite3.connect('patient_data.db')
            cursor = conn.cursor()

            # Ambil waktu login terakhir
            login_time = get_login_time()  # Ganti dengan fungsi baru

            # Ambil pilihan waktu dari ComboBox
            selected_text = self.time_range_combo.currentText()
            if selected_text == '1 jam':
                cutoff = datetime.now() - timedelta(hours=1)
            elif selected_text == '6 jam':
                cutoff = datetime.now() - timedelta(hours=6)
            else:  # Default 12 jam
                cutoff = datetime.now() - timedelta(hours=12)

            # Gunakan waktu yang lebih baru antara login_time dan cutoff
            cutoff_str = max(
                datetime.strptime(login_time, '%Y-%m-%d %H:%M:%S'),
                cutoff
            ).strftime('%Y-%m-%d %H:%M:%S')

            # Eksekusi query
            cursor.execute('''
                SELECT * FROM vital_signs 
                WHERE timestamp > ? 
                ORDER BY timestamp DESC
            ''', (cutoff_str,))
            data = cursor.fetchall()

            # Update tabel
            self.table.setRowCount(len(data))
            for row, record in enumerate(data):
                for col, value in enumerate(record):
                    self.table.setItem(row, col, QTableWidgetItem(str(value)))

                # Tentukan kondisi
                condition = self.get_condition(record[1], record[2], record[3], 
                                            record[4], record[5], record[6])
                self.table.setItem(row, len(record), QTableWidgetItem(condition))

        except Exception as e:
            print(f"Error updating table: {e}")
        finally:
            # Pastikan koneksi ditutup
            if 'conn' in locals():
                conn.close()

    def store_current_values(self, ecg, spo2, nibp, resp, temp, co2):
        """Menyimpan data vital signs ke dalam database dengan pengecekan timestamp"""
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Cek apakah data dengan timestamp yang sama sudah ada
        conn = sqlite3.connect('patient_data.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM vital_signs 
            WHERE timestamp = ?
        ''', (current_time,))
        
        count = cursor.fetchone()[0]
        
        # Jika belum ada data dengan timestamp ini, simpan
        if count == 0:
            cursor.execute('''
                INSERT INTO vital_signs (timestamp, ecg, spo2, nibp, resp, temp, co2)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (current_time, ecg, spo2, nibp, resp, temp, co2))
            conn.commit()
        
        conn.close()

    def save_as_csv(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Save As", "", "CSV Files (*.csv)", options=options)
        
        if file_name:
            # Ambil data pasien
            try:
                with open('patient_data.json', 'r') as file:
                    patient_data = json.load(file)
                    patient_name = patient_data.get('nama', 'N/A')
                    patient_id = patient_data.get('nrm', 'N/A')
            except Exception as e:
                print(f"Error loading patient data: {e}")
                patient_name = 'N/A'
                patient_id = 'N/A'

            login_time = get_login_time()
            
            # Tentukan cutoff time berdasarkan ComboBox (sama seperti di update_table)
            selected_text = self.time_range_combo.currentText()
            if selected_text == '1 jam':
                cutoff = datetime.now() - timedelta(hours=1)
            elif selected_text == '6 jam':
                cutoff = datetime.now() - timedelta(hours=6)
            else:  # Default 12 jam
                cutoff = datetime.now() - timedelta(hours=12)

            # Gunakan waktu yang lebih baru antara login_time dan cutoff
            cutoff_str = max(
                datetime.strptime(login_time, '%Y-%m-%d %H:%M:%S'),
                cutoff
            ).strftime('%Y-%m-%d %H:%M:%S')

            # Query data dengan filter waktu
            conn = sqlite3.connect('patient_data.db')
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM vital_signs 
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
            ''', (cutoff_str,))
            
            data = cursor.fetchall()
            conn.close()

            # Tulis ke CSV
            with open(file_name, 'w', newline='') as file:
                writer = csv.writer(file, delimiter=';')
                writer.writerow(['Nama Pasien:', patient_name])
                writer.writerow(['NRM:', patient_id])
                writer.writerow(['Waktu Login:', login_time])
                writer.writerow(['Rentang Waktu:', selected_text])  # Tambahkan info rentang waktu
                writer.writerow([])
                writer.writerow(['Waktu', 'ECG', 'SpO2', 'NIBP', 'RESP', 'Temp', 'CO2', 'Status'])
                
                for row in data:
                    condition = self.get_condition(row[1], row[2], row[3], row[4], row[5], row[6])
                    writer.writerow([*row, condition])

        def showEvent(self, event):
            self.timer.start()
            super().showEvent(event)

        def hideEvent(self, event):
            self.timer.stop()
            super().hideEvent(event)

        def clear_table(self):
            """Clear all data from the trend table."""
            self.table.setRowCount(0)

    def clear_database(self):
            print("Resetting database...")  # Debug log
            conn = sqlite3.connect('patient_data.db')
            cursor = conn.cursor()
            cursor.execute('DELETE FROM vital_signs')  # Lebih aman daripada DROP TABLE
            conn.commit()
            conn.close()
            
# Main Application
def main():
    app = QApplication(sys.argv)
    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec_())

# Run the application
if __name__ == '__main__':
    main()
