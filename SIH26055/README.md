SpectraMind — cognitive spectrum scanner

## Demo quick start

From PowerShell at the workspace root, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\start_demo.ps1
```

The script opens the FastAPI backend and React dashboard in separate terminals.
Open `http://127.0.0.1:5173/` when both terminals are ready.

activation comment
cd "C:\Users\dravi\OneDrive\Desktop\hackothan_26"
.\.venv\Scripts\Activate.ps1
cd SIH26055
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000

open link:
http://127.0.0.1:8000/
api routes :
http://127.0.0.1:8000/api/health
http://127.0.0.1:8000/api/mission?steps=40
http://127.0.0.1:8000/api/benchmark?steps=40
WebSocket stream: ws://127.0.0.1:8000/api/realtime

The dashboard controls the live scanner through this stream:

- **Start** resumes scanning.
- **Pause** holds the latest telemetry without advancing the RF world.
- **Stop** ends scanning while keeping the last result visible.
- **Reset** clears learned state and starts a fresh mission.
- The scenario selector changes the RF world and starts a fresh mission.
- Clicking a spectrum band tunes that band for the next scan.

To run the simulation directly:
python main.py

To use the React development server instead:

cd dashboard\react-app
npm install
npm run dev -- --host 127.0.0.1 --port 5173

Then open:

http://127.0.0.1:5173/

## Demo presentation flow

1. Start the demo with `start_demo.ps1`.
2. Choose **Stable emitter** and press **Reset**.
3. Point out the moving frequency-flow beam and receiver cursor.
4. Explain the five scan stages: advance world, score bands, tune, measure, and update the model.
5. Select **Frequency agile** to show the signal moving between bands.
6. Select **Bursty signal** or **Periodic signal** to demonstrate prediction and repeated activity.
7. Use **Pause** to inspect the current HIT/MISS result and metrics.
8. Click a band to force the next receiver scan to that frequency.

## Demo validation

Run the backend and WebSocket tests with:

```powershell
cd SIH26055
..\.venv\Scripts\python.exe -m pytest tests -q
```

Build the dashboard with:

```powershell
cd dashboard\react-app
npm run build
```

The dashboard connects to `/api/realtime` automatically and displays the
currently selected band plus each live HIT/MISS event. The stream currently
uses the deterministic simulated RF world; an SDR adapter can replace the
receiver later without changing the dashboard protocol.


cd "C:\Users\dravi\OneDrive\Desktop\hackothan_26"
.\.venv\Scripts\Activate.ps1
cd SIH26055
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000

Set-ExecutionPolicy -Scope CurrentUser RemoteSigned