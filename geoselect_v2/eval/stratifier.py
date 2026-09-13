"""Deterministic TEXT stratifier.

Extends V1's reference-type classifier (geogrounder.data.ref_type: image / object / attribute)
with the four V2 grammar tags whose handling is V2's contribution:

    superlative   — picks THE extreme one ("leftmost", "top-most", "largest", "closest")
    ordinal       — picks the n-th ("the second ship from the left", "the 3rd building")
    group         — refers to multiple / counted objects ("all the ships", "the three tanks")
    compositional — multi-hop spatial structure (2+ chained spatial constraints / nested anchor)

CRITICAL: the stratifier is TEXT-only and METHOD-INDEPENDENT — it
must NOT depend on V2's own synthesised program, else the stratified V1-vs-V2 comparison is
circular. The V2 gains are reported on these slices; the slice membership is fixed by the
sentence text alone. A sentence may carry several tags (the tags are a SET, not a partition).

These are HEURISTICS (like V1's ref_type) — calibrate against a hand-labelled sample before
quoting exact slice sizes. The four tag functions are pure (no model / no geogrounder import),
so they unit-test on the dev box; stratum_tags() adds the V1 base type via a lazy import.
"""

from __future__ import annotations

import re
from typing import Set

V2_TAGS = ('superlative', 'ordinal', 'group', 'compositional')
ALL_STRATA = ('image', 'object', 'attribute') + V2_TAGS


# --- superlative -------------------------------------------------------------------------
# THE single extreme: positional (-most / furthest / closest) or size/extent (largest / longest).
_SUPERLATIVE = re.compile(
    r'\b(?:'
    r'(?:left|right|top|bottom|upper|lower|inner|outer|fore)[\s-]?most'   # leftmost, top-most
    r'|most\s+(?:left|right|upper|lower|central|distant)'                  # "most central"
    r'|(?:far|fur)thest|closest|nearest|remotest'
    r'|largest|biggest|smallest|tiniest|longest|shortest|widest|narrowest'
    r'|tallest|highest|lowest|deepest'
    r')\b', re.IGNORECASE)


# --- ordinal -----------------------------------------------------------------------------
_ORDINAL = re.compile(
    r'\b(?:second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|last'
    r'|\d+(?:st|nd|rd|th))\b', re.IGNORECASE)
# "first" alone is noisy ("first responder"); only count it in a counting context ("first ... from").
_ORDINAL_FIRST = re.compile(r'\bfirst\b[^.]*\bfrom\b', re.IGNORECASE)


# --- group / counting --------------------------------------------------------------------
# Group-ness is a property of the TARGET (sentence SUBJECT), not the descriptive predicate
# ("...near a cluster of trees" describes context, not a group referent). So we judge group on
# the SUBJECT SPAN = text before the first main verb, and use are/were subject-verb agreement as
# a strong plural signal. RISBench sentences are declarative ("The X is/are ...").
_SPLIT_VERB = re.compile(
    r'\b(is|are|was|were|appears?|seems?|lies|sits|stands?|located|situated|positioned'
    r'|occupy|occupies|features?|spans?|connects?|extends?|borders?|measures?|rests?'
    r'|has|have|contains?|shows?|can\s+be)\b', re.IGNORECASE)
# Strong quantifiers + collective nouns that denote MULTIPLE referent objects. 'series/set/array
# of' are EXCLUDED — they usually describe ONE object's parts ("a series of fairways" = one golf
# field). 'several/numerous/various/multiple/many' added (plural quantifiers).
_GROUP_QUANT = re.compile(
    r'\b(?:all|every|each|both|several|numerous|various|multiple|many)\b', re.IGNORECASE)
_GROUP_COLL = re.compile(r'\b(?:group|row|line|cluster|fleet|pair|bunch)\s+of\b', re.IGNORECASE)
# A count word followed (within 2 words) by a PLURAL head ("three tennis courts", "two ships").
_GROUP_NUM_PLURAL = re.compile(
    r'\b(two|three|four|five|six|seven|eight|nine|ten)\s+(?:\w+\s+){0,2}\w+s\b', re.IGNORECASE)


# --- compositional (multi-hop) -----------------------------------------------------------
# An anchor preposition introducing ANOTHER object ("of the river", "next to the harbor", ...).
_ANCHOR_PREP = re.compile(
    r'\b(?:of|above|below|under(?:neath)?|over|behind|beside|inside|within|near|atop)\s+the\b'
    r'|\bnext\s+to\b|\badjacent\s+to\b|\bbetween\b', re.IGNORECASE)
# A relative clause usually adds a SECOND constraint ("the ship that is near the dock").
_REL_CLAUSE = re.compile(r'\b(?:that|which)\s+(?:is|are|has|have|lies?|sits?)\b', re.IGNORECASE)
# Image-frame "of the image/scene" is NOT an object anchor — mask it before counting anchors.
_IMAGE_OF = re.compile(r'\bof\s+the\s+(?:image|frame|scene|picture|photo|photograph)\b', re.IGNORECASE)
# An image-frame DIRECTION phrase ("on the right", "in the middle") — a spatial hop, but NOT when
# it is the head of an object relation ("to the left OF THE harbor"), which the anchor counter
# already owns; the negative lookahead avoids double-counting that case.
_IMAGE_DIR = re.compile(
    r'\b(?:on|in|at|to|toward|towards)\s+the\s+'
    r'(?:left|right|top|bottom|middle|center|centre|corner|upper|lower)\b(?!\s+of\s+the)',
    re.IGNORECASE)


def is_superlative(sentence: str) -> bool:
    return bool(_SUPERLATIVE.search(sentence or ''))


def is_ordinal(sentence: str) -> bool:
    s = sentence or ''
    return bool(_ORDINAL.search(s) or _ORDINAL_FIRST.search(s))


def is_group(sentence: str) -> bool:
    s = sentence or ''
    mv = _SPLIT_VERB.search(s)
    if mv and mv.group(1).lower() in ('are', 'were'):
        return True                                    # plural subject-verb agreement
    subj = s[:mv.start()] if mv else s                 # judge group on the SUBJECT span only
    if _GROUP_QUANT.search(subj) or _GROUP_COLL.search(subj):
        return True
    # "<number> ... <plural>" in the subject — but NOT a binary-relation descriptor ("between two
    # areas") nor a PARTITIVE ("the smaller OF THE TWO vehicles" picks ONE, a singular referent).
    for m in _GROUP_NUM_PLURAL.finditer(subj):
        pre = subj[:m.start()].rstrip().lower()
        if pre.endswith('between') or pre.endswith('of the') or pre.endswith('one of'):
            continue
        return True
    return False


def is_compositional(sentence: str) -> bool:
    """Multi-hop: >=2 chained spatial constraints. Counts object-anchor prepositions (excluding
    image-frame 'of the image'), a relative clause, and a superlative/ordinal head as separate
    spatial 'hops'; >=2 distinct hops -> compositional ("the ship to the left of the harbor in
    the middle", "the leftmost building near the river")."""
    s = sentence or ''
    masked = _IMAGE_OF.sub(' ', s)                     # don't count "of the image" as an anchor
    hops = len(_ANCHOR_PREP.findall(masked))           # object-anchor relations
    hops += len(_IMAGE_DIR.findall(masked))            # image-frame direction phrases
    if _REL_CLAUSE.search(s):
        hops += 1
    if is_superlative(s) or is_ordinal(s):
        hops += 1
    return hops >= 2


def v2_tags(sentence: str) -> Set[str]:
    """The subset of {superlative, ordinal, group, compositional} that applies to `sentence`."""
    tags = set()
    if is_superlative(sentence):
        tags.add('superlative')
    if is_ordinal(sentence):
        tags.add('ordinal')
    if is_group(sentence):
        tags.add('group')
    if is_compositional(sentence):
        tags.add('compositional')
    return tags


def stratum_tags(sentence: str) -> Set[str]:
    """Full strata set: V1 base type (image|object|attribute) + the applicable V2 tags.
    Lazy-imports geogrounder.data.ref_type so the V2 tag functions stay dependency-free."""
    from geogrounder.data.ref_type import classify_reference
    return {classify_reference(sentence)} | v2_tags(sentence)
