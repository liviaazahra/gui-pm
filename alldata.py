import sys
import random
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QMainWindow, QDialog
from PyQt5.QtCore import QTimer, QTime, QDate


class AlarmDialog(QDialog):
    def __init__(self):
        super(AlarmDialog, self).__init__()
        try:
            uic.loadUi('alarm.ui', self)
            # Set initial values for QSpinBox and QDoubleSpinBox
            self.HRlow.setValue(60)
            self.HRhigh.setValue(100)
            self.HRhigh.setMaximum(100)
            self.diasLow.setValue(40)
            self.diasHigh.setMaximum(100)
            self.sysLow.setValue(60)
            self.sysHigh.setValue(190)
            self.sysHigh.setMaximum(190)
            self.etco2low.setValue(35)
            self.etco2High.setValue(47)
            self.spO2low.setValue(90)
            self.spO2high.setValue(100)
            self.tempLow.setValue(36.0)
            self.tempHigh.setValue(37.5)
        except Exception as e:
            print("Error loading alarm UI:", e)

class PatientDialog(QDialog):
    def __init__(self):
        super(PatientDialog, self).__init__()
        uic.loadUi('patient.ui', self)

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        
        # Load UI
        uic.loadUi('alldata.ui', self)
        
        # Setup timer untuk update waktu dan tanggal
        self.datetime_timer = QTimer()
        self.datetime_timer.timeout.connect(self.update_datetime)
        self.datetime_timer.start(1000)  # Update setiap 1 detik
        
        # Setup timer untuk simulasi sensor
        self.sensor_timer = QTimer()
        self.sensor_timer.timeout.connect(self.update_sensor_values)
        self.sensor_timer.start(1000)  # Update setiap 1 detik
        
        # Setup tombol menu
        self.alarmButton.clicked.connect(self.show_alarm_dialog)
        self.exitButton.clicked.connect(self.close)
        self.patientButton.clicked.connect(self.show_patient_dialog)
        self.nibpButton.clicked.connect(self.toggle_nibp)
        
        # Inisialisasi status NIBP
        self.nibp_running = False
        
        # Update datetime pertama kali
        self.update_datetime()
        
        # Set mode ke OFF
        self.set_modes_off()
        
        self.show()
    
    def update_datetime(self):
        """Update tanggal dan waktu real-time"""
        current_time = QTime.currentTime()
        current_date = QDate.currentDate()
        
        self.date.setText(current_date.toString('dd/MM/yyyy'))
        self.time.setText(current_time.toString('HH:mm'))
    
    def update_sensor_values(self):
        """Update nilai-nilai sensor dengan simulasi random"""
        # ECG (BPM: 60-100)
        self.ecgInput.setText(str(random.randint(60, 100)))
        
        # NIBP (Systolic: 90-140, Diastolic: 60-90)
        sys = random.randint(90, 140)
        dias = random.randint(60, 90)
        self.nibpInput.setText(f"{sys}/{dias}")
        
        # NIBP Volume (80-120)
        self.nibpvolInput.setText(str(random.randint(80, 120)))
        
        # SpO2 (95-100%)
        self.spo2Input.setText(str(random.randint(95, 100)))
        
        # CO2 related
        self.awrrInput.setText(str(random.randint(12, 20)))  # breaths per minute
        self.insInput.setText(str(random.randint(15, 25)))   # inspiratory flow
        self.co2Input.setText(str(random.randint(35, 45)))   # ETCO2
        
        # Respiratory rate (12-20 breaths per minute)
        self.respInput.setText(str(random.randint(12, 20)))
        
        # Temperature (36.5-37.5°C)
        temp = round(random.uniform(36.5, 37.5), 1)
        self.tempInput.setText(f"{temp}")
    
    def set_modes_off(self):
        """Set semua mode ke OFF"""
        self.pvcsmode.setText("OFF")
        self.st1mode.setText("OFF")
        self.st2mode.setText("OFF")
    
    def show_alarm_dialog(self):
        """Menampilkan dialog alarm"""
        dialog = AlarmDialog()
        dialog.exec_()
    
    def show_patient_dialog(self):
        """Menampilkan dialog patient info"""
        dialog = PatientDialog()
        dialog.exec_()
    
    def toggle_nibp(self):
        """Toggle status NIBP start/stop"""
        self.nibp_running = not self.nibp_running
        if self.nibp_running:
            self.nibpButton.setText("Stop NIBP")
        else:
            self.nibpButton.setText("Start NIBP")

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()