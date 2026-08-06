"""JSON-schema shapes the pipeline asks the LLM to fill in (via LLMClient.complete's `schema` arg).

Kept separate from prompts.py so a concrete provider can pass these directly
to constrained/structured decoding.
"""

from metrics.allen_relations import RELATIONS

NODE_EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "events": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "the sentence's number in the input passage, e.g. 's3'"},
                    "thread_id": {"type": "string", "description": "a short label for the storyline this sentence belongs to"},
                },
                "required": ["id", "thread_id"],
            },
        }
    },
    "required": ["events"],
}

EDGE_EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "edges": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "node_i": {"type": "string"},
                    "node_j": {"type": "string"},
                    "allen_relation": {"type": "string", "enum": RELATIONS},
                },
                "required": ["node_i", "node_j", "allen_relation"],
            },
        },
        "candidate_convergence_pairs": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "members": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 2,
                        "description": "every node id, across two or more different threads, that "
                                       "depicts this exact same shared moment -- list them all together "
                                       "rather than guessing a single partner for each one",
                    },
                    "shared_detail": {
                        "type": "string",
                        "description": "the specific textual cue (shared timestamp, synchronizing "
                                       "phrase, shared location/object, or causal handoff) that ties "
                                       "these sentences to the same moment",
                    },
                },
                "required": ["members", "shared_detail"],
            },
            "description": "groups of node ids (regardless of thread) the model believes depict the "
                           "same moment, each grounded in a specific shared_detail from the text",
        },
    },
    "required": ["edges", "candidate_convergence_pairs"],
}

CONVERGENCE_RECALL_CRITIQUE_SCHEMA = {
    "type": "object",
    "properties": {
        "missed_convergence_pairs": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "members": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 2,
                        "description": "every node id, across two or more different threads, "
                                       "depicting this same moment, that was NOT already flagged",
                    },
                    "shared_detail": {
                        "type": "string",
                        "description": "the specific textual cue tying these sentences to the "
                                       "same moment",
                    },
                },
                "required": ["members", "shared_detail"],
            },
        },
    },
    "required": ["missed_convergence_pairs"],
}

DIRECT_BASELINE_SCHEMA = {
    "type": "object",
    "properties": {
        "events": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "thread_id": {"type": "string"},
                },
                "required": ["id", "thread_id"],
            },
        },
        "global_order": {
            "type": "array",
            "items": {"type": "string"},
            "description": "node ids in the model's believed chronological order",
        },
        "convergence_points": {
            "type": "array",
            "items": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 2,
                "maxItems": 2,
            },
        },
    },
    "required": ["events", "global_order", "convergence_points"],
}
