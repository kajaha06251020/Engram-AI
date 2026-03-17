<div align="center">

<img src="https://raw.githubusercontent.com/kajaha06251020/Engram-AI/main/docs/assets/logo.svg" alt="Engram-AI Logo" width="200"/>

# Engram-AI

### Infraestructura de Memoria Basada en Experiencias para Agentes de IA

[![PyPI version](https://img.shields.io/pypi/v/engram-ai?style=flat-square&color=blue)](https://pypi.org/project/engram-ai/)
[![Python](https://img.shields.io/pypi/pyversions/engram-ai?style=flat-square)](https://pypi.org/project/engram-ai/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green?style=flat-square)](../../LICENSE)
[![Tests](https://img.shields.io/github/actions/workflow/status/kajaha06251020/Engram-AI/tests.yml?style=flat-square&label=tests)](https://github.com/kajaha06251020/Engram-AI/actions)
[![codecov](https://img.shields.io/codecov/c/github/kajaha06251020/Engram-AI?style=flat-square)](https://codecov.io/gh/kajaha06251020/Engram-AI)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json&style=flat-square)](https://github.com/astral-sh/ruff)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat-square)](../../CONTRIBUTING.md)
[![GitHub Stars](https://img.shields.io/github/stars/kajaha06251020/Engram-AI?style=flat-square)](https://github.com/kajaha06251020/Engram-AI/stargazers)
[![Discord](https://img.shields.io/badge/Discord-unirse%20al%20chat-7289DA?style=flat-square&logo=discord&logoColor=white)](https://discord.gg/engram-ai)

**[English](../../README.md)** | **[日本語](README_ja.md)** | **[中文](README_zh.md)** | **[한국어](README_ko.md)** | **Español**

---

*La memoria actual de IA almacena texto. Engram-AI crea **cicatrices** — estructuras causales que permiten a los agentes aprender de lo que hicieron y de lo que ocurrió.*

</div>

## ¿Qué es Engram-AI?

La mayoría de los sistemas de memoria para IA funcionan como un **diario** — almacenan hechos en texto: *"El usuario prefiere Python"*, *"La API utiliza REST"*. Pero el aprendizaje real no proviene de memorizar hechos. Proviene de la **experiencia**.

Engram-AI otorga a los agentes de IA **memoria experiencial**. En lugar de almacenar lo que el agente *sabe*, almacena lo que el agente *hizo*, lo que *ocurrió* y si el resultado fue *bueno o malo*:

```
Acción:    Se usó Optional[str] para el campo de respuesta de la API
Contexto:  Diseñando modelo de respuesta de la API REST
Resultado: El usuario lo rechazó — "sin valores nulos en las respuestas"
Valencia:  -0.8 (experiencia negativa)
```

Con el tiempo, estas experiencias se **cristalizan** en habilidades — reglas generalizadas que el agente aprende de los patrones en su propio historial:

```
Habilidad:  "Evitar tipos Optional en modelos de respuesta de API"
Confianza:  0.85
Evidencia:  5 experiencias (3 negativas, 2 positivas)
```

Luego las habilidades **evolucionan** hacia la configuración del agente, haciendo que el agente mejore de forma permanente:

```markdown
<!-- engram-ai:start -->
## Engram-AI: Learned Skills
- Avoid Optional types in API response models (confidence: 0.85)
- Use descriptive variable names in test files (confidence: 0.92)
<!-- engram-ai:end -->
```

## ¿Por qué Engram-AI?

| Característica | Memoria Tradicional (Mem0, etc.) | Engram-AI |
|----------------|----------------------------------|-----------|
| **Qué almacena** | Hechos en texto ("al usuario le gusta X") | Estructuras causales (acción → contexto → resultado) |
| **Cómo aprende** | Recuperación de texto almacenado | Cristalización de patrones a partir de experiencias |
| **Señal de aprendizaje** | Ninguna | Valencia (-1.0 a +1.0) por experiencia |
| **Mejora del agente** | Ajuste manual de prompts | Evolución automática de habilidades hacia la configuración |
| **Modelo de memoria** | Entradas de diario | Engramas neurales (cicatrices de la experiencia) |

## Inicio Rápido

### Instalación

```bash
pip install engram-ai
```

### Como Biblioteca de Python

```python
from engram_ai import Forge

forge = Forge()

# Record an experience
forge.record(
    action="Used list comprehension for data transform",
    context="Processing CSV with 10k rows",
    outcome="Fast and readable, user approved",
    valence=0.9,
)

# Query past experiences
result = forge.query("data transformation approach")
print(result["best"])   # Positive experiences
print(result["avoid"])  # Negative experiences

# Crystallize patterns into skills
skills = forge.crystallize()

# Evolve agent config with learned skills
forge.evolve(config_path="./CLAUDE.md")
```

### Con Claude Code (Recomendado)

Un solo comando para configurar el registro automático de experiencias:

```bash
# Install and configure
pip install engram-ai
engram-ai setup

# That's it! Engram-AI now:
# 1. Records experiences via hooks (PostToolUse, UserPromptSubmit)
# 2. Exposes tools via MCP server (query, crystallize, evolve)
# 3. Detects outcome valence from your reactions (keyword + LLM)
```

Después de la configuración, tu agente Claude Code automáticamente:
- **Registra** cada uso de herramienta como una experiencia pendiente
- **Detecta** si tu respuesta fue positiva o negativa
- **Aprende** patrones a partir de las experiencias acumuladas
- **Evoluciona** su propio CLAUDE.md con las habilidades aprendidas

## Arquitectura

```
┌─────────────────────────────────────────────────────┐
│                    Forge (Facade)                     │
├──────────┬──────────┬──────────────┬────────────────┤
│ Recorder │ Querier  │ Crystallizer │    Evolver     │
├──────────┴──────────┴──────────────┴────────────────┤
│                    EventBus                          │
├─────────────────┬───────────────────────────────────┤
│  Storage Layer  │          LLM Layer                │
│  (ChromaDB)     │     (Claude API)                  │
├─────────────────┴───────────────────────────────────┤
│              Adapters (Claude Code)                  │
└─────────────────────────────────────────────────────┘
```

**Operaciones Principales:**

| Operación | Qué hace |
|-----------|----------|
| **Record** | Almacena una experiencia (acción + contexto + resultado + valencia) |
| **Query** | Encuentra experiencias pasadas relevantes, divididas en "mejores" y "a evitar" |
| **Crystallize** | Agrupa experiencias similares y extrae patrones de habilidades mediante LLM |
| **Evolve** | Escribe las habilidades aprendidas en la configuración del agente (CLAUDE.md) |

## Referencia de CLI

```bash
engram-ai setup          # Configuración automática para Claude Code
engram-ai status         # Muestra conteo de experiencias y habilidades
engram-ai query "tema"   # Busca experiencias pasadas
engram-ai crystallize    # Extrae habilidades de las experiencias
engram-ai evolve         # Escribe habilidades en CLAUDE.md
engram-ai serve          # Inicia el servidor MCP
engram-ai dashboard      # Lanza el panel web (por defecto: http://127.0.0.1:3333)
```

## Herramientas MCP

Al ejecutarse como servidor MCP, Engram-AI expone estas herramientas:

| Herramienta | Descripción |
|-------------|-------------|
| `engram_record` | Registra una experiencia con valencia |
| `engram_query` | Busca experiencias pasadas |
| `engram_crystallize` | Extrae habilidades de los patrones |
| `engram_evolve` | Escribe habilidades en la configuración |
| `engram_status` | Muestra estadísticas |

## Cómo Funciona

### Registro en Dos Fases

```
PostToolUse Hook          UserPromptSubmit Hook
     │                           │
     ▼                           ▼
Record Pending ──────────► Complete with Valence
(action + context)         (outcome + valence detection)
     │                           │
     ▼                           ▼
pending.jsonl              ChromaDB Storage
```

### Detección de Valencia (Por Niveles)

1. **Coincidencia de palabras clave** (gratuita) — Detecta patrones positivos/negativos en japonés e inglés
2. **Fallback con LLM** (llamada a la API) — Cuando las palabras clave no coinciden
3. **Valor predeterminado 0.3** — Suposición levemente positiva cuando ambos fallan

### Pipeline de Cristalización

```
Experiences ──► Cluster by similarity ──► LLM extracts pattern ──► Skill
                (ChromaDB cosine)         (per cluster)            (rule + confidence)
```

## Panel Web

Engram-AI incluye un panel web en tiempo real integrado para visualizar experiencias, habilidades y grafos neurales.

```bash
engram-ai dashboard --port 3333
```

**4 páginas:**

| Página | Descripción |
|--------|-------------|
| **Resumen** | Tarjetas de estadísticas, gráfico de tendencia de valencia, mini grafo neural, experiencias recientes |
| **Experiencias** | Tabla con búsqueda, filtros, ordenamiento y filas expandibles |
| **Habilidades** | Cuadrícula de tarjetas con barras de confianza, botones de acción para cristalizar y evolucionar |
| **Grafo** | Grafo neural dirigido por fuerzas con nodos hexagonales de habilidades, resaltado al hacer clic |

**Características:**
- Actualizaciones en tiempo real mediante WebSocket (las nuevas experiencias y habilidades aparecen al instante)
- Tema oscuro con paleta de colores personalizada
- Servicio sin dependencias externas (exportación estática de Next.js incluida en el paquete)
- No requiere Node.js para los usuarios

## Hoja de Ruta

Engram-AI v0.1 es la base. La arquitectura soporta estas funcionalidades planificadas:

- [x] **Dashboard** — Interfaz web para visualización de experiencias y habilidades
- [ ] **Etiquetado emocional** — Afecto más rico más allá de la valencia
- [ ] **Cadenas de experiencias** — Secuencias enlazadas de experiencias relacionadas
- [ ] **Curvas de olvido** — Decaimiento de relevancia ponderado por el tiempo
- [ ] **Mercado de habilidades** — Compartir habilidades aprendidas entre agentes
- [ ] **Transferencia entre agentes** — Transferencia de aprendizaje entre instancias de agentes
- [ ] **Soporte multi-LLM** — OpenAI, modelos locales, etc.
- [ ] **Políticas de modelado de recompensas** — Estrategias de valencia personalizadas
- [ ] **Memoria jerárquica** — Capas de episodio → habilidad → meta-habilidad
- [ ] **Controles de privacidad** — Memoria selectiva, eliminación controlada por el usuario

Consulta la [hoja de ruta completa](docs/specs/2026-03-17-engram-ai-v0.1-design.md) para ver las 20 funcionalidades planificadas.

## Contribuir

¡Damos la bienvenida a contribuciones de todo el mundo! Consulta nuestra [Guía de Contribución](../../CONTRIBUTING.md) para más detalles.

**Inicio rápido para colaboradores:**

```bash
git clone https://github.com/kajaha06251020/Engram-AI.git
cd Engram-AI
python -m venv .venv
source .venv/bin/activate  # o .venv\Scripts\activate en Windows
pip install -e ".[dev]"
pytest
```

¡Echa un vistazo a nuestros [good first issues](https://github.com/kajaha06251020/Engram-AI/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) para empezar!

## Comunidad

- [GitHub Discussions](https://github.com/kajaha06251020/Engram-AI/discussions) — Preguntas, ideas y demostraciones
- [Discord](https://discord.gg/engram-ai) — Chat en tiempo real
- [Issues](https://github.com/kajaha06251020/Engram-AI/issues) — Reportes de errores y solicitudes de funcionalidades

## Historial de Estrellas

<div align="center">

[![Star History Chart](https://api.star-history.com/svg?repos=kajaha06251020/Engram-AI&type=Date)](https://star-history.com/#kajaha06251020/Engram-AI&Date)

</div>

## Licencia

Apache License 2.0 — consulta [LICENSE](../../LICENSE) para más detalles.

---

<div align="center">

**Si Engram-AI ayuda a tus agentes de IA a aprender de la experiencia, ¡dale una estrella!**

<a href="https://github.com/kajaha06251020/Engram-AI/stargazers">
  <img src="https://img.shields.io/github/stars/kajaha06251020/Engram-AI?style=social" alt="GitHub Stars"/>
</a>

</div>
