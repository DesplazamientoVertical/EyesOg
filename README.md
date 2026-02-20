# Minecraft OG Name Finder (rápido)

Script en Python para probar nombres de Minecraft de 4 letras (o la longitud que quieras) con alta concurrencia.

## Qué detecta

- `TAKEN`: el nombre está en uso actualmente.
- `AVAILABLE_PREVIOUSLY_USED`: el nombre está libre, pero ya se usó alguna vez.
- `AVAILABLE_NEVER_USED`: libre y sin historial (nunca usado según API pública).
- `UNKNOWN_NETWORK`: no se pudo verificar por red/proxy/rate-limit.

## Instalación

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Ejemplos de uso

### 1) Aleatorio ultra-rápido de 4 letras

```bash
python3 mc_og_finder.py --length 4 --mode random --charset lower --max-candidates 2000 --concurrency 200 --out og.csv
```

### 2) Buscar estilo `aaa*`

```bash
python3 mc_og_finder.py --length 4 --mode sequential --charset lower --prefix aaa --max-candidates 26
```

### 3) Probar palabras comunes

```bash
python3 mc_og_finder.py --mode wordlist --length 4 --include-builtin-common-words
```

### 4) Tu propio diccionario

```bash
python3 mc_og_finder.py --mode wordlist --length 4 --wordlist palabras.txt
```

## Consejos de velocidad

- Sube `--concurrency` (ej. 100-300), pero cuidado con rate-limits.
- Usa `--mode random` para encontrar rápido disponibles sin recorrer todo el espacio.
- Si quieres exactitud histórica, deja que el script consulte ambas APIs (ya incluido).

## Nota

La disponibilidad puede cambiar en segundos. Verifica manualmente antes de intentar reclamar un nombre.
