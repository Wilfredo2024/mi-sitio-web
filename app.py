from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mysqldb import MySQL
import datetime

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Clave secreta para mensajes flash

# Configuración de la base de datos MySQL
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'ciber_ventas'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

# Ruta para el inicio
@app.route('/')
def index():
    return render_template('index.html')

# Ruta para agregar producto
@app.route('/agregar_producto', methods=['GET', 'POST'])
def agregar_producto():
    if request.method == 'POST':
        nombre_producto = request.form['nombre_producto']
        precio = float(request.form['precio'])
        
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO productos (nombre_producto, precio) VALUES (%s, %s)", (nombre_producto, precio))
        mysql.connection.commit()
        cur.close()
        
        flash('Producto agregado exitosamente', 'success')
        return redirect(url_for('agregar_producto'))
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM productos")
    productos = cur.fetchall()
    cur.close()
    
    return render_template('agregar_producto.html', productos=productos)

# Ruta para editar producto
@app.route('/editar_producto/<int:id>', methods=['GET', 'POST'])
def editar_producto(id):
    if request.method == 'POST':
        nombre_producto = request.form['nombre_producto']
        precio = float(request.form['precio'])
        
        cur = mysql.connection.cursor()
        cur.execute("UPDATE productos SET nombre_producto = %s, precio = %s WHERE id = %s", (nombre_producto, precio, id))
        mysql.connection.commit()
        cur.close()
        
        flash('Producto actualizado exitosamente', 'success')
        return redirect(url_for('agregar_producto'))
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM productos WHERE id = %s", [id])
    producto = cur.fetchone()
    cur.close()
    
    return render_template('editar_producto.html', producto=producto)

# Ruta para eliminar producto
@app.route('/eliminar_producto/<int:id>', methods=['POST'])
def eliminar_producto(id):
    pin = request.form['pin']  # Asegúrate de cambiar este PIN por uno más seguro
    if pin != '210501':  # Reemplazar con tu PIN real
        flash('PIN incorrecto. Inténtelo de nuevo.', 'danger')
    else:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM productos WHERE id = %s", [id])
        mysql.connection.commit()
        cur.close()
        
        flash('Producto eliminado exitosamente', 'success')
    
    return redirect(url_for('agregar_producto'))

# Ruta para el catálogo de productos
@app.route('/catalogo')
def catalogo():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM productos")
    productos = cur.fetchall()
    cur.close()
    
    return render_template('catalogo.html', productos=productos)

# Ruta para registrar venta
@app.route('/registrar_venta', methods=['GET', 'POST'])
def registrar_venta():
    if request.method == 'POST':
        productos_vendidos = request.form.getlist('productos_vendidos[]')
        producto_manual_nombre = request.form.get('producto_manual_nombre')
        producto_manual_precio = request.form.get('producto_manual_precio')
        producto_manual_cantidad = request.form.get('producto_manual_cantidad')

        if not productos_vendidos and not (producto_manual_nombre and producto_manual_precio and producto_manual_cantidad):
            flash('Debe agregar al menos un producto para registrar la venta.', 'danger')
            return redirect(url_for('registrar_venta'))

        total_venta = float(request.form['total_venta'])
        efectivo_recibido = float(request.form['efectivo'])
        vuelto = float(request.form['vuelto_calculado'])

        if efectivo_recibido < total_venta:
            flash('El efectivo recibido no puede ser menor que el total de la venta.', 'danger')
            return redirect(url_for('registrar_venta'))

        cur = mysql.connection.cursor()

        try:
            for producto in productos_vendidos:
                producto_id, cantidad, precio = producto.split(',')
                cur.execute("SELECT nombre_producto FROM productos WHERE id = %s", [producto_id])
                result = cur.fetchone()
                
                if result:
                    producto_nombre = result['nombre_producto']
                    total = float(precio) * int(cantidad)
                    fecha_venta = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                    cur.execute("INSERT INTO ventas (nombre_producto, cantidad, precio, total, fecha_venta) VALUES (%s, %s, %s, %s, %s)",
                                (producto_nombre, cantidad, precio, total, fecha_venta))
                    mysql.connection.commit()
                else:
                    flash(f'Producto con ID {producto_id} no encontrado.', 'danger')
                    return redirect(url_for('registrar_venta'))

            if producto_manual_nombre and producto_manual_precio and producto_manual_cantidad:
                total_manual = float(producto_manual_precio) * int(producto_manual_cantidad)
                fecha_venta = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                cur.execute("INSERT INTO ventas (nombre_producto, cantidad, precio, total, fecha_venta) VALUES (%s, %s, %s, %s, %s)",
                            (producto_manual_nombre, producto_manual_cantidad, producto_manual_precio, total_manual, fecha_venta))
                mysql.connection.commit()

            flash('Venta registrada exitosamente', 'success')
            return redirect(url_for('registrar_venta'))

        except Exception as e:
            flash(f'Error al registrar la venta: {str(e)}', 'danger')

        finally:
            cur.close()

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM productos")
    productos = cur.fetchall()
    cur.close()

    return render_template('registrar_venta.html', productos=productos)


# Ruta para buscar ventas
@app.route('/buscar_ventas', methods=['GET', 'POST'])
def buscar_ventas():
    total_vendido = 0
    data = []
    if request.method == 'POST':
        pin = request.form.get('pin')  # Obtener el valor del campo 'pin' de manera segura
        if pin != '210501':  # Comprobar el PIN
            flash('PIN incorrecto. Inténtelo de nuevo.', 'danger')
            return redirect(url_for('index'))

        mostrar_todo = 'mostrar_todo' in request.form
        cur = mysql.connection.cursor()

        if mostrar_todo:
            cur.execute("SELECT * FROM ventas")
            data = cur.fetchall()
            cur.execute("SELECT SUM(total) AS total_vendido FROM ventas")
            total_vendido = cur.fetchone()['total_vendido'] or 0
        else:
            fecha = request.form['fecha']
            if not fecha:
                flash('Debe seleccionar una fecha para buscar ventas.', 'danger')
                return redirect(url_for('index'))

            cur.execute("SELECT * FROM ventas WHERE fecha_venta LIKE %s", [f"%{fecha}%"])
            data = cur.fetchall()
            cur.execute("SELECT SUM(total) AS total_vendido FROM ventas WHERE fecha_venta LIKE %s", [f"%{fecha}%"])
            total_vendido = cur.fetchone()['total_vendido'] or 0

        cur.close()

    return render_template('buscar_ventas.html', data=data, total_vendido=total_vendido)

# Ruta para eliminar una venta específica
@app.route('/eliminar/<int:id>', methods=['POST'])
def eliminar_venta(id):
    pin = request.form['pin']
    if pin != '210501':  # Reemplazar con tu PIN real
        flash('PIN incorrecto. Inténtelo de nuevo.', 'danger')
    else:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM ventas WHERE id = %s", [id])
        mysql.connection.commit()
        cur.close()
        
        flash('Venta eliminada exitosamente', 'success')

    # Redirigir de vuelta a la página de búsqueda de ventas
    return redirect(url_for('buscar_ventas'))

# Ruta para eliminar todas las ventas
@app.route('/eliminar_todo', methods=['POST'])
def eliminar_todas_ventas():
    pin = request.form['pin']  # Asegúrate de cambiar este PIN por uno más seguro
    if pin != '210501':  # Reemplazar con tu PIN real
        flash('PIN incorrecto. Inténtelo de nuevo.', 'danger')
    else:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM ventas")
        mysql.connection.commit()
        cur.close()
        
        flash('Se han eliminado todas las ventas exitosamente', 'success')

    return redirect(url_for('index'))



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
