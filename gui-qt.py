from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget
from PyQt5.QtCore import pyqtSlot

class BlankTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Layout and content for your blank tab can be added here
        # For example, you can add labels, buttons, text boxes, etc.

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("3 Blank Tabs")

        # Create tab widget
        self.tab_widget = QTabWidget()

        # Create 3 blank tabs
        for i in range(3):
            tab = BlankTab()
            self.tab_widget.addTab(tab, f"Tab {i+1}")

        # Set central widget
        self.setCentralWidget(self.tab_widget)

        # Show the window
        self.show()

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    app.exec_()
