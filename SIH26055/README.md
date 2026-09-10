SpectraMind — cognitive spectrum scanner

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

To run the simulation directly:
python main.py

To use the React development server instead:

cd dashboard\react-app
npm run dev -- --host 127.0.0.1 --port 5173

Then open:

http://127.0.0.1:5173/


cd "C:\Users\dravi\OneDrive\Desktop\hackothan_26"
.\.venv\Scripts\Activate.ps1
cd SIH26055
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000

Set-ExecutionPolicy -Scope CurrentUser RemoteSigned