<div align="center">

# Engram-AI

### Infraestructura de Memoria Basada en Experiencia para Agentes de IA

[![PyPI version](https://img.shields.io/pypi/v/engram-ai?style=flat-square&color=blue)](https://pypi.org/project/engram-ai/)
[![Python](https://img.shields.io/pypi/pyversions/engram-ai?style=flat-square)](https://pypi.org/project/engram-ai/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green?style=flat-square)](../../LICENSE)
[![Tests](https://img.shields.io/github/actions/workflow/status/kajaha06251020/Engram-AI/tests.yml?style=flat-square&label=tests)](https://github.com/kajaha06251020/Engram-AI/actions)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat-square)](../../CONTRIBUTING.md)

**[English](../../README.md)** | **[日本語](README_ja.md)** | **[中文](README_zh.md)** | **[한국어](README_ko.md)** | **Español**

---

*La memoria de IA actual almacena texto. Engram-AI crea **engramas** — estructuras causales que permiten a los agentes aprender de lo que hicieron y lo que sucedió.*

</div>

## ¿Qué es Engram-AI?

La mayoría de los sistemas de memoria de IA funcionan como un **diario** — almacenan hechos textuales: *"Al usuario le gusta Python"*, *"La API usa REST"*. Pero el aprendizaje real no viene de memorizar hechos. Viene de la **experiencia**.

Engram-AI proporciona a los agentes de IA **memoria experiencial**. En lugar de almacenar lo que el agente *sabe*, almacena lo que *hizo*, lo que *sucedió*, y si el resultado fue *bueno o malo*:

```
Acción:   Usó Optional[str] en campo de respuesta API
Contexto: Diseñando modelo de respuesta REST API
Resultado: Usuario lo rechazó — "no quiero valores null en respuestas"
Valencia:  -0.8 (experiencia negativa)
```

Con el tiempo, estas experiencias se **cristalizan** en habilidades — reglas generalizadas que el agente aprende de patrones en su propio historial.

## Inicio Rápido

### Instalación

```bash
pip install engram-ai
```

### Como Biblioteca Python

```python
from engram_ai import Forge

forge = Forge()

# Registrar una experiencia
forge.record(
    action="Usó list comprehension para transformar datos",
    context="Procesando CSV con 10k filas",
    outcome="Rápido y legible, usuario aprobó",
    valence=0.9,
)

# Consultar experiencias pasadas
result = forge.query("enfoque de transformación de datos")

# Cristalizar patrones en habilidades
skills = forge.crystallize()

# Evolucionar configuración del agente
forge.evolve(config_path="./CLAUDE.md")
```

### Con Claude Code (Recomendado)

```bash
pip install engram-ai
engram-ai setup
# ¡Listo! Ahora registra experiencias automáticamente y comienza a aprender
```

## Operaciones Principales

| Operación | Descripción |
|-----------|-------------|
| **Record (Registrar)** | Almacena experiencia (acción + contexto + resultado + valencia) |
| **Query (Consultar)** | Busca experiencias pasadas relevantes, clasificadas en "mejores" y "evitar" |
| **Crystallize (Cristalizar)** | Agrupa experiencias similares y extrae patrones de habilidades con LLM |
| **Evolve (Evolucionar)** | Escribe habilidades aprendidas en la configuración del agente (CLAUDE.md) |

## Contribuir

¡Damos la bienvenida a contribuciones de todos! Consulta nuestra [Guía de Contribución](../../CONTRIBUTING.md).

```bash
git clone https://github.com/kajaha06251020/Engram-AI.git
cd Engram-AI
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest
```

## Licencia

Apache License 2.0 — ver [LICENSE](../../LICENSE) para más detalles.
