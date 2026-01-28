# 🛡️ Genesis Shop - E-commerce de Seguridad Inteligente

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-2.0+-green?style=for-the-badge&logo=flask&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Production-336791?style=for-the-badge&logo=postgresql&logoColor=white)
![MercadoPago](https://img.shields.io/badge/MercadoPago-Integration-009EE3?style=for-the-badge&logo=mercadolibre&logoColor=white)

Plataforma completa de comercio electrónico desarrollada con **Python y Flask**, enfocada en la venta de equipos de seguridad electrónica. Este proyecto simula un entorno de producción real integrando pagos en línea y facturación electrónica.

## 🚀 Funcionalidades Clave

* 🛒 **Carrito de Compras:** Gestión de estado mediante sesiones de servidor.
* 💳 **Pasarela de Pagos:** Integración real con la API de **MercadoPago** (Checkout Pro).
* 🧾 **Facturación Electrónica:** Conexión vía API REST con **Factus** para emisión de facturas legales (Simulación DIAN).
* ☁️ **Despliegue Cloud:** Base de datos **PostgreSQL** y hosting en **Render**.
* 🔒 **Seguridad:** Gestión de variables de entorno y protección de rutas.

## 🛠️ Tecnologías Utilizadas

* **Backend:** Python, Flask, Jinja2.
* **Base de Datos:** SQLite (Desarrollo) / PostgreSQL (Producción).
* **ORM:** SQLAlchemy.
* **Frontend:** HTML5, CSS3, JavaScript (Responsive Design).
* **APIs Externas:** MercadoPago SDK, Factus API.

---

## 📸 Demo del Proyecto


> **[Ver Video Demo del Funcionamiento](https://www.linkedin.com/posts/rafael-rodriguez-dev_python-flask-webdevelopment-activity-7422063270641106944-Ld9A?utm_source=share&utm_medium=member_desktop&rcm=ACoAAC3VIzgBbdWPOrEARXZjTIVa-BDS76N4pkg)**

---

## ⚙️ Instalación y Configuración Local

Sigue estos pasos para correr el proyecto en tu máquina:

1.  **Clonar el repositorio:**
    ```bash
    git clone [https://github.com/tu-usuario/security-shop.git](https://github.com/tu-usuario/security-shop.git)
    cd security-shop
    ```

2.  **Crear entorno virtual:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # En Windows: venv\Scripts\activate
    ```

3.  **Instalar dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configurar Variables de Entorno (.env):**
    Crea un archivo `.env` en la raíz y agrega tus propias credenciales (no incluidas por seguridad):
    ```env
    SECRET_KEY=tu_clave_secreta_flask
    
    # Base de datos (Opcional, usa SQLite por defecto si se deja vacío)
    DATABASE_URL=
    
    # Credenciales MercadoPago
    MP_ACCESS_TOKEN=tu_token_de_prueba
    
    # Credenciales Factus (Facturación)
    FACTUS_API_URL=[https://api-sandbox.factus.com.co](https://api-sandbox.factus.com.co)
    FACTUS_CLIENT_ID=tu_client_id
    FACTUS_CLIENT_SECRET=tu_client_secret
    FACTUS_EMAIL=tu_email_factus
    FACTUS_PASSWORD=tu_password_factus
    ```

5.  **Ejecutar la aplicación:**
    ```bash
    python app.py
    ```
    Visita `http://127.0.0.1:5000` en tu navegador.

---

## 👨‍💻 Autor

**Rafael Rodríguez**
* [LinkedIn](https://www.linkedin.com/in/rafael-rodriguez-dev/)
* [GitHub](https://github.com/rafael-rodriguez-dev)

---
*Proyecto desarrollado con fines educativos y de portafolio.*
