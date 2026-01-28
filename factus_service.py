import os
import requests
import json
from datetime import datetime

class FactusService:
    # Mapeo: 'Código HTML/DIAN' -> ID Interno Factus
    DICCIONARIO_TIPOS_DOC = {
        '13': 3,  # Cédula de Ciudadanía
        '31': 6,  # NIT
        '42': 5,  # Documento Extranjero / Pasaporte
        '22': 4,  # Cédula de Extranjería
    }

    def __init__(self):
        self.api_url = os.environ.get('FACTUS_API_URL')
        self.client_id = os.environ.get('FACTUS_CLIENT_ID')
        self.client_secret = os.environ.get('FACTUS_CLIENT_SECRET')
        self.email = os.environ.get('FACTUS_EMAIL')
        self.password = os.environ.get('FACTUS_PASSWORD')
        self.token = None

    def _obtener_token(self):
        print("🔐 Solicitando Token a Factus...")
        url = f"{self.api_url}/oauth/token"
        payload = {
            "grant_type": "password",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "username": self.email,
            "password": self.password,
            "scope": "*"
        }
        
        try:
            response = requests.post(url, data=payload)
            if response.status_code == 200:
                self.token = response.json()['access_token']
                return self.token
            else:
                print(f"❌ Error Auth: {response.text}")
                return None
        except Exception as e:
            print(f"🔥 Error Conexión Auth: {str(e)}")
            return None

    def _obtener_rango_activo(self):
        print("🔍 Consultando Rango de Numeración...")
        url = f"{self.api_url}/v1/numbering-ranges?filter[code]=BILL"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json"
        }

        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                
                # LÓGICA DE RANGOS MEJORADA (Maneja lista o diccionario)
                datos_rango = data.get('data')
                
                if isinstance(datos_rango, list) and len(datos_rango) > 0:
                    rango = datos_rango[0]
                    print(f"✅ Rango encontrado (Lista): ID {rango['id']}")
                    return rango['id']
                elif isinstance(datos_rango, dict) and 'id' in datos_rango:
                    print(f"✅ Rango encontrado (Dict): ID {datos_rango['id']}")
                    return datos_rango['id']
                else:
                    print(f"⚠️ Estructura de rangos inesperada: {type(datos_rango)}")
                    # Imprimir para debuggear si vuelve a fallar
                    print(json.dumps(data, indent=2))
                    return None
            else:
                print(f"❌ Error Rangos: {response.status_code}")
                return None
        except Exception as e:
            print(f"🔥 Error buscando rangos: {str(e)}")
            return None

    def crear_factura(self, datos_cliente, items_carrito, total):
        # 1. Token
        if not self.token:
            if not self._obtener_token():
                return {"status": "error", "message": "Fallo de autenticación"}

        # 2. Rango
        rango_id = self._obtener_rango_activo()
        if not rango_id:
            print("⚠️ Usando Rango ID 8 por defecto (Fallback)")
            rango_id = 8 

        # 3. TRADUCCIÓN DE TIPO DE DOCUMENTO (El arreglo clave)
        tipo_doc_html = str(datos_cliente['tipo_doc'])
        # Buscamos en el diccionario, si no existe usamos 3 (Cédula) por defecto
        id_tipo_doc_factus = self.DICCIONARIO_TIPOS_DOC.get(tipo_doc_html, 3)
        
        # Lógica de Empresa (Si es NIT/6 es empresa)
        es_empresa = (id_tipo_doc_factus == 6)
        legal_org_id = "1" if es_empresa else "2" # 1=Jurídica, 2=Natural

        # 4. Preparar Items
        items_api = []
        for item in items_carrito:
            items_api.append({
                "code_reference": item['info'].referencia,
                "name": item['info'].nombre,
                "quantity": item['cantidad'],
                "discount_rate": 0,
                "price": item['info'].precio,
                "tax_rate": "19.00",
                "unit_measure_id": 70,
                "standard_code_id": 1,
                "is_excluded": 0,
                "tribute_id": 1,
                "withholding_taxes": []
            })

        # 5. Payload
        payload = {
            "numbering_range_id": rango_id,
            "reference_code": f"GEN-{int(datetime.now().timestamp())}",
            "observation": f"Pedido Web - {datos_cliente['nombre']}",
            "payment_form": "1",      
            "payment_method_code": "10", 
            "customer": {
                "identification": datos_cliente['documento'],
                
                # --- AQUÍ USAMOS EL ID TRADUCIDO ---
                "identification_document_id": id_tipo_doc_factus,
                # -----------------------------------
                
                "dv": "3",
                "company": datos_cliente['nombre'] if es_empresa else None,
                "trade_name": datos_cliente['nombre'] if es_empresa else None,
                "names": datos_cliente['nombre'],
                "address": datos_cliente['direccion'],
                "email": datos_cliente['email'],
                "phone": datos_cliente['telefono'],
                "legal_organization_id": legal_org_id,
                "tribute_id": "21",
                "municipality_id": "980"
            },
            "items": items_api
        }

        # 6. Enviar
        url = f"{self.api_url}/v1/bills/validate"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        try:
            print(f"🚀 Enviando factura (Doc ID: {id_tipo_doc_factus})...")
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code in [200, 201]:
                return {"status": "ok", "data": response.json()}
            else:
                print(f"❌ Error Factus API: {response.text}")
                return {"status": "error", "message": f"Error Validación: {response.json().get('message')}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}