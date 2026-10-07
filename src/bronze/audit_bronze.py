import duckdb
import os

def auditar_todas_las_tablas():
    db_path = os.path.join("database", "instacart_dwh.duckdb")
    
    if not os.path.exists(db_path):
        print(" La base de datos no existe. Ejecuta primero 'ingest_bronze.py'.")
        return

    con = duckdb.connect(db_path)

 
    # 1. VOLUMETRÍA GENERAL
    print("1️VOLUMETRÍA TOTAL DE TABLAS")
    print("-" * 50)
    tablas = con.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'bronze'").fetchall()
    
    for t in tablas:
        tabla = t[0]
        total = con.execute(f"SELECT COUNT(*) FROM bronze.{tabla}").fetchone()[0]
        print(f" • bronze.{tabla:<22}: {total:>12,} registros")

    # 2. DIAGNÓSTICO DE VALORES NULOS EN TABLAS CLAVE
    print("\n2️ DIAGNÓSTICO DE VALORES NULOS (NULLS)")
    print("-" * 50)
    
    # Nulos en orders
    nulls_orders = con.execute("""
        SELECT 
            COUNT(*) - COUNT(order_id) AS nulos_order_id,
            COUNT(*) - COUNT(user_id) AS nulos_user_id,
            COUNT(*) - COUNT(days_since_prior_order) AS nulos_days_since_prior
        FROM bronze.orders
    """).df()
    print(" Tabla 'bronze.orders':")
    print(nulls_orders.to_string(index=False))

    # Nulos en order_products (prior)
    nulls_op = con.execute("""
        SELECT 
            COUNT(*) - COUNT(order_id) AS nulos_order_id,
            COUNT(*) - COUNT(product_id) AS nulos_product_id,
            COUNT(*) - COUNT(add_to_cart_order) AS nulos_add_to_cart
        FROM bronze.order_products__prior
    """).df()
    print("\n Tabla 'bronze.order_products__prior':")
    print(nulls_op.to_string(index=False))

    # 3. VERIFICACIÓN DE CLAVES DUPLICADAS
    print("\n3️ PRUEBA DE DUPLICADOS EN CLAVES PRIMARIAS")
    print("-" * 50)
    
    dup_orders = con.execute("""
        SELECT order_id, COUNT(*) as repeticiones 
        FROM bronze.orders 
        GROUP BY order_id 
        HAVING COUNT(*) > 1
    """).fetchall()
    
    print(f" • Duplicados en bronze.orders (order_id): {len(dup_orders)}")

    dup_products = con.execute("""
        SELECT product_id, COUNT(*) as repeticiones 
        FROM bronze.products 
        GROUP BY product_id 
        HAVING COUNT(*) > 1
    """).fetchall()
    
    print(f" • Duplicados en bronze.products (product_id): {len(dup_products)}")

    # 4. VERIFICACIÓN DE METADATOS
    print("\n4️  VERIFICACIÓN DE TRAZABILIDAD (METADATOS)")
    print("-" * 50)
    sample = con.execute("SELECT order_id, _ingestion_timestamp, _source_file FROM bronze.orders LIMIT 1").df()
    print(sample.to_string(index=False))

    con.close()


if __name__ == "__main__":
    auditar_todas_las_tablas()