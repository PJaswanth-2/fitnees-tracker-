"""Demo-data seeder for the Fitness & Workout Progress Tracker.

Generates ~8 weeks of realistic workouts across a handful of exercises plus a
body-metrics trend. This module IS the committed demo dataset — the app never
relies on the gitignored .db file for demo content.

Seeding is idempotent: it only runs when the main tables are empty, so
re-running setup or restarting the app never duplicates rows.
"""

from datetime import date, timedelta

import db

# Program spanning 8 weeks (3 sessions/week). Each exercise progresses in
# weight over time so the "weight lifted over time" chart trends upward.
# fmt: off
_EXERCISE_PLAN = {
    #                     start weight, weekly increment, sets, reps
    "Bench Press":       (135.0, 5.0,  4, 8),
    "Squat":             (185.0, 10.0, 5, 5),
    "Deadlift":          (225.0, 10.0, 3, 5),
    "Overhead Press":    (75.0,  2.5,  4, 8),
    "Barbell Row":       (115.0, 5.0,  4, 10),
}
# fmt: on

# Which exercises are trained on which weekday of a 3-day split.
# 0 = first session of the week, 1 = second, 2 = third.
_SPLIT = {
    0: ["Squat", "Bench Press", "Barbell Row"],
    1: ["Deadlift", "Overhead Press"],
    2: ["Squat", "Bench Press", "Overhead Press"],
}

_WEEKS = 8


def _build_workout_rows(start_date):
    """Return a list of (date, exercise, sets, reps, weight) tuples."""
    rows = []
    for week in range(_WEEKS):
        # Three sessions per week: Mon, Wed, Fri offsets.
        for session_idx, day_offset in enumerate((0, 2, 4)):
            session_date = start_date + timedelta(weeks=week, days=day_offset)
            for exercise in _SPLIT[session_idx]:
                base, increment, sets, reps = _EXERCISE_PLAN[exercise]
                # Small mid-week variation so the second squat/bench day differs.
                nudge = 0.0 if session_idx != 2 else -5.0
                weight = base + increment * week + nudge
                weight = max(weight, base)  # never dip below the starting weight
                rows.append(
                    (session_date.isoformat(), exercise, sets, reps, round(weight, 1))
                )
    return rows


def _build_body_metric_rows(start_date):
    """Return a list of (date, weight, body_fat) tuples, roughly weekly."""
    rows = []
    body_weight = 182.0
    body_fat = 20.0
    for week in range(_WEEKS + 1):
        metric_date = start_date + timedelta(weeks=week)
        rows.append(
            (metric_date.isoformat(), round(body_weight, 1), round(body_fat, 1))
        )
        # Gentle recomposition: lose a little fat, hold weight roughly steady.
        body_weight -= 0.6
        body_fat -= 0.4
    return rows


def seed(force=False):
    """Populate demo data. No-op if data already exists (unless force=True)."""
    db.init_db()
    if not force and not db.is_empty():
        return False  # already seeded

    start_date = date.today() - timedelta(weeks=_WEEKS)
    db.bulk_add_workouts(_build_workout_rows(start_date))
    db.bulk_add_body_metrics(_build_body_metric_rows(start_date))
    return True


if __name__ == "__main__":
    created = seed()
    if created:
        print(
            f"Seeded demo data: {db.count_workouts()} workouts, "
            f"{db.count_body_metrics()} body-metric entries."
        )
    else:
        print("Database already contains data — skipped seeding.")
