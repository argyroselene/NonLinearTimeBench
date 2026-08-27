"""
Temporal Reasoning Engine
A lightweight symbolic temporal reasoning engine for extracting,
normalizing, and inferring temporal relations between events.
"""

from temporal_reasoning.events import Event
from temporal_reasoning.relations import TemporalRelation, get_inverse, parse_relation
from temporal_reasoning.expressions import extract_temporal_expressions
from temporal_reasoning.normalizer import TemporalNormalizer, normalize_text
from temporal_reasoning.parser import StatementParser
from temporal_reasoning.graph import TemporalGraph
from temporal_reasoning.inference import InferenceEngine
from temporal_reasoning.consistency import ConsistencyChecker
from temporal_reasoning.engine import TemporalReasoningEngine

__version__ = "0.1.0"
__all__ = [
    "Event",
    "TemporalRelation",
    "get_inverse",
    "parse_relation",
    "extract_temporal_expressions",
    "TemporalNormalizer",
    "normalize_text",
    "StatementParser",
    "TemporalGraph",
    "InferenceEngine",
    "ConsistencyChecker",
    "TemporalReasoningEngine",
]
