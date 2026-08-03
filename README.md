# 🏋️ Fitness & Workout Progress Tracker

A simple, self-contained web app for logging your workouts and body metrics, then
watching your progress on an interactive dashboard. Built with **Streamlit** and
**SQLite** — no accounts, no servers, no cloud. Everything runs on your computer.

---

## ✅ Prerequisites

You only need **Python 3.9 or newer** installed.

- Download it from <https://www.python.org/downloads/>.
- During installation on Windows, **check the box "Add Python to PATH."**

That's it. The setup script handles everything else (creating an isolated
environment, installing the right package versions, loading demo data, and
launching the app).

---

## 🚀 Setup — one command

1. Unzip this project into any folder.
2. **Double-click `setup.bat`** (or, in a terminal, run `setup.bat` from inside
   the project folder).

The script will:

1. Create a virtual environment (`.venv`)
2. Install the pinned dependencies from `requirements.txt`
3. Seed ~8 weeks of demo data into a local SQLite database
4. Open the app in your web browser (usually at <http://localhost:8501>)

The first run takes a minute or two while packages download. After that it
starts almost instantly. To stop the app, press **Ctrl+C** in the terminal
window (or just close it).

> **No login required.** This is a personal, single-user tracker — there are no
> demo accounts because there is no authentication to sign into.

---

## 👀 What you should see on first launch

The app opens on the **Progress Dashboard**, already full of demo data so you can
explore every feature immediately:

- **Summary cards** at the top: number of workouts logged (~100+), exercises
  tracked (5), total training volume, and your latest body weight with the change
  since you started.
- **"Weight lifted over time" chart** — one trending line per exercise
  (Bench Press, Squat, Deadlift, Overhead Press, Barbell Row), each climbing over
  the 8-week program. You can filter which exercises are shown.
- **"Body-weight trend" chart** — a gently declining body-weight line plus a
  body-fat % line, showing a realistic recomposition over two months.
- **🏆 Personal Records table** — the heaviest weight lifted for each exercise and
  the date it was achieved.
- **📅 Weekly Training Volume bar chart** — total volume (sets × reps × weight)
  summed for each week, rising as the weights go up.

Use the sidebar to switch pages:

- **📝 Log Workout** — record a new set (date, exercise, sets, reps, weight). You
  can pick an existing exercise or add a brand-new one. New entries appear in the
  charts right away.
- **⚖️ Log Body Metrics** — record your body weight and body-fat % for a date.

Anything you log is saved to the local database and instantly reflected on the
dashboard.

---

## 🧩 How it's organized

| File               | Purpose                                                              |
| ------------------ | ------------------------------------------------------------------- |
| `app.py`           | The Streamlit UI (dashboard + logging pages)                        |
| `db.py`            | All SQLite logic — schema, inserts, and queries (single source)     |
| `seed.py`          | The committed demo dataset; auto-loads on first run (idempotent)    |
| `requirements.txt` | Pinned package versions                                             |
| `setup.bat`        | One-command Windows setup + launch                                  |
| `fitness.db`       | Your local database (created automatically; not shipped)            |

### Data models

- **Workout** — `date`, `exercise`, `sets`, `reps`, `weight`
- **BodyMetric** — `date`, `weight`, `body_fat`

---

## 🔁 Resetting the demo data

The demo data loads automatically **only when the database is empty**, so
restarting the app never duplicates rows. If you want a completely fresh start,
delete the `fitness.db` file and run `setup.bat` again — it will be recreated and
reseeded.

---

## 🛠️ Running it manually (optional)

If you'd rather not use `setup.bat`:

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python seed.py
streamlit run app.py
```
