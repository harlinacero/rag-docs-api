# Guía de ejecución (Windows)

Cómo instalar, probar y usar Ask My Docs en tu máquina. Todos los comandos se probaron en Windows 11 con PowerShell 5.1.

## 1. Requisitos

| Necesitas | Por qué |
| --- | --- |
| **Python 3.12** | Es la versión de CI y del Dockerfile. **No uses 3.15**: `pip` intenta compilar `pyyaml` (dependencia de `uvicorn[standard]`) porque aún no hay binarios para 3.15, y falla con `Unable to find a compatible Visual Studio installation`. |
| `uv` (recomendado) o el instalador de python.org | `uv` descarga Python 3.12 sin tocar tu instalación global. Ya lo tienes instalado. |
| Docker Desktop (opcional) | Solo si quieres correr el contenedor. |
| Una API key de OpenAI (opcional) | Solo para el modo con embeddings reales y un LLM. |

## 2. Instalar

Desde la raíz del repositorio (`C:\git\rag-docs-api`):

```powershell
uv venv --python 3.12 .venv
uv pip install --python .venv\Scripts\python.exe -r requirements-dev.txt
.\.venv\Scripts\Activate.ps1
```

Si PowerShell bloquea `Activate.ps1`, ejecuta una vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, o no actives el entorno y antepón `.\.venv\Scripts\python.exe -m` a cada comando.

Sin `uv`, instala Python 3.12 desde python.org y usa `py -3.12 -m venv .venv` y `pip install -r requirements-dev.txt`.

## 3. Correr las pruebas

```powershell
python -m pytest -q
```

Resultado esperado:

```
20 passed, 1 warning
```

El warning (`Using httpx with starlette.testclient is deprecated`) viene de una versión nueva de Starlette, no de tu código. No rompe nada.

| Archivo | Qué prueba | Necesita red |
| --- | --- | --- |
| `tests/test_chunking.py` | Cortes, solapamiento, parámetros inválidos | No |
| `tests/test_vector_store.py` | Orden por similitud, borrado, guardar/cargar | No |
| `tests/test_rag.py` | Flujo completo con los documentos de `data/` | No |
| `tests/test_api.py` | Endpoints HTTP, códigos 201/200/422 | No |

Para correr una sola prueba: `python -m pytest tests/test_rag.py::test_unrelated_question_is_not_answered -v`.

## 4. Levantar la API

```powershell
python -m uvicorn app.main:app --reload
```

- Swagger (interfaz para probar): http://127.0.0.1:8000/docs
- Salud: http://127.0.0.1:8000/health

> **Importante:** el almacén vive en memoria. La API arranca **vacía** (no lee `data/` sola) y con `--reload` se vacía cada vez que guardas un archivo. Si `/ask` responde "I don't know" a todo, primero revisa que hayas cargado documentos.

## 5. Cargar documentos y preguntar

### PowerShell

```powershell
$base = "http://127.0.0.1:8000"

# Cargar los documentos de ejemplo
foreach ($f in Get-ChildItem data\*.md) {
  $body = @{ doc_id = $f.BaseName; text = [IO.File]::ReadAllText($f.FullName) } | ConvertTo-Json
  Invoke-RestMethod -Method Post "$base/documents" -ContentType "application/json" -Body $body
}

# Preguntar
$q = @{ question = "How long should access tokens live?"; top_k = 3 } | ConvertTo-Json
Invoke-RestMethod -Method Post "$base/ask" -ContentType "application/json" -Body $q | ConvertTo-Json -Depth 5
```

> Usa `[IO.File]::ReadAllText(...)` y no `Get-Content -Raw`. En PowerShell 5.1, `Get-Content` añade propiedades ocultas (`PSPath`, etc.) y `ConvertTo-Json` envía un objeto en lugar de un texto. La API responde `422 Input should be a valid string`.

El ejemplo con `curl` del README es para bash (Git Bash, WSL, macOS o Linux).

### Respuestas reales (modo offline)

```text
POST /documents jwt   -> {"doc_id":"jwt","chunks":2}
POST /documents oauth -> {"doc_id":"oauth","chunks":1}
```

`jwt.md` tiene 124 palabras. Con `CHUNK_SIZE=120` y `CHUNK_OVERLAP=20` salen dos fragmentos: palabras 0–119 y 100–123.

```json
// "How long should access tokens live?"
{
  "answer": "Access tokens should be short lived, typically between five and fifteen minutes. ... [jwt#0]",
  "grounded": true,
  "sources": [{ "doc_id": "jwt", "chunk_index": 0, "score": 0.2931, "text": "..." }]
}

// "What is the best recipe for chocolate cake?"
{ "answer": "I don't know based on the provided documents.", "grounded": false, "sources": [] }
```

Aunque pediste `top_k` > 1, solo vuelve una fuente: el otro fragmento quedó por debajo de `MIN_SCORE` (0.15) y se descartó. `top_k` es un máximo, no una cantidad garantizada.

## 6. Docker

```powershell
docker build -t ask-my-docs .
docker run --rm -p 8000:8000 ask-my-docs
```

La imagen solo copia `app/`; ni `data/` ni `tests/`. Carga los documentos por la API como en el paso 5.

Para el modo OpenAI dentro del contenedor, instala `requirements-openai.txt` en el Dockerfile y pasa las variables con `-e OPENAI_API_KEY=... -e EMBEDDER=openai -e GENERATOR=openai`.

## 7. Modo OpenAI

```powershell
uv pip install --python .venv\Scripts\python.exe -r requirements-openai.txt
$env:OPENAI_API_KEY = "sk-..."
$env:EMBEDDER = "openai"
$env:GENERATOR = "openai"
$env:MIN_SCORE = "0.30"
python -m uvicorn app.main:app
```

Las variables con `$env:` solo duran en esa ventana de PowerShell. No guardes la key en el repo; `.env` ya está en `.gitignore`, pero el código no lo lee solo.

### Cómo ajustar `MIN_SCORE`

Las puntuaciones del buscador local (0.2–0.3 en los ejemplos) y las de OpenAI no se pueden comparar. Para elegir el umbral:

1. Carga los documentos y haz unas 5 preguntas que **sí** tengan respuesta y 5 que **no** (como la del pastel).
2. Usa `top_k=10` y `MIN_SCORE=0` para ver todas las puntuaciones.
3. Elige un valor entre la puntuación más baja de las buenas y la más alta de las malas.
4. Anota los números. Te sirven para la entrevista y son el inicio del conjunto de evaluación del README.

## 8. Problemas comunes

| Síntoma | Causa | Solución |
| --- | --- | --- |
| `Failed building wheel for pyyaml` | Python 3.15 | Usa Python 3.12 (paso 2) |
| `No module named pytest` | La instalación falló o el entorno no está activo | Revisa el paso 2 |
| `/ask` siempre dice "I don't know" | Almacén vacío (reinicio o `--reload`) | Vuelve a cargar los documentos |
| `422` al cargar un documento | `Get-Content` en PowerShell 5.1 | Usa `[IO.File]::ReadAllText` |
| `422` en `/ask` | Pregunta vacía, más de 1000 caracteres o `top_k` fuera de 1–10 | Corrige el cuerpo de la petición |
| `openai.AuthenticationError` | Falta `OPENAI_API_KEY` | Defínela en la misma ventana |
