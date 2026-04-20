Genera y despliega una propuesta comercial personalizada de NODO One para un nuevo cliente.

## Uso
/nueva-propuesta "Nombre del Cliente" https://url-del-cliente.com

## Argumentos
$ARGUMENTS

## Instrucciones paso a paso

Ejecuta cada paso en orden. Si alguno falla, informa al usuario y detente.

### Paso 1 — Extraer datos del cliente y personalizar el HTML

Calcula el slug (nombre en minúsculas con guiones, sin acentos, ej: "clinica-dental-norte"). Ejecuta el script desde el directorio del proyecto:

```bash
cd "/Users/santiagorodriguez/Downloads/NODO presentaciones " && python3 scripts/generar_propuesta.py --nombre "NOMBRE_CLIENTE" --url "URL_CLIENTE" --output-dir /tmp/propuesta-SLUG
```

Reemplaza NOMBRE_CLIENTE, URL_CLIENTE y SLUG con los valores del usuario. Muéstrale un resumen: nombre, ciudad, sector, horario.

### Paso 2 — Crear repositorio en GitHub

```bash
cd /tmp/propuesta-SLUG && git init && git add . && git commit -m "Propuesta NODO One · NOMBRE_CLIENTE" && gh repo create infobynodo-hue/nodo-propuesta-SLUG --public --source=. --push
```

### Paso 3 — Desplegar en Vercel

```bash
cd /tmp/propuesta-SLUG && vercel --yes --prod --name nodo-propuesta-SLUG
```

### Paso 4 — Agregar API key y redesplegar

Lee la API key del archivo .env del proyecto base y agrégala al proyecto de Vercel:

```bash
ANTHROPIC_KEY=$(grep ANTHROPIC_KEY "/Users/santiagorodriguez/Downloads/NODO presentaciones /.env" | cut -d= -f2) && echo "$ANTHROPIC_KEY" | vercel env add ANTHROPIC_KEY production --cwd /tmp/propuesta-SLUG && cd /tmp/propuesta-SLUG && vercel --yes --prod
```

Captura la URL de producción final.

### Paso 5 — Resultado final

Muéstrale al usuario:
- El nombre del cliente y datos extraídos
- El link del repo en GitHub: `https://github.com/infobynodo-hue/nodo-propuesta-SLUG`
- El link en vivo de Vercel (la URL que devolvió el deploy)
- Instrucción: "Copia el link de Vercel y envíaselo directamente al cliente."
