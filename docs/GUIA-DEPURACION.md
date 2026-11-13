# Guía de depuración en Python

Si sabes depurar Java, C# o TypeScript, ya sabes depurar Python. Los conceptos son los mismos: puntos de interrupción, paso a paso, variables y pila de llamadas. Lo que cambia son las herramientas.

## 1. Lo que cambia respecto a Java o C#

| Java / C# / TypeScript | Python |
| --- | --- |
| Compilas y luego depuras el binario o el bundle | No hay compilación: el depurador ejecuta el `.py` directamente. Guardas y vuelves a lanzar. |
| Depurador del IDE (JDWP, vsdbg) o DevTools | **debugpy** en VS Code (equivalente al IDE) y **pdb** en la terminal (viene con Python) |
| `debugger;` en JavaScript | `breakpoint()`: una función de Python que detiene la ejecución en esa línea |
| Source maps en TypeScript | No hacen falta: lo que ejecutas es lo que escribiste |
| Errores de tipos al compilar | Aparecen al ejecutar. Por eso el depurador y las pruebas pesan más. |

Lo más útil de Python: estando detenido puedes **ejecutar cualquier expresión** con las variables de ese momento, como en la consola de DevTools.

## 2. Opción A: VS Code (la más parecida a lo que conoces)

El proyecto ya trae `.vscode/launch.json` y `.vscode/settings.json`. Abre la carpeta **en VS Code**: las extensiones de Python y debugpy están instaladas ahí, no en Cursor.

1. Abre `C:\git\rag-docs-api` en VS Code.
2. Si te pide intérprete, elige `.venv` (`Ctrl+Shift+P` → *Python: Select Interpreter*). `settings.json` ya lo apunta.
3. Abre la vista **Run and Debug** (`Ctrl+Shift+D`) y elige una configuración:

| Configuración | Para qué |
| --- | --- |
| **API (uvicorn)** | Levanta la API con el depurador. Llamas desde Swagger y se detiene en tus breakpoints. |
| **Pytest: archivo actual** | Depura las pruebas del archivo de prueba que tengas abierto. |
| **Script: archivo actual** | Depura cualquier script suelto que tengas abierto. |

Teclas, iguales que en Visual Studio:

| Tecla | Acción |
| --- | --- |
| `F9` | Poner o quitar un breakpoint |
| `F5` | Iniciar o continuar |
| `F10` | Siguiente línea (step over) |
| `F11` | Entrar en la función (step into) |
| `Shift+F11` | Salir de la función (step out) |
| `Shift+F5` | Detener |

Paneles útiles: **Variables**, **Watch**, **Call Stack** y la **Debug Console**, donde escribes expresiones de Python con las variables del momento.

Otra forma con pruebas: en la vista **Testing** (el ícono del matraz) cada prueba tiene un botón para depurarla.

> La configuración de la API no usa `--reload` a propósito. `--reload` ejecuta tu código en un proceso hijo, y eso complica el depurador. Después de cambiar código, detén (`Shift+F5`) y vuelve a lanzar (`F5`).

### Ejercicio 1: ver por qué responde "I don't know"

1. En `app/rag.py`, pon un breakpoint (`F9`) en la línea `relevant = [h for h in hits if h.score >= self.min_score]`.
2. Lanza **API (uvicorn)** con `F5`.
3. En http://127.0.0.1:8000/docs, carga un documento con `POST /documents` y pregunta "What is the best recipe for chocolate cake?" en `POST /ask`.
4. VS Code se detiene. En **Variables** abre `hits`. En la **Debug Console** escribe:
   ```python
   [round(h.score, 3) for h in hits]
   self.min_score
   ```
5. Pulsa `F10` dos veces: verás que entra en el `if not relevant:` y nunca llega al generador.
6. Prueba con "How long should access tokens live?" y pulsa `F11` en la línea del `generate` para entrar en `llm.py`.

### Ejercicio 2: depurar una prueba

1. Abre `tests/test_rag.py` y pon un breakpoint en la primera línea de `test_finds_the_right_document`.
2. Elige **Pytest: archivo actual** y pulsa `F5`.
3. Pulsa `F11` para entrar en `service.ask(...)`. Revisa el **Call Stack**: verás pytest abajo y tu código arriba.

## 3. Opción B: pdb en la terminal

`pdb` viene con Python y funciona en cualquier lugar: en un servidor, en Docker o por SSH. Vale la pena conocerlo aunque uses VS Code.

### Tres formas de entrar

```powershell
# 1. Escribe breakpoint() en el código, en la línea donde quieras detenerte, y ejecuta normal
python mi_script.py

# 2. Detenerse justo donde falla una prueba
python -m pytest --pdb tests/test_rag.py

# 3. Detenerse al inicio de una prueba concreta
python -m pytest --trace tests/test_rag.py::test_unrelated_question_is_not_answered
```

### Comandos

| Comando | Qué hace | En VS Code |
| --- | --- | --- |
| `n` | Siguiente línea | `F10` |
| `s` | Entrar en la función | `F11` |
| `r` | Seguir hasta que la función retorne | `Shift+F11` |
| `c` | Continuar hasta el siguiente breakpoint | `F5` |
| `ll` | Ver la función actual completa | (el editor) |
| `p expr` / `pp expr` | Imprimir una expresión (`pp` la formatea) | Debug Console |
| `w` | Pila de llamadas | Call Stack |
| `u` / `d` | Subir o bajar en la pila | clic en Call Stack |
| `b archivo:línea` | Poner un breakpoint | `F9` |
| `interact` | Abrir una consola de Python con las variables actuales (`Ctrl+Z` y Enter para salir) | Debug Console |
| `q` | Salir | `Shift+F5` |

Ojo: si tienes una variable llamada `n`, `c` o `p`, escribe `p n` para verla, porque `n` solo avanza una línea.

### Sesión real con este proyecto

Script de prueba (guárdalo en `scratch/explorar.py`; la carpeta `scratch/` está en `.gitignore`):

```python
from pathlib import Path
from app.embeddings import HashingEmbedder
from app.llm import ExtractiveGenerator
from app.rag import RagService

svc = RagService(HashingEmbedder(), ExtractiveGenerator())
for path in sorted(Path("data").glob("*.md")):
    svc.ingest(path.stem, path.read_text(encoding="utf-8"))
breakpoint()
result = svc.ask("What is the best recipe for chocolate cake?", top_k=3)
print(result.grounded)
```

Ejecútalo desde la raíz del repositorio. `PYTHONPATH` hace que Python encuentre el paquete `app`:

```powershell
$env:PYTHONPATH = "."
python scratch\explorar.py
```

Salida real (lo que escribí va después de `(Pdb)`):

```text
> scratch\explorar.py(10)<module>()
-> result = svc.ask("What is the best recipe for chocolate cake?", top_k=3)
(Pdb) s
--Call--
> c:\git\rag-docs-api\app\rag.py(50)ask()
(Pdb) n
> c:\git\rag-docs-api\app\rag.py(51)ask()
-> query_vector = self.embedder.embed([question])[0]
(Pdb) n
(Pdb) n
> c:\git\rag-docs-api\app\rag.py(53)ask()
-> relevant = [h for h in hits if h.score >= self.min_score]
(Pdb) p [round(h.score, 3) for h in hits]
[0.082, 0.0, 0.0]
(Pdb) p self.min_score
0.15
(Pdb) c
False
```

Ahí ves el guardrail con números: el mejor fragmento puntúa 0.082, el umbral es 0.15, así que no hay contexto y la respuesta es `grounded=False`.

## 4. Herramientas que complementan al depurador

- **Leer el traceback de abajo hacia arriba.** La última línea dice el error; la línea anterior, dónde ocurrió. Las de más arriba son quién llamó a quién.
- **La consola interactiva.** `python` (o `python -i script.py`, que ejecuta el script y deja la consola abierta). Importas una función y la pruebas sola, sin levantar la API:
  ```python
  >>> from app.chunking import chunk_text
  >>> chunk_text("a b c d e f", chunk_size=4, overlap=1)
  ['a b c d', 'd e f']
  ```
- **`pytest -x -vv`**: se detiene en la primera prueba que falla y muestra la comparación completa. `-k palabra` corre solo las pruebas cuyo nombre contiene esa palabra.
- **`print` está bien para empezar**, pero el depurador te deja ver todo el estado sin editar y reejecutar.

## 5. Problemas comunes

| Síntoma | Causa | Solución |
| --- | --- | --- |
| El breakpoint queda gris o no se detiene | VS Code usa otro intérprete | Elige `.venv` en *Python: Select Interpreter* |
| No se detiene en librerías (FastAPI, NumPy) | `justMyCode: true` | Cámbialo a `false` en `launch.json` si quieres entrar en código ajeno |
| `ModuleNotFoundError: No module named 'app'` | Ejecutas desde otra carpeta | Ejecuta desde la raíz o define `PYTHONPATH` |
| `Address already in use` en el puerto 8000 | Ya hay otra API corriendo | Detén la otra o cambia `--port` en `launch.json` |
| Olvidaste un `breakpoint()` y la API se queda colgada | pdb espera tu entrada en la terminal | Quita el `breakpoint()` antes de subir el código |
