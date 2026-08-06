"""Prompt templates for the direct baseline and each graph-pipeline stage.

Passages are always the same shuffled, numbered-sentence format the predecessor
paper (and the blueprint's worked example) uses, so node ids can be sentence
numbers directly -- see the plan's node-correspondence note in metrics/awt_f1.py.
"""

from metrics.allen_relations import RELATIONS


def _numbered_passage(passage):
    return "\n".join(f"{i + 1}. {sentence}" for i, sentence in enumerate(passage))


def direct_baseline_prompt(passage):
    return f"""You will be given a shuffled passage made of numbered sentences. The
sentences interleave two or more storylines (threads) that are not in
chronological order.

Passage:
{_numbered_passage(passage)}

Task:
1. Assign every sentence to a thread (a short label for the storyline it belongs to).
2. Give the full chronological order of all sentences as you believe it to be.
3. List any pairs of sentences that depict the exact same moment across two different threads.

Every sentence id you output (in `events`, `global_order`, and
`convergence_points`) MUST be its sentence number prefixed with "s", e.g.
sentence 3 is "s3" -- never a bare number.

Return only JSON matching the requested schema."""


def node_extraction_prompt(passage):
    return f"""You will be given a shuffled passage made of numbered sentences. The
sentences interleave two or more storylines (threads).

Passage:
{_numbered_passage(passage)}

Task: for every sentence, output its sentence number as `id` (e.g. "s3") and a
short `thread_id` label for the storyline it belongs to. Infer thread identity
from recurring characters, settings, or narrative voice -- there is no explicit
naming convention to key off.

Return only JSON matching the requested schema."""


def edge_extraction_prompt(passage, nodes):
    node_lines = "\n".join(f"- {n['id']} (thread {n['thread_id']}): {passage[int(n['id'][1:]) - 1]}" for n in nodes)
    relation_list = ", ".join(RELATIONS)
    return f"""You previously assigned these sentences to threads:
{node_lines}

Task 1: for pairs of sentences whose relative timing is stated or clearly
implied by the text, output an edge giving the Allen interval-algebra relation
between them. You MUST choose `allen_relation` from exactly this vocabulary:
{relation_list}

Task 2: find every set of sentences from two or more DIFFERENT threads that
depict the exact same moment in time -- a "convergence point" -- and list each
such set as one entry in `candidate_convergence_pairs`, with `members` holding
every node id that belongs to that moment. These are candidates only, not yet
verified, so err toward including a plausible one rather than omitting it.

Do this in two passes:
  1. First, scan every sentence and flag any that describes an instant tied to
     another thread via one of these signals:
       - a shared or matching timestamp/duration ("at 10:15", "the exact
         second", "one hour later" when it lands on another thread's stated
         time);
       - a synchronizing phrase directly linking two actions ("just as", "at
         the same moment", "the instant that", "just then");
       - a shared physical anchor -- the same location, object, or witness
         that both threads independently describe being at/observing at that
         point;
       - a direct causal handoff, where one thread's action is the immediate
         trigger for or response to the other thread's action.
     Don't limit yourself to sentences you already connected with an edge
     above -- a convergence is about depicting one moment, not about a
     precedence relation.
  2. Then, for each flagged sentence, find every OTHER flagged sentence (in a
     different thread) that describes that exact same moment, and group them
     together into a single `members` list -- do not pick a partner for a
     flagged sentence in isolation; only group sentences that genuinely
     describe the same instant as each other. A moment can involve more than
     two sentences if more than two threads witness it. If a flagged sentence
     has no genuine match, leave it out rather than forcing a pairing.

For each group, set `shared_detail` to the specific phrase or fact from the
text that grounds the match (not a generic restatement).

Example (a different passage, for illustration only):
  1. Mira taps the emergency brake at 3:04 as the platform doors seal shut.
  2. Reyes, three cars back, feels the whole train lurch to a stop.
  -> candidate_convergence_pairs: [{{"members": ["s1", "s2"],
     "shared_detail": "the train lurching to a stop (s2) is the direct
     physical effect of Mira's brake at 3:04 (s1) -- same instant"}}]

Do not attempt to produce a full global ordering yourself; only report the
local pairwise relations you can directly support from the text.

Return only JSON matching the requested schema."""


def convergence_recall_critique_prompt(passage, nodes, already_flagged):
    """Stage 2.5 (opt-in): a dedicated second pass whose only job is finding
    convergence pairs the edge-extraction call MISSED, not re-judging the ones
    it already found. Separated from edge_extraction_prompt because that
    prompt already juggles relation extraction plus convergence detection in
    one call, and empirically convergence recall is the bottleneck -- a
    focused, single-purpose omission check is the thing being tested here."""
    node_lines = "\n".join(f"- {n['id']} (thread {n['thread_id']}): {passage[int(n['id'][1:]) - 1]}" for n in nodes)
    if already_flagged:
        flagged_lines = "\n".join(
            f"- {{{', '.join(g['members'])}}}: {g['shared_detail']}" for g in already_flagged
        )
    else:
        flagged_lines = "(none)"

    return f"""You previously read this passage and flagged the following groups of
sentences, from different threads, as describing the same moment:
{flagged_lines}

Full sentence list, with thread assignments, for reference:
{node_lines}

Task: re-read the passage with fresh attention. List ONLY cross-thread
same-moment groups you did NOT already flag above -- do not repeat any group
already listed. Be permissive: a borderline or loosely-signaled match you are
only somewhat confident about should still be included, since a later
deterministic verification step will filter out any group that isn't
internally consistent with each thread's own event order. It is fine, and
expected, for `missed_convergence_pairs` to be empty if you already found
everything.

Return only JSON matching the requested schema."""
