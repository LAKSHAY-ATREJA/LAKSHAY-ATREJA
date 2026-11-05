"""VisionDelta Streamlit demo: aligned image differences and defect-region review."""
import json
from PIL import Image, UnidentifiedImageError
import streamlit as st
from logic import demo_images, inspect, png_bytes

st.set_page_config(page_title='VisionDelta | Visual Inspection',page_icon='🔎',layout='wide')
st.title('VisionDelta')
st.caption('Visual change inspection | classical computer vision | interactive Streamlit demo')
st.info('Portfolio prototype, not a trained defect classifier. Images should be aligned. Demo images are synthetic, and no external model is called.')

with st.sidebar:
    st.header('Images and sensitivity')
    before_file=st.file_uploader('Reference image',type=['png','jpg','jpeg'],key='reference')
    after_file=st.file_uploader('Candidate image',type=['png','jpg','jpeg'],key='candidate')
    threshold=st.slider('Mean RGB change threshold',1,160,40)
    min_area=st.slider('Minimum changed region (pixels)',5,600,30)
    st.caption('Leave both upload fields empty to try the built-in synthetic demonstration.')

if before_file is None and after_file is None:
    before,after=demo_images()
    st.caption('Showing built-in synthetic example.')
elif before_file is not None and after_file is not None:
    try:
        if len(before_file.getvalue())>8_000_000 or len(after_file.getvalue())>8_000_000:
            raise ValueError('Each image must be smaller than 8 MB.')
        before=Image.open(before_file); after=Image.open(after_file)
        before.load();after.load()
    except (ValueError,UnidentifiedImageError,OSError) as exc:
        st.error(f'Could not read images: {exc}')
        st.stop()
else:
    st.warning('Upload both images to compare, or remove uploads to run the demo.')
    st.stop()

result=inspect(before,after,threshold,min_area)
s=result['summary']
a,b,c=st.columns(3)
a.metric('Changed pixels',f"{s['changed_pixel_percent']:.2f}%")
b.metric('Regions above min area',len(s['regions']))
c.metric('Mean RGB difference',f"{s['mean_rgb_difference']:.1f}/255")

st.subheader('Compare the inputs')
left,right=st.columns(2)
with left: st.image(result['reference'],caption='Reference',use_container_width=True)
with right: st.image(result['candidate'],caption='Candidate',use_container_width=True)

st.subheader('Annotated changes and difference map')
left,right=st.columns(2)
with left: st.image(result['annotated'],caption='Connected changed regions',use_container_width=True)
with right: st.image(result['heatmap'],caption='Pixel-level difference intensity',use_container_width=True)

st.subheader('Detected regions')
if s['regions']:
    st.dataframe(s['regions'],hide_index=True,use_container_width=True)
else:
    st.success('No connected changed regions above the chosen minimum area.')

left,right=st.columns(2)
with left: st.download_button('Download annotated PNG',png_bytes(result['annotated']),'visiondelta_review.png','image/png')
with right: st.download_button('Download JSON report',json.dumps(s,indent=2).encode(),'visiondelta_report.json','application/json')

with st.expander('Method and limitations'):
    st.write('Both images are fitted into a common 360 × 300 RGB canvas, then per-pixel mean channel differences are thresholded. Four-connected components isolate regions for review.')
    st.write('Different framing, geometry, shadows or lighting can generate false positives. This is classical deterministic image analysis and does not use neural networks, remote APIs or RAG.')
