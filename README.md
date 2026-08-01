Visual Damage/Defect Report Agent

Upload a photo of a physical issue, get an AI-generated description of
what's wrong, confirm it, and an agent logs it to SQLite. Dashboard shows
every logged issue with trend charts and lets you mark items resolved.

 How it works

1. Report an issue upload or take a photo. A Groq vision model
   describes what's visibly wrong in 2\u20134 sentences.
2. You confirm the description is editable. Nothing is logged until
   you click "Confirm & log issue."
3. Agent logs  a small LangChain agent reads the confirmed description, picks the best
   category, and calls the tool exactly once. The tool call inserts a row
   into SQLite (description, category, photo path, timestamp, status).
4. Dashboard pandas reads the table, matplotlib charts show issues
   over time and by category, and every issue is listed with its photo.
   Open issues have a Mark resolved" button.

See agent_tools.py for the agent/tool, db.py for the SQLite schema,
vision.py for the photo description step, and charts.py for the trend
charts.

Setup

Requires Python 3.10+ and a free [Groq API key](https://console.groq.com/keys).

Run
streamlit run app.py


Streamlit opens the app in your browser (usually http://localhost:8501).
The first upload creates data/issues.db and data/photos/ automatically.


.
