# MIRROR — 90-second demo script

Pre-flight: backend on :8000, frontend on :3000, browser on `/demo`.
If anything is stale, click **Reset demo data** on `/demo` and start over.

---

## 0–10s — The hook

Open `http://localhost:3000`.

> "Can AI predict your next decision? More importantly — can it predict
> **you**?"

Point at the loop animation: **observe → learn → predict → test → adapt**.
Point at the **FALLBACK MODE** pill in the top-right:

> "That pill means MIRROR is running without any AI provider. Every number
> you are about to see is computed deterministically from your own
> interactions."

---

## 10–25s — Seed the demo

Click **LOAD DEMO DATA**. You land on `/dashboard`.

Point at the numbers:

> "9 observations. 2 resolved predictions. Every one of these came from
> actual recorded interactions — the demo persona is labeled DEMO DATA and
> nothing is invented."

---

## 25–35s — Show the fingerprint

Click **View fingerprint**.

Point at the radar:

> "Nine axes. Each dot is coloured by confidence. Adaptability is grey
> and marked n/a — MIRROR has not observed you in a scenario where new
> information arrives mid-decision. It will not invent a number to fill
> the gap."

Point at the **Observed patterns** list:

> "These are the patterns the model could support. Notice they are
> statements about observed decisions, not about you as a person."

---

## 35–50s — Let MIRROR commit to a prediction

Back to `/demo`. Click **Step 3**. Then click **Step 4**.

You land on `/predict/<scenarioId>`.

> "MIRROR is committing to a prediction before you decide. It says
> it thinks you will end up on Option B — and it shows you the full
> probability distribution, the confidence components, and the
> evidence it used."

Point at the three confidence components at the bottom of the card:

> "Scenario similarity, decisiveness, sample support. If any of those is
> low, the confidence reflects that."

---

## 50–70s — NOW YOU

Click **NOW YOU →**.

Make a decision. Pick the option that is **not** what MIRROR predicted,
if you want the more dramatic comparison. Click **Submit decision**.

Wait for navigation to `/compare/<predictionId>`.

---

## 70–85s — Prediction vs Reality

Point at the **MIRROR VS YOU** table.

> "Four facets compared line-by-line. MIRROR got two of them wrong. It
> says so — no hedging."

Point at the **Model self-critique** card:

> "Here MIRROR named the specific assumption that failed and told you
> what it will change. That is the loop: observe → predict → compare →
> reflect → update."

---

## 85–90s — Close

Click **Find my blind spots**.

Point at the split:

> "MIRROR knows seven things about your decisions. It does not know two.
> Every unknown comes with a challenge you can take."

Final line:

> "MIRROR doesn't read your mind. It learns the decisions you actually
> make — and discovers where its model of you is wrong."

---

## Recovery paths

| If this happens | Do this |
|---|---|
| Prediction card loads slow | It is a template fallback (~50 ms). Wait one beat. |
| The wrong prediction outcome | That is fine — the miss state is the better demo. |
| Backend not reachable | Check the pill: it will show **offline** in red. Restart uvicorn. |
| The demo profile looks empty | Run `/demo` → **Reset demo data** → **Run step 1**. |
| WiFi is down entirely | Everything works — the demo makes zero external calls. |