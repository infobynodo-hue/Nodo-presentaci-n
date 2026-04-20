#!/usr/bin/env python3
"""
NODO One — Generador de propuestas personalizadas
Uso: python3 scripts/generar_propuesta.py --nombre "Clínica Dental Norte" --url "https://ejemplo.com" --output-dir /tmp/propuesta-slug
"""
import argparse
import json
import os
import re
import shutil
import sys
import urllib.request
import urllib.error
from html.parser import HTMLParser


# ── Extractor de texto de HTML ──────────────────────────────
class TextExtractor(HTMLParser):
    SKIP = {'script', 'style', 'nav', 'footer', 'head', 'noscript', 'svg', 'iframe'}

    def __init__(self):
        super().__init__()
        self.chunks = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self._skip += 1

    def handle_endtag(self, tag):
        if tag in self.SKIP and self._skip > 0:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip:
            t = data.strip()
            if len(t) > 3:
                self.chunks.append(t)

    def result(self):
        return ' '.join(self.chunks)


# ── Fetch website ────────────────────────────────────────────
def fetch_website(url):
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            p = TextExtractor()
            p.feed(html)
            return p.result()[:5000]
    except Exception as e:
        return f"No se pudo acceder: {e}"


# ── Carga API key ────────────────────────────────────────────
def get_api_key():
    key = os.environ.get('ANTHROPIC_KEY') or os.environ.get('ANTHROPIC_API_KEY', '')
    if not key:
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
        if os.path.exists(env_path):
            for line in open(env_path):
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    k, v = line.split('=', 1)
                    if k.strip() in ('ANTHROPIC_KEY', 'ANTHROPIC_API_KEY'):
                        key = v.strip()
                        break
    if not key:
        print('ERROR: No se encontró ANTHROPIC_KEY en entorno ni en .env', file=sys.stderr)
        sys.exit(1)
    return key


# ── Llama a Claude para extraer info ────────────────────────
def call_claude(web_content, nombre, url, api_key):
    prompt = f"""Analiza la siguiente información de un negocio y genera datos para personalizar una propuesta comercial de NODO One (empresa de BPO Digital con agentes de IA para WhatsApp).

NOMBRE DEL CLIENTE: {nombre}
URL: {url}
CONTENIDO WEB:
{web_content}

Responde ÚNICAMENTE con un JSON válido, sin explicaciones, con esta estructura exacta:
{{
  "nombre": "nombre completo del negocio",
  "nombre_corto": "nombre corto (máx 22 caracteres)",
  "ciudad": "Ciudad, País",
  "emoji": "1 emoji representativo del sector",
  "sector": "sector del negocio en 2-3 palabras",
  "horario": "horario en texto natural (ej: lunes a viernes 9am a 6pm)",
  "telefono": "teléfono si está disponible, sino cadena vacía",
  "saludo_inicial": "mensaje de bienvenida del agente Claudia en 1 oración tipo WhatsApp, menciona el nombre del negocio con un emoji al final",
  "sugerencias": [
    "texto corto del botón sugerencia 1 (máx 28 chars)",
    "texto corto del botón sugerencia 2 (máx 28 chars)",
    "texto corto del botón sugerencia 3 (máx 28 chars)"
  ],
  "sugerencias_full": [
    "pregunta completa que el usuario enviaría en el chat 1",
    "pregunta completa que el usuario enviaría en el chat 2",
    "pregunta completa que el usuario enviaría en el chat 3"
  ],
  "sidebar_items": [
    "servicio o dato clave 1",
    "servicio o dato clave 2",
    "servicio o dato clave 3",
    "horario resumido"
  ],
  "sys_prompt": "INSTRUCCIONES: genera el prompt completo siguiendo EXACTAMENTE esta estructura (sustituye los corchetes con datos reales del negocio):\\n\\nEres Claudia, asistente de [NOMBRE NEGOCIO] en [CIUDAD]. Escribes exactamente como una persona real en WhatsApp: natural, cálida, directa. Sin asteriscos, sin listas, sin guiones, sin markdown de ningún tipo.\\n\\nSERVICIOS Y PRECIOS: [lista servicios principales con precios si están disponibles, en lenguaje natural]\\n\\nHORARIO: [horario de atención y dirección si disponible. Indica si solo es atención presencial o también online.]\\n\\nFLUJO DE ATENCIÓN — sigue este proceso natural:\\n1. Si preguntan por un servicio o precio: responde con la info + haz una pregunta para entender mejor su necesidad (para quién es, cuándo, qué busca exactamente).\\n2. Si el cliente muestra interés o hace más preguntas: profundiza y guíale hacia el siguiente paso lógico de este negocio.\\n3. Para agendar, reservar o visitar: pide solo el mínimo necesario — nombre y disponibilidad. En el siguiente mensaje confirma.\\n4. Si el cliente ya dio nombre y disponibilidad: confirma el agendamiento/reserva y di que recibirán confirmación.\\n5. Si preguntan algo fuera del negocio o del sector: explica con amabilidad qué sí puedes hacer y ofrece ayudar con eso.\\n\\nREGLAS IMPORTANTES:\\n- Máximo 2-3 oraciones por mensaje, como WhatsApp real\\n- Sin asteriscos, sin guiones de lista ni ningún formato especial\\n- Si el cliente da info vaga, haz una sola pregunta concreta para avanzar\\n- Siempre termina con el siguiente paso claro: una pregunta, una sugerencia o una confirmación"
}}

Si no encuentras información suficiente en la web, genera datos plausibles y coherentes con el nombre y sector del negocio."""

    payload = json.dumps({
        'model': 'claude-haiku-4-5-20251001',
        'max_tokens': 2400,
        'messages': [{'role': 'user', 'content': prompt}]
    }).encode('utf-8')

    req = urllib.request.Request(
        'https://api.anthropic.com/v1/messages',
        data=payload,
        headers={
            'Content-Type': 'application/json',
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01'
        },
        method='POST'
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode('utf-8'))
        text = result['content'][0]['text']
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise ValueError(f'No se encontró JSON en respuesta:\n{text}')


# ── Slugifica un nombre ──────────────────────────────────────
def slugify(text):
    replacements = {'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
                    'à': 'a', 'è': 'e', 'ì': 'i', 'ò': 'o', 'ù': 'u',
                    'ä': 'a', 'ë': 'e', 'ï': 'i', 'ö': 'o', 'ü': 'u',
                    'ñ': 'n', 'ç': 'c'}
    text = text.lower()
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')[:40]


# ── Personaliza el HTML ──────────────────────────────────────
def personalizar_html(html, d):
    nombre       = d['nombre']
    nombre_corto = d['nombre_corto']
    ciudad       = d['ciudad']
    emoji        = d['emoji']
    saludo       = d['saludo_inicial']
    sugs         = d['sugerencias']
    sugs_full    = d['sugerencias_full']
    sidebar      = d['sidebar_items']
    sys_prompt   = d['sys_prompt']

    # 1 · Título de la página
    html = html.replace(
        'NODO One · BPO Digital — Propuesta Comercial',
        f'NODO One · {nombre_corto} — Propuesta Comercial'
    )

    # 2 · Modal: título personalizado
    html = html.replace(
        'Propuesta para hacer que<br>tu negocio <em>responda y venda 24/7</em>',
        f'Propuesta para {nombre}<br><em>para atender, responder y vender 24/7 sin depender de personas</em>'
    )

    # 3 · Tab del demo: emoji + nombre
    html = html.replace(
        '<button class="dtab active" data-agent="clinica" onclick="switchAgent(\'clinica\')"><span>🦷</span> Clínica Palacios · Bogotá</button>',
        f'<button class="dtab active" data-agent="clinica" onclick="switchAgent(\'clinica\')"><span>{emoji}</span> {nombre_corto} · {ciudad}</button>'
    )

    # 4 · Avatar del chat
    html = html.replace(
        '<div class="chat-av">🦷</div>\n          <div><div class="chat-aname">Claudia</div><div class="chat-arole">Clínica Palacios · Bogotá</div></div>',
        f'<div class="chat-av">{emoji}</div>\n          <div><div class="chat-aname">Claudia</div><div class="chat-arole">{nombre_corto} · {ciudad}</div></div>'
    )

    # 5 · Mensaje inicial del chat
    html = html.replace(
        '¡Hola! Soy Claudia, de Clínica Palacios 😊 cuéntame, ¿en qué te puedo ayudar?',
        saludo
    )

    # 6 · Sugerencias del chat
    old_suggs = (
        '              <div class="sugg" onclick="useSugg(\'clinica\',\'¿Cuánto cuesta una limpieza dental?\')">¿Cuánto cuesta la limpieza?</div>\n'
        '              <div class="sugg" onclick="useSugg(\'clinica\',\'Quiero agendar una cita para mañana\')">Agendar cita</div>\n'
        '              <div class="sugg" onclick="useSugg(\'clinica\',\'¿Tienen ortodoncia y blanqueamiento?\')">Ortodoncia y blanqueamiento</div>'
    )
    new_suggs = (
        f'              <div class="sugg" onclick="useSugg(\'clinica\',\'{sugs_full[0]}\')">{sugs[0]}</div>\n'
        f'              <div class="sugg" onclick="useSugg(\'clinica\',\'{sugs_full[1]}\')">{sugs[1]}</div>\n'
        f'              <div class="sugg" onclick="useSugg(\'clinica\',\'{sugs_full[2]}\')">{sugs[2]}</div>'
    )
    html = html.replace(old_suggs, new_suggs)

    # 7 · Sidebar card del cliente (con clase lg)
    old_sidebar = (
        '        <div id="si-clinica">\n'
        '          <div class="dscard lg"><div class="dscard-t">🦷 Clínica Palacios</div>\n'
        '            <div class="dscard-i">Bogotá, Colombia</div>\n'
        '            <div class="dscard-i">Limpiezas · Blanqueamiento</div>\n'
        '            <div class="dscard-i">Ortodoncia metálica e invisible</div>\n'
        '            <div class="dscard-i">Implantes · Carillas · Conductos</div>\n'
        '            <div class="dscard-i">Lun–Vie 8am–6pm · Sáb 8am–2pm</div>\n'
        '          </div>\n'
        '        </div>'
    )
    new_sidebar_items = '\n'.join(
        f'            <div class="dscard-i">{item}</div>' for item in sidebar
    )
    new_sidebar = (
        f'        <div id="si-clinica">\n'
        f'          <div class="dscard lg"><div class="dscard-t">{emoji} {nombre}</div>\n'
        f'            <div class="dscard-i">{ciudad}</div>\n'
        f'{new_sidebar_items}\n'
        f'          </div>\n'
        f'        </div>'
    )
    html = html.replace(old_sidebar, new_sidebar)

    # 8 · System prompt del agente — reemplazo robusto sin regex
    start_marker = "  clinica: {\n    msgs: [],\n    sys: `"
    end_marker   = "`\n  },"
    start_idx = html.find(start_marker)
    if start_idx != -1:
        content_start = start_idx + len(start_marker)
        end_idx = html.find(end_marker, content_start)
        if end_idx != -1:
            html = html[:content_start] + sys_prompt + html[end_idx:]
        else:
            print('⚠  No se encontró el cierre del sys prompt — se omite el reemplazo', file=sys.stderr)
    else:
        print('⚠  No se encontró el bloque clinica sys — se omite el reemplazo', file=sys.stderr)

    # 9 · Eliminar tabs de inmobiliaria y lujo — dejar solo el del cliente
    html = html.replace(
        '\n      <button class="dtab" data-agent="inmobiliaria" onclick="switchAgent(\'inmobiliaria\')"><span>🏠</span> Inmobiliaria Avinguda · Valencia</button>',
        ''
    )
    html = html.replace(
        '\n      <button class="dtab" data-agent="lujo" onclick="switchAgent(\'lujo\')"><span>⛵</span> LuxuriBiz · Ibiza</button>',
        ''
    )

    # 10 · Eliminar paneles de chat de inmobiliaria y lujo
    html = re.sub(
        r'\n\s+<!-- Panel Inmobiliaria -->.*?</div>\n      </div>\n\n      <!-- Panel Lujo -->',
        '\n\n      <!-- Panel Lujo -->',
        html, count=1, flags=re.DOTALL
    )
    html = re.sub(
        r'\n\s+<!-- Panel Lujo -->.*?</div>\n      </div>\n\n      <!-- Sidebar',
        '\n\n      <!-- Sidebar',
        html, count=1, flags=re.DOTALL
    )

    # 11 · Eliminar sidebar items de inmobiliaria y lujo
    html = re.sub(
        r'\n        <div id="si-inmobiliaria".*?</div>\n        </div>',
        '',
        html, count=1, flags=re.DOTALL
    )
    html = re.sub(
        r'\n        <div id="si-lujo".*?</div>\n        </div>',
        '',
        html, count=1, flags=re.DOTALL
    )

    return html


# ── Main ─────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description='Genera propuesta personalizada NODO One')
    parser.add_argument('--nombre', required=True, help='Nombre del cliente')
    parser.add_argument('--url', required=True, help='URL del sitio web del cliente')
    parser.add_argument('--output-dir', default='', help='Directorio de salida (opcional)')
    args = parser.parse_args()

    api_key = get_api_key()

    print(f'🔍  Analizando {args.url}…', file=sys.stderr)
    web_content = fetch_website(args.url)

    print('🤖  Extrayendo información con Claude…', file=sys.stderr)
    data = call_claude(web_content, args.nombre, args.url, api_key)
    data['slug'] = slugify(data.get('nombre_corto', args.nombre))

    # Si se pide output-dir, copiar el proyecto y personalizar
    if args.output_dir:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        out = args.output_dir

        print(f'📁  Creando copia del proyecto en {out}…', file=sys.stderr)
        if os.path.exists(out):
            shutil.rmtree(out)
        shutil.copytree(base_dir, out, ignore=shutil.ignore_patterns(
            '.git', '__pycache__', '*.pyc', '.env', 'node_modules', '.vercel', 'scripts'
        ))

        # Personalizar HTML
        html_path = os.path.join(out, 'public', 'index.html')
        with open(html_path, 'r', encoding='utf-8') as f:
            html = f.read()

        html = personalizar_html(html, data)

        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f'✅  Propuesta personalizada lista en {out}', file=sys.stderr)

    # Siempre imprimir el JSON con los datos
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
