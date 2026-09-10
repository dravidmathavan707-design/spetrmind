import React, { useEffect, useMemo, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { Activity, BrainCircuit, CircleDot, RotateCcw, ScanLine } from 'lucide-react'
import './styles.css'

const API = '/api'

function lastIndexForBand(decisions, bandId) {
  let last = -1
  decisions.forEach((decision, index) => {
    if (decision.band === bandId) last = index
  })
  return last
}

function App() {
  const [mission, setMission] = useState(null)
  const [benchmark, setBenchmark] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [selected, setSelected] = useState(0)
  const [focusedBand, setFocusedBand] = useState(null)
  const [inspectMode, setInspectMode] = useState('timeline')

  async function runMission() {
    setLoading(true)
    setError('')
    try {
      const [missionResponse, benchmarkResponse] = await Promise.all([
        fetch(`${API}/mission?steps=40`),
        fetch(`${API}/benchmark?steps=40`),
      ])
      if (!missionResponse.ok || !benchmarkResponse.ok) {
        throw new Error('The API returned an error response.')
      }
      const nextMission = await missionResponse.json()
      const nextBenchmark = await benchmarkResponse.json()
      setMission(nextMission)
      setBenchmark(nextBenchmark)
      setSelected(0)
      setFocusedBand(nextMission.decisions?.[0]?.band ?? 0)
      setInspectMode('timeline')
    } catch (requestError) {
      setError(`${requestError.message} Start the backend with: uvicorn api.main:app --host 127.0.0.1 --port 8000`)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { runMission() }, [])

  const eventIndex = useMemo(() => {
    if (!mission) return -1
    if (inspectMode === 'timeline') return selected
    return lastIndexForBand(mission.decisions, focusedBand)
  }, [mission, selected, focusedBand, inspectMode])

  const decision = eventIndex >= 0 ? mission?.decisions[eventIndex] : null
  const explanation = eventIndex >= 0 ? mission?.explanations[eventIndex] : null
  const observation = eventIndex >= 0 ? mission?.observations[eventIndex] : null
  const metrics = mission?.metrics
  const activeBand = inspectMode === 'band' ? focusedBand : (decision?.band ?? focusedBand)
  const spectrumState = activeBand != null
    ? mission?.spectrum?.[activeBand] ?? mission?.spectrum?.[String(activeBand)]
    : null

  function inspectBand(bandId) {
    setInspectMode('band')
    setFocusedBand(bandId)
    const last = lastIndexForBand(mission.decisions, bandId)
    if (last >= 0) setSelected(last)
  }

  function inspectEvent(index) {
    setInspectMode('timeline')
    setSelected(index)
    setFocusedBand(mission.decisions[index].band)
  }

  return (
    <main className="shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark"><ScanLine size={20} /></span>
          <div>
            <strong>SPECTRAMIND</strong>
            <small>cognitive spectrum / receiver control room</small>
          </div>
        </div>
        <button type="button" className="run-button" onClick={runMission} disabled={loading}>
          <RotateCcw size={16} /> {loading ? 'Running' : 'Run mission'}
        </button>
      </header>
      <section className="hero">
        <div>
          <p className="kicker">SPECTRAMIND / SYNTHETIC RF WORLD</p>
          <h1>Find the signal<br /><em>before it moves.</em></h1>
          <p className="lede">An uncertainty-aware receiver learns the spectrum one scan at a time.</p>
        </div>
        <div className="status"><span className="pulse" /> SYSTEM ONLINE <small>40-step evaluation</small></div>
      </section>
      {error ? <div className="loading error">{error}</div> : !mission ? <div className="loading">Initializing mission telemetry...</div> : <>
        <section className="grid">
          <article className="panel spectrum-panel">
            <div className="panel-head"><span>01 / SPECTRUM STATE</span><Activity size={17} /></div>
            <div className="bands">
              {Object.entries(mission.spectrum).map(([band, state]) => {
                const bandId = Number(band)
                return (
                  <button
                    type="button"
                    className={`band ${activeBand === bandId ? 'selected' : ''} ${state.activity_probability > 0.65 ? 'hot' : ''}`}
                    key={band}
                    onClick={() => inspectBand(bandId)}
                  >
                    <i style={{ height: `${Math.max(8, state.activity_probability * 100)}%` }} />
                    <span>B{band}</span>
                  </button>
                )
              })}
            </div>
            <div className="legend">
              <span><i className="dot hot-dot" /> learned activity</span>
              <span><i className="dot selected-dot" /> current target</span>
            </div>
          </article>
          <article className="panel decision-panel">
            <div className="panel-head"><span>02 / NEXT DECISION</span><BrainCircuit size={17} /></div>
            {decision ? (
              <>
                <div className="target">
                  <small>SELECTED BAND</small>
                  <strong>B{decision.band}</strong>
                  <span>{Number(decision.dwell).toFixed(0)} ms dwell</span>
                </div>
                <div className="readings">
                  {[['Prediction', decision.activity_score], ['Uncertainty', decision.uncertainty], ['Information', decision.information_gain], ['Drift', decision.drift ? 1 : 0]].map(([label, value]) => (
                    <div key={label}>
                      <span>{label}</span>
                      <b>{Number(value).toFixed(2)}</b>
                      <div className="meter"><i style={{ width: `${Math.max(0, Math.min(1, Number(value))) * 100}%` }} /></div>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <>
                <div className="target">
                  <small>SELECTED BAND</small>
                  <strong>B{activeBand}</strong>
                  <span>not scanned this mission</span>
                </div>
                <div className="readings">
                  <div>
                    <span>Belief</span>
                    <b>{Number(spectrumState?.activity_probability || 0).toFixed(2)}</b>
                    <div className="meter"><i style={{ width: `${(spectrumState?.activity_probability || 0) * 100}%` }} /></div>
                  </div>
                  <div>
                    <span>Scans</span>
                    <b>{spectrumState?.scan_count ?? 0}</b>
                    <div className="meter"><i style={{ width: '0%' }} /></div>
                  </div>
                </div>
              </>
            )}
          </article>
          <article className="panel metrics-panel">
            <div className="panel-head"><span>03 / MISSION RESULT</span><CircleDot size={17} /></div>
            <div className="metric-big">
              <strong>{((metrics?.detection_rate || 0) * 100).toFixed(1)}%</strong>
              <span>scan detection rate</span>
            </div>
            <div className="metric-row">
              <span>hits <b>{metrics?.hits}</b></span>
              <span>misses <b>{metrics?.misses}</b></span>
              <span>first hit <b>{metrics?.first_detection_time ?? '—'}</b></span>
            </div>
          </article>
        </section>
        <section className="lower-grid">
          <article className="panel timeline-panel">
            <div className="panel-head"><span>04 / MISSION REPLAY</span><span className="muted">click an event to inspect</span></div>
            <div className="timeline">
              {mission.observations.map((item, index) => (
                <button
                  type="button"
                  className={`event ${index === eventIndex ? 'active' : ''}`}
                  key={index}
                  onClick={() => inspectEvent(index)}
                >
                  <span>{String(Math.trunc(item.time)).padStart(2, '0')}</span>
                  <b>B{item.band}</b>
                  <i className={item.detected ? 'hit' : 'miss'}>{item.detected ? 'HIT' : 'MISS'}</i>
                </button>
              ))}
            </div>
          </article>
          <article className="panel explain-panel">
            <div className="panel-head"><span>05 / WHY THIS BAND?</span><span className="tag">AUDITABLE</span></div>
            {explanation ? (
              <>
                <h2>B{explanation.selected_band} was selected.</h2>
                <p>{explanation.reason}{observation?.detected ? ' This scan was a HIT.' : ' This scan was a MISS.'}</p>
                <div className="explain-values">
                  {Object.entries(explanation.components).map(([key, value]) => (
                    <div key={key}>
                      <span>{key.replaceAll('_', ' ')}</span>
                      <b>{Number(value).toFixed(2)}</b>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <>
                <h2>B{activeBand} was not scanned.</h2>
                <p>The receiver never selected this band during the 40-step mission. Belief stays at the prior because there is no HIT/MISS evidence yet.</p>
                <div className="explain-values">
                  <div><span>activity probability</span><b>{Number(spectrumState?.activity_probability || 0).toFixed(2)}</b></div>
                  <div><span>scan count</span><b>{spectrumState?.scan_count ?? 0}</b></div>
                </div>
              </>
            )}
          </article>
        </section>
        <section className="panel benchmark">
          <div className="panel-head"><span>06 / HELD-OUT BENCHMARK</span><span className="muted">same world · same horizon</span></div>
          <div className="benchmark-table">
            <div className="table-row header"><span>strategy</span><span>detections</span><span>rate</span></div>
            {benchmark && ['fixed', 'random', 'smart'].map((strategy) => (
              <div className={`table-row ${strategy}`} key={strategy}>
                <span>{strategy}</span>
                <span>{benchmark.summary[strategy].hits}</span>
                <span>{(benchmark.summary[strategy].detection_rate * 100).toFixed(1)}%</span>
              </div>
            ))}
          </div>
        </section>
      </>}
    </main>
  )
}

const root = document.getElementById('root')
if (root) {
  createRoot(root).render(<App />)
}
