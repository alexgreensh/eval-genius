<p align="center">
  <img src="assets/img/eval-genius.png" alt="Eval Genius, el sabio de la medición envuelto en estrellas" width="280">
</p>

<h1 align="center">Eval Genius</h1>
<p align="center"><strong>Respuestas defendibles sobre tu sistema de IA, en lugar de impresiones.</strong></p>

<p align="center">
  Una skill para cualquier agente de codificación con IA que te dice <em>cuándo</em> necesitas un eval,<br>
  dónde encaja, cómo construirlo y cómo interpretar lo que sale.
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache%202.0-blue" alt="License: Apache 2.0"></a>
  <img src="https://img.shields.io/badge/works%20across-Claude%20Code%20·%20Codex%20·%20Cursor%20·%20any%20agent-8A5CF6" alt="Works across any agent">
  <img src="https://img.shields.io/badge/scripts-stdlib%20Python%20·%20zero%20deps-2ea44f" alt="Stdlib Python, zero dependencies">
</p>

<p align="center">
  <strong>English</strong> · <a href="README.zh-CN.md">简体中文</a> · <a href="README.es.md">Español</a> · <a href="README.ko.md">한국어</a> · <a href="README.ja.md">日本語</a>
</p>

---

### Todo el mundo dice "necesitas evals". Casi nadie dice *cuándo*.

## El problema

<p align="center"><img src="assets/img/problem.png" alt="Eval Genius en una encrucijada de caminos flotantes, sin saber hacia dónde van los evals" width="100%"></p>

Los evals están de repente en todas partes. Cada charla de IA, cada post de lanzamiento, cada hilo de contratación dice que los necesitas. Entonces te sientas a hacerlo de verdad, y empiezan las preguntas.

¿Un ajuste de prompt realmente necesita un eval, o es exagerado? ¿En qué punto del desarrollo entra el primero? ¿Qué es un "eval harness", concretamente, más allá de una carpeta llamada `evals/`? ¿Qué métrica, cuántos ejemplos, un modelo juez realmente cuenta? Y cuando por fin sale un número, ¿34 de 40 está bien? ¿Una mejora de 3 puntos es real, o ruido? ¿O la ejecución simplemente se cayó en silencio y reportó un pass?

Responde esto a ojo y obtienes exactamente lo que tienen la mayoría de equipos: un benchmark en el que nadie confía, una gate que ha estado verde durante un mes porque no evalúa nada, y un número en el README que no sobreviviría a una sola pregunta afilada.

## Conoce a Eval Genius

<p align="center"><img src="assets/img/solution.png" alt="Eval Genius con una brújula y un mapa estelar, pesando resultados en una balanza" width="100%"></p>

Eval Genius es ese juicio que faltaba, empaquetado como una skill que tu agente de IA ejecuta *contigo*. Piensa como un ingeniero de medición: decide qué significa "mejor" antes de mirar, empuja cada comprobación que pueda a código plano, trata un crash como *no medido* en lugar de un pass, y confía en el número al final.

No es un curso que tengas que leer primero. Describes dónde estás, en palabras simples, y da el siguiente paso, ya sea "todavía no necesitas uno" o "aquí está la gate, y aquí por qué esta ejecución no puede confiarse".

Es agnóstico de herramientas y sin dependencias: un `SKILL.md` más unos pocos scripts de Python de librería estándar. Se ejecuta en Claude Code, o cualquier agente que cargue skills, o desde tu terminal por su cuenta.

## Qué puedes preguntarle

<p align="center"><img src="assets/img/ask.png" alt="Eval Genius trabajando de forma práctica, metiendo un mapa estelar en un portátil" width="100%"></p>

Preguntas reales, respondidas desde donde realmente estás:

- *"¿Necesito evals para mi chatbot, o es exagerado ahora mismo?"*
- *"¿Dónde encaja un eval en mi build?"*
- *"Saqué 34 de 40, ¿está bien?"*
- *"¿Esta mejora de 3 puntos es real, o ruido?"*
- *"Calibra mi juez LLM contra algunas etiquetas humanas."*

Sin ritual de configuración, sin vocabulario que tengas que aprender primero. Describe la situación, obtén el siguiente movimiento.

## Qué hace por ti

<p align="center"><img src="assets/img/what-it-does.png" alt="Eval Genius cruzando plataformas flotantes a través de una gate de pass/fail hacia los resultados" width="100%"></p>

Recorre el camino completo, y te encuentra en cualquier punto de él, incluido el inicio:

- **Decide si necesitas un eval**, y qué tipo corresponde a tu etapa, desde el primer prototipo hasta producción.
- **Elige el eval:** qué medir, qué evaluador (código primero, un juez solo donde ninguna aserción funciona), qué métrica, cuántos ejemplos, adoptar un benchmark público o construir el tuyo.
- **Lo construye y lo gatilla:** fixture, runner, scorer, reporter, una barra escrita antes de la ejecución, y una gate de CI que termina en PASS, FAIL, o CANNOT-MEASURE y se niega a comparar ejecuciones incompatibles.
- **Lee el resultado contigo:** contra la barra que escribiste, con límites de ruido, diffs por ítem, y una comprobación de bugs del harness antes de creer cualquier número sorprendente.
- **Lo redacta con honestidad,** con salvedades, niveles, y la regla de comparación declarada en voz alta.
- **Rechaza los atajos** que producen mentiras bonitas: barras movidas después de los hechos, puntuaciones mezcladas, ejecutar-hasta-verde, y jueces que nadie calibró.

## Las partes más fáciles de equivocar, resueltas

<p align="center"><img src="assets/img/scripts.png" alt="Eval Genius en un escritorio con una checklist, una curva de campana y una balanza juez-vs-humano" width="100%"></p>

Tres scripts de librería estándar se incluyen con la skill y se ejecutan de forma independiente:

| Script | Lo que resuelve |
|---|---|
| `check_gate.py` | Compara un cambio contra su baseline por ítem; sale con **0 PASS**, **1 FAIL**, **2 CANNOT-MEASURE**, así un crash nunca puede hacerse pasar por un pass |
| `paired_bootstrap.py` | Pone un intervalo de confianza en la diferencia, así "mejoró" realmente significa algo |
| `judge_agreement.py` | Mide cuánto tu juez LLM coincide con etiquetas humanas, antes de dejarlo calificar nada |

## Instalación

Eval Genius es un plugin de Claude Code. Añade el marketplace una vez y luego instala:

```bash
# in Claude Code
/plugin marketplace add alexgreensh/eval-genius
/plugin install eval-genius@eval-genius
```

¿Prefieres una carpeta de skill normal, o usar otro agente? La skill vive en `skills/eval-genius/` — cópiala donde tu agente busque skills:

```bash
cp -R skills/eval-genius ~/.claude/skills/eval-genius
# Any other agent: point it at skills/eval-genius/SKILL.md
```

Luego háblale en lenguaje plano (*"¿necesito evals para mi chatbot?"*, *"¿este delta es real?"*, *"calibra mi juez"*). Los scripts también se ejecutan por su cuenta:

```bash
python3 skills/eval-genius/scripts/check_gate.py --baseline base.json --treatment treat.json
```

En Windows, usa `py -3` en lugar de `python3` si así es como Python está instalado.

## ¿Curioso sobre el razonamiento?

El método completo detrás de la skill, en un documento en lenguaje claro, está en **[METHODOLOGY.md](METHODOLOGY.md)**. No lo necesitas para usar la skill; está ahí si quieres ver el razonamiento.

---

<div align="center">

Construido por **Alex Greenshpun**. Si te ayuda, una estrella o un compartir ayuda a otros a encontrarlo.

<a href="https://github.com/alexgreensh"><img src="https://img.shields.io/badge/GitHub-alexgreensh-181717?logo=github&logoColor=white" alt="GitHub"></a>
<a href="https://alexgreenshpun.com"><img src="https://img.shields.io/badge/Website-alexgreenshpun.com-8A5CF6" alt="Website"></a>
<a href="https://x.com/alexgreensh"><img src="https://img.shields.io/badge/X-%40alexgreensh-000000?logo=x&logoColor=white" alt="X"></a>

**Licencia:** [Apache 2.0](LICENSE)

</div>
