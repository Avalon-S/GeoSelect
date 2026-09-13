"""GeoGrounder — training-free referring remote-sensing image segmentation via
compositional spatial grounding.

Kept import-light on purpose: importing `geogrounder` pulls in NO heavy deps. Import
submodules explicitly, e.g. `from geogrounder.reasoning import SpatialReasoner`
(numpy only) vs `from geogrounder.parsing import QwenParser` (torch/transformers).
"""

__version__ = '0.0.1'
