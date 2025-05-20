import sys
from PyQt5.QtWidgets import QApplication
from simulator.ui import TradeSimulatorUI

def main():
    app = QApplication(sys.argv)
    window = TradeSimulatorUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 