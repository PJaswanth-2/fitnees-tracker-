"""Database helper module for the Fitness & Workout Progress Tracker.

All SQLite access lives here so the Streamlit app (app.py) and the seeder
(seed.py) share one source of truth for the schema and queries.
"""

import os
import sqlite3
from contextlib import contextmanager

import pandas as pd

# Keep the .db file inside the project folder (shippable requirement).
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fitness.db")


@contextmanager
def get_connection():
    """Yield a SQLite connection with row access by name, committing on exit."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Create tables if they do not already exist. Safe to call repeatedly."""
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS workouts (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                date     TEXT    NOT NULL,
                exercise TEXT    NOT NULL,
                sets     INTEGER NOT NULL,
                reps     INTEGER NOT NULL,
                weight   REAL    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS body_metrics (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                date      TEXT    NOT NULL,
                weight    REAL    NOT NULL,
                body_fat  REAL
            );
            """
        )


# --------------------------------------------------------------------------- #
# Insert helpers
# --------------------------------------------------------------------------- #
def add_workout(date, exercise, sets, reps, weight):
    """Insert a single workout row."""
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO workouts (date, exercise, sets, reps, weight) "
            "VALUES (?, ?, ?, ?, ?)",
            (str(date), exercise, int(sets), int(reps), float(weight)),
        )


def add_body_metric(date, weight, body_fat):
    """Insert a single body-metric row (body_fat may be None)."""
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO body_metrics (date, weight, body_fat) VALUES (?, ?, ?)",
            (str(date), float(weight), None if body_fat is None else float(body_fat)),
        )


def bulk_add_workouts(rows):
    """Insert many workout tuples: (date, exercise, sets, reps, weight)."""
    with get_connection() as conn:
        conn.executemany(
            "INSERT INTO workouts (date, exercise, sets, reps, weight) "
            "VALUES (?, ?, ?, ?, ?)",
            rows,
        )


def bulk_add_body_metrics(rows):
    """Insert many body-metric tuples: (date, weight, body_fat)."""
    with get_connection() as conn:
        conn.executemany(
            "INSERT INTO body_metrics (date, weight, body_fat) VALUES (?, ?, ?)",
            rows,
        )


# --------------------------------------------------------------------------- #
# Count / read helpers
# --------------------------------------------------------------------------- #
def count_workouts():
    with get_connection() as conn:
        return conn.execute("SELECT COUNT(*) FROM workouts").fetchone()[0]


def count_body_metrics():
    with get_connection() as conn:
        return conn.execute("SELECT COUNT(*) FROM body_metrics").fetchone()[0]


def is_empty():
    """True when the main tables hold no rows (used for auto-seed)."""
    return count_workouts() == 0 and count_body_metrics() == 0


def get_workouts_df():
    """Return all workouts as a DataFrame sorted by date."""
    with get_connection() as conn:
        df = pd.read_sql_query(
            "SELECT date, exercise, sets, reps, weight FROM workouts ORDER BY date",
            conn,
        )
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
        # Total volume for a row = sets * reps * weight (useful for summaries).
        df["volume"] = df["sets"] * df["reps"] * df["weight"]
    return df


def get_body_metrics_df():
    """Return all body metrics as a DataFrame sorted by date."""
    with get_connection() as conn:
        df = pd.read_sql_query(
            "SELECT date, weight, body_fat FROM body_metrics ORDER BY date",
            conn,
        )
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
    return df


def get_exercises():
    """Distinct exercise names currently logged (sorted)."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT exercise FROM workouts ORDER BY exercise"
        ).fetchall()
    return [r[0] for r in rows]


def get_personal_records():
    """Max weight lifted per exercise, with the date it was achieved."""
    with get_connection() as conn:
        df = pd.read_sql_query(
            """
            SELECT w.exercise            AS Exercise,
                   MAX(w.weight)         AS "Max Weight (lb)",
                   (SELECT date FROM workouts w2
                     WHERE w2.exercise = w.exercise
                     ORDER BY w2.weight DESC, w2.date ASC LIMIT 1) AS "Date Achieved"
            FROM workouts w
            GROUP BY w.exercise
            ORDER BY "Max Weight (lb)" DESC
            """,
            conn,
        )
    return df
