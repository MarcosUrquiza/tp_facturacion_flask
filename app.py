from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from datetime import date
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secreto123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

db = SQLAlchemy(app)
login_manager = LoginManager(app)

class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    rol = db.Column(db.String(20))

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    direccion = db.Column(db.String(100))
    telefono = db.Column(db.String(50))
    email = db.Column(db.String(100))

class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.String(100))
    precio = db.Column(db.Float)
    stock = db.Column(db.Integer)

class Factura(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_cliente = db.Column(db.Integer, db.ForeignKey('cliente.id'))
    fecha = db.Column(db.String(20))
    total = db.Column(db.Float)

    cliente = db.relationship('Cliente', backref=db.backref('facturas', lazy=True))

class DetalleFactura(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_factura = db.Column(db.Integer, db.ForeignKey('factura.id'))
    id_producto = db.Column(db.Integer, db.ForeignKey('producto.id'))
    cantidad = db.Column(db.Integer)
    precio_unitario = db.Column(db.Float)
    subtotal = db.Column(db.Float)

    producto = db.relationship('Producto')


@app.route('/facturas/nueva', methods=['GET', 'POST'])
@login_required
def nueva_factura():
    clientes = Cliente.query.all()
    productos = Producto.query.all()
    if request.method == 'POST':
        id_cliente = request.form['id_cliente']
        fecha = date.today().strftime("%Y-%m-%d")
        total = 0

        factura = Factura(id_cliente=id_cliente, fecha=fecha, total=0)
        db.session.add(factura)
        db.session.commit()

        for p in productos:
            cantidad = request.form.get(f'producto_{p.id}')
            if cantidad and int(cantidad) > 0:
                cantidad = int(cantidad)
                subtotal = cantidad * p.precio
                detalle = DetalleFactura(
                    id_factura=factura.id,
                    id_producto=p.id,
                    cantidad=cantidad,
                    precio_unitario=p.precio,
                    subtotal=subtotal
                )
                db.session.add(detalle)
                total += subtotal

                p.stock -= cantidad

        factura.total = total
        db.session.commit()
        return redirect(url_for('facturas_view'))

    return render_template('nueva_factura.html', clientes=clientes, productos=productos)


@app.route('/facturas/<int:id>')
@login_required
def detalle_factura(id):
    factura = Factura.query.get_or_404(id)
    cliente = Cliente.query.get(factura.id_cliente)
    detalles = DetalleFactura.query.filter_by(id_factura=id).all()
    return render_template('detalle_factura.html', factura=factura, cliente=cliente, detalles=detalles)

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = Usuario.query.filter_by(email=email, password=password).first()
        if user:
            login_user(user)
            return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/reportes/clientes', methods=['GET', 'POST'])
@login_required
def reportes_clientes():
    clientes = Cliente.query.all()
    facturas = []

    if request.method == 'POST':
        id_cliente = request.form['id_cliente']
        facturas = Factura.query.filter_by(id_cliente=id_cliente).all()

    return render_template('reportes_clientes.html', clientes=clientes, facturas=facturas)


@app.route('/reportes/ventas', methods=['GET', 'POST'])
@login_required
def reportes_ventas():
    total = None
    facturas = []
    if request.method == 'POST':
        fecha_inicio = request.form['fecha_inicio']
        fecha_fin = request.form['fecha_fin']
        facturas = Factura.query.filter(Factura.fecha >= fecha_inicio, Factura.fecha <= fecha_fin).all()
        total = sum(f.total for f in facturas)

    return render_template('reportes_ventas.html', facturas=facturas, total=total)

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/clientes')
@login_required
def clientes_view():
    clientes = Cliente.query.all()
    return render_template('clientes.html', clientes=clientes)

@app.route('/clientes/add', methods=['POST'])
@login_required
def add_cliente():
    nombre = request.form['nombre']
    direccion = request.form['direccion']
    telefono = request.form['telefono']
    email = request.form['email']
    nuevo = Cliente(nombre=nombre, direccion=direccion, telefono=telefono, email=email)
    db.session.add(nuevo)
    db.session.commit()
    return redirect(url_for('clientes_view'))

@app.route('/clientes/edit/<int:id>', methods=['POST'])
@login_required
def edit_cliente(id):
    cliente = Cliente.query.get(id)
    cliente.nombre = request.form['nombre']
    cliente.direccion = request.form['direccion']
    cliente.telefono = request.form['telefono']
    cliente.email = request.form['email']
    db.session.commit()
    return redirect(url_for('clientes_view'))

@app.route('/clientes/delete/<int:id>')
@login_required
def delete_cliente(id):
    cliente = Cliente.query.get(id)
    db.session.delete(cliente)
    db.session.commit()
    return redirect(url_for('clientes_view'))

@app.route('/productos')
@login_required
def productos_view():
    productos = Producto.query.all()
    return render_template('productos.html', productos=productos)

@app.route('/productos/add', methods=['POST'])
@login_required
def add_producto():
    descripcion = request.form['descripcion']
    precio = request.form['precio']
    stock = request.form['stock']
    nuevo = Producto(descripcion=descripcion, precio=precio, stock=stock)
    db.session.add(nuevo)
    db.session.commit()
    return redirect(url_for('productos_view'))

@app.route('/productos/edit/<int:id>', methods=['POST'])
@login_required
def edit_producto(id):
    producto = Producto.query.get(id)
    producto.descripcion = request.form['descripcion']
    producto.precio = request.form['precio']
    producto.stock = request.form['stock']
    db.session.commit()
    return redirect(url_for('productos_view'))

@app.route('/productos/delete/<int:id>')
@login_required
def delete_producto(id):
    producto = Producto.query.get(id)
    db.session.delete(producto)
    db.session.commit()
    return redirect(url_for('productos_view'))

@app.route('/facturas')
@login_required
def facturas_view():
    facturas = Factura.query.all()
    return render_template('facturas.html', facturas=facturas)

@app.route('/facturas/add', methods=['POST'])
@login_required
def add_factura():
    id_cliente = request.form['id_cliente']
    fecha = request.form['fecha']
    total = request.form['total']
    nueva = Factura(id_cliente=id_cliente, fecha=fecha, total=total)
    db.session.add(nueva)
    db.session.commit()
    return redirect(url_for('facturas_view'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not Usuario.query.filter_by(email="admin@admin.com").first():
            admin = Usuario(nombre="Admin", email="admin@admin.com", password="1234", rol="admin")
            db.session.add(admin)
            db.session.commit()
    app.run(debug=True)
