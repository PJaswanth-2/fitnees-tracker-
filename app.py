"""Fitness & Workout Progress Tracker — Streamlit front end.

Run with:  streamlit run app.py

All database access is delegated to db.py; demo data is auto-loaded on first
run via seed.py so every chart is populated immediately.
"""

from datetime import date

import altair as alt
import pandas as pd
import streamlit as st

import db
import seed

st.set_page_config(page_title="Fitness & Workout Tracker", page_icon="🏋️", layout="wide")


# --------------------------------------------------------------------------- #
# First-run setup: create tables and auto-seed demo data if empty.
# --------------------------------------------------------------------------- #
@st.cache_resource
def bootstrap():
    db.init_db()
    seed.seed()  # idempotent — only fills empty tables
    return True


bootstrap()


def refresh():
    """Clear cached data-loaders after a write so the UI reflects new rows."""
    load_workouts.clear()
    load_body_metrics.clear()
    load_exercises.clear()


@st.cache_data
def load_workouts():
    return db.get_workouts_df()


@st.cache_data
def load_body_metrics():
    return db.get_body_metrics_df()


@st.cache_data
def load_exercises():
    return db.get_exercises()


# --------------------------------------------------------------------------- #
# Sidebar navigation
# --------------------------------------------------------------------------- #
st.sidebar.title("🏋️ Fitness Tracker")
page = st.sidebar.radio(
    "Navigate",
    ["📊 Progress Dashboard", "📝 Log Workout", "⚖️ Log Body Metrics"],
)
st.sidebar.markdown("---")
st.sidebar.caption(
    "Demo data (~8 weeks) is loaded automatically on first launch so every "
    "chart is populated. Log your own entries to see them appear."
)


# --------------------------------------------------------------------------- #
# Page: Log Workout
# --------------------------------------------------------------------------- #
def page_log_workout():
    st.header("📝 Log a Workout")
    exercises = load_exercises()

    with st.form("workout_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            w_date = st.date_input("Date", value=date.today())
            existing = st.selectbox(
                "Exercise", options=exercises + ["➕ New exercise…"]
            )
            new_exercise = ""
            if existing == "➕ New exercise…":
                new_exercise = st.text_input("New exercise name")
        with col2:
            sets = st.number_input("Sets", min_value=1, max_value=20, value=3, step=1)
            reps = st.number_input("Reps", min_value=1, max_value=100, value=8, step=1)
            weight = st.number_input(
                "Weight (lb)", min_value=0.0, max_value=2000.0, value=135.0, step=5.0
            )

        submitted = st.form_submit_button("Save workout", type="primary")
        if submitted:
            exercise = new_exercise.strip() if existing == "➕ New exercise…" else existing
            if not exercise:
                st.error("Please enter an exercise name.")
            else:
                db.add_workout(w_date, exercise, sets, reps, weight)
                refresh()
                st.success(
                    f"Logged {exercise}: {sets}×{reps} @ {weight:g} lb on {w_date}."
                )

    st.subheader("Recent workouts")
    df = load_workouts()
    if df.empty:
        st.info("No workouts yet.")
    else:
        recent = df.sort_values("date", ascending=False).head(15).copy()
        recent["date"] = recent["date"].dt.strftime("%Y-%m-%d")
        st.dataframe(
            recent[["date", "exercise", "sets", "reps", "weight"]],
            use_container_width=True,
            hide_index=True,
        )


# --------------------------------------------------------------------------- #
# Page: Log Body Metrics
# --------------------------------------------------------------------------- #
def page_log_metrics():
    st.header("⚖️ Log Body Metrics")

    with st.form("metric_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            m_date = st.date_input("Date", value=date.today())
        with col2:
            body_weight = st.number_input(
                "Body weight (lb)", min_value=0.0, max_value=1000.0, value=180.0, step=0.1
            )
        with col3:
            body_fat = st.number_input(
                "Body fat (%)", min_value=0.0, max_value=100.0, value=18.0, step=0.1
            )
        submitted = st.form_submit_button("Save metrics", type="primary")
        if submitted:
            db.add_body_metric(m_date, body_weight, body_fat)
            refresh()
            st.success(f"Logged {body_weight:g} lb / {body_fat:g}% on {m_date}.")

    st.subheader("Recent entries")
    df = load_body_metrics()
    if df.empty:
        st.info("No body metrics yet.")
    else:
        recent = df.sort_values("date", ascending=False).head(15).copy()
        recent["date"] = recent["date"].dt.strftime("%Y-%m-%d")
        st.dataframe(
            recent.rename(
                columns={"date": "Date", "weight": "Weight (lb)", "body_fat": "Body Fat (%)"}
            ),
            use_container_width=True,
            hide_index=True,
        )


# --------------------------------------------------------------------------- #
# Page: Progress Dashboard
# --------------------------------------------------------------------------- #
def page_dashboard():
    st.header("📊 Progress Dashboard")
    workouts = load_workouts()
    metrics = load_body_metrics()

    if workouts.empty and metrics.empty:
        st.info("No data yet — log a workout or body metric to get started.")
        return

    # --- Top-line metrics -------------------------------------------------- #
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Workouts logged", f"{len(workouts):,}")
    c2.metric("Exercises tracked", workouts["exercise"].nunique() if not workouts.empty else 0)
    total_volume = int(workouts["volume"].sum()) if not workouts.empty else 0
    c3.metric("Total volume (lb)", f"{total_volume:,}")
    if not metrics.empty:
        latest = metrics.sort_values("date").iloc[-1]
        first = metrics.sort_values("date").iloc[0]
        delta = latest["weight"] - first["weight"]
        c4.metric("Body weight (lb)", f"{latest['weight']:g}", f"{delta:+.1f}")
    else:
        c4.metric("Body weight (lb)", "—")

    st.markdown("---")

    # --- Weight lifted over time per exercise ------------------------------ #
    st.subheader("🏋️ Weight lifted over time (per exercise)")
    if workouts.empty:
        st.info("No workout data.")
    else:
        all_exercises = load_exercises()
        selected = st.multiselect(
            "Filter exercises", options=all_exercises, default=all_exercises
        )
        plot_df = workouts[workouts["exercise"].isin(selected)]
        if plot_df.empty:
            st.info("Select at least one exercise.")
        else:
            line = (
                alt.Chart(plot_df)
                .mark_line(point=True)
                .encode(
                    x=alt.X("date:T", title="Date"),
                    y=alt.Y("weight:Q", title="Weight (lb)"),
                    color=alt.Color("exercise:N", title="Exercise"),
                    tooltip=[
                        alt.Tooltip("date:T", title="Date"),
                        "exercise:N",
                        alt.Tooltip("weight:Q", title="Weight (lb)"),
                        "sets:Q",
                        "reps:Q",
                    ],
                )
                .properties(height=380)
                .interactive()
            )
            st.altair_chart(line, use_container_width=True)

    # --- Body-weight trend ------------------------------------------------- #
    st.subheader("⚖️ Body-weight trend")
    if metrics.empty:
        st.info("No body-metric data.")
    else:
        base = alt.Chart(metrics).encode(x=alt.X("date:T", title="Date"))
        weight_line = base.mark_line(point=True, color="#4C78A8").encode(
            y=alt.Y("weight:Q", title="Body weight (lb)", scale=alt.Scale(zero=False)),
            tooltip=[
                alt.Tooltip("date:T", title="Date"),
                alt.Tooltip("weight:Q", title="Weight (lb)"),
                alt.Tooltip("body_fat:Q", title="Body fat (%)"),
            ],
        )
        st.altair_chart(weight_line.properties(height=320).interactive(), use_container_width=True)

        if metrics["body_fat"].notna().any():
            st.caption("Body-fat % trend")
            fat_line = base.mark_line(point=True, color="#E45756").encode(
                y=alt.Y("body_fat:Q", title="Body fat (%)", scale=alt.Scale(zero=False)),
                tooltip=[alt.Tooltip("date:T", title="Date"), alt.Tooltip("body_fat:Q", title="Body fat (%)")],
            )
            st.altair_chart(fat_line.properties(height=260).interactive(), use_container_width=True)

    st.markdown("---")

    # --- Personal records + weekly volume side by side --------------------- #
    left, right = st.columns(2)

    with left:
        st.subheader("🏆 Personal Records")
        if workouts.empty:
            st.info("No records yet.")
        else:
            pr = db.get_personal_records()
            pr["Date Achieved"] = pd.to_datetime(pr["Date Achieved"]).dt.strftime("%Y-%m-%d")
            st.dataframe(pr, use_container_width=True, hide_index=True)

    with right:
        st.subheader("📅 Weekly Training Volume")
        if workouts.empty:
            st.info("No volume yet.")
        else:
            wv = workouts.copy()
            # ISO week starting Monday -> label by the week's Monday date.
            wv["week"] = wv["date"].dt.to_period("W-SUN").apply(lambda p: p.start_time)
            weekly = wv.groupby("week", as_index=False)["volume"].sum()
            bar = (
                alt.Chart(weekly)
                .mark_bar(color="#54A24B")
                .encode(
                    x=alt.X("week:T", title="Week of"),
                    y=alt.Y("volume:Q", title="Total volume (lb)"),
                    tooltip=[
                        alt.Tooltip("week:T", title="Week of"),
                        alt.Tooltip("volume:Q", title="Volume (lb)", format=","),
                    ],
                )
                .properties(height=300)
            )
            st.altair_chart(bar, use_container_width=True)
            st.caption("Volume = sets × reps × weight, summed per week.")


# --------------------------------------------------------------------------- #
# Router
# --------------------------------------------------------------------------- #
if page == "📊 Progress Dashboard":
    page_dashboard()
elif page == "📝 Log Workout":
    page_log_workout()
else:
    page_log_metrics()
