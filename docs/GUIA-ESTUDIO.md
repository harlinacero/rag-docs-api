# Guía de estudio

Un plan para entender el proyecto lo bastante bien como para defenderlo en una entrevista. Calcula unas 3 o 4 horas.

## 1. Orden de lectura

Lee de abajo hacia arriba: primero las piezas sin dependencias y al final la API.

| # | Archivo | Qué buscar | Prueba que lo acompaña |
| --- | --- | --- | --- |
| 1 | `app/chunking.py` | Cómo se calcula `step` y cuándo termina el ciclo | `tests/test_chunking.py` |
| 2 | `app/embeddings.py` | Por qué `md5` y por qué normalizar | (indirecta, en `test_rag.py`) |
| 3 | `app/vector_store.py` | Por qué la búsqueda es un producto de matrices | `tests/test_vector_store.py` |
| 4 | `app/llm.py` | El `SYSTEM_PROMPT`, línea por línea | (sin prueba: necesita red) |
| 5 | `app/rag.py` | El guardrail de `ask` | `tests/test_rag.py` |
| 6 | `app/config.py` y `app/main.py` | `lru_cache`, `Depends`, modelos Pydantic | `tests/test_api.py` |

Después de cada archivo, lee su prueba y córrela sola con `python -m pytest tests/<archivo>.py -v`.

Usa [ARQUITECTURA.md](ARQUITECTURA.md) para los diagramas de secuencia. Recorrer un flujo con el depurador ayuda mucho: ver [GUIA-DEPURACION.md](GUIA-DEPURACION.md).

## 2. Ejercicios para comprobar que entiendes

Haz cada uno, observa el resultado y deshaz el cambio (`git checkout -- .` cuando el repo esté en git).

1. **Chunking a mano.** En una consola de Python:
   ```python
   from app.chunking import chunk_text
   chunk_text(" ".join(f"w{i}" for i in range(10)), chunk_size=4, overlap=1)
   ```
   Predice el resultado antes de ejecutarlo.
2. **Ver las puntuaciones.** Con la API corriendo y los documentos cargados, define `$env:MIN_SCORE="0"`, reinicia y pregunta lo del pastel con `top_k=10`. Verás puntuaciones bajas pero no cero. Así entiendes para qué sirve el umbral.
3. **Romper el guardrail.** En `rag.py`, cambia `if not relevant:` por `if not hits:`. Corre `test_rag.py`: `test_unrelated_question_is_not_answered` debe fallar. Esa prueba es la que protege la regla de IA responsable.
4. **Límite del buscador local.** Pregunta "How long do access token last?" y luego "What is the lifespan of a credential?". La segunda no comparte palabras con el documento; observa la diferencia de puntuación.
5. **Idempotencia.** Carga `jwt` dos veces y comprueba que el número de fragmentos no se duplica (pregunta con `top_k=10`).
6. **Modo OpenAI.** Repite el ejercicio 4 con `EMBEDDER=openai`. Si la segunda pregunta ahora sí encuentra el documento, viste la diferencia entre palabras y significado.

## 3. Preguntas probables de entrevista

**¿Qué es RAG y por qué no mandar todos los documentos al LLM?**
El contexto del modelo es limitado y cada token cuesta. Además, con menos texto irrelevante el modelo se confunde menos. RAG recupera solo los fragmentos útiles y obliga a responder con ellos, lo que también permite citar fuentes.

**¿Por qué fragmentos con solapamiento?**
Los embeddings funcionan mejor con textos cortos y enfocados. El solapamiento evita que una idea partida en el borde se pierda. El costo es guardar algo de texto repetido.

**¿Por qué 120 palabras?**
Es un punto de partida, no un valor medido. Fragmentos grandes traen más ruido; pequeños pierden contexto. Lo correcto es ajustarlo con un conjunto de evaluación (siguiente paso del README).

**¿Cómo funciona la búsqueda?**
Todos los vectores están normalizados, así que la similitud coseno es un producto punto. Un solo producto matriz-vector da todas las puntuaciones. Es búsqueda exacta, O(N); para millones de vectores usaría pgvector con un índice HNSW.

**¿Qué pasa si no hay información para responder?**
Si ningún fragmento supera `MIN_SCORE`, el servicio responde "I don't know" y no llama al LLM. Se ahorra costo y se evita una respuesta inventada. Hay una prueba que lo cubre.

**¿`grounded=true` garantiza que no hay alucinación?**
No. Solo indica que hubo contexto relevante. El LLM podría añadir algo que no está en las fuentes. Para medirlo haría falta verificar la respuesta contra las fuentes (por ejemplo, con un segundo modelo como juez o comprobando las citas).

**¿Cómo te defiendes de prompt injection?**
El system prompt pide tratar el contexto como datos y el contexto va en el mensaje del usuario, separado. Es una defensa básica, no completa. Además, solo quien carga documentos puede inyectar, y hoy no hay autenticación: ese es el riesgo real.

**¿Por qué `md5` si es inseguro?**
No se usa para seguridad, solo para repartir palabras de forma estable. `hash()` de Python cambia entre ejecuciones y rompería la reproducibilidad.

**¿Cómo probaste sin red?**
Con interfaces (`Protocol`) e implementaciones offline. El `RagService` recibe sus dependencias por constructor, y la API usa `Depends`, que las pruebas sustituyen con `dependency_overrides`.

**¿Qué falta para producción?**
Almacén persistente (pgvector), autenticación y aislamiento por usuario, límites de uso, evaluación de calidad, logs sin datos personales, endpoints asíncronos y manejo de errores del proveedor (reintentos, timeouts).

**¿Qué cambiarías primero?**
Un conjunto de evaluación: sin medir, no sabes si un cambio de `CHUNK_SIZE`, de embedder o de `MIN_SCORE` mejora o empeora.

## 4. Cómo describirlo

En el CV: *Small RAG API (FastAPI, embeddings, grounded answers with source citations).* Es un proyecto personal, no experiencia en producción.

En 30 segundos: "Es una API en FastAPI que responde preguntas solo con documentos que le cargas. Divide los documentos en fragmentos, los convierte en embeddings y busca por similitud coseno. Si nada supera un umbral, responde que no sabe sin llamar al modelo. Cada respuesta trae sus fuentes. Funciona offline para las pruebas y con OpenAI cambiando dos variables."
