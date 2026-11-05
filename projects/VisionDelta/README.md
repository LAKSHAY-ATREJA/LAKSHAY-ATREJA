# VisionDelta | Visual Inspection Studio

A visual quality engineering prototype that takes two inspection images, estimates geometric alignment, measures structural and colour changes, isolates candidate defect regions and exports reviewable evidence. The Streamlit application opens directly into a synthetic industrial-inspection example so reviewers can inspect the full workflow without uploading anything or supplying an API key.

## What the interactive demo shows

1. **Reference versus candidate:** two images of the same asset, including changes in camera position and exposure.
2. **Automatic registration:** ORB feature matching with RANSAC homography, backed by ECC affine alignment when needed.
3. **Change evidence:** local illumination-normalized structural similarity blended with colour-difference evidence.
4. **Region review:** filtered connected components, bounding boxes, region ranking and local inspection crops.
5. **Comparison studio:** adjustable before/after blend, visual difference heatmap and mask explorer.
6. **Batch inspection:** up to six corresponding pairs in a ZIP file, scored and summarized as a review table.
7. **Review exports:** annotated PNG, change mask, heatmap and structured JSON/CSV summaries.

The sample changes and their optional reference labels are **synthetic**. They help demonstrate the system; they do not establish real-world defect-detection accuracy.

## Run in Streamlit

**Application entrypoint:** `projects/VisionDelta/app.py`

Streamlit Community Cloud settings:
- Repository: `LAKSHAY-ATREJA/LAKSHAY-ATREJA`
- Branch: `main`
- Main file path: `projects/VisionDelta/app.py`

A public demo link will be placed here after the actual hosted application is confirmed to work.

Local setup from repository root:

```bash
python -m pip install -r projects/VisionDelta/requirements.txt
streamlit run projects/VisionDelta/app.py
```

## Data contract

Single-image mode supports PNG/JPEG input and a built-in demo. Batch mode expects pairs with the same basename in `before/` and `after/` inside a ZIP. Uploaded images are processed on the hosting server; do not upload proprietary images to public deployments.

## Engineering structure

- `engine.py`: deterministic synthetic fixture, image registration, structural and chromatic evidence maps, morphology, region ranking, quality summary and ZIP batch processing.
- `app.py`: Streamlit inspection studio, comparison and finding-review screens, measurement controls, downloadable evidence.
- `test_engine.py`: reproducibility, positive/negative comparisons, parameter validation, PNG and batch tests.
- `requirements.txt`: OpenCV headless, Pillow, NumPy, pandas, Plotly and Streamlit.

Python test command:

```bash
python -m unittest discover -s projects/VisionDelta -p 'test_*.py' -v
```

The repository's workflow also runs these tests and checks the default Streamlit interface.

## Technical limits

This is an **engineering portfolio prototype**, not a trained defect classifier or certified production inspection system. Poor registration, occlusions, reflections, lighting differences or unseen geometry can produce false positives and false negatives. Image registration assumes sufficient overlap and features. The system intentionally treats outputs as candidates for human review rather than autonomous safety decisions.
