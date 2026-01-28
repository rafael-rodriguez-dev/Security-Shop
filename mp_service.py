import mercadopago
import os

class MercadoPagoService:
    def __init__(self):
        # Cargamos el Access Token desde el .env
        self.access_token = os.environ.get('MP_ACCESS_TOKEN')
        # Inicializamos el SDK
        self.sdk = mercadopago.SDK(self.access_token)

    def crear_preferencia(self, items_carrito, datos_cliente, referencia_pedido):
        """
        Crea la 'Preferencia de Pago' (el carrito que le enviamos a MP).
        """
        
        # 1. Transformar items de Genesis al formato de MercadoPago
        items_mp = []
        for item in items_carrito:
            items_mp.append({
                "id": item['info'].referencia,
                "title": item['info'].nombre,
                "quantity": item['cantidad'],
                "unit_price": float(item['info'].precio),
                "currency_id": "COP"
            })

        # 2. Configurar urls de retorno (A dónde vuelve el usuario)
        # En local usamos localhost, en producción será tu dominio de Render
        base_url = os.environ.get('BASE_URL', 'http://127.0.0.1:5000')

        # 3. Armar el diccionario de preferencia
        preference_data = {
            "items": items_mp,
            "payer": {
                "name": datos_cliente['nombre'],
                "email": datos_cliente['email'],
                "phone": {
                    "area_code": "57",
                    "number": datos_cliente['telefono']
                },
                "address": {
                    "street_name": datos_cliente['direccion']
                }
            },
            "back_urls": {
                "success": f"{base_url}/pago-exitoso",
                "failure": f"{base_url}/pago-fallido",
                "pending": f"{base_url}/pago-pendiente"
            },
            "auto_return": "approved", # Vuelve automático si aprueban
            "external_reference": referencia_pedido, # Para rastrear luego
            "statement_descriptor": "GENESIS SHOP"
        }

        # 4. Crear la preferencia en MP
        try:
            preference_response = self.sdk.preference().create(preference_data)
            rta = preference_response["response"]
            return rta["init_point"] # Este es el LINK de pago
        except Exception as e:
            print(f"🔥 Error creando preferencia MP: {e}")
            return None