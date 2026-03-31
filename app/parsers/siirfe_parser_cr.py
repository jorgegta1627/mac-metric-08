import pandas as pd


def parse_siirfe_cr_file(file_path):
    try:
        print("Leyendo archivo CR...")

        header_df = pd.read_excel(
            file_path,
            header=None,
            skiprows=15,
            nrows=2
        )

        columns = []
        for col1, col2 in zip(header_df.iloc[0], header_df.iloc[1]):
            if pd.notna(col1) and pd.notna(col2):
                columns.append(f"{str(col1).strip()}_{str(col2).strip()}")
            elif pd.notna(col1):
                columns.append(str(col1).strip())
            elif pd.notna(col2):
                columns.append(str(col2).strip())
            else:
                columns.append("col_sin_nombre")

        df = pd.read_excel(
            file_path,
            header=None,
            skiprows=17
        )

        df.columns = columns
        df = df.dropna(axis=1, how="all")
        df = df.dropna(how="all").reset_index(drop=True)

        return {
            "success": True,
            "data": df
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }