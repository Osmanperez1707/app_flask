from flask import Flask, render_template, redirect, request, session, url_for,flash, jsonify, abort
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user,current_user
from flask import request, redirect, url_for, flash
from flask_mysqldb import MySQL
import conexionbd as db
import MySQLdb.cursors 


app = Flask(__name__, template_folder='templates')

# Configuración de Flask-Login
app.secret_key = 'emily_pe'
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
mysql = MySQL(app)# Nombre de la ruta para la vista de login

# Modelo de usuario 
class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    conexion = db.dbconexion()
    if conexion:
        try:
            # Crear cursor como DictCursor
            cur = conexion.cursor(MySQLdb.cursors.DictCursor)
            cur.execute("USE stock")
            cur.execute("SELECT * FROM usuarios WHERE id_usuario = %s", (user_id,))
            account = cur.fetchone()
            
            # Si el usuario es encontrado, devolver el objeto User
            if account:
                return User(account['id_usuario'])
            else:
                return None  # Si el usuario no existe, devolver None

        finally:
            # Asegurarse de cerrar cursor y conexión
            cur.close()
            conexion.close()
    
    # Si la conexión falla, devolver None
    return None

@app.route('/')
def home():
    conexion = db.dbconexion()  # Conexión a la base de datos
    cur = conexion.cursor(MySQLdb.cursors.DictCursor)  # Usar la conexión para crear el cursor
    cur.execute("SELECT * FROM usuarios")
    myrsult = cur.fetchall()  # Obtener todos los registros
    insertObjet = []  # Crear la lista donde almacenar los registros
    columNames = [column[0] for column in cur.description]  # Obtener los nombres de las columnas
    for record in myrsult:
        insertObjet.append(record)  # Añadir directamente cada registro
    cur.close()
    conexion.close()  # Cerrar la conexión
    return render_template('home.html', data=insertObjet)  # Pasar los datos a la plantilla

@app.route('/admin')
@login_required
def admin():
    return render_template('admin.html')

def crear_notificacion(id_usuario, mensaje):
    conexion = db.dbconexion()
    if conexion:
        cur = conexion.cursor()
        cur.execute("USE stock")
        cur.execute(
            "INSERT INTO notificaciones (id_usuario, mensaje) VALUES (%s, %s)",
            (id_usuario, mensaje)
        )
        conexion.commit()
        cur.close()
        conexion.close()
    else:
        print("Error: No se pudo establecer la conexión a la base de datos.")
        
@app.route('/notificaciones')
@login_required
def notificaciones():
    conexion = db.dbconexion()
    if conexion:
        cur = conexion.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("USE stock")
        cur.execute(
            "SELECT * FROM notificaciones WHERE id_usuario = %s ORDER BY fecha DESC", 
            (current_user.id,)
        )
        notificaciones = cur.fetchall()
        cur.close()
        conexion.close()
        
        return render_template('notificaciones.html', notificaciones=notificaciones)
    else:
        print("Error: No se pudo establecer la conexión a la base de datos.")
        return render_template('notificaciones.html', notificaciones=[])
    
@app.route('/marcar_como_leida/<int:id_notificacion>', methods=['POST'])
@login_required
def marcar_como_leida(id_notificacion):
    conexion = db.dbconexion()
    if conexion:
        cur = conexion.cursor()
        cur.execute("USE stock")
        cur.execute(
            "UPDATE notificaciones SET leida = TRUE WHERE id_notificacion = %s AND id_usuario = %s",
            (id_notificacion, current_user.id)
        )
        conexion.commit()
        cur.close()
        conexion.close()
    return redirect(url_for('notificaciones'))

def obtener_notificaciones_no_leidas(id_usuario):
    conexion = db.dbconexion()
    if conexion:
        cur = conexion.cursor()
        cur.execute("USE stock")
        cur.execute(
            "SELECT COUNT(*) FROM notificaciones WHERE id_usuario = %s AND leida = FALSE",
            (id_usuario,)
        )
        resultado = cur.fetchone()
        cur.close()
        conexion.close()
        return resultado[0] if resultado else 0
    else:
        print("Error: No se pudo establecer la conexión a la base de datos.")
        return 0

@app.context_processor
def inject_notificaciones_no_leidas():
    if current_user.is_authenticated:
        num_notificaciones_no_leidas = obtener_notificaciones_no_leidas(current_user.id)
        return dict(num_notificaciones_no_leidas=num_notificaciones_no_leidas)
    return dict(num_notificaciones_no_leidas=0)


@app.route('/agregar', methods=['GET', 'POST'])
@login_required
def agregar_producto():
    conexion = db.dbconexion()
    if conexion:
        cur = conexion.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("USE stock")
        cur.execute("SELECT id_categoria, nombre_categoria FROM categorias")
        categorias = cur.fetchall()  # Obtenemos todas las categorías
        cur.close()
        conexion.close()

        return render_template('agregar.html', categorias=categorias)  # Pasamos las categorías a la plantilla
    else:
        print("Error: No se pudo establecer la conexión a la base de datos.")
        return render_template('agregar.html', categorias=[])


@app.route('/agregar_bebidas', methods=['POST'])
@login_required
def registrar_bebidas():
    nombreproducto = request.form['txtnom']
    descripcion = request.form['txtdes']
    estado = request.form['txtest']
    precio = request.form['txtpre']
    cantidad = request.form['txtcant']
    id_categoria = request.form['txtcategoria']  # Obtenemos el id de la categoría

    if nombreproducto and descripcion and precio and cantidad and estado and id_categoria:
        conexion = db.dbconexion()
        if conexion:
            cur = conexion.cursor()
            try:
                id_categoria = int(id_categoria)
                sql_producto = 'INSERT INTO productos (nombre_producto, descripcion, precio, cantidad, estado, id_categoria) VALUES (%s, %s, %s, %s, %s, %s)'
                data_producto = (nombreproducto, descripcion, precio, cantidad, estado, id_categoria)
                cur.execute(sql_producto, data_producto)
                id_producto = cur.lastrowid
                conexion.commit()
                print("Producto y foto agregados exitosamente.")
                crear_notificacion(current_user.id, f'Se ha añadido el producto "{nombreproducto}".')
            except Exception as e:
                print(f"Error al insertar el producto o la foto: {str(e)}")
            finally:
                cur.close()
                conexion.close()
        else:
            print("Error: No se pudo establecer la conexión a la base de datos.")
    else:
        print("Error: Datos incompletos.")
    return render_template('agregar.html')  

@app.route('/editar', methods=['GET', 'POST'])
@login_required
def mostrar_formulario_editar_producto():
    conexion = db.dbconexion()
    if conexion:
        cur = conexion.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("USE stock")
        cur.execute("SELECT id_categoria, nombre_categoria FROM categorias")
        categorias = cur.fetchall() 
        cur.execute("SELECT id_producto, nombre_producto FROM productos")  # Ajusta esta consulta según tus necesidades
        productos = cur.fetchall()  # Cargar productos si es necesario 
        cur.close()
        conexion.close()

        return render_template('editar.html', categorias=categorias, productos=productos)  # Pasamos las categorías a la plantilla
    else:
        print("Error: No se pudo establecer la conexión a la base de datos.")
        return render_template('editar.html', categorias=[], productos=[])


@app.route('/editar_producto', methods=['POST'])
def editar_producto():
    # Recogemos todos los datos del formulario
    nombreproducto = request.form['txtnom']
    descripcion = request.form['txtdes']
    estado = request.form['txtest']
    precio = request.form['txtpre']
    cantidad = int(request.form['txtcant'])
    id_producto = request.form['id_producto']  # Asegúrate de que el campo para el ID esté en el formulario

    if nombreproducto and descripcion and precio and cantidad and estado and id_producto:  
        conexion = db.dbconexion()  # Conectar a la base de datos
        cur = conexion.cursor()

        # Obtener la cantidad actual del producto desde la base de datos
        cur.execute("SELECT cantidad FROM productos WHERE id_producto = %s", (id_producto,))
        resultado = cur.fetchone()
        cantidad_actual = resultado[0] if resultado else 0

        # Ajustar la cantidad según el estado
        if estado == 'entrando':
            nueva_cantidad = cantidad_actual + cantidad
        elif estado == 'saliendo':
            nueva_cantidad = cantidad_actual - cantidad
        else:
            nueva_cantidad = cantidad  # Si no es 'entrando' ni 'saliendo', se usa la cantidad ingresada
        
        if nueva_cantidad < 1:
            flash("La cantidad del producto no puede ser menor a 1.", "error")
            return render_template('/admin.html')
        
        # Consulta para actualizar el producto con la nueva cantidad
        sql = '''UPDATE productos 
                 SET nombre_producto=%s, descripcion=%s, estado=%s, precio=%s, cantidad=%s 
                 WHERE id_producto=%s'''
        data = (nombreproducto, descripcion, estado, precio, nueva_cantidad, id_producto)
        
        try:
            cur.execute(sql, data)
            conexion.commit()
            print("Producto actualizado exitosamente.")
            flash("Producto actualizado exitosamente.", "success") 
            crear_notificacion(current_user.id, f'Se ha actualizado el producto "{nombreproducto}".')
            
            # Notificación de bajo stock si la cantidad es menor a 10
            if nueva_cantidad < 10:
                crear_notificacion(current_user.id, f'La cantidad del producto "{nombreproducto}" está bajo stock.')

        except Exception as e:
            print(f"Error al actualizar el producto: {str(e)}")
            flash("Error al actualizar el producto. Intente de nuevo.", "error")
        finally:
            cur.close()
            conexion.close()
    else:
        flash("Por favor, complete todos los campos requeridos.", "warning")

    return render_template('/admin.html')



@app.route('/eliminar', methods=['GET'])
@login_required
def eliminar_producto():
     conexion = db.dbconexion()
     if conexion:
         cur = conexion.cursor(MySQLdb.cursors.DictCursor)
         cur.execute("USE stock")
         cur.execute("SELECT id_producto, nombre_producto FROM productos")
         productos=cur.fetchall()
         cur.close()
         conexion.close()
         
         return render_template('/eliminar.html', productos=productos) 
     else:
         print("Error: No se pudo establecer la conexión a la base de datos.")
         return render_template('eliminar.html', productos=[])
     

@app.route('/obtener_producto/<int:id_producto>', methods=['GET'])
@login_required
def obtener_producto(id_producto):
    conexion = db.dbconexion()
    if conexion:
        cur = conexion.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("USE stock")
        cur.execute("SELECT nombre_producto FROM productos WHERE id_producto = %s", (id_producto,))
        producto = cur.fetchone()
        cur.close()
        conexion.close()
        if producto:
            return jsonify(nombre=producto['nombre_producto'])
        else:
            return jsonify(error="Producto no encontrado")  , 404
    else:
        print("Error: No se pudo establecer la conexión a la base de datos.")
        return jsonify(error="Error de conexión"), 500
         

@app.route('/eliminar_productos/<string:id>', methods=['POST'])
@login_required
def delete(id):
    conexion = db.dbconexion()
    cur = conexion.cursor(MySQLdb.cursors.DictCursor)
    sql = 'DELETE FROM productos WHERE id_producto = %s'
    data = (id,)
    try:
        cur.execute(sql, data)
        conexion.commit()
        print("Producto eliminado exitosamente.") 
        # Mensaje de éxito en la consola
    finally:
        cur.close()
        conexion.close()
    
    return redirect(url_for('eliminar'))  # Redirigir a la página de eliminación

@app.route('/visualizar', methods=['GET'])
@login_required
def visualizar():
    conexion = db.dbconexion()
    if conexion:
        cur = conexion.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("USE stock")
        cur.execute('''SELECT p.id_producto, p.nombre_producto, p.descripcion, p.precio, p.cantidad, p.estado, c.nombre_categoria FROM productos as p 
                    LEFT JOIN categorias as c ON p.id_categoria = c.id_categoria''')
        productos = cur.fetchall()  # Obtenemos todas las categorías
        cur.close()
        conexion.close()

        return render_template('visualizar.html', productos=productos)  # Pasamos las categorías a la plantilla
    else:
        print("Error: No se pudo establecer la conexión a la base de datos.")
        return render_template('visualizar.html',productos=[])

@app.route('/settings')
@login_required
def settings():
    conexion = db.dbconexion()
    if conexion:
        cur = conexion.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("USE stock")
        # Obtenemos la información del usuario actual basado en el ID del usuario
        cur.execute("SELECT id_usuario, nombre_usuario, rol,eps,numero, nombre FROM usuarios WHERE id_usuario = %s", (current_user.id,))
        usuario_actual = cur.fetchone()  # Obtenemos la información del usuario actual

        # Cierra la conexión
        cur.close()
        conexion.close()

        # Pasa la información del usuario actual a la plantilla
        return render_template('settings.html', usuario=    usuario_actual)  # Asegúrate de que 'agregar.html' es la plantilla correcta
    else:
        print("Error: No se pudo establecer la conexión a la base de datos.")
        return render_template('settings.html', usuario=None)  # Manejo de error



@app.route('/acceso-login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and 'txtusuarios' in request.form and 'txtcontra' in request.form:
        _usuarios = request.form['txtusuarios']
        _contraseña = request.form['txtcontra']
        conexion = db.dbconexion()  
        if conexion:
            try:
                cur = conexion.cursor(MySQLdb.cursors.DictCursor)
                cur.execute("USE stock")
                cur.execute("SELECT * FROM usuarios WHERE nombre_usuario = %s AND contraseña = %s", (_usuarios, _contraseña))
                account = cur.fetchone()
                if account:
                    user = User(account['id_usuario'])  
                    login_user(user)  # Iniciar sesión
                    return redirect(url_for('admin'))  
                else:
                    return render_template('home.html', mensaje='Usuario o contraseña incorrecta')
            finally:
                cur.close()
                conexion.close()
        else:
            return render_template('home.html', mensaje='Error al conectar con la base de datos')
    return render_template('home.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()  
    session.clear()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)