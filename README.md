# Cloudflare DNS Local IP Updater

Este script actualiza automáticamente un registro DNS en Cloudflare con la dirección IP pública actual de tu máquina. Es útil para mantener un dominio apuntando a tu IP dinámica (DDNS).

## Requisitos

- Python 3.6 o superior
- Una cuenta en Cloudflare con un dominio configurado
- Un registro DNS tipo A existente que deseas mantener actualizado

## Instalación

1. Clona este repositorio o descarga los archivos
2. Instala las dependencias:

```bash
pip install -r requirements.txt
```

## Configuración

### 1. Crear un API Token en Cloudflare

El problema actual es que el API Token no tiene permisos suficientes para acceder a los registros DNS. Sigue estos pasos para crear un nuevo token con los permisos correctos:

1. Inicia sesión en tu [dashboard de Cloudflare](https://dash.cloudflare.com/)
2. Ve a "Mi Perfil" > "API Tokens" > "Crear Token"
3. Selecciona "Crear Token Personalizado"
4. Asigna un nombre descriptivo como "DNS Updater"
5. En "Permisos", agrega los siguientes:
   - Zone > Zone > Read
   - Zone > DNS > Edit
6. En "Recursos de Zona", selecciona "Incluir" > "Zonas Específicas" y elige tu dominio
7. Opcionalmente, puedes establecer una fecha de caducidad del token
8. Haz clic en "Continuar para revisar" y luego en "Crear Token"
9. **¡IMPORTANTE!** Copia el token generado, ya que solo se mostrará una vez

### 2. Configurar el archivo .env

Actualiza el archivo `.env` con tus credenciales:

```
# API Token (método de autenticación recomendado)
CF_API_KEY="tu_nuevo_api_token_aquí"

# ID de la zona de Cloudflare
CF_ZONE_ID="tu_zone_id_aquí"

# Nombre del registro DNS a actualizar
CF_DNS_RECORD_NAME="tu_dominio.com"
```

Para encontrar tu Zone ID:
1. Ve al dashboard de Cloudflare
2. Selecciona tu dominio
3. En la página de información general, desplázate hacia abajo hasta "API"
4. Copia el "Zone ID"

## Uso

Ejecuta el script:

```bash
python main.py
```

El script:
1. Obtendrá tu IP pública actual
2. Verificará el registro DNS en Cloudflare
3. Actualizará el registro si la IP ha cambiado

## Automatización

Para mantener tu IP actualizada automáticamente, puedes configurar el script para que se ejecute periódicamente:

### En Linux/Mac (usando cron)

Edita tu crontab:

```bash
crontab -e
```

Agrega una línea para ejecutar el script cada 15 minutos:

```
*/15 * * * * cd /ruta/a/tu/script && python main.py >> /ruta/a/tu/script/dns_updater.log 2>&1
```

### En Windows (usando el Programador de tareas)

1. Abre el Programador de tareas
2. Crea una nueva tarea básica
3. Configúrala para que se ejecute cada 15 minutos
4. Establece la acción como "Iniciar un programa"
5. Programa: `python`
6. Argumentos: `main.py`
7. Iniciar en: `C:\ruta\a\tu\script`

## Solución de problemas

Si encuentras errores de autenticación, verifica:
1. Que el API Token tenga los permisos correctos (Zone:Read y DNS:Edit)
2. Que el Zone ID sea correcto
3. Que el nombre del registro DNS exista en tu zona de Cloudflare

Puedes usar el script `test_credentials.py` para verificar tus credenciales:

```bash
python test_credentials.py
```
