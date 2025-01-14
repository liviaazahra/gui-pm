from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QMessageBox
import sys

class LoginWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        # Load file UI
        uic.loadUi('login.ui', self)
        
        # Kredensial yang valid
        self.valid_username = "liviazahra"
        self.valid_password = "1234"
        
        # Menghubungkan tombol login dengan fungsi
        self.loginButton.clicked.connect(self.check_login)
        
        # Mengatur label error (awalnya kosong)
        self.label_5.setText("")
        
    def check_login(self):
        # Mengambil input username dan password
        username = self.usernameInput.text()
        password = self.passwordInput.text()
        
        # Memeriksa kredensial
        if username == self.valid_username and password == self.valid_password:
            self.label_5.setText("")  # Menghapus pesan error jika ada
            # TODO: Tambahkan kode untuk membuka alldata.ui di sini
            print("Login berhasil!")  # Sementara hanya print
            
            # Uncomment kode di bawah ini nanti setelah alldata.ui siap
            # self.open_alldata()
            
        else:
            # Menampilkan pesan error
            self.label_5.setText("Wrong Password!")
            self.label_5.setStyleSheet("color: red;")  # Optional: membuat text merah
            
    # Fungsi untuk membuka alldata.ui (akan diimplementasikan nanti)
    def open_alldata(self):
        pass
        # TODO: Implementasikan pembukaan alldata.ui di sini

# Menjalankan aplikasi
def main():
    app = QtWidgets.QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()