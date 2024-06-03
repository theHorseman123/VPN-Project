from PyQt5.QtWidgets import *
from PyQt5.QtGui import QFont

def main():
    app = QApplication([])
    window = QWidget()
    window.setGeometry(100, 100, 200, 300)
    window.setWindowTitle("VPN client")


    label = QLabel(window)
    label.setText("hello")
    label.setFont(QFont("Arial", 16))

    window.show()
    app.exec_()

if __name__ == "__main__":
    main()