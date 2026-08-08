"""story_07 -- "Tide Watch"

Second relation-balanced, referentially indirect story, so the interval-rich
condition is not a single data point. Same design rules as story_06:

  - before/after is a deliberate minority of gold edges, so a method that can
    only SORT events (the direct baseline's structural limit) is capped well
    below ceiling instead of scoring ~0.85 for free.
  - No event opens with its own thread's character name; threads are carried
    by pronouns, role nouns, location, and continuity of activity.
  - Every gold relation is DERIVED from the intervals by build_story.py, never
    hand-typed, so a label cannot disagree with the timeline the prose states.
  - Events described as instantaneous get one minute of duration, because
    Allen's algebra is undefined over zero-length intervals.

Deliberately different in shape from story_06 so the two are not near-
duplicates: a coastal flood-response night, five threads rather than four,
with a different interleaving pattern (two long spine intervals that overlap
each other rather than one global frame, and convergence anchored on handoffs
between teams rather than on shared instrument readings).

Timeline is integer minutes from 03:00 (t=0) to 05:00 (t=120).
"""

SPEC = {
    "story_id": "story_07",
    "title": "Tide Watch (relation-balanced, referentially indirect)",
    "source": (
        "Hand-authored interval spec; gold relations derived from event intervals "
        "by scripts/build_story.py. Second story in the interval-rich condition."
    ),
    "counterfactual_names": {
        "Pell": "Rourke",
        "Nadia": "Imogen",
        "Sorley": "Achterberg",
        "Wren": "Castellan",
        "Ingold": "Marchetti",
    },
    "threads": [
        {"id": "P", "label": "the pump-house operator, below the sea wall", "granularity": "minutes"},
        {"id": "N", "label": "the dispatcher, in the harbour office", "granularity": "minutes"},
        {"id": "S", "label": "the sandbag crew, on the esplanade", "granularity": "minutes"},
        {"id": "W", "label": "the lifeboat coxswain, in the channel", "granularity": "minutes"},
        {"id": "I", "label": "the surveyor, walking the flood line", "granularity": "minutes"},
    ],
    "events": [
        # ---- P: pump-house operator ----
        {"id": "s1", "thread_id": "P", "start": 0, "end": 90, "time_expr": "03:00-04:30",
         "text": "The pumps ran from three until half four without anyone touching them."},
        {"id": "s6", "thread_id": "P", "start": 0, "end": 20, "time_expr": "03:00-03:20",
         "text": "The opening twenty minutes of that went on priming the intake."},
        {"id": "s11", "thread_id": "P", "start": 70, "end": 90, "time_expr": "04:10-04:30",
         "text": "The last twenty minutes before shutdown were spent bleeding air from the line."},
        {"id": "s16", "thread_id": "P", "start": 25, "end": 65, "time_expr": "03:25-04:05",
         "text": "In between, he sat watching the sump gauge climb and refuse to fall."},
        {"id": "s21", "thread_id": "P", "start": 40, "end": 55, "time_expr": "03:40-03:55",
         "text": "A quarter of an hour of that was spent on the radio, arguing."},
        {"id": "s26", "thread_id": "P", "start": 20, "end": 45, "time_expr": "03:20-03:45",
         "text": "Once priming finished the secondary pump came on and ran twenty-five minutes."},
        {"id": "s31", "thread_id": "P", "start": 55, "end": 80, "time_expr": "03:55-04:20",
         "text": "Ending that call started a long stretch of shovelling grit off the floor plate."},
        {"id": "s36", "thread_id": "P", "start": 10, "end": 35, "time_expr": "03:10-03:35",
         "text": "Pell had the floor drains open from ten past until twenty-five to."},
        {"id": "s41", "thread_id": "P", "start": 90, "end": 120, "time_expr": "04:30-05:00",
         "text": "After the pumps stopped he stayed on another half hour writing it up."},

        # ---- N: dispatcher, harbour office ----
        {"id": "s2", "thread_id": "N", "start": 15, "end": 105, "time_expr": "03:15-04:45",
         "text": "Upstairs in the office the radio watch covered a quarter past three to quarter to five."},
        {"id": "s7", "thread_id": "N", "start": 15, "end": 40, "time_expr": "03:15-03:40",
         "text": "Its first twenty-five minutes were nothing but hold music and apologies."},
        {"id": "s12", "thread_id": "N", "start": 85, "end": 105, "time_expr": "04:25-04:45",
         "text": "The watch ended with twenty minutes of handover notes read aloud."},
        {"id": "s17", "thread_id": "N", "start": 30, "end": 75, "time_expr": "03:30-04:15",
         "text": "Three quarters of an hour in the middle went on the county flood line."},
        {"id": "s22", "thread_id": "N", "start": 55, "end": 56, "time_expr": "03:55 (instant)",
         "text": "At five to four the board lit up red across every channel at once."},
        {"id": "s27", "thread_id": "N", "start": 40, "end": 70, "time_expr": "03:40-04:10",
         "text": "Half an hour of logging positions overlapped the tail of the first quiet spell."},
        {"id": "s32", "thread_id": "N", "start": 75, "end": 100, "time_expr": "04:15-04:40",
         "text": "When the flood line finally cleared, Nadia started calling the outlying farms."},
        {"id": "s37", "thread_id": "N", "start": 0, "end": 15, "time_expr": "03:00-03:15",
         "text": "The quarter hour before any of that was spent finding the spare handset."},
        {"id": "s42", "thread_id": "N", "start": 105, "end": 120, "time_expr": "04:45-05:00",
         "text": "The moment the watch closed she went down to the quay to see it herself."},

        # ---- S: sandbag crew, esplanade ----
        {"id": "s3", "thread_id": "S", "start": 20, "end": 100, "time_expr": "03:20-04:40",
         "text": "Out on the esplanade the filling line worked from twenty past until twenty to five."},
        {"id": "s8", "thread_id": "S", "start": 20, "end": 50, "time_expr": "03:20-03:50",
         "text": "The first half hour of it produced more argument than sandbags."},
        {"id": "s13", "thread_id": "S", "start": 80, "end": 100, "time_expr": "04:20-04:40",
         "text": "The closing twenty minutes were spent stacking what they had against the railings."},
        {"id": "s18", "thread_id": "S", "start": 45, "end": 75, "time_expr": "03:45-04:15",
         "text": "A half-hour stretch in the middle ran with the lorry headlights as the only light."},
        {"id": "s23", "thread_id": "S", "start": 55, "end": 56, "time_expr": "03:55 (instant)",
         "text": "At five to four the whole crew stopped dead and looked up at the same sound."},
        {"id": "s28", "thread_id": "S", "start": 30, "end": 60, "time_expr": "03:30-04:00",
         "text": "Half an hour of ferrying bags to the corner overlapped the early argument."},
        {"id": "s33", "thread_id": "S", "start": 100, "end": 115, "time_expr": "04:40-04:55",
         "text": "After the line broke up, Sorley kept a quarter-hour watch on the join."},
        {"id": "s38", "thread_id": "S", "start": 60, "end": 80, "time_expr": "04:00-04:20",
         "text": "From four o'clock the second pallet was opened and worked through."},
        {"id": "s43", "thread_id": "S", "start": 10, "end": 30, "time_expr": "03:10-03:30",
         "text": "They had been out since ten past, before the filling line properly began."},

        # ---- W: lifeboat coxswain, channel ----
        {"id": "s4", "thread_id": "W", "start": 35, "end": 115, "time_expr": "03:35-04:55",
         "text": "The boat was in the channel from twenty-five to four until five to five."},
        {"id": "s9", "thread_id": "W", "start": 35, "end": 55, "time_expr": "03:35-03:55",
         "text": "Its first twenty minutes out were spent simply getting clear of the moorings."},
        {"id": "s14", "thread_id": "W", "start": 95, "end": 115, "time_expr": "04:35-04:55",
         "text": "The run back in took the last twenty minutes of the same trip."},
        {"id": "s19", "thread_id": "W", "start": 60, "end": 90, "time_expr": "04:00-04:30",
         "text": "Half an hour in the middle went on a search box off the point."},
        {"id": "s24", "thread_id": "W", "start": 55, "end": 56, "time_expr": "03:55 (instant)",
         "text": "At five to four a flare went up somewhere off the starboard bow."},
        {"id": "s29", "thread_id": "W", "start": 45, "end": 70, "time_expr": "03:45-04:10",
         "text": "A long spell on the searchlight overlapped the end of the outbound leg."},
        {"id": "s34", "thread_id": "W", "start": 90, "end": 95, "time_expr": "04:30-04:35",
         "text": "Abandoning the box took five minutes of hard turning before the run home."},
        {"id": "s39", "thread_id": "W", "start": 20, "end": 35, "time_expr": "03:20-03:35",
         "text": "Wren had the crew aboard a quarter of an hour before they slipped."},
        {"id": "s44", "thread_id": "W", "start": 70, "end": 100, "time_expr": "04:10-04:40",
         "text": "Half an hour of that search was worked with no radio contact at all."},

        # ---- I: surveyor, flood line ----
        {"id": "s5", "thread_id": "I", "start": 5, "end": 85, "time_expr": "03:05-04:25",
         "text": "The walk along the flood line lasted from five past three to twenty-five past four."},
        {"id": "s10", "thread_id": "I", "start": 5, "end": 25, "time_expr": "03:05-03:25",
         "text": "It opened with twenty minutes spent marking the first row of gardens."},
        {"id": "s15", "thread_id": "I", "start": 65, "end": 85, "time_expr": "04:05-04:25",
         "text": "The final twenty minutes of the walk were done at a run."},
        {"id": "s20", "thread_id": "I", "start": 30, "end": 50, "time_expr": "03:30-03:50",
         "text": "Twenty minutes of the middle stretch went on a culvert that would not clear."},
        {"id": "s25", "thread_id": "I", "start": 50, "end": 75, "time_expr": "03:50-04:15",
         "text": "Leaving the culvert began a twenty-five minute climb up the back lane."},
        {"id": "s30", "thread_id": "I", "start": 85, "end": 110, "time_expr": "04:25-04:50",
         "text": "Once the line was walked, Ingold spent twenty-five minutes on the phone to the office."},
        {"id": "s35", "thread_id": "I", "start": 15, "end": 40, "time_expr": "03:15-03:40",
         "text": "A quarter-hour in, she began photographing every marker she passed."},
        {"id": "s40", "thread_id": "I", "start": 55, "end": 56, "time_expr": "03:55 (instant)",
         "text": "At five to four the water came over the kerb in one push, all along the row."},
        {"id": "s45", "thread_id": "I", "start": 110, "end": 120, "time_expr": "04:50-05:00",
         "text": "The last ten minutes before five were spent waiting for someone to answer."},
    ],

    "edges": [
        # P internal
        ["s6", "s1"], ["s11", "s1"], ["s16", "s1"], ["s21", "s16"],
        ["s6", "s26"], ["s26", "s21"], ["s31", "s16"], ["s36", "s6"],
        ["s1", "s41"], ["s36", "s26"],
        # N internal
        ["s7", "s2"], ["s12", "s2"], ["s17", "s2"], ["s22", "s17"],
        ["s27", "s7"], ["s37", "s2"], ["s32", "s17"], ["s2", "s42"],
        ["s27", "s17"],
        # S internal
        ["s8", "s3"], ["s13", "s3"], ["s18", "s3"], ["s23", "s18"],
        ["s28", "s8"], ["s3", "s33"], ["s38", "s18"], ["s43", "s3"],
        ["s28", "s38"],
        # W internal
        ["s9", "s4"], ["s14", "s4"], ["s19", "s4"], ["s24", "s9"],
        ["s29", "s9"], ["s34", "s14"], ["s39", "s4"], ["s44", "s19"],
        ["s19", "s34"],
        # I internal
        ["s10", "s5"], ["s15", "s5"], ["s20", "s5"], ["s25", "s20"],
        ["s30", "s5"], ["s35", "s10"], ["s40", "s25"], ["s5", "s45"],
        ["s25", "s15"],
        # a deliberate minority of before/after plus the otherwise-absent
        # relations, so all 13 stay covered without handing the dataset to an
        # order-only method
        ["s41", "s6"],   # after
        ["s1", "s6"],    # started-by
        ["s1", "s21"],   # contains
        ["s1", "s11"],   # finished-by
        # cross-thread convergence anchors (within the 3-7 target)
        ["s22", "s23"], ["s23", "s24"], ["s24", "s40"], ["s22", "s40"],
    ],

    # The 03:55 beat is witnessed from four different threads at once; the
    # remaining anchor is a handoff where one team's interval ends exactly as
    # another's begins.
    "convergence_points": [
        ["s22", "s23"],
        ["s23", "s24"],
        ["s24", "s40"],
    ],
}
