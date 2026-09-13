"""Reference-expression type classification (image-relative / object-anchor / attribute).

Used for (a) dataset composition stats, (b) STRATIFIED evaluation — reporting oIoU/mIoU per
reference type so the explicit-geometry contribution shows on the subsets where it acts,
instead of being diluted by the ~30% pure-attribute samples.

⚠ This is a HEURISTIC, calibrated against a hand-labelled gold set. The rules cover
directional+object ("above the stadium"), in/on containment, and comparative ("bigger than
the ship") anchors — see _OBJECT_ANCHOR_RE. Known residual: the "frustum of a cone" shape
idiom. Stratification is a
PRESENTATION/analysis device only — it re-buckets fixed per-sample IoUs and never changes any
overall metric. The manual labels remain ground truth; re-validate if applied to a new dataset.

Types:
  object  — references ANOTHER object as anchor ("left OF the stadium", "next to the river")
  image   — position within the image frame, no anchor object ("on the right", "in the middle")
  attribute — no spatial cue, only attributes ("the gray windmill")
"""

import re

_DIRECTION = ['left', 'right', 'above', 'below', 'upper', 'lower', 'top', 'bottom',
              'north', 'south', 'east', 'west', 'middle', 'center', 'centre', 'corner']
# A second entity the target is anchored to. Two detectors:
#  (1) _LEX_LINK: fixed lexical links that always imply an anchor object.
#  (2) _OBJECT_ANCHOR_RE: a locative/comparative preposition + article + a HEAD NOUN that is
#      NOT an image-region word -> "above the stadium" / "in the harbor" / "bigger than the ship" /
#      "of the building" => object; while "on the right" / "in the middle" / "of the lower right"
#      => image-frame (blocked by the (?!_DIR_RE) lookahead). Replaces an earlier fixed
#      " of the / next to " list, which missed directional+object, in/on containment and
#      comparatives. Known residual: "frustum of a cone" reads as an anchor (shape idiom).
_LEX_LINK = [' next to ', ' beside ', ' adjacent to ', ' nearest to ',
             ' surrounding ', ' surrounded by ']
_DIR_RE = (r'(?:left|right|above|below|upper|lower|top|bottom|north|south|east|west|'
           r'middle|center|centre|corner|side|front|back|edge)')
_ANCHOR_PREP = (r'(?:of|above|below|underneath|under|over|behind|beside|atop|'
                r'inside|within|in|on|than|to)')
_OBJECT_ANCHOR_RE = re.compile(
    r'\b' + _ANCHOR_PREP + r'\s+(?:the|a|an)\s+(?!' + _DIR_RE + r'\b)\w+', re.IGNORECASE)
# Image-frame phrasings that LOOK like object anchors due to "of the X" but actually
# reference the image. Common in long-descriptive datasets (RISBench, RefSegRS variants):
# "in the corner of the image", "located on the left side of the picture". The regex masks
# them out before the _OBJECT_LINK check so they don't get tagged as 'object'. Uses \b so
# trailing punctuation ("...image.", "...image,", "...image's") is handled.
_IMAGE_FRAME_RE = re.compile(
    r'\s+(of|in|across|within|throughout)\s+the\s+(image|frame|scene|picture|photo|photograph)\b',
    re.IGNORECASE,
)
_COMPARATIVE = ['than', 'larger', 'smaller', 'bigger', 'closer', 'farther',
                'nearest', 'leftmost', 'rightmost', 'topmost', 'similar in size']


def _has_word(s, words):
    return any(re.search(r'\b' + re.escape(w) + r'\b', s) for w in words)


def classify_reference(sentence):
    """-> 'object' | 'image' | 'attribute' (heuristic; calibrate before quoting).

    Masks "{of,in,across,within} the {image,frame,scene,picture,photo}" before the object-link
    check, so image-frame phrasings aren't tagged as 'object'. See _IMAGE_FRAME_RE note.
    """
    s = ' ' + sentence.lower().strip() + ' '
    s_masked = _IMAGE_FRAME_RE.sub(' ', s)
    has_object_link = bool(_OBJECT_ANCHOR_RE.search(s_masked)) or any(p in s_masked for p in _LEX_LINK)
    has_direction = _has_word(s, _DIRECTION)
    if has_object_link:
        return 'object'
    if has_direction:
        return 'image'
    return 'attribute'


def classify_reference_parsed(rel):
    """Parser-based ref_type classifier — strictly more accurate than the text heuristic.

    Uses the parser's extracted anchor (image/frame/scene -> image-frame; non-empty named
    class -> object) instead of regex on raw text. Recommended for post-hoc analytics
    when parser output is available (e.g. when re-aggregating a pipeline_samples.jsonl
    that was paired with a parse_detect cache).
    """
    IMAGE_SET = {'image', 'frame', 'scene', 'whole image', 'the image',
                 'picture', 'photo', 'photograph', ''}
    if not rel or not rel.get('relations'):
        return 'attribute'
    first = rel['relations'][0]
    a = first.get('anchor', 'image')
    if isinstance(a, str):
        return 'image' if a.strip().lower() in IMAGE_SET else 'object'
    if isinstance(a, dict):
        return 'object'
    return 'attribute'


def is_comparative(sentence):
    s = ' ' + sentence.lower().strip() + ' '
    return _has_word(s, _COMPARATIVE) or any(p in s for p in (' than ',))
