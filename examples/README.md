# Engram-AI Examples

Ready-to-run sample scripts. Most require only `pip install engram-forge`.

| Script | Description | API key? |
|--------|-------------|----------|
| [`01_basic.py`](01_basic.py) | Record, query, crystallize, evolve | No |
| [`02_teach_and_warn.py`](02_teach_and_warn.py) | Teach rules directly, check warnings before acting | No |
| [`03_multi_project.py`](03_multi_project.py) | Isolated memory per project with ProjectManager | No |
| [`04_no_api_key.py`](04_no_api_key.py) | Full workflow using keyword-only mode | No |
| [`05_observe.py`](05_observe.py) | Auto-record from conversation messages | Anthropic |
| [`06_custom_llm.py`](06_custom_llm.py) | Plug in OpenAI (or any other LLM) | OpenAI |

## Running the examples

```bash
pip install engram-forge          # core — enough for examples 01–04
pip install "engram-forge[claude]"  # adds Anthropic SDK for example 05
pip install "engram-forge" openai   # adds OpenAI SDK for example 06

python examples/01_basic.py
python examples/02_teach_and_warn.py
# ...
```
