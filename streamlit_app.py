"""WorthWearing Streamlit demo — try-on plus wardrobe intelligence."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "backend"))

import streamlit as st

from app.config import get_settings
from app.models import ProviderMode, Recommendation, TryOnStatus
from app.runtime import (
    analyze_candidate,
    image_source,
    prepared_result,
    provider_label,
    run_try_on,
    try_on_mode,
)
from app.store import load_demo

REC_COLOR = {
    Recommendation.WORTH_IT: "#0F7B4B",
    Recommendation.THINK_AGAIN: "#B45309",
    Recommendation.SKIP_IT: "#B42318",
}


def _apply_secrets() -> None:
    try:
        secrets = st.secrets
    except Exception:
        return
    for key in (
        "DEMO_MODE",
        "PERFECT_CORP_API_KEY",
        "PERFECT_CORP_BASE_URL",
        "PERFECT_CORP_TRYON_PATH",
        "PERFECT_CORP_STATUS_PATH",
        "PERFECT_CORP_IMAGE_GENERATOR_PATH",
    ):
        value = secrets.get(key)
        if value not in (None, ""):
            os.environ[key] = str(value)
    get_settings.cache_clear()


_apply_secrets()

st.set_page_config(
    page_title="WorthWearing — Try it on. Know if it’s worth owning.",
    page_icon="🧥",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
      .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background: #ffffff;
      }
      [data-testid="stToolbar"] { display: none; }
      footer { visibility: hidden; }
      h1, h2, h3 { letter-spacing: -0.02em; color: #111111 !important; }
      .eyebrow { font-size: 11px; letter-spacing: 0.18em; text-transform: uppercase; color: #5c5c5c; }
      .rec { font-size: 2.4rem; font-weight: 600; line-height: 1.1; }
      .muted { color: #5c5c5c; }
      div[data-testid="stHorizontalBlock"] { align-items: start; }
    </style>
    """,
    unsafe_allow_html=True,
)

demo = load_demo()
candidates = {item.id: item for item in demo.candidates}

if "selected_id" not in st.session_state:
    st.session_state.selected_id = "jacket-a"
if "analyses" not in st.session_state:
    st.session_state.analyses = {}
if "jobs" not in st.session_state:
    st.session_state.jobs = {}
if "previous_id" not in st.session_state:
    st.session_state.previous_id = None
if "using_prepared" not in st.session_state:
    st.session_state.using_prepared = {}
if "error" not in st.session_state:
    st.session_state.error = None


def select_jacket(jacket_id: str) -> None:
    if jacket_id != st.session_state.selected_id:
        st.session_state.previous_id = st.session_state.selected_id
        st.session_state.selected_id = jacket_id
        st.session_state.error = None


st.markdown('<p class="eyebrow">WorthWearing Intelligence</p>', unsafe_allow_html=True)
st.title("Try it on. Know if it’s worth owning.")
st.caption(
    "Virtual try-on shows whether it looks good. WorthWearing shows whether it deserves a place in your wardrobe."
)

mode = try_on_mode()
badge = "Live API" if mode == ProviderMode.LIVE else "Prepared demo"
st.markdown(
    f'<p class="eyebrow">Provider · {badge} · Maya Chen · {demo.shopper.city}</p>',
    unsafe_allow_html=True,
)

visual, analytics = st.columns([3, 2], gap="large")
candidate = candidates[st.session_state.selected_id]
job = st.session_state.jobs.get(candidate.id)
analysis = st.session_state.analyses.get(candidate.id)
using_prepared = st.session_state.using_prepared.get(candidate.id, False)

with visual:
    st.markdown('<p class="eyebrow">Perfect Corp try-on</p>', unsafe_allow_html=True)
    stage_url = demo.shopper.photo_url
    stage_caption = demo.shopper.photo_alt
    if job and job.result_image_url:
        stage_url = job.result_image_url
        stage_caption = f"Try-on of {candidate.name} on {demo.shopper.name}"
    if using_prepared or (job and job.provider == ProviderMode.DEMO and job.result_image_url):
        st.caption("Prepared demo")
    elif job and job.provider == ProviderMode.LIVE and job.status == TryOnStatus.COMPLETED:
        st.caption("Live API")
    st.image(image_source(stage_url), caption=stage_caption, use_container_width=True)

    if job and job.status in {TryOnStatus.FAILED, TryOnStatus.QUEUED, TryOnStatus.PROCESSING}:
        if job.error_message or job.error_category == "timeout":
            st.warning(job.error_message or "Live try-on did not finish.")
            if st.button("Use prepared demo result", key="fallback"):
                st.session_state.jobs[candidate.id] = prepared_result(candidate.id)
                st.session_state.using_prepared[candidate.id] = True
                st.rerun()

    if candidate.scenario_assets:
        st.markdown('<p class="eyebrow">Occasion scenarios</p>', unsafe_allow_html=True)
        scenario_cols = st.columns(len(candidate.scenario_assets))
        for column, scenario in zip(scenario_cols, candidate.scenario_assets):
            with column:
                st.image(image_source(scenario.image_url), caption=scenario.label, use_container_width=True)

    st.markdown('<p class="eyebrow">Choose a jacket</p>', unsafe_allow_html=True)
    jacket_cols = st.columns(2)
    for column, item in zip(jacket_cols, demo.candidates):
        with column:
            selected = item.id == candidate.id
            st.image(image_source(item.image_url), caption=f"{item.short_label} · {item.name}", use_container_width=True)
            if st.button(
                f"{'Selected · ' if selected else ''}{item.short_label}",
                key=f"pick-{item.id}",
                type="primary" if selected else "secondary",
                use_container_width=True,
            ):
                select_jacket(item.id)
                st.rerun()
            if item.price is not None:
                st.caption(f"${item.price:.0f}")

    if st.button("Try it with my wardrobe", type="primary", use_container_width=True):
        st.session_state.error = None
        st.session_state.using_prepared[candidate.id] = False
        with st.status("Working through the wardrobe…", expanded=True) as status:
            st.write("Analyzing garment")
            try:
                result = analyze_candidate(candidate.id)
                st.session_state.analyses[candidate.id] = result
                st.write("Generating try-on")
                st.write("Comparing wardrobe")
                finished = run_try_on(candidate.id)
                st.session_state.jobs[candidate.id] = finished
                if finished.provider == ProviderMode.DEMO:
                    st.session_state.using_prepared[candidate.id] = True
                st.write("Calculating recommendation")
                if finished.status == TryOnStatus.COMPLETED:
                    status.update(label="Recommendation ready", state="complete")
                else:
                    status.update(label="Scoring ready · try-on needs attention", state="error")
            except Exception as exc:
                st.session_state.error = str(exc)
                status.update(label="Analysis failed", state="error")
        st.rerun()

    if st.session_state.error:
        st.error(st.session_state.error)

    st.markdown(
        f'<p class="eyebrow">{demo.shopper.name}’s closet · {demo.shopper.city}</p>',
        unsafe_allow_html=True,
    )
    closet_cols = st.columns(6)
    for index, item in enumerate(demo.closet):
        with closet_cols[index % 6]:
            st.image(image_source(item.image_url), caption=item.name, use_container_width=True)

with analytics:
    if analysis:
        color = REC_COLOR[analysis.recommendation]
        st.markdown(
            f'<p class="rec" style="color:{color}">{analysis.recommendation_label}</p>',
            unsafe_allow_html=True,
        )
        st.caption(analysis.summary)
        score_col, compat_col, risk_col = st.columns(3)
        score_col.metric("Worth Score", analysis.worth_score)
        compat_col.metric("Wardrobe Compatibility", analysis.wardrobe_compatibility)
        risk_col.metric("Return Risk", analysis.return_risk)
        st.caption("Return Risk is a deterministic proxy, not a predicted return rate.")
        st.write(f"Estimated outfits: **{analysis.outfit_count}**")

        st.markdown('<p class="eyebrow">Weighted contributions</p>', unsafe_allow_html=True)
        chart_rows = {
            factor.label: round(factor.contribution * 100, 1) for factor in analysis.factors
        }
        st.bar_chart(chart_rows, horizontal=True, color="#111111", height=220)
        for factor in analysis.factors:
            st.caption(
                f"{factor.label} · {factor.weight * 100:.0f}% × {factor.value:.2f} = "
                f"{factor.contribution * 100:.1f} pts — {factor.explanation}"
            )

        if analysis.cost_per_wear:
            cpw = analysis.cost_per_wear
            st.markdown('<p class="eyebrow">Estimated CPW scenario</p>', unsafe_allow_html=True)
            st.metric("Estimated CPW", f"${cpw.estimated_cpw:.2f}")
            st.caption(
                f"${cpw.price:.0f} ÷ {cpw.estimated_wears} wears over {cpw.horizon_months} months. "
                "This is a scenario, not a prediction."
            )
            with st.expander("CPW assumptions"):
                for assumption in cpw.assumptions:
                    st.write(f"- {assumption}")

        st.markdown('<p class="eyebrow">Supporting closet items</p>', unsafe_allow_html=True)
        for item in analysis.matched_items[:8]:
            match_img, match_copy = st.columns([1, 4])
            match_img.image(image_source(item.image_url), use_container_width=True)
            match_copy.markdown(f"**{item.name}**  \n{item.reason}")

        st.markdown('<p class="eyebrow">Compatible outfits</p>', unsafe_allow_html=True)
        if analysis.outfits:
            for outfit in analysis.outfits:
                st.caption(f"{outfit.occasion} · {outfit.rationale}")
                piece_cols = st.columns(min(4, len(outfit.pieces)))
                for column, piece in zip(piece_cols, outfit.pieces):
                    column.image(image_source(piece.image_url), caption=piece.name, use_container_width=True)
        else:
            st.caption("No compatible outfits under the current rules.")

        with st.expander("Why this result?"):
            for note in analysis.methodology_notes:
                st.write(f"- {note}")
            st.markdown('<p class="eyebrow">Rejected combinations</p>', unsafe_allow_html=True)
            for row in analysis.rejected_combinations[:8]:
                st.caption(f"{row.rule}: {row.reason}")

        previous = st.session_state.analyses.get(st.session_state.previous_id or "")
        if previous and previous.candidate_id != analysis.candidate_id:
            st.markdown('<p class="eyebrow">Before and after</p>', unsafe_allow_html=True)
            before, after = st.columns(2)
            before.metric(previous.candidate_name, previous.recommendation_label, help=f"Return Risk {previous.return_risk}")
            after.metric(analysis.candidate_name, analysis.recommendation_label, help=f"Return Risk {analysis.return_risk}")
            before.caption(f"Return Risk {previous.return_risk}")
            after.caption(f"Return Risk {analysis.return_risk}")
    else:
        st.subheader("Wardrobe intelligence")
        st.write(
            "Select a jacket, then run try-on and scoring together. Recommendations are "
            "deterministic. This is a decision-support prototype, not a proven return model."
        )

    st.divider()
    st.markdown('<p class="eyebrow">Retailer value</p>', unsafe_allow_html=True)
    st.write(
        "A future retailer pilot could measure recommendation acceptance, purchases, "
        "keep rate, and returns. This prototype does not display invented improvements."
    )
    st.info(demo.close_line)
    st.caption(f"Active provider: {provider_label()}. MCP is not active.")
