"""VisionDelta: visual inspection studio for explainable industrial QA."""
import json
from io import BytesIO
import cv2
import pandas as pd
import streamlit as st
from PIL import Image, UnidentifiedImageError
from engine import demo_pair, inspect_pair, png_bytes, batch_inspect

st.set_page_config(page_title="VisionDelta | Visual QA Studio", page_icon="🔬", layout="wide")
st.markdown("""
<style>
.block-container {max-width:1420px;padding-top:1.3rem;padding-bottom:4rem}
h1,h2,h3 {letter-spacing:-.035em}
h1{font-weight:780!important;font-size:3rem!important}
[data-testid="stMetric"]{border:1px solid rgba(136,160,185,.25);border-radius:15px;
background:linear-gradient(135deg,rgba(51,119,166,.15),rgba(70,90,120,.035));padding:15px 19px;min-height:108px}
[data-testid="stMetricValue"]{font-size:1.8rem}
[data-testid="stImage"]{border:1px solid rgba(148,163,184,.21);border-radius:14px;overflow:hidden}
div[data-testid="stTabs"] button{font-weight:600}
div[data-testid="stDownloadButton"] button{border-radius:10px}
.kicker{font-size:.75rem;color:#61b8f5;letter-spacing:.18em;font-weight:700}
.hero{max-width:1000px;color:#9fb1c4;font-size:1.03rem;line-height:1.6}
.pill{display:inline-block;border:1px solid rgba(53,155,215,.25);background:rgba(50,160,214,.09);
color:#8acaf4;border-radius:40px;padding:6px 12px;font-size:.79rem;margin:0 8px 12px 0}
.micro{font-size:.79rem;color:#8da6bd;text-transform:uppercase;letter-spacing:.11em}
</style>
""", unsafe_allow_html=True)
st.markdown('<div class="kicker">COMPUTER VISION / QUALITY ENGINEERING</div>', unsafe_allow_html=True)
st.title("VisionDelta  |  Inspection Studio")
st.markdown('<p class="hero">Align inspection images. Expose subtle structural and colour changes. '
            'Review measured regions, compare evidence and export traceable quality reports.</p>', unsafe_allow_html=True)
st.markdown('<span class="pill">Image registration</span><span class="pill">Structural comparison</span>'
            '<span class="pill">Region inspection</span><span class="pill">Batch QA</span>', unsafe_allow_html=True)

with st.sidebar:
    st.header("Inspection workspace")
    source=st.radio("Dataset",["Live example","Compare my images","Batch review"],help="A visual example is available immediately.")
    st.divider()
    sensitivity=st.slider("Change sensitivity",.12,.70,.28,.02,
        help="Lower values show subtle differences but may increase false positives.")
    minimum=st.slider("Minimum detected region (px)",20,650,65,5)
    alignment=st.selectbox("Registration algorithm",["auto","feature","ecc","off"],0)
    margin=st.slider("Exclude image borders (%)",0,10,2)
    st.caption("Engine: ORB/RANSAC, ECC, local structural comparison and connected regions.")
    st.caption("Prototype. No trained defect model. Upload only non-confidential images.")

if source=="Batch review":
    st.subheader("Batch inspection")
    st.write("Use a ZIP containing matching before/name.png and after/name.png pairs.")
    upload=st.file_uploader("Upload inspection batch ZIP",type="zip")
    if upload:
        try:
            with st.spinner("Reviewing image pairs..."):
                table=batch_inspect(upload.getvalue(),sensitivity,minimum)
            a,b,c=st.columns(3)
            a.metric("Pairs inspected",len(table))
            b.metric("Flagged regions",int(table.regions.sum()))
            c.metric("Pairs with changes",int((table.regions>0).sum()))
            st.dataframe(table,hide_index=True,use_container_width=True)
            st.bar_chart(table.set_index("image")[["flagged_area_pct"]])
            st.download_button("Export batch summary",table.to_csv(index=False).encode(),
                               "visiondelta_batch.csv","text/csv",type="primary")
        except (ValueError,OSError) as exc:
            st.error(f"Batch review failed: {exc}")
    else:
        st.info("Select a batch file or choose Live example to explore the complete inspection studio.")
    st.stop()

truth=None
if source=="Live example":
    before,after,truth=demo_pair()
    st.caption("LIVE EXAMPLE: Synthetic industrial panel with a changed module, missing fastener, "
               "surface damage, lighting variation and camera movement.")
else:
    c1,c2=st.columns(2)
    with c1: left_file=st.file_uploader("Baseline image",type=["png","jpg","jpeg"],key="left")
    with c2: right_file=st.file_uploader("Candidate image",type=["png","jpg","jpeg"],key="right")
    if not left_file or not right_file:
        st.info("Upload two images, or choose Live example for an instant demonstration.")
        st.stop()
    try:
        if len(left_file.getvalue())>12_000_000 or len(right_file.getvalue())>12_000_000:
            raise ValueError("Each image must be smaller than 12 MB.")
        before=Image.open(left_file);after=Image.open(right_file)
        before.load();after.load()
    except (ValueError,UnidentifiedImageError,OSError) as exc:
        st.error(f"Cannot open an image: {exc}")
        st.stop()

@st.cache_data(show_spinner="Registering images and extracting change evidence...",max_entries=12)
def analyse(before_png,after_png,truth_png,sensitivity,minimum,alignment,margin):
    a=Image.open(BytesIO(before_png))
    b=Image.open(BytesIO(after_png))
    truth_image=Image.open(BytesIO(truth_png)) if truth_png else None
    return inspect_pair(a,b,sensitivity,min_area=minimum,alignment=alignment,
                        edge_margin=margin,truth=truth_image)

try:
    report=analyse(png_bytes(before),png_bytes(after),
                   png_bytes(truth) if truth else None,
                   sensitivity,minimum,alignment,margin)
except (ValueError,cv2.error,OSError) as exc:
    st.error(f"Unable to run inspection: {exc}")
    st.stop()

summary=report["summary"]
views=report["images"]
a,b,c,d=st.columns(4)
a.metric("Candidate regions",summary["region_count"])
b.metric("Surface flagged",f"{summary['flagged_area_pct']:.2f}%")
c.metric("Structural similarity",f"{summary['structural_similarity']:.3f}")
d.metric("Valid overlap",f"{summary['valid_overlap_pct']:.1f}%")
reg=summary["registration"]
if reg["success"]:
    st.success(f"Automatic registration completed using {reg['method']}. Alignment quality: {reg['quality']}")
else:
    st.warning("Registration was not established. Consider adjusting the alignment method or image framing.")

tabs=st.tabs(["01   Visual studio","02   Findings","03   Diagnostics","04   Export"])
with tabs[0]:
    st.subheader("What's different?")
    st.caption("The complete workflow is visible by default. No API keys, uploads or setup needed for the sample.")
    left,right=st.columns(2,gap="large")
    with left:
        st.markdown('<span class="micro">01 / reference</span>',unsafe_allow_html=True)
        st.image(views["Reference"],use_container_width=True)
    with right:
        st.markdown('<span class="micro">02 / candidate</span>',unsafe_allow_html=True)
        st.image(views["Candidate"],use_container_width=True)
    left,right=st.columns(2,gap="large")
    with left:
        st.markdown('<span class="micro">03 / annotated changes</span>',unsafe_allow_html=True)
        st.image(views["Regions"],use_container_width=True)
    with right:
        st.markdown('<span class="micro">04 / structural evidence</span>',unsafe_allow_html=True)
        st.image(views["Evidence heatmap"],use_container_width=True)
    st.divider()
    st.subheader("Interactive before and after")
    mix=st.slider("Reveal registered candidate",0,100,50,5)
    overlay=Image.blend(views["Reference"],views["Registered"],mix/100)
    st.image(overlay,use_container_width=True,
             caption="Move the slider to compare matching geometry and inspect suspected changes.")

with tabs[1]:
    st.subheader("Inspection findings")
    if summary["regions"]:
        frame=pd.DataFrame(summary["regions"])
        st.dataframe(frame[["region","priority","area_px","change_score","x","y","width","height"]],
                     hide_index=True,use_container_width=True)
        st.bar_chart(frame.set_index("region")[["area_px"]])
        chosen=st.selectbox("Open evidence for a region",frame["region"].tolist())
        record=next(r for r in summary["regions"] if r["region"]==chosen)
        x,y,w,h=[record[k] for k in ("x","y","width","height")]
        bbox=(max(0,x-25),max(0,y-25),
              min(views["Reference"].width,x+w+25),min(views["Reference"].height,y+h+25))
        l,r=st.columns(2)
        l.image(views["Reference"].crop(bbox),caption="Reference detail",use_container_width=True)
        r.image(views["Regions"].crop(bbox),caption=f"{chosen}: {record['priority']} finding",use_container_width=True)
    else:
        st.success("No regions were flagged at the selected sensitivity.")
    if summary["evaluation"] is not None:
        st.subheader("Known changes, synthetic example only")
        p=summary["evaluation"]
        a,b,c=st.columns(3)
        a.metric("Precision",f"{p['precision']:.0%}")
        b.metric("Recall",f"{p['recall']:.0%}")
        c.metric("Intersection over union",f"{p['iou']:.2f}")
        st.caption("Ground truth is from intentionally created synthetic changes, not a production benchmark.")

with tabs[2]:
    st.subheader("Explainable inspection pipeline")
    st.write("Feature correspondence → geometric registration → local structural and colour comparison "
             "→ connected-component segmentation → region review → evidence export.")
    st.json(summary["registration"])
    left,right=st.columns(2)
    left.image(views["Overlay"],caption="Registration overlay",use_container_width=True)
    right.image(views["Segmentation mask"],caption="Region segmentation",use_container_width=True)
    st.json(summary["parameters"])
    st.warning("Detection depends on camera framing, reflections and lighting. All findings require human review.")

with tabs[3]:
    st.subheader("Deliver inspection evidence")
    st.write("Export annotated findings, difference intensity, final segmentation or a structured JSON report.")
    l,r=st.columns(2)
    l.download_button("Annotated inspection PNG",png_bytes(views["Regions"]),
                      "visiondelta_annotated.png","image/png",use_container_width=True)
    r.download_button("Evidence heatmap PNG",png_bytes(views["Evidence heatmap"]),
                      "visiondelta_heatmap.png","image/png",use_container_width=True)
    l.download_button("Binary region mask",png_bytes(views["Segmentation mask"]),
                      "visiondelta_mask.png","image/png",use_container_width=True)
    r.download_button("Structured JSON report",json.dumps(summary,indent=2).encode(),
                      "visiondelta_report.json","application/json",use_container_width=True)
    st.caption("For engineering review only. This application does not automate safety-critical pass/fail decisions.")
