import os


def detectar_mac(nombre_archivo):
    if "090852" in nombre_archivo:
        return "090852"
    elif "090853" in nombre_archivo:
        return "090853"
    else:
        return "DESCONOCIDO"


def detectar_tipo(nombre_archivo):
    nombre = nombre_archivo.upper()

    if "TIEMATEN_SOL" in nombre or "_SOL_" in nombre:
        return "TIEMPOS_SOL"
    elif "TIEMATEN_CR" in nombre or "_CR_" in nombre:
        return "TIEMPOS_CR"
    elif "TIEM" in nombre or "ATEN" in nombre:
        return "TIEMPOS"
    elif "TRAM" in nombre:
        return "TRAMITES"
    elif "INVE" in nombre:
        return "INVENTARIO"
    else:
        return "OTRO"


def clasificar_archivos(ruta_carpeta):
    resultados = []

    for archivo in os.listdir(ruta_carpeta):
        if archivo.endswith(".xls") or archivo.endswith(".xlsx"):

            mac = detectar_mac(archivo)
            tipo = detectar_tipo(archivo)

            resultados.append({
                "archivo": archivo,
                "mac": mac,
                "tipo": tipo
            })

    return resultados