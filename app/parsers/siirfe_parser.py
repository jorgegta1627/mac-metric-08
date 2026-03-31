import pandas as pd


def parse_siirfe_file(file_path):
    try:
        print("Leyendo archivo...")

        # Leer encabezados (filas 21 y 22)
        header_df = pd.read_excel(
            file_path,
            header=None,
            skiprows=20,
            nrows=2
        )

        print("Encabezados leídos")

        # Construir nombres de columnas
        columns = []
        for col1, col2 in zip(header_df.iloc[0], header_df.iloc[1]):
            if pd.notna(col1) and pd.notna(col2):
                columns.append(f"{col1}_{col2}")
            elif pd.notna(col1):
                columns.append(str(col1))
            elif pd.notna(col2):
                columns.append(str(col2))
            else:
                columns.append("col_sin_nombre")

        # Leer datos desde fila 23
        df = pd.read_excel(
            file_path,
            header=None,
            skiprows=22
        )

        # Asignar columnas
        df.columns = columns

        # Eliminar columnas vacías
        df = df.dropna(axis=1, how='all')

        print("Datos procesados")

        return {
            "success": True,
            "data": df
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }