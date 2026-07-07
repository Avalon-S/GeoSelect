window.CASES = [
 {
  "id": "rrsisd_image_422",
  "dataset": "RRSIS-D",
  "type": "image",
  "idx": 422,
  "sentence": "The expressway service area in the middle",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "expressway service area"
   },
   "pred": "CENTER",
   "anchor": "image",
   "kernel_mode": "MONOTONE"
  },
  "iou": 97.4,
  "stages": {
   "input": "static/cases/rrsisd_image_422/input.jpg",
   "candidates": "static/cases/rrsisd_image_422/candidates.jpg",
   "scored": "static/cases/rrsisd_image_422/scored.jpg",
   "mask": "static/cases/rrsisd_image_422/mask.jpg",
   "thumb": "static/cases/rrsisd_image_422/thumb.jpg",
   "gt": "static/cases/rrsisd_image_422/gt.jpg"
  }
 },
 {
  "id": "rrsisd_image_624",
  "dataset": "RRSIS-D",
  "type": "image",
  "idx": 624,
  "sentence": "The storage tank at the bottom",
  "program": {
   "op": "argmax",
   "child": {
    "op": "select",
    "type": "storage tank"
   },
   "axis": "Y"
  },
  "iou": 95.8,
  "stages": {
   "input": "static/cases/rrsisd_image_624/input.jpg",
   "candidates": "static/cases/rrsisd_image_624/candidates.jpg",
   "scored": "static/cases/rrsisd_image_624/scored.jpg",
   "mask": "static/cases/rrsisd_image_624/mask.jpg",
   "thumb": "static/cases/rrsisd_image_624/thumb.jpg",
   "gt": "static/cases/rrsisd_image_624/gt.jpg"
  }
 },
 {
  "id": "rrsisd_image_698",
  "dataset": "RRSIS-D",
  "type": "image",
  "idx": 698,
  "sentence": "A chimney in the middle",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "chimney"
   },
   "pred": "CENTER",
   "anchor": "image",
   "kernel_mode": "MONOTONE"
  },
  "iou": 96.2,
  "stages": {
   "input": "static/cases/rrsisd_image_698/input.jpg",
   "candidates": "static/cases/rrsisd_image_698/candidates.jpg",
   "scored": "static/cases/rrsisd_image_698/scored.jpg",
   "mask": "static/cases/rrsisd_image_698/mask.jpg",
   "thumb": "static/cases/rrsisd_image_698/thumb.jpg",
   "gt": "static/cases/rrsisd_image_698/gt.jpg"
  }
 },
 {
  "id": "rrsisd_image_980",
  "dataset": "RRSIS-D",
  "type": "image",
  "idx": 980,
  "sentence": "The expressway toll station on the left",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "expressway toll station"
   },
   "pred": "LEFT",
   "anchor": "image",
   "kernel_mode": "MONOTONE"
  },
  "iou": 93.0,
  "stages": {
   "input": "static/cases/rrsisd_image_980/input.jpg",
   "candidates": "static/cases/rrsisd_image_980/candidates.jpg",
   "scored": "static/cases/rrsisd_image_980/scored.jpg",
   "mask": "static/cases/rrsisd_image_980/mask.jpg",
   "thumb": "static/cases/rrsisd_image_980/thumb.jpg",
   "gt": "static/cases/rrsisd_image_980/gt.jpg"
  }
 },
 {
  "id": "rrsisd_image_1093",
  "dataset": "RRSIS-D",
  "type": "image",
  "idx": 1093,
  "sentence": "The airplane on the right",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "airplane"
   },
   "pred": "RIGHT",
   "anchor": "image",
   "kernel_mode": "MONOTONE"
  },
  "iou": 88.4,
  "stages": {
   "input": "static/cases/rrsisd_image_1093/input.jpg",
   "candidates": "static/cases/rrsisd_image_1093/candidates.jpg",
   "scored": "static/cases/rrsisd_image_1093/scored.jpg",
   "mask": "static/cases/rrsisd_image_1093/mask.jpg",
   "thumb": "static/cases/rrsisd_image_1093/thumb.jpg",
   "gt": "static/cases/rrsisd_image_1093/gt.jpg"
  }
 },
 {
  "id": "rrsisd_image_1444",
  "dataset": "RRSIS-D",
  "type": "image",
  "idx": 1444,
  "sentence": "A basketball court in the middle",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "basketball court"
   },
   "pred": "CENTER",
   "anchor": "image",
   "kernel_mode": "MONOTONE"
  },
  "iou": 96.9,
  "stages": {
   "input": "static/cases/rrsisd_image_1444/input.jpg",
   "candidates": "static/cases/rrsisd_image_1444/candidates.jpg",
   "scored": "static/cases/rrsisd_image_1444/scored.jpg",
   "mask": "static/cases/rrsisd_image_1444/mask.jpg",
   "thumb": "static/cases/rrsisd_image_1444/thumb.jpg",
   "gt": "static/cases/rrsisd_image_1444/gt.jpg"
  }
 },
 {
  "id": "rrsisd_image_1538",
  "dataset": "RRSIS-D",
  "type": "image",
  "idx": 1538,
  "sentence": "The ground track field on the upper left",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "ground track field"
   },
   "pred": "UL",
   "anchor": "image",
   "kernel_mode": "MONOTONE"
  },
  "iou": 91.8,
  "stages": {
   "input": "static/cases/rrsisd_image_1538/input.jpg",
   "candidates": "static/cases/rrsisd_image_1538/candidates.jpg",
   "scored": "static/cases/rrsisd_image_1538/scored.jpg",
   "mask": "static/cases/rrsisd_image_1538/mask.jpg",
   "thumb": "static/cases/rrsisd_image_1538/thumb.jpg",
   "gt": "static/cases/rrsisd_image_1538/gt.jpg"
  }
 },
 {
  "id": "rrsisd_image_1595",
  "dataset": "RRSIS-D",
  "type": "image",
  "idx": 1595,
  "sentence": "A vehicle on the left",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "vehicle"
   },
   "pred": "LEFT",
   "anchor": "image",
   "kernel_mode": "MONOTONE"
  },
  "iou": 91.3,
  "stages": {
   "input": "static/cases/rrsisd_image_1595/input.jpg",
   "candidates": "static/cases/rrsisd_image_1595/candidates.jpg",
   "scored": "static/cases/rrsisd_image_1595/scored.jpg",
   "mask": "static/cases/rrsisd_image_1595/mask.jpg",
   "thumb": "static/cases/rrsisd_image_1595/thumb.jpg",
   "gt": "static/cases/rrsisd_image_1595/gt.jpg"
  }
 },
 {
  "id": "rrsisd_image_1858",
  "dataset": "RRSIS-D",
  "type": "image",
  "idx": 1858,
  "sentence": "A bridge in the middle",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "bridge"
   },
   "pred": "CENTER",
   "anchor": "image",
   "kernel_mode": "MONOTONE"
  },
  "iou": 95.6,
  "stages": {
   "input": "static/cases/rrsisd_image_1858/input.jpg",
   "candidates": "static/cases/rrsisd_image_1858/candidates.jpg",
   "scored": "static/cases/rrsisd_image_1858/scored.jpg",
   "mask": "static/cases/rrsisd_image_1858/mask.jpg",
   "thumb": "static/cases/rrsisd_image_1858/thumb.jpg",
   "gt": "static/cases/rrsisd_image_1858/gt.jpg"
  }
 },
 {
  "id": "rrsisd_image_2258",
  "dataset": "RRSIS-D",
  "type": "image",
  "idx": 2258,
  "sentence": "A ship on the left",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "ship"
   },
   "pred": "LEFT",
   "anchor": "image",
   "kernel_mode": "MONOTONE"
  },
  "iou": 93.4,
  "stages": {
   "input": "static/cases/rrsisd_image_2258/input.jpg",
   "candidates": "static/cases/rrsisd_image_2258/candidates.jpg",
   "scored": "static/cases/rrsisd_image_2258/scored.jpg",
   "mask": "static/cases/rrsisd_image_2258/mask.jpg",
   "thumb": "static/cases/rrsisd_image_2258/thumb.jpg",
   "gt": "static/cases/rrsisd_image_2258/gt.jpg"
  }
 },
 {
  "id": "rrsisd_image_2433",
  "dataset": "RRSIS-D",
  "type": "image",
  "idx": 2433,
  "sentence": "The windmill on the lower right",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "windmill"
   },
   "pred": "LR",
   "anchor": "image",
   "kernel_mode": "MONOTONE"
  },
  "iou": 71.7,
  "stages": {
   "input": "static/cases/rrsisd_image_2433/input.jpg",
   "candidates": "static/cases/rrsisd_image_2433/candidates.jpg",
   "scored": "static/cases/rrsisd_image_2433/scored.jpg",
   "mask": "static/cases/rrsisd_image_2433/mask.jpg",
   "thumb": "static/cases/rrsisd_image_2433/thumb.jpg",
   "gt": "static/cases/rrsisd_image_2433/gt.jpg"
  }
 },
 {
  "id": "rrsisd_image_2480",
  "dataset": "RRSIS-D",
  "type": "image",
  "idx": 2480,
  "sentence": "A baseball field on the lower left",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "baseball field"
   },
   "pred": "LL",
   "anchor": "image",
   "kernel_mode": "MONOTONE"
  },
  "iou": 96.5,
  "stages": {
   "input": "static/cases/rrsisd_image_2480/input.jpg",
   "candidates": "static/cases/rrsisd_image_2480/candidates.jpg",
   "scored": "static/cases/rrsisd_image_2480/scored.jpg",
   "mask": "static/cases/rrsisd_image_2480/mask.jpg",
   "thumb": "static/cases/rrsisd_image_2480/thumb.jpg",
   "gt": "static/cases/rrsisd_image_2480/gt.jpg"
  }
 },
 {
  "id": "rrsisd_image_2600",
  "dataset": "RRSIS-D",
  "type": "image",
  "idx": 2600,
  "sentence": "The tennis court on the right",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "tennis court"
   },
   "pred": "RIGHT",
   "anchor": "image",
   "kernel_mode": "MONOTONE"
  },
  "iou": 98.1,
  "stages": {
   "input": "static/cases/rrsisd_image_2600/input.jpg",
   "candidates": "static/cases/rrsisd_image_2600/candidates.jpg",
   "scored": "static/cases/rrsisd_image_2600/scored.jpg",
   "mask": "static/cases/rrsisd_image_2600/mask.jpg",
   "thumb": "static/cases/rrsisd_image_2600/thumb.jpg",
   "gt": "static/cases/rrsisd_image_2600/gt.jpg"
  }
 },
 {
  "id": "rrsisd_image_2925",
  "dataset": "RRSIS-D",
  "type": "image",
  "idx": 2925,
  "sentence": "A overpass in the middle",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "overpass"
   },
   "pred": "CENTER",
   "anchor": "image",
   "kernel_mode": "MONOTONE"
  },
  "iou": 97.1,
  "stages": {
   "input": "static/cases/rrsisd_image_2925/input.jpg",
   "candidates": "static/cases/rrsisd_image_2925/candidates.jpg",
   "scored": "static/cases/rrsisd_image_2925/scored.jpg",
   "mask": "static/cases/rrsisd_image_2925/mask.jpg",
   "thumb": "static/cases/rrsisd_image_2925/thumb.jpg",
   "gt": "static/cases/rrsisd_image_2925/gt.jpg"
  }
 },
 {
  "id": "rrsisd_image_2999",
  "dataset": "RRSIS-D",
  "type": "image",
  "idx": 2999,
  "sentence": "A golf field in the middle",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "golf field"
   },
   "pred": "CENTER",
   "anchor": "image",
   "kernel_mode": "MONOTONE"
  },
  "iou": 97.0,
  "stages": {
   "input": "static/cases/rrsisd_image_2999/input.jpg",
   "candidates": "static/cases/rrsisd_image_2999/candidates.jpg",
   "scored": "static/cases/rrsisd_image_2999/scored.jpg",
   "mask": "static/cases/rrsisd_image_2999/mask.jpg",
   "thumb": "static/cases/rrsisd_image_2999/thumb.jpg",
   "gt": "static/cases/rrsisd_image_2999/gt.jpg"
  }
 },
 {
  "id": "rrsisd_object_214",
  "dataset": "RRSIS-D",
  "type": "object",
  "idx": 214,
  "sentence": "The ship on the far right",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "ship"
   },
   "pred": "RIGHT",
   "anchor": "image",
   "kernel_mode": "MONOTONE"
  },
  "iou": 91.0,
  "stages": {
   "input": "static/cases/rrsisd_object_214/input.jpg",
   "candidates": "static/cases/rrsisd_object_214/candidates.jpg",
   "scored": "static/cases/rrsisd_object_214/scored.jpg",
   "mask": "static/cases/rrsisd_object_214/mask.jpg",
   "thumb": "static/cases/rrsisd_object_214/thumb.jpg",
   "gt": "static/cases/rrsisd_object_214/gt.jpg"
  }
 },
 {
  "id": "rrsisd_object_342",
  "dataset": "RRSIS-D",
  "type": "object",
  "idx": 342,
  "sentence": "A huge frustum of a cone chimney in the middle",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "huge frustum of a cone chimney"
   },
   "pred": "CENTER",
   "anchor": "image",
   "kernel_mode": "MONOTONE"
  },
  "iou": 97.9,
  "stages": {
   "input": "static/cases/rrsisd_object_342/input.jpg",
   "candidates": "static/cases/rrsisd_object_342/candidates.jpg",
   "scored": "static/cases/rrsisd_object_342/scored.jpg",
   "mask": "static/cases/rrsisd_object_342/mask.jpg",
   "thumb": "static/cases/rrsisd_object_342/thumb.jpg",
   "gt": "static/cases/rrsisd_object_342/gt.jpg"
  }
 },
 {
  "id": "rrsisd_object_455",
  "dataset": "RRSIS-D",
  "type": "object",
  "idx": 455,
  "sentence": "The expressway service area is above the gray tiny vehicle",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "expressway service area"
   },
   "pred": "TOP",
   "anchor": {
    "op": "select",
    "type": "gray tiny vehicle"
   },
   "kernel_mode": "MONOTONE"
  },
  "iou": 94.0,
  "stages": {
   "input": "static/cases/rrsisd_object_455/input.jpg",
   "candidates": "static/cases/rrsisd_object_455/candidates.jpg",
   "scored": "static/cases/rrsisd_object_455/scored.jpg",
   "mask": "static/cases/rrsisd_object_455/mask.jpg",
   "thumb": "static/cases/rrsisd_object_455/thumb.jpg",
   "gt": "static/cases/rrsisd_object_455/gt.jpg"
  }
 },
 {
  "id": "rrsisd_object_514",
  "dataset": "RRSIS-D",
  "type": "object",
  "idx": 514,
  "sentence": "A blue frustum of a cone chimney in the middle",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "blue frustum of a cone chimney"
   },
   "pred": "CENTER",
   "anchor": "image",
   "kernel_mode": "MONOTONE"
  },
  "iou": 96.7,
  "stages": {
   "input": "static/cases/rrsisd_object_514/input.jpg",
   "candidates": "static/cases/rrsisd_object_514/candidates.jpg",
   "scored": "static/cases/rrsisd_object_514/scored.jpg",
   "mask": "static/cases/rrsisd_object_514/mask.jpg",
   "thumb": "static/cases/rrsisd_object_514/thumb.jpg",
   "gt": "static/cases/rrsisd_object_514/gt.jpg"
  }
 },
 {
  "id": "rrsisd_object_835",
  "dataset": "RRSIS-D",
  "type": "object",
  "idx": 835,
  "sentence": "The tennis court is on the right of the green and orange baseball field",
  "program": null,
  "iou": 94.4,
  "stages": {
   "input": "static/cases/rrsisd_object_835/input.jpg",
   "candidates": "static/cases/rrsisd_object_835/candidates.jpg",
   "scored": "static/cases/rrsisd_object_835/scored.jpg",
   "mask": "static/cases/rrsisd_object_835/mask.jpg",
   "thumb": "static/cases/rrsisd_object_835/thumb.jpg",
   "gt": "static/cases/rrsisd_object_835/gt.jpg"
  }
 },
 {
  "id": "rrsisd_object_931",
  "dataset": "RRSIS-D",
  "type": "object",
  "idx": 931,
  "sentence": "A vehicle is on the right of the red vehicle",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "vehicle"
   },
   "pred": "RIGHT",
   "anchor": {
    "op": "select",
    "type": "red vehicle"
   },
   "kernel_mode": "MONOTONE"
  },
  "iou": 80.9,
  "stages": {
   "input": "static/cases/rrsisd_object_931/input.jpg",
   "candidates": "static/cases/rrsisd_object_931/candidates.jpg",
   "scored": "static/cases/rrsisd_object_931/scored.jpg",
   "mask": "static/cases/rrsisd_object_931/mask.jpg",
   "thumb": "static/cases/rrsisd_object_931/thumb.jpg",
   "gt": "static/cases/rrsisd_object_931/gt.jpg"
  }
 },
 {
  "id": "rrsisd_object_1561",
  "dataset": "RRSIS-D",
  "type": "object",
  "idx": 1561,
  "sentence": "A tennis court on the far left",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "tennis court"
   },
   "pred": "LEFT",
   "anchor": "image",
   "kernel_mode": "MONOTONE"
  },
  "iou": 95.1,
  "stages": {
   "input": "static/cases/rrsisd_object_1561/input.jpg",
   "candidates": "static/cases/rrsisd_object_1561/candidates.jpg",
   "scored": "static/cases/rrsisd_object_1561/scored.jpg",
   "mask": "static/cases/rrsisd_object_1561/mask.jpg",
   "thumb": "static/cases/rrsisd_object_1561/thumb.jpg",
   "gt": "static/cases/rrsisd_object_1561/gt.jpg"
  }
 },
 {
  "id": "rrsisd_object_1587",
  "dataset": "RRSIS-D",
  "type": "object",
  "idx": 1587,
  "sentence": "A bridge is above the slender dam",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "bridge"
   },
   "pred": "TOP",
   "anchor": {
    "op": "select",
    "type": "dam"
   },
   "kernel_mode": "MONOTONE"
  },
  "iou": 78.0,
  "stages": {
   "input": "static/cases/rrsisd_object_1587/input.jpg",
   "candidates": "static/cases/rrsisd_object_1587/candidates.jpg",
   "scored": "static/cases/rrsisd_object_1587/scored.jpg",
   "mask": "static/cases/rrsisd_object_1587/mask.jpg",
   "thumb": "static/cases/rrsisd_object_1587/thumb.jpg",
   "gt": "static/cases/rrsisd_object_1587/gt.jpg"
  }
 },
 {
  "id": "rrsisd_object_1663",
  "dataset": "RRSIS-D",
  "type": "object",
  "idx": 1663,
  "sentence": "A ground track field is in the stadium in the middle",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "ground track field"
   },
   "pred": "CENTER",
   "anchor": "image",
   "kernel_mode": "MONOTONE"
  },
  "iou": 97.9,
  "stages": {
   "input": "static/cases/rrsisd_object_1663/input.jpg",
   "candidates": "static/cases/rrsisd_object_1663/candidates.jpg",
   "scored": "static/cases/rrsisd_object_1663/scored.jpg",
   "mask": "static/cases/rrsisd_object_1663/mask.jpg",
   "thumb": "static/cases/rrsisd_object_1663/thumb.jpg",
   "gt": "static/cases/rrsisd_object_1663/gt.jpg"
  }
 },
 {
  "id": "rrsisd_object_1697",
  "dataset": "RRSIS-D",
  "type": "object",
  "idx": 1697,
  "sentence": "The gray frustum of a cone large chimney",
  "program": {
   "op": "select",
   "type": "gray frustum of a cone large chimney"
  },
  "iou": 96.8,
  "stages": {
   "input": "static/cases/rrsisd_object_1697/input.jpg",
   "candidates": "static/cases/rrsisd_object_1697/candidates.jpg",
   "scored": "static/cases/rrsisd_object_1697/scored.jpg",
   "mask": "static/cases/rrsisd_object_1697/mask.jpg",
   "thumb": "static/cases/rrsisd_object_1697/thumb.jpg",
   "gt": "static/cases/rrsisd_object_1697/gt.jpg"
  }
 },
 {
  "id": "rrsisd_object_2111",
  "dataset": "RRSIS-D",
  "type": "object",
  "idx": 2111,
  "sentence": "The basketball court is on the right of the huge orange baseball field",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "basketball court"
   },
   "pred": "RIGHT",
   "anchor": {
    "op": "select",
    "type": "huge orange baseball field"
   },
   "kernel_mode": "MONOTONE"
  },
  "iou": 94.3,
  "stages": {
   "input": "static/cases/rrsisd_object_2111/input.jpg",
   "candidates": "static/cases/rrsisd_object_2111/candidates.jpg",
   "scored": "static/cases/rrsisd_object_2111/scored.jpg",
   "mask": "static/cases/rrsisd_object_2111/mask.jpg",
   "thumb": "static/cases/rrsisd_object_2111/thumb.jpg",
   "gt": "static/cases/rrsisd_object_2111/gt.jpg"
  }
 },
 {
  "id": "rrsisd_object_2578",
  "dataset": "RRSIS-D",
  "type": "object",
  "idx": 2578,
  "sentence": "A small frustum of a cone chimney",
  "program": {
   "op": "select",
   "type": "small frustum of a cone chimney"
  },
  "iou": 94.8,
  "stages": {
   "input": "static/cases/rrsisd_object_2578/input.jpg",
   "candidates": "static/cases/rrsisd_object_2578/candidates.jpg",
   "scored": "static/cases/rrsisd_object_2578/scored.jpg",
   "mask": "static/cases/rrsisd_object_2578/mask.jpg",
   "thumb": "static/cases/rrsisd_object_2578/thumb.jpg",
   "gt": "static/cases/rrsisd_object_2578/gt.jpg"
  }
 },
 {
  "id": "rrsisd_object_3004",
  "dataset": "RRSIS-D",
  "type": "object",
  "idx": 3004,
  "sentence": "The frustum of a cone large gray chimney",
  "program": {
   "op": "select",
   "type": "frustum of a cone large gray chimney"
  },
  "iou": 97.3,
  "stages": {
   "input": "static/cases/rrsisd_object_3004/input.jpg",
   "candidates": "static/cases/rrsisd_object_3004/candidates.jpg",
   "scored": "static/cases/rrsisd_object_3004/scored.jpg",
   "mask": "static/cases/rrsisd_object_3004/mask.jpg",
   "thumb": "static/cases/rrsisd_object_3004/thumb.jpg",
   "gt": "static/cases/rrsisd_object_3004/gt.jpg"
  }
 },
 {
  "id": "rrsisd_object_3188",
  "dataset": "RRSIS-D",
  "type": "object",
  "idx": 3188,
  "sentence": "A bridge is above the huge gray dam",
  "program": null,
  "iou": 75.1,
  "stages": {
   "input": "static/cases/rrsisd_object_3188/input.jpg",
   "candidates": "static/cases/rrsisd_object_3188/candidates.jpg",
   "scored": "static/cases/rrsisd_object_3188/scored.jpg",
   "mask": "static/cases/rrsisd_object_3188/mask.jpg",
   "thumb": "static/cases/rrsisd_object_3188/thumb.jpg",
   "gt": "static/cases/rrsisd_object_3188/gt.jpg"
  }
 },
 {
  "id": "rrsisd_object_3455",
  "dataset": "RRSIS-D",
  "type": "object",
  "idx": 3455,
  "sentence": "A overpass is on the right of the tiny vehicle",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "overpass"
   },
   "pred": "RIGHT",
   "anchor": {
    "op": "select",
    "type": "tiny vehicle"
   },
   "kernel_mode": "MONOTONE"
  },
  "iou": 94.5,
  "stages": {
   "input": "static/cases/rrsisd_object_3455/input.jpg",
   "candidates": "static/cases/rrsisd_object_3455/candidates.jpg",
   "scored": "static/cases/rrsisd_object_3455/scored.jpg",
   "mask": "static/cases/rrsisd_object_3455/mask.jpg",
   "thumb": "static/cases/rrsisd_object_3455/thumb.jpg",
   "gt": "static/cases/rrsisd_object_3455/gt.jpg"
  }
 },
 {
  "id": "rrsisd_attribute_136",
  "dataset": "RRSIS-D",
  "type": "attribute",
  "idx": 136,
  "sentence": "A gray train station",
  "program": {
   "op": "select",
   "type": "gray train station"
  },
  "iou": 95.8,
  "stages": {
   "input": "static/cases/rrsisd_attribute_136/input.jpg",
   "candidates": "static/cases/rrsisd_attribute_136/candidates.jpg",
   "scored": "static/cases/rrsisd_attribute_136/scored.jpg",
   "mask": "static/cases/rrsisd_attribute_136/mask.jpg",
   "thumb": "static/cases/rrsisd_attribute_136/thumb.jpg",
   "gt": "static/cases/rrsisd_attribute_136/gt.jpg"
  }
 },
 {
  "id": "rrsisd_attribute_552",
  "dataset": "RRSIS-D",
  "type": "attribute",
  "idx": 552,
  "sentence": "A rectangular basketball court",
  "program": {
   "op": "select",
   "type": "rectangular basketball court"
  },
  "iou": 96.8,
  "stages": {
   "input": "static/cases/rrsisd_attribute_552/input.jpg",
   "candidates": "static/cases/rrsisd_attribute_552/candidates.jpg",
   "scored": "static/cases/rrsisd_attribute_552/scored.jpg",
   "mask": "static/cases/rrsisd_attribute_552/mask.jpg",
   "thumb": "static/cases/rrsisd_attribute_552/thumb.jpg",
   "gt": "static/cases/rrsisd_attribute_552/gt.jpg"
  }
 },
 {
  "id": "rrsisd_attribute_864",
  "dataset": "RRSIS-D",
  "type": "attribute",
  "idx": 864,
  "sentence": "A gray bridge",
  "program": {
   "op": "select",
   "type": "gray bridge"
  },
  "iou": 92.6,
  "stages": {
   "input": "static/cases/rrsisd_attribute_864/input.jpg",
   "candidates": "static/cases/rrsisd_attribute_864/candidates.jpg",
   "scored": "static/cases/rrsisd_attribute_864/scored.jpg",
   "mask": "static/cases/rrsisd_attribute_864/mask.jpg",
   "thumb": "static/cases/rrsisd_attribute_864/thumb.jpg",
   "gt": "static/cases/rrsisd_attribute_864/gt.jpg"
  }
 },
 {
  "id": "rrsisd_attribute_928",
  "dataset": "RRSIS-D",
  "type": "attribute",
  "idx": 928,
  "sentence": "The gray stadium",
  "program": {
   "op": "select",
   "type": "gray stadium"
  },
  "iou": 96.2,
  "stages": {
   "input": "static/cases/rrsisd_attribute_928/input.jpg",
   "candidates": "static/cases/rrsisd_attribute_928/candidates.jpg",
   "scored": "static/cases/rrsisd_attribute_928/scored.jpg",
   "mask": "static/cases/rrsisd_attribute_928/mask.jpg",
   "thumb": "static/cases/rrsisd_attribute_928/thumb.jpg",
   "gt": "static/cases/rrsisd_attribute_928/gt.jpg"
  }
 },
 {
  "id": "rrsisd_attribute_1088",
  "dataset": "RRSIS-D",
  "type": "attribute",
  "idx": 1088,
  "sentence": "The large bridge",
  "program": {
   "op": "select",
   "type": "large bridge"
  },
  "iou": 95.5,
  "stages": {
   "input": "static/cases/rrsisd_attribute_1088/input.jpg",
   "candidates": "static/cases/rrsisd_attribute_1088/candidates.jpg",
   "scored": "static/cases/rrsisd_attribute_1088/scored.jpg",
   "mask": "static/cases/rrsisd_attribute_1088/mask.jpg",
   "thumb": "static/cases/rrsisd_attribute_1088/thumb.jpg",
   "gt": "static/cases/rrsisd_attribute_1088/gt.jpg"
  }
 },
 {
  "id": "rrsisd_attribute_1195",
  "dataset": "RRSIS-D",
  "type": "attribute",
  "idx": 1195,
  "sentence": "The small expressway toll station",
  "program": {
   "op": "select",
   "type": "small expressway toll station"
  },
  "iou": 91.9,
  "stages": {
   "input": "static/cases/rrsisd_attribute_1195/input.jpg",
   "candidates": "static/cases/rrsisd_attribute_1195/candidates.jpg",
   "scored": "static/cases/rrsisd_attribute_1195/scored.jpg",
   "mask": "static/cases/rrsisd_attribute_1195/mask.jpg",
   "thumb": "static/cases/rrsisd_attribute_1195/thumb.jpg",
   "gt": "static/cases/rrsisd_attribute_1195/gt.jpg"
  }
 },
 {
  "id": "rrsisd_attribute_1422",
  "dataset": "RRSIS-D",
  "type": "attribute",
  "idx": 1422,
  "sentence": "A large windmill",
  "program": {
   "op": "select",
   "type": "large windmill"
  },
  "iou": 79.7,
  "stages": {
   "input": "static/cases/rrsisd_attribute_1422/input.jpg",
   "candidates": "static/cases/rrsisd_attribute_1422/candidates.jpg",
   "scored": "static/cases/rrsisd_attribute_1422/scored.jpg",
   "mask": "static/cases/rrsisd_attribute_1422/mask.jpg",
   "thumb": "static/cases/rrsisd_attribute_1422/thumb.jpg",
   "gt": "static/cases/rrsisd_attribute_1422/gt.jpg"
  }
 },
 {
  "id": "rrsisd_attribute_1549",
  "dataset": "RRSIS-D",
  "type": "attribute",
  "idx": 1549,
  "sentence": "The gray overpass",
  "program": {
   "op": "select",
   "type": "gray overpass"
  },
  "iou": 96.8,
  "stages": {
   "input": "static/cases/rrsisd_attribute_1549/input.jpg",
   "candidates": "static/cases/rrsisd_attribute_1549/candidates.jpg",
   "scored": "static/cases/rrsisd_attribute_1549/scored.jpg",
   "mask": "static/cases/rrsisd_attribute_1549/mask.jpg",
   "thumb": "static/cases/rrsisd_attribute_1549/thumb.jpg",
   "gt": "static/cases/rrsisd_attribute_1549/gt.jpg"
  }
 },
 {
  "id": "rrsisd_attribute_1604",
  "dataset": "RRSIS-D",
  "type": "attribute",
  "idx": 1604,
  "sentence": "The large storage tank",
  "program": {
   "op": "select",
   "type": "large storage tank"
  },
  "iou": 95.8,
  "stages": {
   "input": "static/cases/rrsisd_attribute_1604/input.jpg",
   "candidates": "static/cases/rrsisd_attribute_1604/candidates.jpg",
   "scored": "static/cases/rrsisd_attribute_1604/scored.jpg",
   "mask": "static/cases/rrsisd_attribute_1604/mask.jpg",
   "thumb": "static/cases/rrsisd_attribute_1604/thumb.jpg",
   "gt": "static/cases/rrsisd_attribute_1604/gt.jpg"
  }
 },
 {
  "id": "rrsisd_attribute_1852",
  "dataset": "RRSIS-D",
  "type": "attribute",
  "idx": 1852,
  "sentence": "A tiny ship",
  "program": {
   "op": "select",
   "type": "tiny ship"
  },
  "iou": 84.1,
  "stages": {
   "input": "static/cases/rrsisd_attribute_1852/input.jpg",
   "candidates": "static/cases/rrsisd_attribute_1852/candidates.jpg",
   "scored": "static/cases/rrsisd_attribute_1852/scored.jpg",
   "mask": "static/cases/rrsisd_attribute_1852/mask.jpg",
   "thumb": "static/cases/rrsisd_attribute_1852/thumb.jpg",
   "gt": "static/cases/rrsisd_attribute_1852/gt.jpg"
  }
 },
 {
  "id": "rrsisd_attribute_3081",
  "dataset": "RRSIS-D",
  "type": "attribute",
  "idx": 3081,
  "sentence": "A large expressway toll station",
  "program": {
   "op": "select",
   "type": "large expressway toll station"
  },
  "iou": 93.0,
  "stages": {
   "input": "static/cases/rrsisd_attribute_3081/input.jpg",
   "candidates": "static/cases/rrsisd_attribute_3081/candidates.jpg",
   "scored": "static/cases/rrsisd_attribute_3081/scored.jpg",
   "mask": "static/cases/rrsisd_attribute_3081/mask.jpg",
   "thumb": "static/cases/rrsisd_attribute_3081/thumb.jpg",
   "gt": "static/cases/rrsisd_attribute_3081/gt.jpg"
  }
 },
 {
  "id": "rrsisd_attribute_3135",
  "dataset": "RRSIS-D",
  "type": "attribute",
  "idx": 3135,
  "sentence": "A large dam",
  "program": {
   "op": "select",
   "type": "large dam"
  },
  "iou": 92.6,
  "stages": {
   "input": "static/cases/rrsisd_attribute_3135/input.jpg",
   "candidates": "static/cases/rrsisd_attribute_3135/candidates.jpg",
   "scored": "static/cases/rrsisd_attribute_3135/scored.jpg",
   "mask": "static/cases/rrsisd_attribute_3135/mask.jpg",
   "thumb": "static/cases/rrsisd_attribute_3135/thumb.jpg",
   "gt": "static/cases/rrsisd_attribute_3135/gt.jpg"
  }
 },
 {
  "id": "rrsisd_attribute_3147",
  "dataset": "RRSIS-D",
  "type": "attribute",
  "idx": 3147,
  "sentence": "The large stadium",
  "program": {
   "op": "select",
   "type": "large stadium"
  },
  "iou": 97.8,
  "stages": {
   "input": "static/cases/rrsisd_attribute_3147/input.jpg",
   "candidates": "static/cases/rrsisd_attribute_3147/candidates.jpg",
   "scored": "static/cases/rrsisd_attribute_3147/scored.jpg",
   "mask": "static/cases/rrsisd_attribute_3147/mask.jpg",
   "thumb": "static/cases/rrsisd_attribute_3147/thumb.jpg",
   "gt": "static/cases/rrsisd_attribute_3147/gt.jpg"
  }
 },
 {
  "id": "rrsisd_attribute_3173",
  "dataset": "RRSIS-D",
  "type": "attribute",
  "idx": 3173,
  "sentence": "A tiny vehicle",
  "program": {
   "op": "select",
   "type": "tiny vehicle"
  },
  "iou": 82.4,
  "stages": {
   "input": "static/cases/rrsisd_attribute_3173/input.jpg",
   "candidates": "static/cases/rrsisd_attribute_3173/candidates.jpg",
   "scored": "static/cases/rrsisd_attribute_3173/scored.jpg",
   "mask": "static/cases/rrsisd_attribute_3173/mask.jpg",
   "thumb": "static/cases/rrsisd_attribute_3173/thumb.jpg",
   "gt": "static/cases/rrsisd_attribute_3173/gt.jpg"
  }
 },
 {
  "id": "rrsisd_attribute_3225",
  "dataset": "RRSIS-D",
  "type": "attribute",
  "idx": 3225,
  "sentence": "The gray windmill",
  "program": {
   "op": "select",
   "type": "gray windmill"
  },
  "iou": 88.1,
  "stages": {
   "input": "static/cases/rrsisd_attribute_3225/input.jpg",
   "candidates": "static/cases/rrsisd_attribute_3225/candidates.jpg",
   "scored": "static/cases/rrsisd_attribute_3225/scored.jpg",
   "mask": "static/cases/rrsisd_attribute_3225/mask.jpg",
   "thumb": "static/cases/rrsisd_attribute_3225/thumb.jpg",
   "gt": "static/cases/rrsisd_attribute_3225/gt.jpg"
  }
 },
 {
  "id": "rrsisd_compositional_51",
  "dataset": "RRSIS-D",
  "type": "compositional",
  "idx": 51,
  "sentence": "The overpass is on the lower right of the small gray vehicle",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "overpass"
   },
   "pred": "LR",
   "anchor": {
    "op": "filter",
    "child": {
     "op": "select",
     "type": "small gray vehicle"
    },
    "pred": "LEFT",
    "anchor": "image",
    "kernel_mode": "MONOTONE"
   },
   "kernel_mode": "MONOTONE"
  },
  "iou": 95.9,
  "stages": {
   "input": "static/cases/rrsisd_compositional_51/input.jpg",
   "candidates": "static/cases/rrsisd_compositional_51/candidates.jpg",
   "scored": "static/cases/rrsisd_compositional_51/scored.jpg",
   "mask": "static/cases/rrsisd_compositional_51/mask.jpg",
   "thumb": "static/cases/rrsisd_compositional_51/thumb.jpg",
   "gt": "static/cases/rrsisd_compositional_51/gt.jpg"
  }
 },
 {
  "id": "rrsisd_compositional_164",
  "dataset": "RRSIS-D",
  "type": "compositional",
  "idx": 164,
  "sentence": "The vehicle is on the lower left of the baseball field on the upper right",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "vehicle"
   },
   "pred": "LL",
   "anchor": {
    "op": "filter",
    "child": {
     "op": "select",
     "type": "baseball field"
    },
    "pred": "UR",
    "anchor": "image",
    "kernel_mode": "MONOTONE"
   },
   "kernel_mode": "MONOTONE"
  },
  "iou": 96.8,
  "stages": {
   "input": "static/cases/rrsisd_compositional_164/input.jpg",
   "candidates": "static/cases/rrsisd_compositional_164/candidates.jpg",
   "scored": "static/cases/rrsisd_compositional_164/scored.jpg",
   "mask": "static/cases/rrsisd_compositional_164/mask.jpg",
   "thumb": "static/cases/rrsisd_compositional_164/thumb.jpg",
   "gt": "static/cases/rrsisd_compositional_164/gt.jpg"
  }
 },
 {
  "id": "rrsisd_compositional_176",
  "dataset": "RRSIS-D",
  "type": "compositional",
  "idx": 176,
  "sentence": "A stadium is on the right of the rectangular blue basketball court on the left",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "stadium"
   },
   "pred": "RIGHT",
   "anchor": {
    "op": "filter",
    "child": {
     "op": "select",
     "type": "rectangular blue basketball court"
    },
    "pred": "LEFT",
    "anchor": "image",
    "kernel_mode": "MONOTONE"
   },
   "kernel_mode": "MONOTONE"
  },
  "iou": 83.4,
  "stages": {
   "input": "static/cases/rrsisd_compositional_176/input.jpg",
   "candidates": "static/cases/rrsisd_compositional_176/candidates.jpg",
   "scored": "static/cases/rrsisd_compositional_176/scored.jpg",
   "mask": "static/cases/rrsisd_compositional_176/mask.jpg",
   "thumb": "static/cases/rrsisd_compositional_176/thumb.jpg",
   "gt": "static/cases/rrsisd_compositional_176/gt.jpg"
  }
 },
 {
  "id": "rrsisd_compositional_207",
  "dataset": "RRSIS-D",
  "type": "compositional",
  "idx": 207,
  "sentence": "The baseball field is on the right of the basketball court in the middle",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "baseball field"
   },
   "pred": "RIGHT",
   "anchor": {
    "op": "filter",
    "child": {
     "op": "select",
     "type": "basketball court"
    },
    "pred": "CENTER",
    "anchor": "image",
    "kernel_mode": "MONOTONE"
   },
   "kernel_mode": "MONOTONE"
  },
  "iou": 96.7,
  "stages": {
   "input": "static/cases/rrsisd_compositional_207/input.jpg",
   "candidates": "static/cases/rrsisd_compositional_207/candidates.jpg",
   "scored": "static/cases/rrsisd_compositional_207/scored.jpg",
   "mask": "static/cases/rrsisd_compositional_207/mask.jpg",
   "thumb": "static/cases/rrsisd_compositional_207/thumb.jpg",
   "gt": "static/cases/rrsisd_compositional_207/gt.jpg"
  }
 },
 {
  "id": "rrsisd_compositional_351",
  "dataset": "RRSIS-D",
  "type": "compositional",
  "idx": 351,
  "sentence": "A chimney is on the upper right of the chimney at the bottom",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "chimney"
   },
   "pred": "UR",
   "anchor": {
    "op": "filter",
    "child": {
     "op": "select",
     "type": "chimney"
    },
    "pred": "BOTTOM",
    "anchor": "image",
    "kernel_mode": "MONOTONE"
   },
   "kernel_mode": "MONOTONE"
  },
  "iou": 84.3,
  "stages": {
   "input": "static/cases/rrsisd_compositional_351/input.jpg",
   "candidates": "static/cases/rrsisd_compositional_351/candidates.jpg",
   "scored": "static/cases/rrsisd_compositional_351/scored.jpg",
   "mask": "static/cases/rrsisd_compositional_351/mask.jpg",
   "thumb": "static/cases/rrsisd_compositional_351/thumb.jpg",
   "gt": "static/cases/rrsisd_compositional_351/gt.jpg"
  }
 },
 {
  "id": "rrsisd_compositional_635",
  "dataset": "RRSIS-D",
  "type": "compositional",
  "idx": 635,
  "sentence": "A ground track field is on the lower right of the small baseball field on the upper left",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "ground track field"
   },
   "pred": "LR",
   "anchor": {
    "op": "filter",
    "child": {
     "op": "select",
     "type": "small baseball field"
    },
    "pred": "UL",
    "anchor": "image",
    "kernel_mode": "MONOTONE"
   },
   "kernel_mode": "MONOTONE"
  },
  "iou": 96.7,
  "stages": {
   "input": "static/cases/rrsisd_compositional_635/input.jpg",
   "candidates": "static/cases/rrsisd_compositional_635/candidates.jpg",
   "scored": "static/cases/rrsisd_compositional_635/scored.jpg",
   "mask": "static/cases/rrsisd_compositional_635/mask.jpg",
   "thumb": "static/cases/rrsisd_compositional_635/thumb.jpg",
   "gt": "static/cases/rrsisd_compositional_635/gt.jpg"
  }
 },
 {
  "id": "rrsisd_compositional_1027",
  "dataset": "RRSIS-D",
  "type": "compositional",
  "idx": 1027,
  "sentence": "The airplane is below the airplane on the upper right",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "airplane"
   },
   "pred": "BOTTOM",
   "anchor": {
    "op": "filter",
    "child": {
     "op": "select",
     "type": "airplane"
    },
    "pred": "UR",
    "anchor": "image",
    "kernel_mode": "MONOTONE"
   },
   "kernel_mode": "MONOTONE"
  },
  "iou": 70.6,
  "stages": {
   "input": "static/cases/rrsisd_compositional_1027/input.jpg",
   "candidates": "static/cases/rrsisd_compositional_1027/candidates.jpg",
   "scored": "static/cases/rrsisd_compositional_1027/scored.jpg",
   "mask": "static/cases/rrsisd_compositional_1027/mask.jpg",
   "thumb": "static/cases/rrsisd_compositional_1027/thumb.jpg",
   "gt": "static/cases/rrsisd_compositional_1027/gt.jpg"
  }
 },
 {
  "id": "rrsisd_compositional_1101",
  "dataset": "RRSIS-D",
  "type": "compositional",
  "idx": 1101,
  "sentence": "The expressway service area is on the right of the vehicle on the top",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "expressway service area"
   },
   "pred": "RIGHT",
   "anchor": {
    "op": "filter",
    "child": {
     "op": "select",
     "type": "vehicle"
    },
    "pred": "TOP",
    "anchor": "image",
    "kernel_mode": "MONOTONE"
   },
   "kernel_mode": "MONOTONE"
  },
  "iou": 96.1,
  "stages": {
   "input": "static/cases/rrsisd_compositional_1101/input.jpg",
   "candidates": "static/cases/rrsisd_compositional_1101/candidates.jpg",
   "scored": "static/cases/rrsisd_compositional_1101/scored.jpg",
   "mask": "static/cases/rrsisd_compositional_1101/mask.jpg",
   "thumb": "static/cases/rrsisd_compositional_1101/thumb.jpg",
   "gt": "static/cases/rrsisd_compositional_1101/gt.jpg"
  }
 },
 {
  "id": "rrsisd_compositional_1748",
  "dataset": "RRSIS-D",
  "type": "compositional",
  "idx": 1748,
  "sentence": "The harbor is on the left of the ship on the right",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "harbor"
   },
   "pred": "LEFT",
   "anchor": {
    "op": "filter",
    "child": {
     "op": "select",
     "type": "ship"
    },
    "pred": "RIGHT",
    "anchor": "image",
    "kernel_mode": "MONOTONE"
   },
   "kernel_mode": "MONOTONE"
  },
  "iou": 88.0,
  "stages": {
   "input": "static/cases/rrsisd_compositional_1748/input.jpg",
   "candidates": "static/cases/rrsisd_compositional_1748/candidates.jpg",
   "scored": "static/cases/rrsisd_compositional_1748/scored.jpg",
   "mask": "static/cases/rrsisd_compositional_1748/mask.jpg",
   "thumb": "static/cases/rrsisd_compositional_1748/thumb.jpg",
   "gt": "static/cases/rrsisd_compositional_1748/gt.jpg"
  }
 },
 {
  "id": "rrsisd_compositional_1957",
  "dataset": "RRSIS-D",
  "type": "compositional",
  "idx": 1957,
  "sentence": "The ship is on the lower right of the large train station",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "ship"
   },
   "pred": "LR",
   "anchor": {
    "op": "select",
    "type": "large train station"
   },
   "kernel_mode": "MONOTONE"
  },
  "iou": 89.3,
  "stages": {
   "input": "static/cases/rrsisd_compositional_1957/input.jpg",
   "candidates": "static/cases/rrsisd_compositional_1957/candidates.jpg",
   "scored": "static/cases/rrsisd_compositional_1957/scored.jpg",
   "mask": "static/cases/rrsisd_compositional_1957/mask.jpg",
   "thumb": "static/cases/rrsisd_compositional_1957/thumb.jpg",
   "gt": "static/cases/rrsisd_compositional_1957/gt.jpg"
  }
 },
 {
  "id": "rrsisd_compositional_1988",
  "dataset": "RRSIS-D",
  "type": "compositional",
  "idx": 1988,
  "sentence": "The basketball court is on the lower right of the tennis court on the top",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "basketball court"
   },
   "pred": "LR",
   "anchor": {
    "op": "filter",
    "child": {
     "op": "select",
     "type": "tennis court"
    },
    "pred": "TOP",
    "anchor": "image",
    "kernel_mode": "MONOTONE"
   },
   "kernel_mode": "MONOTONE"
  },
  "iou": 95.5,
  "stages": {
   "input": "static/cases/rrsisd_compositional_1988/input.jpg",
   "candidates": "static/cases/rrsisd_compositional_1988/candidates.jpg",
   "scored": "static/cases/rrsisd_compositional_1988/scored.jpg",
   "mask": "static/cases/rrsisd_compositional_1988/mask.jpg",
   "thumb": "static/cases/rrsisd_compositional_1988/thumb.jpg",
   "gt": "static/cases/rrsisd_compositional_1988/gt.jpg"
  }
 },
 {
  "id": "rrsisd_compositional_2430",
  "dataset": "RRSIS-D",
  "type": "compositional",
  "idx": 2430,
  "sentence": "A expressway toll station is on the lower left of the vehicle on the top",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "expressway toll station"
   },
   "pred": "LL",
   "anchor": {
    "op": "filter",
    "child": {
     "op": "select",
     "type": "vehicle"
    },
    "pred": "TOP",
    "anchor": "image",
    "kernel_mode": "MONOTONE"
   },
   "kernel_mode": "MONOTONE"
  },
  "iou": 89.8,
  "stages": {
   "input": "static/cases/rrsisd_compositional_2430/input.jpg",
   "candidates": "static/cases/rrsisd_compositional_2430/candidates.jpg",
   "scored": "static/cases/rrsisd_compositional_2430/scored.jpg",
   "mask": "static/cases/rrsisd_compositional_2430/mask.jpg",
   "thumb": "static/cases/rrsisd_compositional_2430/thumb.jpg",
   "gt": "static/cases/rrsisd_compositional_2430/gt.jpg"
  }
 },
 {
  "id": "rrsisd_compositional_2561",
  "dataset": "RRSIS-D",
  "type": "compositional",
  "idx": 2561,
  "sentence": "A bridge is on the upper right of the vehicle on the lower left",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "bridge"
   },
   "pred": "UR",
   "anchor": {
    "op": "filter",
    "child": {
     "op": "select",
     "type": "vehicle"
    },
    "pred": "LL",
    "anchor": "image",
    "kernel_mode": "MONOTONE"
   },
   "kernel_mode": "MONOTONE"
  },
  "iou": 96.0,
  "stages": {
   "input": "static/cases/rrsisd_compositional_2561/input.jpg",
   "candidates": "static/cases/rrsisd_compositional_2561/candidates.jpg",
   "scored": "static/cases/rrsisd_compositional_2561/scored.jpg",
   "mask": "static/cases/rrsisd_compositional_2561/mask.jpg",
   "thumb": "static/cases/rrsisd_compositional_2561/thumb.jpg",
   "gt": "static/cases/rrsisd_compositional_2561/gt.jpg"
  }
 },
 {
  "id": "rrsisd_compositional_2668",
  "dataset": "RRSIS-D",
  "type": "compositional",
  "idx": 2668,
  "sentence": "The tennis court is on the lower right of the basketball court on the top",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "tennis court"
   },
   "pred": "LR",
   "anchor": {
    "op": "filter",
    "child": {
     "op": "select",
     "type": "basketball court"
    },
    "pred": "TOP",
    "anchor": "image",
    "kernel_mode": "MONOTONE"
   },
   "kernel_mode": "MONOTONE"
  },
  "iou": 96.1,
  "stages": {
   "input": "static/cases/rrsisd_compositional_2668/input.jpg",
   "candidates": "static/cases/rrsisd_compositional_2668/candidates.jpg",
   "scored": "static/cases/rrsisd_compositional_2668/scored.jpg",
   "mask": "static/cases/rrsisd_compositional_2668/mask.jpg",
   "thumb": "static/cases/rrsisd_compositional_2668/thumb.jpg",
   "gt": "static/cases/rrsisd_compositional_2668/gt.jpg"
  }
 },
 {
  "id": "rrsisd_compositional_2731",
  "dataset": "RRSIS-D",
  "type": "compositional",
  "idx": 2731,
  "sentence": "A storage tank is on the upper left of the chimney in the middle",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "storage tank"
   },
   "pred": "UL",
   "anchor": {
    "op": "filter",
    "child": {
     "op": "select",
     "type": "chimney"
    },
    "pred": "CENTER",
    "anchor": "image",
    "kernel_mode": "MONOTONE"
   },
   "kernel_mode": "MONOTONE"
  },
  "iou": 89.3,
  "stages": {
   "input": "static/cases/rrsisd_compositional_2731/input.jpg",
   "candidates": "static/cases/rrsisd_compositional_2731/candidates.jpg",
   "scored": "static/cases/rrsisd_compositional_2731/scored.jpg",
   "mask": "static/cases/rrsisd_compositional_2731/mask.jpg",
   "thumb": "static/cases/rrsisd_compositional_2731/thumb.jpg",
   "gt": "static/cases/rrsisd_compositional_2731/gt.jpg"
  }
 },
 {
  "id": "risbench_image_1080",
  "dataset": "RISBench",
  "type": "image",
  "idx": 1080,
  "sentence": "The small vehicle is located near the bottom left corner of the image.",
  "program": {
   "op": "relate",
   "child": {
    "op": "select",
    "type": "small vehicle"
   },
   "rel": "NEAR",
   "anchor": {
    "op": "select",
    "type": "bottom left corner"
   }
  },
  "iou": 100.0,
  "stages": {
   "input": "static/cases/risbench_image_1080/input.jpg",
   "candidates": "static/cases/risbench_image_1080/candidates.jpg",
   "scored": "static/cases/risbench_image_1080/scored.jpg",
   "mask": "static/cases/risbench_image_1080/mask.jpg",
   "thumb": "static/cases/risbench_image_1080/thumb.jpg",
   "gt": "static/cases/risbench_image_1080/gt.jpg"
  }
 },
 {
  "id": "risbench_image_1399",
  "dataset": "RISBench",
  "type": "image",
  "idx": 1399,
  "sentence": "The harbor located toward the bottom middle of the image, by the water.",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "harbor"
   },
   "pred": "BOTTOM",
   "anchor": "image",
   "kernel_mode": "MONOTONE"
  },
  "iou": 99.2,
  "stages": {
   "input": "static/cases/risbench_image_1399/input.jpg",
   "candidates": "static/cases/risbench_image_1399/candidates.jpg",
   "scored": "static/cases/risbench_image_1399/scored.jpg",
   "mask": "static/cases/risbench_image_1399/mask.jpg",
   "thumb": "static/cases/risbench_image_1399/thumb.jpg",
   "gt": "static/cases/risbench_image_1399/gt.jpg"
  }
 },
 {
  "id": "risbench_image_1491",
  "dataset": "RISBench",
  "type": "image",
  "idx": 1491,
  "sentence": "The large vehicle is located in the top-left of the image.",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "large vehicle"
   },
   "pred": "UL",
   "anchor": "image",
   "kernel_mode": "MONOTONE"
  },
  "iou": 99.3,
  "stages": {
   "input": "static/cases/risbench_image_1491/input.jpg",
   "candidates": "static/cases/risbench_image_1491/candidates.jpg",
   "scored": "static/cases/risbench_image_1491/scored.jpg",
   "mask": "static/cases/risbench_image_1491/mask.jpg",
   "thumb": "static/cases/risbench_image_1491/thumb.jpg",
   "gt": "static/cases/risbench_image_1491/gt.jpg"
  }
 },
 {
  "id": "risbench_image_1978",
  "dataset": "RISBench",
  "type": "image",
  "idx": 1978,
  "sentence": "The tennis court located on the left side of the image.",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "tennis court"
   },
   "pred": "LEFT",
   "anchor": "image",
   "kernel_mode": "MONOTONE"
  },
  "iou": 99.9,
  "stages": {
   "input": "static/cases/risbench_image_1978/input.jpg",
   "candidates": "static/cases/risbench_image_1978/candidates.jpg",
   "scored": "static/cases/risbench_image_1978/scored.jpg",
   "mask": "static/cases/risbench_image_1978/mask.jpg",
   "thumb": "static/cases/risbench_image_1978/thumb.jpg",
   "gt": "static/cases/risbench_image_1978/gt.jpg"
  }
 },
 {
  "id": "risbench_image_3420",
  "dataset": "RISBench",
  "type": "image",
  "idx": 3420,
  "sentence": "The ship located in the right side of the image.",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "ship"
   },
   "pred": "RIGHT",
   "anchor": "image",
   "kernel_mode": "MONOTONE"
  },
  "iou": 100.0,
  "stages": {
   "input": "static/cases/risbench_image_3420/input.jpg",
   "candidates": "static/cases/risbench_image_3420/candidates.jpg",
   "scored": "static/cases/risbench_image_3420/scored.jpg",
   "mask": "static/cases/risbench_image_3420/mask.jpg",
   "thumb": "static/cases/risbench_image_3420/thumb.jpg",
   "gt": "static/cases/risbench_image_3420/gt.jpg"
  }
 },
 {
  "id": "risbench_image_10151",
  "dataset": "RISBench",
  "type": "image",
  "idx": 10151,
  "sentence": "The vehicle towards the middle-right part of the image.",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "vehicle"
   },
   "pred": "RIGHT",
   "anchor": "image",
   "kernel_mode": "MONOTONE"
  },
  "iou": 99.6,
  "stages": {
   "input": "static/cases/risbench_image_10151/input.jpg",
   "candidates": "static/cases/risbench_image_10151/candidates.jpg",
   "scored": "static/cases/risbench_image_10151/scored.jpg",
   "mask": "static/cases/risbench_image_10151/mask.jpg",
   "thumb": "static/cases/risbench_image_10151/thumb.jpg",
   "gt": "static/cases/risbench_image_10151/gt.jpg"
  }
 },
 {
  "id": "risbench_image_11470",
  "dataset": "RISBench",
  "type": "image",
  "idx": 11470,
  "sentence": "The bridge is located at the right of the image.",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "bridge"
   },
   "pred": "RIGHT",
   "anchor": "image",
   "kernel_mode": "MONOTONE"
  },
  "iou": 99.6,
  "stages": {
   "input": "static/cases/risbench_image_11470/input.jpg",
   "candidates": "static/cases/risbench_image_11470/candidates.jpg",
   "scored": "static/cases/risbench_image_11470/scored.jpg",
   "mask": "static/cases/risbench_image_11470/mask.jpg",
   "thumb": "static/cases/risbench_image_11470/thumb.jpg",
   "gt": "static/cases/risbench_image_11470/gt.jpg"
  }
 },
 {
  "id": "risbench_image_12090",
  "dataset": "RISBench",
  "type": "image",
  "idx": 12090,
  "sentence": "The storage tank located at the top-right corner of the image is partially cut off by the edge of the frame.",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "storage tank"
   },
   "pred": "UR",
   "anchor": "image",
   "kernel_mode": "MONOTONE"
  },
  "iou": 99.6,
  "stages": {
   "input": "static/cases/risbench_image_12090/input.jpg",
   "candidates": "static/cases/risbench_image_12090/candidates.jpg",
   "scored": "static/cases/risbench_image_12090/scored.jpg",
   "mask": "static/cases/risbench_image_12090/mask.jpg",
   "thumb": "static/cases/risbench_image_12090/thumb.jpg",
   "gt": "static/cases/risbench_image_12090/gt.jpg"
  }
 },
 {
  "id": "risbench_image_14041",
  "dataset": "RISBench",
  "type": "image",
  "idx": 14041,
  "sentence": "The plane at the very bottom of the image.",
  "program": {
   "op": "argmax",
   "child": {
    "op": "select",
    "type": "plane"
   },
   "axis": "Y"
  },
  "iou": 99.2,
  "stages": {
   "input": "static/cases/risbench_image_14041/input.jpg",
   "candidates": "static/cases/risbench_image_14041/candidates.jpg",
   "scored": "static/cases/risbench_image_14041/scored.jpg",
   "mask": "static/cases/risbench_image_14041/mask.jpg",
   "thumb": "static/cases/risbench_image_14041/thumb.jpg",
   "gt": "static/cases/risbench_image_14041/gt.jpg"
  }
 },
 {
  "id": "risbench_object_86",
  "dataset": "RISBench",
  "type": "object",
  "idx": 86,
  "sentence": "The large vehicle located near the top-middle of the image, closer to the buildings with gray rooftops.",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "large vehicle"
   },
   "pred": "NEAR",
   "anchor": {
    "op": "filter",
    "child": {
     "op": "select",
     "type": "building"
    },
    "pred": "CENTER",
    "anchor": "image",
    "kernel_mode": "MONOTONE"
   },
   "kernel_mode": "MONOTONE"
  },
  "iou": 98.2,
  "stages": {
   "input": "static/cases/risbench_object_86/input.jpg",
   "candidates": "static/cases/risbench_object_86/candidates.jpg",
   "scored": "static/cases/risbench_object_86/scored.jpg",
   "mask": "static/cases/risbench_object_86/mask.jpg",
   "thumb": "static/cases/risbench_object_86/thumb.jpg",
   "gt": "static/cases/risbench_object_86/gt.jpg"
  }
 },
 {
  "id": "risbench_object_259",
  "dataset": "RISBench",
  "type": "object",
  "idx": 259,
  "sentence": "The small ship is located towards the bottom-left corner, making a distinctive trail in the water.",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "small ship"
   },
   "pred": "LL",
   "anchor": "image",
   "kernel_mode": "MONOTONE"
  },
  "iou": 99.2,
  "stages": {
   "input": "static/cases/risbench_object_259/input.jpg",
   "candidates": "static/cases/risbench_object_259/candidates.jpg",
   "scored": "static/cases/risbench_object_259/scored.jpg",
   "mask": "static/cases/risbench_object_259/mask.jpg",
   "thumb": "static/cases/risbench_object_259/thumb.jpg",
   "gt": "static/cases/risbench_object_259/gt.jpg"
  }
 },
 {
  "id": "risbench_object_6344",
  "dataset": "RISBench",
  "type": "object",
  "idx": 6344,
  "sentence": "The small vehicle at the bottom right is positioned on the road.",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "small vehicle"
   },
   "pred": "LR",
   "anchor": "image",
   "kernel_mode": "MONOTONE"
  },
  "iou": 100.0,
  "stages": {
   "input": "static/cases/risbench_object_6344/input.jpg",
   "candidates": "static/cases/risbench_object_6344/candidates.jpg",
   "scored": "static/cases/risbench_object_6344/scored.jpg",
   "mask": "static/cases/risbench_object_6344/mask.jpg",
   "thumb": "static/cases/risbench_object_6344/thumb.jpg",
   "gt": "static/cases/risbench_object_6344/gt.jpg"
  }
 },
 {
  "id": "risbench_object_6591",
  "dataset": "RISBench",
  "type": "object",
  "idx": 6591,
  "sentence": "The small plane located towards the bottom middle part of the image on an airstrip.",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "small plane"
   },
   "pred": "BOTTOM",
   "anchor": "image",
   "kernel_mode": "MONOTONE"
  },
  "iou": 98.8,
  "stages": {
   "input": "static/cases/risbench_object_6591/input.jpg",
   "candidates": "static/cases/risbench_object_6591/candidates.jpg",
   "scored": "static/cases/risbench_object_6591/scored.jpg",
   "mask": "static/cases/risbench_object_6591/mask.jpg",
   "thumb": "static/cases/risbench_object_6591/thumb.jpg",
   "gt": "static/cases/risbench_object_6591/gt.jpg"
  }
 },
 {
  "id": "risbench_object_7576",
  "dataset": "RISBench",
  "type": "object",
  "idx": 7576,
  "sentence": "The vehicle can be seen parked on the right side of a driveway.",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "vehicle"
   },
   "pred": "RIGHT",
   "anchor": "image",
   "kernel_mode": "MONOTONE"
  },
  "iou": 99.8,
  "stages": {
   "input": "static/cases/risbench_object_7576/input.jpg",
   "candidates": "static/cases/risbench_object_7576/candidates.jpg",
   "scored": "static/cases/risbench_object_7576/scored.jpg",
   "mask": "static/cases/risbench_object_7576/mask.jpg",
   "thumb": "static/cases/risbench_object_7576/thumb.jpg",
   "gt": "static/cases/risbench_object_7576/gt.jpg"
  }
 },
 {
  "id": "risbench_object_9469",
  "dataset": "RISBench",
  "type": "object",
  "idx": 9469,
  "sentence": "The harbor located in the middle-right of the image has a dock that aligns parallel to the image's right edge.",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "harbor"
   },
   "pred": "RIGHT",
   "anchor": "image",
   "kernel_mode": "MONOTONE"
  },
  "iou": 99.6,
  "stages": {
   "input": "static/cases/risbench_object_9469/input.jpg",
   "candidates": "static/cases/risbench_object_9469/candidates.jpg",
   "scored": "static/cases/risbench_object_9469/scored.jpg",
   "mask": "static/cases/risbench_object_9469/mask.jpg",
   "thumb": "static/cases/risbench_object_9469/thumb.jpg",
   "gt": "static/cases/risbench_object_9469/gt.jpg"
  }
 },
 {
  "id": "risbench_object_10666",
  "dataset": "RISBench",
  "type": "object",
  "idx": 10666,
  "sentence": "The ship located on the water body towards the top-left of the image.",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "ship"
   },
   "pred": "UL",
   "anchor": "image",
   "kernel_mode": "MONOTONE"
  },
  "iou": 99.2,
  "stages": {
   "input": "static/cases/risbench_object_10666/input.jpg",
   "candidates": "static/cases/risbench_object_10666/candidates.jpg",
   "scored": "static/cases/risbench_object_10666/scored.jpg",
   "mask": "static/cases/risbench_object_10666/mask.jpg",
   "thumb": "static/cases/risbench_object_10666/thumb.jpg",
   "gt": "static/cases/risbench_object_10666/gt.jpg"
  }
 },
 {
  "id": "risbench_object_12430",
  "dataset": "RISBench",
  "type": "object",
  "idx": 12430,
  "sentence": "The small bridge spans across the image vertically over a body of water.",
  "program": null,
  "iou": 99.7,
  "stages": {
   "input": "static/cases/risbench_object_12430/input.jpg",
   "candidates": "static/cases/risbench_object_12430/candidates.jpg",
   "scored": "static/cases/risbench_object_12430/scored.jpg",
   "mask": "static/cases/risbench_object_12430/mask.jpg",
   "thumb": "static/cases/risbench_object_12430/thumb.jpg",
   "gt": "static/cases/risbench_object_12430/gt.jpg"
  }
 },
 {
  "id": "risbench_object_16111",
  "dataset": "RISBench",
  "type": "object",
  "idx": 16111,
  "sentence": "The tennis court abutting the right edge of the image is marked with clear boundary lines and surrounded by a red area.",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "tennis court"
   },
   "pred": "RIGHT",
   "anchor": "image",
   "kernel_mode": "MONOTONE"
  },
  "iou": 99.9,
  "stages": {
   "input": "static/cases/risbench_object_16111/input.jpg",
   "candidates": "static/cases/risbench_object_16111/candidates.jpg",
   "scored": "static/cases/risbench_object_16111/scored.jpg",
   "mask": "static/cases/risbench_object_16111/mask.jpg",
   "thumb": "static/cases/risbench_object_16111/thumb.jpg",
   "gt": "static/cases/risbench_object_16111/gt.jpg"
  }
 },
 {
  "id": "risbench_attribute_2144",
  "dataset": "RISBench",
  "type": "attribute",
  "idx": 2144,
  "sentence": "The ship is located at the rght edge of the image and it extends into the water.",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "ship"
   },
   "pred": "RIGHT",
   "anchor": "image",
   "kernel_mode": "MONOTONE"
  },
  "iou": 99.6,
  "stages": {
   "input": "static/cases/risbench_attribute_2144/input.jpg",
   "candidates": "static/cases/risbench_attribute_2144/candidates.jpg",
   "scored": "static/cases/risbench_attribute_2144/scored.jpg",
   "mask": "static/cases/risbench_attribute_2144/mask.jpg",
   "thumb": "static/cases/risbench_attribute_2144/thumb.jpg",
   "gt": "static/cases/risbench_attribute_2144/gt.jpg"
  }
 },
 {
  "id": "risbench_attribute_9240",
  "dataset": "RISBench",
  "type": "attribute",
  "idx": 9240,
  "sentence": "The expressway service area is characterized by its large size and a distinctive terracotta colored roof.",
  "program": {
   "op": "select",
   "type": "expressway service area"
  },
  "iou": 96.6,
  "stages": {
   "input": "static/cases/risbench_attribute_9240/input.jpg",
   "candidates": "static/cases/risbench_attribute_9240/candidates.jpg",
   "scored": "static/cases/risbench_attribute_9240/scored.jpg",
   "mask": "static/cases/risbench_attribute_9240/mask.jpg",
   "thumb": "static/cases/risbench_attribute_9240/thumb.jpg",
   "gt": "static/cases/risbench_attribute_9240/gt.jpg"
  }
 },
 {
  "id": "risbench_attribute_10596",
  "dataset": "RISBench",
  "type": "attribute",
  "idx": 10596,
  "sentence": "The bridge in the image spans the river and is visible as a distinct line connecting the roadways across the water.",
  "program": {
   "op": "select",
   "type": "bridge"
  },
  "iou": 98.1,
  "stages": {
   "input": "static/cases/risbench_attribute_10596/input.jpg",
   "candidates": "static/cases/risbench_attribute_10596/candidates.jpg",
   "scored": "static/cases/risbench_attribute_10596/scored.jpg",
   "mask": "static/cases/risbench_attribute_10596/mask.jpg",
   "thumb": "static/cases/risbench_attribute_10596/thumb.jpg",
   "gt": "static/cases/risbench_attribute_10596/gt.jpg"
  }
 },
 {
  "id": "risbench_attribute_11655",
  "dataset": "RISBench",
  "type": "attribute",
  "idx": 11655,
  "sentence": "The overpass that spans the width of the image and intersects other roads.",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "overpass"
   },
   "pred": "LEFT",
   "anchor": "image",
   "kernel_mode": "MONOTONE"
  },
  "iou": 98.4,
  "stages": {
   "input": "static/cases/risbench_attribute_11655/input.jpg",
   "candidates": "static/cases/risbench_attribute_11655/candidates.jpg",
   "scored": "static/cases/risbench_attribute_11655/scored.jpg",
   "mask": "static/cases/risbench_attribute_11655/mask.jpg",
   "thumb": "static/cases/risbench_attribute_11655/thumb.jpg",
   "gt": "static/cases/risbench_attribute_11655/gt.jpg"
  }
 },
 {
  "id": "risbench_superlative_403",
  "dataset": "RISBench",
  "type": "superlative",
  "idx": 403,
  "sentence": "The right-most large vehicle parked towards the middle-right of the image.",
  "program": {
   "op": "argmax",
   "child": {
    "op": "filter",
    "child": {
     "op": "select",
     "type": "large vehicle"
    },
    "pred": "RIGHT",
    "anchor": "image",
    "kernel_mode": "MONOTONE"
   },
   "axis": "X"
  },
  "iou": 99.0,
  "stages": {
   "input": "static/cases/risbench_superlative_403/input.jpg",
   "candidates": "static/cases/risbench_superlative_403/candidates.jpg",
   "scored": "static/cases/risbench_superlative_403/scored.jpg",
   "mask": "static/cases/risbench_superlative_403/mask.jpg",
   "thumb": "static/cases/risbench_superlative_403/thumb.jpg",
   "gt": "static/cases/risbench_superlative_403/gt.jpg"
  }
 },
 {
  "id": "risbench_superlative_1412",
  "dataset": "RISBench",
  "type": "superlative",
  "idx": 1412,
  "sentence": "The top-most swimming pool located just above the lower swimming pool near the center of the image.",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "swimming pool"
   },
   "pred": "TOP",
   "anchor": {
    "op": "filter",
    "child": {
     "op": "select",
     "type": "swimming pool"
    },
    "pred": "BOTTOM",
    "anchor": "image",
    "kernel_mode": "MONOTONE"
   },
   "kernel_mode": "MONOTONE"
  },
  "iou": 99.4,
  "stages": {
   "input": "static/cases/risbench_superlative_1412/input.jpg",
   "candidates": "static/cases/risbench_superlative_1412/candidates.jpg",
   "scored": "static/cases/risbench_superlative_1412/scored.jpg",
   "mask": "static/cases/risbench_superlative_1412/mask.jpg",
   "thumb": "static/cases/risbench_superlative_1412/thumb.jpg",
   "gt": "static/cases/risbench_superlative_1412/gt.jpg"
  }
 },
 {
  "id": "risbench_superlative_1823",
  "dataset": "RISBench",
  "type": "superlative",
  "idx": 1823,
  "sentence": "The top-most basketball court is rotated relative to the other, with its longer dimension not parallel to the edges of the image.",
  "program": {
   "op": "argmin",
   "child": {
    "op": "select",
    "type": "basketball court"
   },
   "axis": "Y"
  },
  "iou": 98.8,
  "stages": {
   "input": "static/cases/risbench_superlative_1823/input.jpg",
   "candidates": "static/cases/risbench_superlative_1823/candidates.jpg",
   "scored": "static/cases/risbench_superlative_1823/scored.jpg",
   "mask": "static/cases/risbench_superlative_1823/mask.jpg",
   "thumb": "static/cases/risbench_superlative_1823/thumb.jpg",
   "gt": "static/cases/risbench_superlative_1823/gt.jpg"
  }
 },
 {
  "id": "risbench_superlative_3440",
  "dataset": "RISBench",
  "type": "superlative",
  "idx": 3440,
  "sentence": "The left-most ship on the pier exhibits a predominantly white hue with a small dark area on its front.",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "ship"
   },
   "pred": "LEFT",
   "anchor": "image",
   "kernel_mode": "MONOTONE"
  },
  "iou": 99.5,
  "stages": {
   "input": "static/cases/risbench_superlative_3440/input.jpg",
   "candidates": "static/cases/risbench_superlative_3440/candidates.jpg",
   "scored": "static/cases/risbench_superlative_3440/scored.jpg",
   "mask": "static/cases/risbench_superlative_3440/mask.jpg",
   "thumb": "static/cases/risbench_superlative_3440/thumb.jpg",
   "gt": "static/cases/risbench_superlative_3440/gt.jpg"
  }
 },
 {
  "id": "risbench_superlative_4031",
  "dataset": "RISBench",
  "type": "superlative",
  "idx": 4031,
  "sentence": "The right-most tennis court in the image has a green playing area with blue surroundings.",
  "program": {
   "op": "argmax",
   "child": {
    "op": "select",
    "type": "tennis court"
   },
   "axis": "X"
  },
  "iou": 99.9,
  "stages": {
   "input": "static/cases/risbench_superlative_4031/input.jpg",
   "candidates": "static/cases/risbench_superlative_4031/candidates.jpg",
   "scored": "static/cases/risbench_superlative_4031/scored.jpg",
   "mask": "static/cases/risbench_superlative_4031/mask.jpg",
   "thumb": "static/cases/risbench_superlative_4031/thumb.jpg",
   "gt": "static/cases/risbench_superlative_4031/gt.jpg"
  }
 },
 {
  "id": "risbench_superlative_4384",
  "dataset": "RISBench",
  "type": "superlative",
  "idx": 4384,
  "sentence": "The left-most small plane on the tarmac is positioned at the bottom-left.",
  "program": {
   "op": "argmin",
   "child": {
    "op": "filter",
    "child": {
     "op": "select",
     "type": "small plane"
    },
    "pred": "LEFT",
    "anchor": "image",
    "kernel_mode": "MONOTONE"
   },
   "axis": "X"
  },
  "iou": 98.5,
  "stages": {
   "input": "static/cases/risbench_superlative_4384/input.jpg",
   "candidates": "static/cases/risbench_superlative_4384/candidates.jpg",
   "scored": "static/cases/risbench_superlative_4384/scored.jpg",
   "mask": "static/cases/risbench_superlative_4384/mask.jpg",
   "thumb": "static/cases/risbench_superlative_4384/thumb.jpg",
   "gt": "static/cases/risbench_superlative_4384/gt.jpg"
  }
 },
 {
  "id": "risbench_superlative_5751",
  "dataset": "RISBench",
  "type": "superlative",
  "idx": 5751,
  "sentence": "The left-most plane located at the edge of the image near the tarmac.",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "plane"
   },
   "pred": "LEFT",
   "anchor": "image",
   "kernel_mode": "MONOTONE"
  },
  "iou": 99.0,
  "stages": {
   "input": "static/cases/risbench_superlative_5751/input.jpg",
   "candidates": "static/cases/risbench_superlative_5751/candidates.jpg",
   "scored": "static/cases/risbench_superlative_5751/scored.jpg",
   "mask": "static/cases/risbench_superlative_5751/mask.jpg",
   "thumb": "static/cases/risbench_superlative_5751/thumb.jpg",
   "gt": "static/cases/risbench_superlative_5751/gt.jpg"
  }
 },
 {
  "id": "risbench_superlative_8061",
  "dataset": "RISBench",
  "type": "superlative",
  "idx": 8061,
  "sentence": "The airplane located at the top-most position in the image.",
  "program": {
   "op": "argmin",
   "child": {
    "op": "select",
    "type": "airplane"
   },
   "axis": "Y"
  },
  "iou": 97.0,
  "stages": {
   "input": "static/cases/risbench_superlative_8061/input.jpg",
   "candidates": "static/cases/risbench_superlative_8061/candidates.jpg",
   "scored": "static/cases/risbench_superlative_8061/scored.jpg",
   "mask": "static/cases/risbench_superlative_8061/mask.jpg",
   "thumb": "static/cases/risbench_superlative_8061/thumb.jpg",
   "gt": "static/cases/risbench_superlative_8061/gt.jpg"
  }
 },
 {
  "id": "risbench_superlative_8680",
  "dataset": "RISBench",
  "type": "superlative",
  "idx": 8680,
  "sentence": "The top-most storage tank in the top right corner of the image.",
  "program": {
   "op": "argmin",
   "child": {
    "op": "filter",
    "child": {
     "op": "select",
     "type": "storage tank"
    },
    "pred": "TOP",
    "anchor": "image",
    "kernel_mode": "MONOTONE"
   },
   "axis": "Y"
  },
  "iou": 99.5,
  "stages": {
   "input": "static/cases/risbench_superlative_8680/input.jpg",
   "candidates": "static/cases/risbench_superlative_8680/candidates.jpg",
   "scored": "static/cases/risbench_superlative_8680/scored.jpg",
   "mask": "static/cases/risbench_superlative_8680/mask.jpg",
   "thumb": "static/cases/risbench_superlative_8680/thumb.jpg",
   "gt": "static/cases/risbench_superlative_8680/gt.jpg"
  }
 },
 {
  "id": "risbench_superlative_12422",
  "dataset": "RISBench",
  "type": "superlative",
  "idx": 12422,
  "sentence": "The vehicle located at the bottom-middle of the image is the most bottom-most vehicle present.",
  "program": {
   "op": "argmax",
   "child": {
    "op": "filter",
    "child": {
     "op": "select",
     "type": "vehicle"
    },
    "pred": "BOTTOM",
    "anchor": "image",
    "kernel_mode": "MONOTONE"
   },
   "axis": "Y"
  },
  "iou": 99.6,
  "stages": {
   "input": "static/cases/risbench_superlative_12422/input.jpg",
   "candidates": "static/cases/risbench_superlative_12422/candidates.jpg",
   "scored": "static/cases/risbench_superlative_12422/scored.jpg",
   "mask": "static/cases/risbench_superlative_12422/mask.jpg",
   "thumb": "static/cases/risbench_superlative_12422/thumb.jpg",
   "gt": "static/cases/risbench_superlative_12422/gt.jpg"
  }
 },
 {
  "id": "risbench_superlative_14399",
  "dataset": "RISBench",
  "type": "superlative",
  "idx": 14399,
  "sentence": "The left-most harbor in the scene.",
  "program": {
   "op": "argmin",
   "child": {
    "op": "select",
    "type": "harbor"
   },
   "axis": "X"
  },
  "iou": 98.6,
  "stages": {
   "input": "static/cases/risbench_superlative_14399/input.jpg",
   "candidates": "static/cases/risbench_superlative_14399/candidates.jpg",
   "scored": "static/cases/risbench_superlative_14399/scored.jpg",
   "mask": "static/cases/risbench_superlative_14399/mask.jpg",
   "thumb": "static/cases/risbench_superlative_14399/thumb.jpg",
   "gt": "static/cases/risbench_superlative_14399/gt.jpg"
  }
 },
 {
  "id": "risbench_superlative_16060",
  "dataset": "RISBench",
  "type": "superlative",
  "idx": 16060,
  "sentence": "The top-most small vehicle appears in the top-right sector of the image.",
  "program": {
   "op": "argmin",
   "child": {
    "op": "filter",
    "child": {
     "op": "select",
     "type": "small vehicle"
    },
    "pred": "TOP",
    "anchor": "image",
    "kernel_mode": "MONOTONE"
   },
   "axis": "Y"
  },
  "iou": 99.5,
  "stages": {
   "input": "static/cases/risbench_superlative_16060/input.jpg",
   "candidates": "static/cases/risbench_superlative_16060/candidates.jpg",
   "scored": "static/cases/risbench_superlative_16060/scored.jpg",
   "mask": "static/cases/risbench_superlative_16060/mask.jpg",
   "thumb": "static/cases/risbench_superlative_16060/thumb.jpg",
   "gt": "static/cases/risbench_superlative_16060/gt.jpg"
  }
 },
 {
  "id": "risbench_compositional_4906",
  "dataset": "RISBench",
  "type": "compositional",
  "idx": 4906,
  "sentence": "The larger plane is positioned closer to the center and to the right of the image.",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "plane"
   },
   "pred": "CENTER",
   "anchor": "image",
   "kernel_mode": "MONOTONE"
  },
  "iou": 98.4,
  "stages": {
   "input": "static/cases/risbench_compositional_4906/input.jpg",
   "candidates": "static/cases/risbench_compositional_4906/candidates.jpg",
   "scored": "static/cases/risbench_compositional_4906/scored.jpg",
   "mask": "static/cases/risbench_compositional_4906/mask.jpg",
   "thumb": "static/cases/risbench_compositional_4906/thumb.jpg",
   "gt": "static/cases/risbench_compositional_4906/gt.jpg"
  }
 },
 {
  "id": "risbench_compositional_4976",
  "dataset": "RISBench",
  "type": "compositional",
  "idx": 4976,
  "sentence": "The partially visible airplane situated at the bottom section of the tarmac.",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "airplane"
   },
   "pred": "BOTTOM",
   "anchor": "image",
   "kernel_mode": "MONOTONE"
  },
  "iou": 98.3,
  "stages": {
   "input": "static/cases/risbench_compositional_4976/input.jpg",
   "candidates": "static/cases/risbench_compositional_4976/candidates.jpg",
   "scored": "static/cases/risbench_compositional_4976/scored.jpg",
   "mask": "static/cases/risbench_compositional_4976/mask.jpg",
   "thumb": "static/cases/risbench_compositional_4976/thumb.jpg",
   "gt": "static/cases/risbench_compositional_4976/gt.jpg"
  }
 },
 {
  "id": "risbench_compositional_5625",
  "dataset": "RISBench",
  "type": "compositional",
  "idx": 5625,
  "sentence": "The harbor that crosses from the bank on the bottom left to the upper right side of the image.",
  "program": {
   "op": "relate",
   "child": {
    "op": "select",
    "type": "harbor"
   },
   "rel": "BETWEEN",
   "anchor": {
    "op": "filter",
    "child": {
     "op": "select",
     "type": "bank"
    },
    "pred": "LL",
    "anchor": "image",
    "kernel_mode": "MONOTONE"
   },
   "anchor2": {
    "op": "filter",
    "child": {
     "op": "select",
     "type": "image"
    },
    "pred": "UR",
    "anchor": "image",
    "kernel_mode": "MONOTONE"
   }
  },
  "iou": 97.8,
  "stages": {
   "input": "static/cases/risbench_compositional_5625/input.jpg",
   "candidates": "static/cases/risbench_compositional_5625/candidates.jpg",
   "scored": "static/cases/risbench_compositional_5625/scored.jpg",
   "mask": "static/cases/risbench_compositional_5625/mask.jpg",
   "thumb": "static/cases/risbench_compositional_5625/thumb.jpg",
   "gt": "static/cases/risbench_compositional_5625/gt.jpg"
  }
 },
 {
  "id": "risbench_compositional_5798",
  "dataset": "RISBench",
  "type": "compositional",
  "idx": 5798,
  "sentence": "The overpass in the image stretches from the left middle towards the top right, traversing over the highway.",
  "program": {
   "op": "relate",
   "child": {
    "op": "select",
    "type": "overpass"
   },
   "rel": "NEAR",
   "anchor": {
    "op": "filter",
    "child": {
     "op": "select",
     "type": "highway"
    },
    "pred": "BOTTOM",
    "anchor": "image",
    "kernel_mode": "MONOTONE"
   }
  },
  "iou": 97.0,
  "stages": {
   "input": "static/cases/risbench_compositional_5798/input.jpg",
   "candidates": "static/cases/risbench_compositional_5798/candidates.jpg",
   "scored": "static/cases/risbench_compositional_5798/scored.jpg",
   "mask": "static/cases/risbench_compositional_5798/mask.jpg",
   "thumb": "static/cases/risbench_compositional_5798/thumb.jpg",
   "gt": "static/cases/risbench_compositional_5798/gt.jpg"
  }
 },
 {
  "id": "risbench_compositional_7828",
  "dataset": "RISBench",
  "type": "compositional",
  "idx": 7828,
  "sentence": "The ship docked near the coast is located in the middle-left.",
  "program": {
   "op": "filter",
   "child": {
    "op": "filter",
    "child": {
     "op": "select",
     "type": "ship"
    },
    "pred": "NEAR",
    "anchor": {
     "op": "select",
     "type": "coast"
    },
    "kernel_mode": "MONOTONE"
   },
   "pred": "LEFT",
   "anchor": "image",
   "kernel_mode": "MONOTONE"
  },
  "iou": 99.0,
  "stages": {
   "input": "static/cases/risbench_compositional_7828/input.jpg",
   "candidates": "static/cases/risbench_compositional_7828/candidates.jpg",
   "scored": "static/cases/risbench_compositional_7828/scored.jpg",
   "mask": "static/cases/risbench_compositional_7828/mask.jpg",
   "thumb": "static/cases/risbench_compositional_7828/thumb.jpg",
   "gt": "static/cases/risbench_compositional_7828/gt.jpg"
  }
 },
 {
  "id": "risbench_compositional_12082",
  "dataset": "RISBench",
  "type": "compositional",
  "idx": 12082,
  "sentence": "The storage tank situated closer to the right edge of the image in the middle-right section can be distinguished by its proximity to the other tank and residential spaces.",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "storage tank"
   },
   "pred": "RIGHT",
   "anchor": "image",
   "kernel_mode": "MONOTONE"
  },
  "iou": 99.3,
  "stages": {
   "input": "static/cases/risbench_compositional_12082/input.jpg",
   "candidates": "static/cases/risbench_compositional_12082/candidates.jpg",
   "scored": "static/cases/risbench_compositional_12082/scored.jpg",
   "mask": "static/cases/risbench_compositional_12082/mask.jpg",
   "thumb": "static/cases/risbench_compositional_12082/thumb.jpg",
   "gt": "static/cases/risbench_compositional_12082/gt.jpg"
  }
 },
 {
  "id": "risbench_compositional_12129",
  "dataset": "RISBench",
  "type": "compositional",
  "idx": 12129,
  "sentence": "The small vehicle located on the right side of the road.",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "small vehicle"
   },
   "pred": "RIGHT",
   "anchor": {
    "op": "select",
    "type": "road"
   },
   "kernel_mode": "MONOTONE"
  },
  "iou": 99.5,
  "stages": {
   "input": "static/cases/risbench_compositional_12129/input.jpg",
   "candidates": "static/cases/risbench_compositional_12129/candidates.jpg",
   "scored": "static/cases/risbench_compositional_12129/scored.jpg",
   "mask": "static/cases/risbench_compositional_12129/mask.jpg",
   "thumb": "static/cases/risbench_compositional_12129/thumb.jpg",
   "gt": "static/cases/risbench_compositional_12129/gt.jpg"
  }
 },
 {
  "id": "risbench_compositional_12260",
  "dataset": "RISBench",
  "type": "compositional",
  "idx": 12260,
  "sentence": "The smaller vehicle located towards the bottom left side of the overpass.",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "vehicle"
   },
   "pred": "LL",
   "anchor": "image",
   "kernel_mode": "MONOTONE"
  },
  "iou": 99.8,
  "stages": {
   "input": "static/cases/risbench_compositional_12260/input.jpg",
   "candidates": "static/cases/risbench_compositional_12260/candidates.jpg",
   "scored": "static/cases/risbench_compositional_12260/scored.jpg",
   "mask": "static/cases/risbench_compositional_12260/mask.jpg",
   "thumb": "static/cases/risbench_compositional_12260/thumb.jpg",
   "gt": "static/cases/risbench_compositional_12260/gt.jpg"
  }
 },
 {
  "id": "risbench_compositional_12757",
  "dataset": "RISBench",
  "type": "compositional",
  "idx": 12757,
  "sentence": "The bridge on the right side of the image runs vertically and is larger of the two bridges.",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "bridge"
   },
   "pred": "RIGHT",
   "anchor": "image",
   "kernel_mode": "MONOTONE"
  },
  "iou": 99.2,
  "stages": {
   "input": "static/cases/risbench_compositional_12757/input.jpg",
   "candidates": "static/cases/risbench_compositional_12757/candidates.jpg",
   "scored": "static/cases/risbench_compositional_12757/scored.jpg",
   "mask": "static/cases/risbench_compositional_12757/mask.jpg",
   "thumb": "static/cases/risbench_compositional_12757/thumb.jpg",
   "gt": "static/cases/risbench_compositional_12757/gt.jpg"
  }
 },
 {
  "id": "risbench_compositional_12781",
  "dataset": "RISBench",
  "type": "compositional",
  "idx": 12781,
  "sentence": "The large vehicle that is situated slightly above and to the left of the bottom-left vehicle.",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "large vehicle"
   },
   "pred": "LEFT",
   "anchor": {
    "op": "filter",
    "child": {
     "op": "select",
     "type": "vehicle"
    },
    "pred": "LL",
    "anchor": "image",
    "kernel_mode": "MONOTONE"
   },
   "kernel_mode": "MONOTONE"
  },
  "iou": 98.3,
  "stages": {
   "input": "static/cases/risbench_compositional_12781/input.jpg",
   "candidates": "static/cases/risbench_compositional_12781/candidates.jpg",
   "scored": "static/cases/risbench_compositional_12781/scored.jpg",
   "mask": "static/cases/risbench_compositional_12781/mask.jpg",
   "thumb": "static/cases/risbench_compositional_12781/thumb.jpg",
   "gt": "static/cases/risbench_compositional_12781/gt.jpg"
  }
 },
 {
  "id": "risbench_compositional_13368",
  "dataset": "RISBench",
  "type": "compositional",
  "idx": 13368,
  "sentence": "The tennis court that is aligned to the left side of the image.",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "tennis court"
   },
   "pred": "LEFT",
   "anchor": "image",
   "kernel_mode": "MONOTONE"
  },
  "iou": 99.6,
  "stages": {
   "input": "static/cases/risbench_compositional_13368/input.jpg",
   "candidates": "static/cases/risbench_compositional_13368/candidates.jpg",
   "scored": "static/cases/risbench_compositional_13368/scored.jpg",
   "mask": "static/cases/risbench_compositional_13368/mask.jpg",
   "thumb": "static/cases/risbench_compositional_13368/thumb.jpg",
   "gt": "static/cases/risbench_compositional_13368/gt.jpg"
  }
 },
 {
  "id": "risbench_compositional_13985",
  "dataset": "RISBench",
  "type": "compositional",
  "idx": 13985,
  "sentence": "The small ship is found at the top left, just above the upper edge of the image boundary.",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "small ship"
   },
   "pred": "UL",
   "anchor": "image",
   "kernel_mode": "MONOTONE"
  },
  "iou": 99.2,
  "stages": {
   "input": "static/cases/risbench_compositional_13985/input.jpg",
   "candidates": "static/cases/risbench_compositional_13985/candidates.jpg",
   "scored": "static/cases/risbench_compositional_13985/scored.jpg",
   "mask": "static/cases/risbench_compositional_13985/mask.jpg",
   "thumb": "static/cases/risbench_compositional_13985/thumb.jpg",
   "gt": "static/cases/risbench_compositional_13985/gt.jpg"
  }
 },
 {
  "id": "risbench_ordinal_5438",
  "dataset": "RISBench",
  "type": "ordinal",
  "idx": 5438,
  "sentence": "The tennis court on the bottom is surrounded by greenery on three sides and is adjacent to a curving road on the fourth side.",
  "program": {
   "op": "relate",
   "child": {
    "op": "select",
    "type": "tennis court"
   },
   "rel": "INSIDE",
   "anchor": {
    "op": "filter",
    "child": {
     "op": "select",
     "type": "greenery"
    },
    "pred": "BOTTOM",
    "anchor": "image",
    "kernel_mode": "MONOTONE"
   }
  },
  "iou": 98.9,
  "stages": {
   "input": "static/cases/risbench_ordinal_5438/input.jpg",
   "candidates": "static/cases/risbench_ordinal_5438/candidates.jpg",
   "scored": "static/cases/risbench_ordinal_5438/scored.jpg",
   "mask": "static/cases/risbench_ordinal_5438/mask.jpg",
   "thumb": "static/cases/risbench_ordinal_5438/thumb.jpg",
   "gt": "static/cases/risbench_ordinal_5438/gt.jpg"
  }
 },
 {
  "id": "risbench_ordinal_6987",
  "dataset": "RISBench",
  "type": "ordinal",
  "idx": 6987,
  "sentence": "The second vehicle is positioned at the bottom-middle of the image.",
  "program": {
   "op": "nth",
   "child": {
    "op": "filter",
    "child": {
     "op": "select",
     "type": "vehicle"
    },
    "pred": "BOTTOM",
    "anchor": "image",
    "kernel_mode": "MONOTONE"
   },
   "n": 1,
   "axis": "Y"
  },
  "iou": 99.3,
  "stages": {
   "input": "static/cases/risbench_ordinal_6987/input.jpg",
   "candidates": "static/cases/risbench_ordinal_6987/candidates.jpg",
   "scored": "static/cases/risbench_ordinal_6987/scored.jpg",
   "mask": "static/cases/risbench_ordinal_6987/mask.jpg",
   "thumb": "static/cases/risbench_ordinal_6987/thumb.jpg",
   "gt": "static/cases/risbench_ordinal_6987/gt.jpg"
  }
 },
 {
  "id": "risbench_ordinal_7651",
  "dataset": "RISBench",
  "type": "ordinal",
  "idx": 7651,
  "sentence": "The overpass situated to the right of the first one stretches from slightly below the center all the way to the bottom edge of the image.",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "overpass"
   },
   "pred": "RIGHT",
   "anchor": {
    "op": "nth",
    "child": {
     "op": "select",
     "type": "overpass"
    },
    "n": 0,
    "axis": "X"
   },
   "kernel_mode": "MONOTONE"
  },
  "iou": 95.0,
  "stages": {
   "input": "static/cases/risbench_ordinal_7651/input.jpg",
   "candidates": "static/cases/risbench_ordinal_7651/candidates.jpg",
   "scored": "static/cases/risbench_ordinal_7651/scored.jpg",
   "mask": "static/cases/risbench_ordinal_7651/mask.jpg",
   "thumb": "static/cases/risbench_ordinal_7651/thumb.jpg",
   "gt": "static/cases/risbench_ordinal_7651/gt.jpg"
  }
 },
 {
  "id": "risbench_ordinal_9947",
  "dataset": "RISBench",
  "type": "ordinal",
  "idx": 9947,
  "sentence": "The windmill positioned at the bottom-middle stands as the last in the vertical line.",
  "program": {
   "op": "argmax",
   "child": {
    "op": "filter",
    "child": {
     "op": "select",
     "type": "windmill"
    },
    "pred": "BOTTOM",
    "anchor": "image",
    "kernel_mode": "MONOTONE"
   },
   "axis": "Y"
  },
  "iou": 93.4,
  "stages": {
   "input": "static/cases/risbench_ordinal_9947/input.jpg",
   "candidates": "static/cases/risbench_ordinal_9947/candidates.jpg",
   "scored": "static/cases/risbench_ordinal_9947/scored.jpg",
   "mask": "static/cases/risbench_ordinal_9947/mask.jpg",
   "thumb": "static/cases/risbench_ordinal_9947/thumb.jpg",
   "gt": "static/cases/risbench_ordinal_9947/gt.jpg"
  }
 },
 {
  "id": "risbench_ordinal_11670",
  "dataset": "RISBench",
  "type": "ordinal",
  "idx": 11670,
  "sentence": "The ship located at the left-most docking section of the harbor is the first in a sequence from left to right.",
  "program": {
   "op": "argmin",
   "child": {
    "op": "filter",
    "child": {
     "op": "select",
     "type": "ship"
    },
    "pred": "LEFT",
    "anchor": {
     "op": "select",
     "type": "harbor"
    },
    "kernel_mode": "MONOTONE"
   },
   "axis": "X"
  },
  "iou": 98.3,
  "stages": {
   "input": "static/cases/risbench_ordinal_11670/input.jpg",
   "candidates": "static/cases/risbench_ordinal_11670/candidates.jpg",
   "scored": "static/cases/risbench_ordinal_11670/scored.jpg",
   "mask": "static/cases/risbench_ordinal_11670/mask.jpg",
   "thumb": "static/cases/risbench_ordinal_11670/thumb.jpg",
   "gt": "static/cases/risbench_ordinal_11670/gt.jpg"
  }
 },
 {
  "id": "risbench_ordinal_12291",
  "dataset": "RISBench",
  "type": "ordinal",
  "idx": 12291,
  "sentence": "The baseball field located at the top-right of the image, extending from the top edge to about one-third of the way down, is enclosed by a fence.",
  "program": {
   "op": "filter",
   "child": {
    "op": "select",
    "type": "baseball field"
   },
   "pred": "UR",
   "anchor": "image",
   "kernel_mode": "MONOTONE"
  },
  "iou": 98.2,
  "stages": {
   "input": "static/cases/risbench_ordinal_12291/input.jpg",
   "candidates": "static/cases/risbench_ordinal_12291/candidates.jpg",
   "scored": "static/cases/risbench_ordinal_12291/scored.jpg",
   "mask": "static/cases/risbench_ordinal_12291/mask.jpg",
   "thumb": "static/cases/risbench_ordinal_12291/thumb.jpg",
   "gt": "static/cases/risbench_ordinal_12291/gt.jpg"
  }
 }
];
