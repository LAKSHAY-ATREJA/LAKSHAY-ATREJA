# VisionDelta — Visual Inspection Lab

A fully functional, **non-RAG** browser-based computer vision tool for explainable image comparison and defect-region inspection.

## What works
- Upload reference and candidate images; or open a reproducible synthetic demonstration.
- Scale images into a shared 360x360 inspection canvas.
- Pixel-level RGB difference thresholding with configurable sensitivity.
- 4-connected component segmentation with minimum-area filtering.
- Mark each region on an annotated inspection view.
- Inspect changed pixel percentage, average RGB difference, component bounding boxes.
- Export annotated PNG and a machine-readable JSON inspection report.
- Works entirely in the user's browser: no external model, API key, server, or uploads.

**Method honesty:** This is classical computer vision (difference thresholding + connected components), *not* a trained defect classification model or production-certified quality system. It requires aligned images; lighting, scale, framing, or camera changes can create false positives.

## Run
```bash
python -m http.server 8080
# open http://localhost:8080/projects/VisionDelta/ from repository root
```
Or, from this folder: `python -m http.server 8080`, then open `http://localhost:8080`.

## Test
Node.js >=18 with no dependencies:
```bash
node projects/VisionDelta/tests.mjs
```

## Potential next steps
Automated image registration, illumination invariance, segmentation model backends, offline batch report generation, and dataset-based performance validation.
