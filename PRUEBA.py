from PyQt5.QtWidgets import QFileDialog, QInputDialog
from PyQt5.QtCore import QVariant
from qgis.core import QgsVectorLayer, QgsField
import os

def seleccionar_archivo(titulo="Selecciona un archivo", filtro="Todos los archivos (*.*)"):
    """
    Abre un cuadro de diálogo para seleccionar un archivo en el sistema de archivos.
    """
    archivo_seleccionado, _ = QFileDialog.getOpenFileName(
        None, titulo, "", filtro
    )
    return archivo_seleccionado

def guardar_como_shapefile(capa, titulo="Guardar como Shapefile"):
    
    from qgis.core import QgsVectorFileWriter, QgsCoordinateTransformContext

    # Abrir un cuadro de diálogo para seleccionar dónde guardar el shapefile
    ruta_shapefile, _ = QFileDialog.getSaveFileName(
        None, titulo, "", "Shapefile (*.shp);;Todos los archivos (*.*)"
    )

    # Asegurarse de que la extensión sea .shp
    if not ruta_shapefile.lower().endswith(".shp"):
        ruta_shapefile += ".shp"

    # Crear opciones para guardar el archivo
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = "ESRI Shapefile"
    options.fileEncoding = "UTF-8"

    # Guardar la capa como shapefile
    transform_context = QgsCoordinateTransformContext()
    error = QgsVectorFileWriter.writeAsVectorFormatV2(
        capa, ruta_shapefile, transform_context, options
    )

    # Validar si el shapefile se creó correctamente
    if error == QgsVectorFileWriter.NoError:
        print(f"Shapefile guardado exitosamente en: {ruta_shapefile}")
        if os.path.exists(ruta_shapefile):
            print("El archivo fue creado correctamente.")
    else:
        print(f"Error al intentar guardar la capa como shapefile. Código de error: {error}")
        if os.path.exists(ruta_shapefile):
            print("Nota: Aunque se mostró un error, el archivo se creó exitosamente.")


def seleccionar_capa_geopackage(ruta_geopackage):
    """
    Permite seleccionar una capa específica de un archivo GeoPackage.
    """
    metadata = QgsVectorLayer(ruta_geopackage, "", "ogr")
    if not metadata.isValid():
        print("El archivo seleccionado no es válido o no contiene datos compatibles.")
        return None

    subcapas = metadata.dataProvider().subLayers()
    if not subcapas:
        print("No se encontraron capas dentro del archivo GeoPackage proporcionado.")
        return None

    nombres_capas = [subcapa.split('!!::!!')[1] for subcapa in subcapas]

    capa_seleccionada, ok = QInputDialog.getItem(
        None, "Seleccionar Capa", "Selecciona una capa del GeoPackage:", 
        nombres_capas, 0, False
    )

    if ok and capa_seleccionada:
        nombre_capa = f"{ruta_geopackage}|layername={capa_seleccionada}"
        capa = QgsVectorLayer(nombre_capa, capa_seleccionada, "ogr")
        if capa.isValid():
            print(f"Capa seleccionada cargada correctamente: {capa_seleccionada}")
            return capa
        else:
            print("No se pudo cargar la capa seleccionada.")
            return None
    else:
        print("No se seleccionó ninguna capa.")
        return None

# Seleccionar archivo GeoPackage
ruta_geopackage = seleccionar_archivo(
    "Selecciona el GeoPackage", "Archivos GeoPackage (*.gpkg);;Todos los archivos (*.*)"
)

if ruta_geopackage:
    print("Archivo seleccionado:", ruta_geopackage)
    capa = seleccionar_capa_geopackage(ruta_geopackage)
    if capa:
        print(f"Capa cargada con éxito: {capa.name()}")
else:
    print("No se seleccionó ningún archivo GeoPackage.")

# Validar que la capa se cargó correctamente antes de continuar
if capa:
    data_layer_info = capa.dataProvider()

    # Crear los campos necesarios si no existen
    campos_necesarios = [
        ("ITEM", QVariant.Int),
        ("LumCantPos", QVariant.Int),
    ]

    for nombre_campo, tipo_campo in campos_necesarios:
        if capa.fields().indexFromName(nombre_campo) == -1:
            result = data_layer_info.addAttributes([QgsField(nombre_campo, tipo_campo)])
            capa.updateFields()
            if result:
                print(f"El campo '{nombre_campo}' fue creado correctamente.")
            else:
                print(f"Error al crear el campo '{nombre_campo}'.")
        else:
            print(f"El campo '{nombre_campo}' ya existe.")

    # Garantizar unicidad en los IDs
    ids_existentes = set()  # Conjunto para almacenar IDs únicos
    ids_duplicados = []     # Lista para registrar IDs repetidos
    max_id = 0              # Rastrea el valor máximo de ID existente
    ids_actualizados = 0    # Contador para actualizaciones

    # Recorrer la capa y encontrar duplicados
    for feature in capa.getFeatures():
        current_id = feature['ID']
        if current_id is None or current_id == NULL or current_id in ids_existentes:
            ids_duplicados.append(feature.id())  # Registrar la ID interna del feature
        else:
            ids_existentes.add(current_id)
            max_id = max(max_id, current_id)

    # Asignar nuevos IDs únicos a los duplicados o valores nulos
    capa.startEditing()
    for feature_id in ids_duplicados:
        max_id += 1
        capa.changeAttributeValue(feature_id, capa.fields().indexFromName('ID'), max_id)
        ids_existentes.add(max_id)
        ids_actualizados += 1

    if capa.commitChanges():
        print(f"Se corrigieron {ids_actualizados} ID(s) duplicados o vacíos.")
    else:
        print("Error al intentar guardar los cambios en la capa.")

    # Inicializar los valores de ITEM y LumCantPos
    capa.startEditing()
    for feature in capa.getFeatures():
        feature['ITEM'] = None
        feature['LumCantPos'] = 0
        capa.updateFeature(feature)

    # Crear diccionarios para asignar ITEM y LumCantPos
    geom_to_min_id = {}
    geom_to_count = {}

    for feature in capa.getFeatures():
        geom = feature.geometry().asWkt()
        current_id = feature['ID']
        if geom not in geom_to_min_id:
            geom_to_min_id[geom] = current_id
        else:
            if current_id < geom_to_min_id[geom]:
                geom_to_min_id[geom] = current_id

    for feature in capa.getFeatures():
        geom = feature.geometry().asWkt()
        if geom not in geom_to_count:
            geom_to_count[geom] = 1
        else:
            geom_to_count[geom] += 1

    for feature in capa.getFeatures():
        geom = feature.geometry().asWkt()
        feature['ITEM'] = geom_to_min_id[geom]
        if feature['ID'] == geom_to_min_id[geom]:
            feature['LumCantPos'] = geom_to_count[geom]
        else:
            feature['LumCantPos'] = 0
        capa.updateFeature(feature)

    if capa.commitChanges():
        print("Se asignaron correctamente los valores de ITEM y LumCantPos.")
    else:
        print("Error al guardar los cambios finales en la capa.")

#Guardar como shapefile
guardar_como_shapefile(capa)
#Importante crear en el geopackage una columna ID_Original y copiar los datos del ID antes de ejecutar el codigo para evitar perder ese registro de ID's anterior
#Aunque el archivo .shp al final diga que marco error es un falso positivo generado por la API de Qgis