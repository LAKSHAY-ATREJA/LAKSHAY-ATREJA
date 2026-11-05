# VisionDelta | Visual Change Inspection

Interactive **non-RAG**, **non-LLM** classical computer-vision prototype. Compare two images, review changed regions, inspect pixel-level difference intensity and export an annotated PNG and structured JSON report.

## Streamlit demo

**Deploy from GitHub:** In [Streamlit Community Cloud](https://share.streamlit.io/) select repository `LAKSHAY-ATREJA/LAKSHAY-ATREJA`, branch `main`, main file `projects/VisionDelta/app.py`. Dependencies are in `projects/VisionDelta/requirements.txt`.

No live-demo URL is claimed until an actual deployment is created and opened successfully.

## Features
- Interactive two-image upload or built-in synthetic demo
- Both images fitted to a shared 360 × 300 canvas for comparison
- Pixel-level mean RGB differences and adjustable threshold
- Four-connected component segmentation, configurable minimum region size
- Image overlays with marked change regions, difference heatmap
- Downloadable PNG annotations and JSON report

## Local run

```bash
pip install -r projects/VisionDelta/requirements.txt
streamlit run projects/VisionDelta/app.py
```

## Tests

```bash
cd projects/VisionDelta
python -m unittest test_logic.py
```

## Method / limitations

This is a deterministic classical vision algorithm, **not** a trained neural net, defect detector or production inspection system. Misaligned images or differences in perspective, light, camera or resize crop can create false positives. Do not upload confidential images into externally hosted demos.

An earlier JavaScript/browser prototype (`index.html`, `logic.mjs`, `tests.mjs`) is retained. The Streamlit implementation is independent and can run directly from `app.py`.
