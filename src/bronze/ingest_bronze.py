import os
import glob
import time
import duckdb

def ingest_bronze():
    start_time = time.time()
    print("🚀 Iniciando la ingesta a la Capa Bronce en DuckDB...\n")

    # 1. Rutas de carpetas y base de datos
    raw_dir = "data/raw"
    db_path = "database/instacart_dwh.duckdb"

    # Verificar que exista la carpeta de datos crudos
    if not os.path.exists(raw_dir):
        print(f" Error: La carpeta '{raw_dir}' no existe. Asegúrate de colocar ahí tus archivos CSV.")
        return

    # 2. crear la base de datos DuckDB
    con = duckdb.connect(db_path)

    # 3. Crear el esquema 'bronze' 
    con.execute("CREATE SCHEMA IF NOT EXISTS bronze;")
    print(" Esquema 'bronze' verificado/creado correctamente.")

    # 4. Obtener la lista de todos los archivos .csv en data/raw/
    csv_files = glob.glob(os.path.join(raw_dir, "*.csv"))

    if not csv_files:
        print(f" No se encontraron archivos .csv en la carpeta '{raw_dir}'.")
        con.close()
        return

    print(f" Archivos a procesar: {len(csv_files)}\n")

    # 5. Iterar sobre cada CSV y cargarlo en DuckDB
    for csv_path in csv_files:
        # Obtener el nombre del archivo 
        csv_file_name = os.path.basename(csv_path)
        
        # Generar nombre de tabla limpio 
        table_name = os.path.splitext(csv_file_name)[0].lower()

        print(f"⏳ Cargando '{csv_file_name}' en 'bronze.{table_name}'...")
        
        # Consulta SQL: Carga masiva con adición de campos de auditoría/trazabilidad
        query = f"""
        CREATE OR REPLACE TABLE bronze.{table_name} AS 
        SELECT 
            *, 
            CURRENT_TIMESTAMP AS _ingestion_timestamp,
            '{csv_file_name}' AS _source_file
        FROM read_csv_auto('{csv_path.replace(os.sep, "/")}');
        """
        
        # Ejecutar la consulta
        t0 = time.time()
        con.execute(query)
        t1 = time.time()

        # Obtener el conteo de filas insertadas para verificación
        count = con.execute(f"SELECT COUNT(*) FROM bronze.{table_name};").fetchone()[0]
        print(f"    Carga finalizada: {count:,} filas insertadas en {t1 - t0:.2f} segundos.")

    # 6. Cerrar conexión
    con.close()
    
    total_time = time.time() - start_time
    print(f"\n Ingesta completada con éxito en la Capa Bronce en {total_time:.2f} segundos.")
    print(f" Base de datos guardada en: '{db_path}'")

if __name__ == "__main__":
    ingest_bronze()