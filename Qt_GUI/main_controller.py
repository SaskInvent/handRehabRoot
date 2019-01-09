from PyQt5 import QtWidgets
import main

class MainQtApp(main.Ui_MainWindow, QtWidgets.QMainWindow):
    def __init__(self):
        super(MainQtApp, self).__init__()

        self.setupUi(self)
        self.setWindowTitle("Hand Rehab Arduino")

        

if __name__ == '__main__':
    app = QtWidgets.QApplication()
    qt_app = MainQtApp()
    qt_app.show()
    app.exec_()
    app.quitOnLastWindowClosed()
