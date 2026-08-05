"""story_06 -- "Signal Loss"

Built to fix two benchmark-validity problems the first five stories had.

1. RELATION BALANCE. In stories 1-5, 48% of gold edges are before/after, so a
   method that cannot express interval relations at all -- one that merely
   sorts events -- scores 0.849 by construction. The benchmark could not
   distinguish interval reasoning from sorting. Here the intervals are designed
   so that before/after is a minority of the gold edges and the simultaneity
   family (during/contains/overlaps/starts/finishes/equals) dominates. A
   before/after-only method is structurally capped well below ceiling.

2. REFERENTIAL INDIRECTION. Thread attribution must require discourse
   reasoning, not string matching. No event opens with its own thread's
   character name; threads are carried by pronouns, role nouns ("the
   technician"), locations, and continuity of activity. Names appear only
   mid-sentence and sparingly, so the counterfactual variant still has
   entities to perturb.

Timeline is integer minutes from 22:00 (t=0) to midnight (t=120).
Events the prose calls instantaneous are given one minute of duration:
Allen's algebra is defined over non-degenerate intervals only, so a
zero-length event has no well-defined relation to anything. Stories 1-5
contain zero-length 'instant' events with hand-typed relations that were
therefore never well-defined -- a modelling bug the derivation tool caught
on its first run.
Gold relations are NOT written here -- scripts/build_story.py derives every
one of them from the intervals below, so a label cannot disagree with the
timeline the prose describes.
"""

SPEC = {
    "story_id": "story_06",
    "title": "Signal Loss (relation-balanced, referentially indirect)",
    "source": (
        "Hand-authored interval spec; gold relations derived from event intervals "
        "by scripts/build_story.py. Designed for a low before/after share and "
        "no name-opening thread shortcuts."
    ),
    # Surface perturbation for the memorization control. Applied automatically
    # by build_story.py to produce the counterfactual text track, so the two
    # tracks differ only in these substituted forms.
    "counterfactual_names": {
        "Vance": "Ivarsen",
        "Mert": "Dolan",
        "Kesler": "Brandt",
        "Odile": "Saros",
    },
    "threads": [
        {"id": "V", "label": "the duty technician, dish control room", "granularity": "minutes"},
        {"id": "M", "label": "the researcher, data hall", "granularity": "minutes"},
        {"id": "K", "label": "the groundskeeper, outside the perimeter", "granularity": "minutes"},
        {"id": "O", "label": "the duty officer, on the phone line", "granularity": "minutes"},
    ],
    "events": [
        # ---- V: duty technician, dish control room ----
        {"id": "s1", "thread_id": "V", "start": 0, "end": 120, "time_expr": "22:00-00:00",
         "text": "Her whole watch in the control room ran from ten until midnight, unbroken."},
        {"id": "s5", "thread_id": "V", "start": 0, "end": 25, "time_expr": "22:00-22:25",
         "text": "The first stretch of it, up to twenty-five past, went on calibrating the feed horn."},
        {"id": "s9", "thread_id": "V", "start": 95, "end": 120, "time_expr": "23:35-00:00",
         "text": "The last twenty-five minutes of the same watch were spent writing the fault log."},
        {"id": "s13", "thread_id": "V", "start": 30, "end": 70, "time_expr": "22:30-23:10",
         "text": "Somewhere in the middle she nursed the drive motors through the worst of the gusts."},
        {"id": "s17", "thread_id": "V", "start": 40, "end": 55, "time_expr": "22:40-22:55",
         "text": "A quarter-hour of that was spent with the cabinet open and both hands inside it."},
        {"id": "s21", "thread_id": "V", "start": 25, "end": 45, "time_expr": "22:25-22:45",
         "text": "Once the calibration ended she went straight onto the azimuth trim, twenty minutes of it."},
        {"id": "s25", "thread_id": "V", "start": 70, "end": 95, "time_expr": "23:10-23:35",
         "text": "When the motors settled, Vance moved to the receiver chain and stayed there until the log."},
        {"id": "s29", "thread_id": "V", "start": 10, "end": 35, "time_expr": "22:10-22:35",
         "text": "From ten past she also had the backup recorder spinning, and left it running to twenty-five to."},
        {"id": "s33", "thread_id": "V", "start": 55, "end": 80, "time_expr": "22:55-23:20",
         "text": "Closing the cabinet began a long stint of watching the noise floor climb."},

        # ---- M: researcher, data hall ----
        {"id": "s2", "thread_id": "M", "start": 0, "end": 120, "time_expr": "22:00-00:00",
         "text": "Down in the data hall the capture job covered exactly the same two hours, start to finish."},
        {"id": "s6", "thread_id": "M", "start": 15, "end": 60, "time_expr": "22:15-23:00",
         "text": "He let the first integration run from a quarter past until the hour."},
        {"id": "s10", "thread_id": "M", "start": 60, "end": 90, "time_expr": "23:00-23:30",
         "text": "The second one picked up where that left off and ran half an hour."},
        {"id": "s14", "thread_id": "M", "start": 0, "end": 40, "time_expr": "22:00-22:40",
         "text": "The disk array had been staging from the very start of the job, for the first forty minutes."},
        {"id": "s18", "thread_id": "M", "start": 80, "end": 120, "time_expr": "23:20-00:00",
         "text": "Checksumming began at twenty past eleven and was still going when the job itself ended."},
        {"id": "s22", "thread_id": "M", "start": 30, "end": 75, "time_expr": "22:30-23:15",
         "text": "For three quarters of an hour around the middle, Mert had the spectrum plot up on the wall."},
        {"id": "s26", "thread_id": "M", "start": 45, "end": 46, "time_expr": "22:45 (instant)",
         "text": "At a quarter to eleven exactly, every channel in the hall flatlined at once."},
        {"id": "s30", "thread_id": "M", "start": 20, "end": 50, "time_expr": "22:20-22:50",
         "text": "A half-hour tape backup overlapped the early part of all that."},
        {"id": "s34", "thread_id": "M", "start": 90, "end": 110, "time_expr": "23:30-23:50",
         "text": "After the second integration closed, he spent twenty minutes reconciling timestamps."},

        # ---- K: groundskeeper, outside ----
        {"id": "s3", "thread_id": "K", "start": 10, "end": 110, "time_expr": "22:10-23:50",
         "text": "Outside, the perimeter walk began ten minutes into the hour and lasted most of the night."},
        {"id": "s7", "thread_id": "K", "start": 10, "end": 40, "time_expr": "22:10-22:40",
         "text": "It opened with half an hour spent clearing the drainage channel."},
        {"id": "s11", "thread_id": "K", "start": 85, "end": 110, "time_expr": "23:25-23:50",
         "text": "The final stretch of the same walk was a slow sweep back along the fence line."},
        {"id": "s15", "thread_id": "K", "start": 45, "end": 65, "time_expr": "22:45-23:05",
         "text": "Twenty minutes in the middle of it went on the generator shed, door propped open."},
        {"id": "s19", "thread_id": "K", "start": 25, "end": 55, "time_expr": "22:25-22:55",
         "text": "Half an hour of that was in driving rain, boots filling steadily."},
        {"id": "s23", "thread_id": "K", "start": 60, "end": 100, "time_expr": "23:00-23:40",
         "text": "From the hour onwards Kesler was up on the access road with a hand lamp."},
        {"id": "s27", "thread_id": "K", "start": 35, "end": 36, "time_expr": "22:35 (instant)",
         "text": "At twenty-five to eleven something heavy came down across the service track."},
        {"id": "s31", "thread_id": "K", "start": 5, "end": 30, "time_expr": "22:05-22:30",
         "text": "He had already been out five minutes before the walk proper started, checking the gate."},
        {"id": "s35", "thread_id": "K", "start": 100, "end": 115, "time_expr": "23:40-23:55",
         "text": "The last quarter-hour outside was spent waiting by the gate for the relief driver."},

        # ---- O: duty officer, phone line ----
        {"id": "s4", "thread_id": "O", "start": 20, "end": 100, "time_expr": "22:20-23:40",
         "text": "The open line to the regional desk was held from twenty past until twenty to midnight."},
        {"id": "s8", "thread_id": "O", "start": 20, "end": 45, "time_expr": "22:20-22:45",
         "text": "Its opening twenty-five minutes were taken up reading out equipment numbers."},
        {"id": "s12", "thread_id": "O", "start": 75, "end": 100, "time_expr": "23:15-23:40",
         "text": "The call closed with a twenty-five minute handover briefing."},
        {"id": "s16", "thread_id": "O", "start": 50, "end": 70, "time_expr": "22:50-23:10",
         "text": "Partway through, she put the desk on hold for twenty minutes to chase a second line."},
        {"id": "s20", "thread_id": "O", "start": 0, "end": 20, "time_expr": "22:00-22:20",
         "text": "The twenty minutes before that call were spent getting the handset to work at all."},
        {"id": "s24", "thread_id": "O", "start": 100, "end": 120, "time_expr": "23:40-00:00",
         "text": "The moment the line dropped, Odile started the incident write-up and worked to midnight."},
        {"id": "s28", "thread_id": "O", "start": 55, "end": 85, "time_expr": "22:55-23:25",
         "text": "A half-hour argument about whether to send anyone up the road sat in the middle of the call."},
        {"id": "s32", "thread_id": "O", "start": 40, "end": 41, "time_expr": "22:40 (instant)",
         "text": "At twenty to eleven the desk asked for the dish to be stowed, and would not repeat it."},
        {"id": "s36", "thread_id": "O", "start": 10, "end": 60, "time_expr": "22:10-23:00",
         "text": "Her logbook entry covering all of this had been open since ten past."},
    ],

    # Pairs a reader could infer a relation between. The RELATION ITSELF is
    # derived from the intervals above -- these are chosen to make the
    # simultaneity family dominate rather than before/after.
    "edges": [
        # V internal
        ["s5", "s1"],    # starts
        ["s9", "s1"],    # finishes
        ["s13", "s1"],   # during
        ["s17", "s13"],  # during
        ["s5", "s21"],   # meets
        ["s21", "s17"],  # overlaps
        ["s25", "s9"],   # meets
        ["s29", "s5"],   # overlapped-by
        ["s33", "s13"],  # overlapped-by
        ["s17", "s33"],  # meets
        # M internal
        ["s14", "s2"],   # starts
        ["s18", "s2"],   # finishes
        ["s6", "s10"],   # meets
        ["s22", "s6"],   # overlapped-by
        ["s30", "s14"],  # overlaps
        ["s26", "s22"],  # during
        ["s10", "s34"],  # meets
        ["s6", "s2"],    # during
        ["s30", "s6"],   # overlapped-by
        # K internal
        ["s7", "s3"],    # starts
        ["s11", "s3"],   # finishes
        ["s15", "s3"],   # during
        ["s19", "s7"],   # overlapped-by
        ["s31", "s3"],   # overlaps
        ["s23", "s11"],  # overlaps
        ["s27", "s7"],   # during
        ["s35", "s11"],  # overlaps
        ["s19", "s15"],  # meets
        # O internal
        ["s8", "s4"],    # starts
        ["s12", "s4"],   # finishes
        ["s16", "s4"],   # during
        ["s20", "s4"],   # meets
        ["s24", "s4"],   # met-by
        ["s28", "s12"],  # overlaps
        ["s36", "s4"],   # overlaps
        ["s32", "s8"],   # during
        ["s16", "s28"],  # overlaps
        # a deliberate minority of before/after and the remaining relations, so
        # all 13 stay covered without handing an order-only method the dataset
        ["s1", "s17"],   # contains
        ["s1", "s9"],    # finished-by
        ["s5", "s25"],   # before
        ["s34", "s6"],   # after
        # cross-thread (kept within the 3-7 target)
        ["s1", "s2"],    # equals
        ["s26", "s15"],  # starts  (both at 45)
        ["s27", "s29"],  # finishes-adjacent instant
        ["s32", "s17"],  # starts  (both at 40)
        ["s3", "s36"],   # started-by
    ],

    # Cross-thread same-moment anchors. build_story.py verifies each pair
    # genuinely shares an instant rather than trusting the annotation.
    "convergence_points": [
        ["s26", "s15"],  # both at t=45
        ["s32", "s17"],  # both at t=40
        ["s27", "s29"],  # both at t=35
    ],
}
