# archivo: conexionBD.py
import MySQLdb
from MySQLdb import Error

# Función para conectarse a la base de datos MySQL
def dbconexion():
    try:
        # Configuración de la base de datos
        conexion = MySQLdb.connect(
            host='localhost',       
            user='root',      
            password='12345678',  
            db='stock',
            port= 3309,
            charset='utf8mb4',       
        )
        return conexion
    except Error as e:
        print(f"Error en la conexión a la base de datos: {e}")
        return None

if __name__ == "__main__":
    conexion = dbconexion()
    if conexion:
        print("Conexión exitosa a la base de datos")
        conexion.close()

   
