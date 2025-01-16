from PyQt5.QtWidgets import QFileDialog, QInputDialog
from PyQt5.QtCore import QVariant
from qgis.core import QgsVectorLayer, QgsField

def seleccionar_archivo(titulo="Selecciona un archivo", filtro="Todos los archivos (*.*)"):
    """
    Abre un cuadro de diálogo para seleccionar un archivo en el sistema de archivos.
    
    :param titulo: Título que se mostrará en el cuadro de diálogo.
    :param filtro: Filtro para los tipos de archivos visibles (por ejemplo, *.gpkg).
    :return: Ruta del archivo seleccionado o una cadena vacía si se cancela la selección.
    """
    archivo_seleccionado, _ = QFileDialog.getOpenFileName(
        None,  # Ventana principal del cuadro de diálogo
        titulo,  # Título que aparece en el cuadro
        "",  # Directorio inicial al abrir el cuadro
        filtro  # Tipos de archivos permitidos
    )
    return archivo_seleccionado

def seleccionar_capa_geopackage(ruta_geopackage):
    """
    Permite al usuario seleccionar una capa específica de un archivo GeoPackage.
    
    :param ruta_geopackage: Ruta completa al archivo GeoPackage (.gpkg).
    :return: Objeto QgsVectorLayer correspondiente a la capa seleccionada, o None si no se selecciona ninguna.
    """
    # Crear un vector temporal para extraer las subcapas del GeoPackage
    metadata = QgsVectorLayer(ruta_geopackage, "", "ogr")
    if not metadata.isValid():
        print("El archivo seleccionado no es válido o no contiene datos compatibles.")
        return None

    # Obtener las subcapas disponibles en el GeoPackage
    subcapas = metadata.dataProvider().subLayers()
    if not subcapas:
        print("No se encontraron capas dentro del archivo GeoPackage proporcionado.")
        return None

    # Extraer los nombres de las subcapas disponibles
    nombres_capas = [subcapa.split('!!::!!')[1] for subcapa in subcapas]
    print("Capas disponibles en el GeoPackage:", nombres_capas)  # Mensaje de depuración

    # Mostrar cuadro de diálogo para que el usuario seleccione una capa
    capa_seleccionada, ok = QInputDialog.getItem(
        None,  # Ventana principal para el cuadro de diálogo
        "Seleccionar Capa",  # Título del cuadro
        "Selecciona una capa del GeoPackage:",  # Etiqueta informativa
        nombres_capas,  # Opciones a mostrar
        0,  # Índice inicial seleccionado
        False  # No permitir entrada de texto personalizada
    )

    if ok and capa_seleccionada:
        # Construir el URI para cargar la capa seleccionada
        nombre_capa = f"{ruta_geopackage}|layername={capa_seleccionada}"
        print("Intentando cargar la capa con URI:", nombre_capa)  # Mensaje de depuración

        # Cargar la capa seleccionada
        capa = QgsVectorLayer(nombre_capa, capa_seleccionada, "ogr")

        if capa.isValid():
            print(f"Capa seleccionada cargada correctamente: {capa_seleccionada}")
            return capa
        else:
            print("No se pudo cargar la capa seleccionada. Verifique el archivo.")
            return None
    else:
        print("No se seleccionó ninguna capa en el cuadro de diálogo.")
        return None

# Seleccionar el archivo GeoPackage (.gpkg) desde el sistema de archivos
ruta_geopackage = seleccionar_archivo(
    "Selecciona el GeoPackage", "Archivos GeoPackage (*.gpkg);;Todos los archivos (*.*)"
)

if ruta_geopackage:
    print("Archivo seleccionado:", ruta_geopackage)  # Mensaje de depuración
    # Seleccionar una capa específica del GeoPackage
    capa = seleccionar_capa_geopackage(ruta_geopackage)
    if capa:
        print(f"Capa cargada con éxito: {capa.name()}")
else:
    print("No se seleccionó ningún archivo GeoPackage.")

# Validar que existe una capa seleccionada antes de continuar
if capa:
    # Obtener el proveedor de datos de la capa seleccionada
    data_layer_info = capa.dataProvider()

    # Lista de campos necesarios que se deben verificar/crear
    campos_necesarios = [
        ("ITEM", QVariant.Int),
        ("LumCantPos", QVariant.Int),
    ]

    for nombre_campo, tipo_campo in campos_necesarios:
        # Verificar si el campo existe en la capa
        if capa.fields().indexFromName(nombre_campo) == -1:
            # Si no existe, intentar crear el campo
            result = data_layer_info.addAttributes([QgsField(nombre_campo, tipo_campo)])
            capa.updateFields()  # Actualizar los campos de la capa

            # Confirmar si el campo se creó correctamente
            if result:
                print(f"El campo '{nombre_campo}' no existía y fue creado satisfactoriamente.")
            else:
                print(f"Error: El campo '{nombre_campo}' no existía, pero no se pudo crear.")
        else:
            print(f"El campo '{nombre_campo}' ya existe en la capa.")
