# Temporal Reasoning Engine

A lightweight, interpretable, and symbolic temporal reasoning engine in Python for extracting, normalizing, and inferring temporal relations between events described in natural language.

## Overview

Natural language statements often describe events ordered in time, anchored to specific dates, or bounded by durations:

- *"Alice arrived before Bob."*
- *"Bob left before Charlie."*
- *"The meeting started at 10:00 and lasted for 90 minutes."*

The **Temporal Reasoning Engine** extracts event representations, normalizes temporal expressions, constructs a directed temporal relation graph, and deterministically derives non-explicit temporal inferences (such as transitivity, point-interval bounds, and inverse relations) while verifying temporal consistency.

## Project Structure

```text
temporal-reasoning-engine/
├── src/
│   └── temporal_reasoning/
│       ├── __init__.py
│       ├── events.py
│       ├── expressions.py
│       ├── relations.py
│       ├── normalizer.py
│       ├── parser.py
│       ├── graph.py
│       ├── inference.py
│       ├── consistency.py
│       ├── evaluator.py
│       └── cli.py
├── data/
│   ├── examples.json
│   └── benchmark.json
├── tests/
├── examples/
├── docs/
├── pyproject.toml
└── requirements.txt
```

## Installation

```bash
git clone https://github.com/argyroselene/NonLinearTimeBench.git
cd NonLinearTimeBench
pip install -e .
```

For development and testing:

```bash
pip install -r requirements.txt
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
