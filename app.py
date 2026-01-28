import os
import uuid
from flask import Flask, render_template, session, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

# Importamos nuestros servicios especializados
from factus_service import FactusService
from mp_service import MercadoPagoService

# Cargar variables de entorno locales (si existe .env)
load_dotenv()

# --- PRUEBA DE VARIABLES (Borrar luego) ---
token_mp = os.environ.get('MP_ACCESS_TOKEN')
if token_mp:
    print(f"✅ MercadoPago Token cargado: {token_mp[:10]}...")
else:
    print("❌ ERROR: No encuentro el Token de MercadoPago en .env")
# ------------------------------------------
# Inicializamos la app
app = Flask(__name__)

# --- CONFIGURACIÓN ---
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key_super_secreta')

# Configuración de Base de Datos (Soporta Render/Postgres y Local/SQLite)
db_url = os.environ.get('DATABASE_URL')
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url or 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'genesis.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- MODELOS (TABLAS) ---
class Producto(db.Model):
    __tablename__ = 'productos'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    referencia = db.Column(db.String(50), unique=True, nullable=False)
    precio = db.Column(db.Integer, nullable=False)
    categoria = db.Column(db.String(50))
    imagen = db.Column(db.String(200), default='https://via.placeholder.com/150')

    def __repr__(self):
        return f'<Producto {self.referencia}>'

# --- RUTAS PRINCIPALES ---

@app.route('/')
def home():
    productos = Producto.query.all()
    return render_template('index.html', title="Inicio", productos=productos)

@app.route('/herramientas/calculadora-discos')
def calculadora_hdd():
    return render_template('herramientas/calculadora_hdd.html', title="Calculadora CCTV")

# --- LÓGICA DEL CARRITO ---

@app.route('/agregar-carrito/<int:producto_id>')
def agregar_carrito(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    carrito = session.get('carrito', {})
    prod_id_str = str(producto_id)
    
    if prod_id_str in carrito:
        carrito[prod_id_str] += 1
    else:
        carrito[prod_id_str] = 1
    
    session['carrito'] = carrito
    session.modified = True
    return redirect(url_for('ver_carrito'))

@app.route('/carrito')
def ver_carrito():
    carrito = session.get('carrito', {})
    productos_en_carrito = []
    gran_total = 0
    
    for prod_id_str, cantidad in carrito.items():
        producto = Producto.query.get(int(prod_id_str))
        if producto:
            subtotal = producto.precio * cantidad
            gran_total += subtotal
            productos_en_carrito.append({
                'info': producto,
                'cantidad': cantidad,
                'subtotal': subtotal
            })
            
    return render_template('carrito.html', productos=productos_en_carrito, total=gran_total, title="Mi Carrito")

@app.route('/limpiar-carrito')
def limpiar_carrito():
    session.pop('carrito', None)
    return redirect(url_for('home'))

# --- CHECKOUT Y PAGOS ---

@app.route('/checkout', methods=['GET'])
def checkout():
    carrito = session.get('carrito', {})
    if not carrito:
        return redirect(url_for('home'))
        
    gran_total = 0
    productos_en_carrito = []
    
    for prod_id_str, cantidad in carrito.items():
        producto = Producto.query.get(int(prod_id_str))
        if producto:
            subtotal = producto.precio * cantidad
            gran_total += subtotal
            productos_en_carrito.append({'info': producto, 'cantidad': cantidad, 'subtotal': subtotal})
            
    return render_template('checkout.html', total=gran_total, productos=productos_en_carrito, title="Finalizar Compra")

@app.route('/confirmar-pedido', methods=['POST'])
def confirmar_pedido():
    """
    1. Guarda datos del cliente.
    2. Genera Link de MercadoPago.
    3. Redirige a pagar.
    """
    # A. Capturar datos del formulario
    datos_cliente = {
        'nombre': request.form['nombre'],
        'tipo_doc': request.form['tipo_doc'],
        'documento': request.form['documento'],
        'email': request.form['email'],
        'direccion': request.form['direccion'],
        'telefono': request.form['telefono']
    }
    
    # B. Guardar en sesión temporalmente
    session['datos_cliente'] = datos_cliente

    # C. Reconstruir items para MercadoPago
    carrito_session = session.get('carrito', {})
    items_carrito = []
    
    for prod_id_str, cantidad in carrito_session.items():
        producto = Producto.query.get(int(prod_id_str))
        if producto:
            items_carrito.append({
                'info': producto,
                'cantidad': cantidad,
                'precio': producto.precio
            })

    if not items_carrito:
        return redirect(url_for('home'))

    # D. Generar referencia única
    ref_pedido = f"GEN-{uuid.uuid4().hex[:8].upper()}"
    session['ref_pedido'] = ref_pedido

    # E. Crear Preferencia en MercadoPago
    mp_service = MercadoPagoService()
    link_de_pago = mp_service.crear_preferencia(items_carrito, datos_cliente, ref_pedido)

    if link_de_pago:
        print(f"🚀 Redirigiendo a MercadoPago: {link_de_pago}")
        return redirect(link_de_pago)
    else:
        return "<h1>Error: No se pudo conectar con la pasarela de pagos.</h1>", 500

# --- RUTAS DE RETORNO (CALLBACKS) ---

@app.route('/pago-exitoso')
def pago_exitoso():
    """
    El usuario pagó y volvió. Ahora facturamos.
    """
    datos_cliente = session.get('datos_cliente')
    carrito_session = session.get('carrito', {})
    # ref_pedido = session.get('ref_pedido') # Opcional: Validar contra MP si el pago está 'approved'
    
    if not datos_cliente or not carrito_session:
        return redirect(url_for('home'))

    # Reconstruir items para Factus
    items_carrito = []
    gran_total = 0
    for prod_id_str, cantidad in carrito_session.items():
        producto = Producto.query.get(int(prod_id_str))
        if producto:
            subtotal = producto.precio * cantidad
            gran_total += subtotal
            items_carrito.append({'info': producto, 'cantidad': cantidad, 'subtotal': subtotal})

    # 🔥 DISPARAR FACTURACIÓN ELECTRÓNICA
    factus = FactusService()
    resultado_factura = None
    
    if items_carrito:
        resultado = factus.crear_factura(datos_cliente, items_carrito, gran_total)
        
        if resultado.get('status') == 'ok':
            # Éxito total
            data_bill = resultado['data']['data']['bill']
            resultado_factura = {
                'numero': data_bill.get('number'),
                'cufe': data_bill.get('cufe'),
                'qr': data_bill.get('qr'),
                'mensaje': "Pago exitoso y Factura Electrónica generada."
            }
        else:
            # Pago ok, Factura falló
            print(f"⚠️ Error Factus: {resultado.get('message')}")
            resultado_factura = {
                'error': True,
                'mensaje': "Pago recibido correctamente, pero la factura electrónica está pendiente por validación técnica."
            }

    # Limpiar sesión
    session.pop('carrito', None)
    session.pop('datos_cliente', None)
    session.pop('ref_pedido', None)

    return render_template('exito.html', cliente=datos_cliente, factura=resultado_factura)

@app.route('/pago-fallido')
def pago_fallido():
    return render_template('base.html', content="<h1>Pago Rechazado o Cancelado</h1><p>Intenta nuevamente.</p><a href='/checkout' class='btn btn-warning'>Volver al Checkout</a>")

@app.route('/pago-pendiente')
def pago_pendiente():
    return render_template('base.html', content="<h1>Pago Pendiente</h1><p>Estamos esperando la confirmación de tu banco (Nequi/PSE).</p>")

# --- UTILIDADES ADMIN ---

@app.route('/semilla-productos')
def semilla():
    if Producto.query.count() > 0: return "⚠️ DB ya tiene datos."
    
    productos = [
        Producto(nombre="Cámara Bullet HIKVISION 1080p", referencia="DS-2CE16D0T-IRPF", precio=85000, categoria="CCTV", imagen="https://m.media-amazon.com/images/I/51r-tqX+LXL._AC_SL1000_.jpg"),
        Producto(nombre="DVR 4 Canales HIKVISION (H.265+)", referencia="DS-7204HGHI-K1", precio=240000, categoria="Grabadores", imagen="https://m.media-amazon.com/images/I/61M5J-zJ+LL._AC_SL1500_.jpg"),
        Producto(nombre="Disco Duro WD Purple 1TB", referencia="WD10PURZ", precio=210000, categoria="Almacenamiento", imagen="https://m.media-amazon.com/images/I/71pC69Iis+L._AC_SL1500_.jpg"),
        Producto(nombre="Kit Alarma Inalámbrica WiFi", referencia="GEN-ALARM-01", precio=450000, categoria="Alarmas", imagen="https://m.media-amazon.com/images/I/61b-KqXvLCL._AC_SL1500_.jpg")
    ]
    db.session.add_all(productos)
    db.session.commit()
    return "✅ Productos cargados."

@app.route('/setup-db')
def setup_db():
    try:
        db.create_all()
        return "✅ Tablas creadas."
    except Exception as e:
        return f"❌ Error: {str(e)}"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)