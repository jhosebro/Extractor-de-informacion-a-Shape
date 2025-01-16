from PyQt5.QtWidgets import QFileDialog, QInputDialog
from qgis.core import QgsVectorLayer

def seleccionar_archivo(titulo="Selecciona un archivo", filtro="Todos los archivos (*.*)"):
    """
    Abre un cuadro de diálogo para seleccionar un archivo.
    """
    archivo_seleccionado, _ = QFileDialog.getOpenFileName(
        None,  # Ventana principal
        titulo,  # Título del diálogo
        "",  # Directorio inicial
        filtro  # Filtro de archivos
    )
    return archivo_seleccionado

def seleccionar_capa_geopackage(ruta_geopackage):
    """
    Permite seleccionar una capa de un archivo GeoPackage.

    :param ruta_geopackage: Ruta al archivo GeoPackage.
    :return: La capa seleccionada por el usuario o None si no se selecciona ninguna.
    """
    # Crear una capa temporal para obtener metadatos de las subcapas
    metadata = QgsVectorLayer(ruta_geopackage, "", "ogr")
    if not metadata.isValid():
        print("El archivo seleccionado no es válido.")
        return None

    # Obtener las subcapas disponibles
    subcapas = metadata.dataProvider().subLayers()
    if not subcapas:
        print("No se encontraron capas en el GeoPackage.")
        return None

    # Limpiar y extraer los nombres reales de las capas
    nombres_capas = [subcapa.split('!!::!!')[1] for subcapa in subcapas]
    print("Capas disponibles (limpias):", nombres_capas)  # Debugging

    # Mostrar un cuadro de diálogo para seleccionar la capa
    capa_seleccionada, ok = QInputDialog.getItem(
        None,  # Ventana principal
        "Seleccionar Capa",  # Título
        "Selecciona una capa del GeoPackage:",  # Etiqueta
        nombres_capas,  # Opciones
        0,  # Índice inicial
        False  # Editable
    )

    if ok and capa_seleccionada:
        # Construir el URI para cargar la capa seleccionada
        nombre_capa = f"{ruta_geopackage}|layername={capa_seleccionada}"
        print("Intentando cargar la capa con URI:", nombre_capa)  # Debugging

        # Cargar la capa seleccionada
        capa = QgsVectorLayer(nombre_capa, capa_seleccionada, "ogr")

        if capa.isValid():
            print(f"Capa seleccionada y cargada correctamente: {capa_seleccionada}")
            return capa
        else:
            print("No se pudo cargar la capa seleccionada.")
            return None
    else:
        print("No se seleccionó ninguna capa.")
        return None

# Seleccionar archivo GeoPackage
ruta_geopackage = seleccionar_archivo("Selecciona el GeoPackage", "Archivos GeoPackage (*.gpkg);;Todos los archivos (*.*)")

if ruta_geopackage:
    print("Archivo seleccionado:", ruta_geopackage)  # Debugging
    # Seleccionar capa dentro del GeoPackage
    capa = seleccionar_capa_geopackage(ruta_geopackage)
    if capa:
        print(f"Capa cargada: {capa.name()}")
else:
    print("No se seleccionó ningún archivo.")
