#!/usr/bin/env python3
import requests
import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

def test_cloudflare_credentials():
    """
    Prueba las credenciales de Cloudflare para verificar si son válidas.
    """
    # Obtener credenciales y configuración
    api_key = os.getenv("CF_API_KEY")
    api_email = os.getenv("CF_EMAIL")
    zone_id = os.getenv("CF_ZONE_ID")
    
    print(f"Probando credenciales de Cloudflare:")
    print(f"- Email: {api_email}")
    print(f"- API Key: {api_key[:5]}...{api_key[-5:]} (oculto por seguridad)")
    print(f"- Zone ID: {zone_id}")
    
    # Configurar los headers para la API de Cloudflare
    headers = {
        'Content-Type': 'application/json',
    }
    
    # Si tenemos email, usamos Global API Key
    if api_email:
        print("\nUsando Global API Key con email")
        headers['X-Auth-Email'] = api_email
        headers['X-Auth-Key'] = api_key
    else:
        # Si no hay email, usamos API Token
        print("\nUsando API Token")
        headers['Authorization'] = f'Bearer {api_key}'
    
    # Probar la autenticación obteniendo información de la zona
    try:
        print(f"\nProbando acceso a la zona {zone_id}...")
        url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                zone_name = data['result']['name']
                print(f"✅ Autenticación exitosa! Zona encontrada: {zone_name}")
                
                # Probar acceso a los registros DNS
                print(f"\nProbando acceso a los registros DNS de la zona...")
                dns_url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
                dns_response = requests.get(dns_url, headers=headers)
                
                if dns_response.status_code == 200:
                    dns_data = dns_response.json()
                    if dns_data['success']:
                        record_count = len(dns_data['result'])
                        print(f"✅ Acceso a registros DNS exitoso! Se encontraron {record_count} registros.")
                        
                        # Mostrar los primeros 5 registros
                        print("\nPrimeros registros encontrados:")
                        for i, record in enumerate(dns_data['result'][:5]):
                            print(f"  {i+1}. {record['name']} ({record['type']}): {record['content']}")
                        
                        return True
                    else:
                        error_messages = ', '.join([error['message'] for error in dns_data['errors']])
                        print(f"❌ Error al acceder a los registros DNS: {error_messages}")
                else:
                    print(f"❌ Error HTTP {dns_response.status_code} al acceder a los registros DNS: {dns_response.text}")
                    
                    # Intentar parsear la respuesta JSON si es posible
                    try:
                        error_data = dns_response.json()
                        if 'errors' in error_data:
                            for error in error_data['errors']:
                                print(f"   - Código: {error.get('code')}, Mensaje: {error.get('message')}")
                    except:
                        pass
            else:
                error_messages = ', '.join([error['message'] for error in data['errors']])
                print(f"❌ Error de la API de Cloudflare: {error_messages}")
        else:
            print(f"❌ Error HTTP {response.status_code}: {response.text}")
            
            # Intentar parsear la respuesta JSON si es posible
            try:
                error_data = response.json()
                if 'errors' in error_data:
                    for error in error_data['errors']:
                        print(f"   - Código: {error.get('code')}, Mensaje: {error.get('message')}")
            except:
                pass
    
    except Exception as e:
        print(f"❌ Error al probar las credenciales: {e}")
    
    return False

if __name__ == "__main__":
    test_cloudflare_credentials()
