# generar_huella.py
import sys
from getmac import get_mac_address
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMessageBox


def mostrar_huella():
    """Obtiene la dirección MAC y la muestra en una ventana de mensaje."""
    try:
        # Obtener la dirección MAC de la interfaz activa (ethernet o wifi)
        mac = get_mac_address()
        if not mac:
            raise Exception("No se pudo obtener una dirección MAC. Verifique la conexión de red.")

        # Crear una ventana de mensaje simple para mostrar la huella
        app = QApplication.instance() or QApplication(sys.argv)
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Huella Digital del Equipo")
        msg_box.setText(
            f"Por favor, envíe el siguiente código al proveedor del software para generar la licencia de la aplicación."
            f"\nSin una licencia válida la aplicación no podrá ejecutarse:\n\n{mac}")
        msg_box.setTextInteractionFlags(Qt.TextSelectableByMouse)  # Permitir copiar el texto
        msg_box.setIcon(QMessageBox.Information)
        msg_box.exec()

    except Exception as e:
        # Manejar errores si no se puede obtener la MAC
        app = QApplication.instance() or QApplication(sys.argv)
        QMessageBox.critical(None, "Error", f"No se pudo generar la huella del equipo:\n{e}")


if __name__ == "__main__":
    mostrar_huella()
