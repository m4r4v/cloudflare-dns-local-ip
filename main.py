#!/usr/bin/env python3
import requests
import os
import sys
import json
import logging
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno desde el archivo .env
load_dotenv()

def get_current_ip():
    """
    Obtiene la dirección IP pública actual utilizando un servicio externo.
    Se prueban múltiples servicios para mayor robustez.
    """
    ip_services = [
        "https://api.ipify.org?format=json",
        "https://icanhazip.com/",
        "https://ident.me/",
        "http://checkip.amazonaws.com/",
    ]
    
    for url in ip_services:
        try:
            logger.debug(f"Intentando obtener IP desde {url}")
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            
            if "ipify" in url:
                ip = response.json()["ip"]
            else:
                ip = response.text.strip()
                
            logger.debug(f"IP obtenida: {ip}")
            return ip
        except requests.exceptions.RequestException as e:
            logger.warning(f"Error al obtener la IP de {url}: {e}")
            continue
    
    logger.error("No se pudo obtener la IP pública actual desde ningún servicio.")
    sys.exit(1)

def get_cloudflare_config():
    """
    Obtiene la configuración de Cloudflare desde las variables de entorno.
    """
    try:
        # Obtener credenciales y configuración
        api_key = os.getenv("CF_API_KEY")
        api_email = os.getenv("CF_EMAIL")
        zone_id = os.getenv("CF_ZONE_ID")
        dns_record_name = os.getenv("CF_DNS_RECORD_NAME")
        
        # Validar que existan las variables necesarias
        if not api_key:
            raise ValueError("CF_API_KEY no está configurada")
        if not zone_id:
            raise ValueError("CF_ZONE_ID no está configurada")
        if not dns_record_name:
            raise ValueError("CF_DNS_RECORD_NAME no está configurada")
        
        # Configurar los headers para la API de Cloudflare
        headers = {
            'Content-Type': 'application/json',
        }
        
        # Si tenemos email, usamos Global API Key
        if api_email:
            logger.info("Usando Global API Key con email")
            headers['X-Auth-Email'] = api_email
            headers['X-Auth-Key'] = api_key
        else:
            # Si no hay email, usamos API Token
            logger.info("Usando API Token")
            headers['Authorization'] = f'Bearer {api_key}'
        
        return headers, zone_id, dns_record_name
    
    except ValueError as e:
        logger.error(f"Error de configuración: {e}")
        logger.error("Asegúrate de configurar CF_API_KEY, CF_ZONE_ID y CF_DNS_RECORD_NAME en el archivo .env")
        logger.error("Si usas una Global API Key, también configura CF_EMAIL")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error al obtener la configuración de Cloudflare: {e}")
        sys.exit(1)

def list_dns_records(headers, zone_id, record_name=None, record_type='A'):
    """
    Lista todos los registros DNS de la zona especificada.
    Si se proporciona record_name, filtra por ese nombre.
    """
    try:
        url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
        params = {}
        
        if record_name:
            params['name'] = record_name
        if record_type:
            params['type'] = record_type
            
        logger.info(f"Listando registros DNS{' para ' + record_name if record_name else ''} (tipo {record_type})")
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if not data['success']:
            error_messages = ', '.join([error['message'] for error in data['errors']])
            raise Exception(f"Error de la API de Cloudflare: {error_messages}")
        
        records = data['result']
        
        if not records:
            logger.warning(f"No se encontraron registros DNS{' para ' + record_name if record_name else ''}")
            return []
        
        logger.info(f"Se encontraron {len(records)} registros DNS")
        return records
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error de la API de Cloudflare al listar registros DNS: {e}")
        # Mostrar el contenido de la respuesta si está disponible
        if hasattr(e, 'response') and e.response is not None:
            try:
                logger.error(f"Detalles de la respuesta: {e.response.json()}")
            except:
                logger.error(f"Código de respuesta: {e.response.status_code}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error inesperado al listar registros DNS: {e}")
        sys.exit(1)

def update_dns_record(headers, zone_id, record_id, record_name, new_ip, existing_record):
    """
    Actualiza un registro DNS con la nueva dirección IP.
    """
    try:
        # Preservar configuraciones existentes
        dns_record = {
            'name': record_name,
            'type': 'A',
            'content': new_ip,
            'ttl': existing_record.get('ttl', 300),
            'proxied': existing_record.get('proxied', False)
        }
        
        url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record_id}"
        
        logger.info(f"Actualizando registro DNS {record_name} a {new_ip}")
        logger.debug(f"Configuración del registro: {dns_record}")
        
        response = requests.put(url, headers=headers, json=dns_record)
        response.raise_for_status()
        
        data = response.json()
        
        if not data['success']:
            error_messages = ', '.join([error['message'] for error in data['errors']])
            raise Exception(f"Error de la API de Cloudflare: {error_messages}")
        
        logger.info(f"Registro DNS '{record_name}' actualizado exitosamente a la IP: {new_ip}")
        return True
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error de la API de Cloudflare al actualizar el registro DNS: {e}")
        # Mostrar el contenido de la respuesta si está disponible
        if hasattr(e, 'response') and e.response is not None:
            try:
                logger.error(f"Detalles de la respuesta: {e.response.json()}")
            except:
                logger.error(f"Código de respuesta: {e.response.status_code}")
        return False
    except Exception as e:
        logger.error(f"Error inesperado al actualizar el registro DNS: {e}")
        return False

def main():
    logger.info("Iniciando el script de actualización de DNS de Cloudflare...")
    
    # 1. Obtener configuración de Cloudflare
    headers, zone_id, dns_record_name = get_cloudflare_config()
    
    # 2. Obtener la IP pública actual
    current_ip = get_current_ip()
    logger.info(f"IP pública actual detectada: {current_ip}")
    
    # 3. Listar todos los registros DNS para depuración
    logger.info("Listando todos los registros DNS de la zona para depuración")
    all_records = list_dns_records(headers, zone_id)
    
    if not all_records:
        logger.error(f"No se encontraron registros DNS en la zona '{zone_id}'")
        sys.exit(1)
    
    # Mostrar todos los registros para depuración
    for record in all_records:
        logger.info(f"Registro encontrado: {record['name']} (tipo {record['type']}) con contenido: {record['content']}")
    
    # 4. Buscar registros DNS específicos
    dns_records = [r for r in all_records if r['name'] == dns_record_name and r['type'] == 'A']
    
    if not dns_records:
        logger.error(f"No se encontró el registro DNS '{dns_record_name}' de tipo 'A' en la zona '{zone_id}'")
        logger.error("Por favor, asegúrate de que el registro exista en Cloudflare y que CF_DNS_RECORD_NAME sea correcto")
        sys.exit(1)
    
    # 5. Procesar cada registro encontrado
    updated = False
    for record in dns_records:
        record_id = record['id']
        existing_ip = record['content']
        record_name = record['name']
        
        logger.info(f"Registro DNS encontrado: '{record_name}' con IP: {existing_ip}")
        
        # 6. Comparar y actualizar si es necesario
        if current_ip == existing_ip:
            logger.info(f"La IP actual ({current_ip}) coincide con la del registro DNS. No se requiere actualización.")
        else:
            logger.info(f"La IP ha cambiado. Actualizando el registro DNS de {existing_ip} a {current_ip}...")
            success = update_dns_record(headers, zone_id, record_id, record_name, current_ip, record)
            if success:
                updated = True
    
    if updated:
        logger.info("Se actualizaron uno o más registros DNS exitosamente.")
    else:
        logger.info("No se requirió actualización de registros DNS.")
    
    logger.info("Proceso finalizado.")

if __name__ == "__main__":
    main()
