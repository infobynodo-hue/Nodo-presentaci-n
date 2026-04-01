Genera y despliega una propuesta comercial personalizada de NODO One para un nuevo cliente.

## Uso
/nueva-propuesta "Nombre del Cliente" https://url-del-cliente.com

## Argumentos
$ARGUMENTS

## Instrucciones paso a paso

Ejecuta cada paso en orden. Si alguno falla, informa al usuario y detente.

### Paso 1 — Extraer datos del cliente y personalizar el HTML

Ejecuta el script de generación con el nombre y URL proporcionados. Crea el output en /tmp/propuesta-{slug} donde {slug} es el nombre en minúsculas con guiones:

```bash
python3 scripts/generar_propuesta.py --nombre "NOMBRE_CLIENTE" --url "URL_CLIENTE" --output-dir /tmp/propuesta-SLUG
```

Reemplaza NOMBRE_CLIENTE, URL_CLIENTE y SLUG con los valores del usuario. El script imprimirá el JSON con los datos extraídos. Muéstrale al usuario un resumen de lo que se encontró: nombre, ciudad, sector, horario.

### Paso 2 — Verificar la personalización

Lee el archivo `/tmp/propuesta-SLUG/public/index.html` y confirma que contiene el nombre del cliente en el título y en el demo del chat.

### Paso 3 — Crear repositorio en GitHub

Desde el directorio del proyecto personalizado, inicializa git y crea el repo:

```bash
cd /tmp/propuesta-SLUG && git init && git add . && git commit -m "Propuesta NODO One · NOMBRE_CLIENTE"
gh repo create infobynodo-hue/nodo-propuesta-SLUG --public --source=. --push
```

### Paso 4 — Desplegar en Vercel

Desde el mismo directorio, despliega en Vercel con el nombre del proyecto:

```bash
cd /tmp/propuesta-SLUG && vercel --yes --prod --name nodo-propuesta-SLUG
```

El comando devuelve la URL de producción. Captúrala.

### Paso 5 — Resultado final

Muéstrale al usuario:
- El nombre del cliente y datos extraídos
- El link del repo en GitHub: `https://github.com/infobynodo-hue/nodo-propuesta-SLUG`
- El link en vivo de Vercel (la URL que devolvió el deploy)
- Instrucción: "Copia el link de Vercel y envíaselo directamente al cliente."
