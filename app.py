"""Visual Damage/Defect Report Agent — Streamlit UI.

Two tabs:
  - Report an issue: upload/capture a photo, get an AI description, confirm
    it, and let the agent log it.
  - Dashboard: trend charts plus the full list of logged issues, with a
    "mark resolved" action per open issue.
"""
import uuid
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

import charts
import db
from agent_tools import run_logging_agent
from vision import describe_image

PHOTOS_DIR = Path(__file__).parent / "data" / "photos"
PHOTOS_DIR.mkdir(parents=True, exist_ok=True)

st.set_page_config(page_title="Visual Issue Reporter", page_icon="\U0001F4F8", layout="wide")
db.init_db()

for key, default in {
    "draft_description": None,
    "photo_bytes": None,
    "photo_mime": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


def reset_draft():
    st.session_state.draft_description = None
    st.session_state.photo_bytes = None
    st.session_state.photo_mime = None


st.title("Visual Issue Reporter")
st.caption("Snap a photo of a problem \u2014 a vision model describes it, and an agent logs it. No forms.")

report_tab, dashboard_tab = st.tabs(["Report an issue", "Dashboard"])

# ---------------------------------------------------------------- Report tab
with report_tab:
    left, right = st.columns([1, 1])

    with left:
        st.subheader("1. Add a photo")
        uploaded = st.file_uploader("Upload a photo", type=["jpg", "jpeg", "png", "webp"])
        camera_photo = st.camera_input("...or take one now")
        photo_file = uploaded or camera_photo

        if photo_file is not None:
            st.image(photo_file, caption="This photo will be described below", width=320)
            if st.button("Describe issue", type="primary"):
                with st.spinner("Looking at the photo..."):
                    image_bytes = photo_file.getvalue()
                    mime = photo_file.type or "image/jpeg"
                    description = describe_image(image_bytes, mime)
                st.session_state.draft_description = description
                st.session_state.photo_bytes = image_bytes
                st.session_state.photo_mime = mime
                st.rerun()

    with right:
        st.subheader("2. Confirm and log")
        if not st.session_state.draft_description:
            st.info("Add a photo on the left and click **Describe issue** to get started.")
        else:
            edited = st.text_area(
                "AI-generated description \u2014 edit if needed:",
                value=st.session_state.draft_description,
                height=150,
                key="edited_description",
            )
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Confirm & log issue", type="primary"):
                    photo_id = uuid.uuid4().hex[:12]
                    mime = st.session_state.photo_mime or "image/jpeg"
                    ext = "jpg" if "jpeg" in mime else mime.split("/")[-1]
                    photo_path = PHOTOS_DIR / f"{photo_id}.{ext}"
                    photo_path.write_bytes(st.session_state.photo_bytes)

                    with st.spinner("Agent is logging the issue..."):
                        result_text = run_logging_agent(edited.strip(), str(photo_path))

                    reset_draft()
                    st.success(result_text)
            with col2:
                if st.button("Discard"):
                    reset_draft()
                    st.rerun()

# ------------------------------------------------------------- Dashboard tab
with dashboard_tab:
    df = db.get_all_issues()

    st.subheader("Trends")
    if df.empty:
        st.info("No issues logged yet \u2014 report one to see charts here.")
    else:
        c1, c2 = st.columns(2)
        with c1:
            st.pyplot(charts.issues_over_time_figure(df), clear_figure=True)
        with c2:
            st.pyplot(charts.category_breakdown_figure(df), clear_figure=True)

    st.divider()
    st.subheader("Logged issues")

    status_filter = st.radio("Filter", ["All", "Open", "Resolved"], horizontal=True)
    if status_filter == "All":
        view = df
    else:
        view = df[df["status"] == status_filter.lower()]

    if view.empty:
        st.info("No issues match this filter.")
    else:
        for _, row in view.iterrows():
            with st.container(border=True):
                photo_col, info_col = st.columns([1, 3])
                with photo_col:
                    if row["photo_path"] and Path(row["photo_path"]).exists():
                        st.image(row["photo_path"], width=180)
                    else:
                        st.caption("No photo on file")
                with info_col:
                    status_label = row["status"].upper()
                    st.markdown(f"**#{row['id']} \u00b7 {row['category']}** \u2014 {status_label}")
                    st.write(row["description"])
                    st.caption(row["timestamp"])
                    if row["status"] == "open":
                        if st.button("Mark resolved", key=f"resolve_{row['id']}"):
                            db.update_status(row["id"], "resolved")
                            st.rerun()