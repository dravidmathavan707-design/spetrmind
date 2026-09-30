import React, { useEffect, useMemo, useRef, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { Activity, BrainCircuit, Check, ChevronDown, CircleDot, History, Pause, Play, Radio, RotateCcw, ScanLine, Square } from 'lucide-react'
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
  const [inspectMode, setInspectMode] = useState('live')
  const [liveEvent, setLiveEvent] = useState(null)
  const [liveEvents, setLiveEvents] = useState([])
  const [liveConnected, setLiveConnected] = useState(false)
  const [runtimeStatus, setRuntimeStatus] = useState('connecting')
  const [islandExpanded, setIslandExpanded] = useState(false)
  const [scenarioMenuOpen, setScenarioMenuOpen] = useState(false)
  const [scenario, setScenario] = useState('stable')
  const [connectionMessage, setConnectionMessage] = useState('connecting to scanner')
  const socketRef = useRef(null)
  const scenarioPickerRef = useRef(null)
  const reconnectTimerRef = useRef(null)
  const reconnectingRef = useRef(false)

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
      setInspectMode('live')
    } catch (requestError) {
      setError(`${requestError.message} Start the backend with: uvicorn api.main:app --host 127.0.0.1 --port 8000`)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { runMission() }, [])

  useEffect(() => {
    function closeScenarioMenu(event) {
      if (!scenarioPickerRef.current?.contains(event.target)) {
        setScenarioMenuOpen(false)
      }
    }

    document.addEventListener('pointerdown', closeScenarioMenu)
    return () => document.removeEventListener('pointerdown', closeScenarioMenu)
  }, [])

  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
    let disposed = false

    function connect() {
      if (disposed || reconnectingRef.current) return
      reconnectingRef.current = true
      setConnectionMessage('connecting to scanner')
      const socket = new WebSocket(`${protocol}://${window.location.host}/api/realtime`)
      socketRef.current = socket

      socket.onopen = () => {
        reconnectingRef.current = false
        setLiveConnected(true)
        setConnectionMessage('scanner connected')
      }
      socket.onmessage = (event) => {
        const receivedEvent = JSON.parse(event.data)
        const nextEvent = {
          ...receivedEvent,
          process: receivedEvent.process && {
            ...receivedEvent.process,
            steps: receivedEvent.process.steps?.map((step) => ({
              ...step,
              status: step.key === 'model' && step.status === 'active' ? 'complete' : step.status,
            })),
          },
        }
        setLiveEvent(nextEvent)
        setRuntimeStatus(nextEvent.runtime_status || 'running')
        setScenario(nextEvent.scenario || 'stable')
        setLiveEvents((events) => [...events.slice(-199), nextEvent])
      }
      socket.onerror = () => {
        setLiveConnected(false)
        setConnectionMessage('backend unavailable, retrying')
      }
      socket.onclose = () => {
        reconnectingRef.current = false
        setLiveConnected(false)
        if (!disposed) {
          setConnectionMessage('backend unavailable, retrying')
          reconnectTimerRef.current = window.setTimeout(connect, 1000)
        }
      }
    }

    connect()

    return () => {
      disposed = true
      if (reconnectTimerRef.current) window.clearTimeout(reconnectTimerRef.current)
      if (socketRef.current && socketRef.current.readyState < WebSocket.CLOSING) {
        socketRef.current.close()
      }
      socketRef.current = null
    }
  }, [])

  const eventIndex = useMemo(() => {
    if (!mission) return -1
    if (inspectMode === 'live') return Math.max(0, mission.decisions.length - 1)
    if (inspectMode === 'timeline') return selected
    return lastIndexForBand(mission.decisions, focusedBand)
  }, [mission, selected, focusedBand, inspectMode])

  const missionDecision = eventIndex >= 0 ? mission?.decisions[eventIndex] : null
  const missionExplanation = eventIndex >= 0 ? mission?.explanations[eventIndex] : null
  const missionObservation = eventIndex >= 0 ? mission?.observations[eventIndex] : null
  const liveSelection = inspectMode === 'live' ? liveEvent : null
  const decision = liveSelection ? {
    band: liveSelection.band,
    dwell: liveSelection.dwell,
    activity_score: liveSelection.activity_score,
    prediction_score: liveSelection.prediction_score,
    periodicity_score: liveSelection.periodicity_score,
    uncertainty: liveSelection.uncertainty,
    information_gain: liveSelection.information_gain,
    drift_score: liveSelection.drift_score,
    drift: liveSelection.drift,
  } : missionDecision
  const explanation = liveSelection ? {
    selected_band: liveSelection.band,
    reason: 'Selected by the live cognitive scheduler using the factors shown below.',
    components: {
      activity_score: liveSelection.activity_score,
      prediction_score: liveSelection.prediction_score,
      periodicity_score: liveSelection.periodicity_score,
      uncertainty: liveSelection.uncertainty,
      information_gain: liveSelection.information_gain,
      drift_score: liveSelection.drift_score,
    },
  } : missionExplanation
  const observation = liveSelection ? liveSelection : missionObservation
  const selectedBandEvents = focusedBand == null ? [] : [
    ...(mission?.observations || []).filter((observation) => observation.band === focusedBand),
    ...liveEvents.filter((event) => event.band === focusedBand),
  ]
  const selectedBandHits = selectedBandEvents.filter((event) => event.detected).length
  const selectedBandRate = selectedBandEvents.length
    ? selectedBandHits / selectedBandEvents.length
    : null
  const showingBandResult = inspectMode === 'band' && focusedBand != null && selectedBandRate != null
  const metrics = showingBandResult
    ? { ...((liveEvent?.metrics || mission?.metrics) || {}), detection_rate: selectedBandRate, hits: selectedBandHits, misses: selectedBandEvents.length - selectedBandHits }
    : (liveSelection?.metrics || mission?.metrics)
  const activeBand = inspectMode === 'band' ? focusedBand : (decision?.band ?? focusedBand)
  const liveSpectrum = liveEvent?.spectrum || mission?.spectrum || {}
  const displayBand = activeBand
  const processSteps = liveEvent?.process?.steps || [
    { key: 'world', label: 'Advance RF world', status: 'waiting' },
    { key: 'score', label: 'Score candidate bands', status: 'waiting' },
    { key: 'tune', label: 'Tune receiver', status: 'waiting' },
    { key: 'measure', label: 'Measure selected frequency', status: 'waiting' },
    { key: 'model', label: 'Update learning model', status: 'waiting' },
  ]
  const spectrumBands = Object.entries(liveSpectrum)
  const spectrumState = displayBand != null
    ? liveSpectrum?.[displayBand] ?? liveSpectrum?.[String(displayBand)]
    : null

  function inspectBand(bandId) {
    setInspectMode('band')
    setFocusedBand(bandId)
    const last = lastIndexForBand(mission?.decisions || [], bandId)
    if (last >= 0) setSelected(last)
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ type: 'tune', band: bandId }))
    }
  }

  function sendCommand(type, payload = {}) {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ type, ...payload }))
    }
  }

  function changeScenario(nextScenario) {
    setScenario(nextScenario)
    setScenarioMenuOpen(false)
    setLiveEvents([])
    setLiveEvent(null)
    setInspectMode('live')
    sendCommand('scenario', { scenario: nextScenario })
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
        <button
          type="button"
          className={`live-island ${islandExpanded ? 'expanded' : ''} ${runtimeStatus}`}
          onClick={() => setIslandExpanded((expanded) => !expanded)}
          aria-expanded={islandExpanded}
          aria-label={`Live scanner ${runtimeStatus}; band ${liveEvent?.band ?? 'unavailable'}. Toggle details.`}
        >
          <span className="island-main">
            <span className="island-light" />
            <Activity size={14} />
            <b>{liveConnected ? runtimeStatus.toUpperCase() : 'CONNECTING'}</b>
            <strong>{liveEvent ? `B${liveEvent.band}` : '—'}</strong>
            <ChevronDown size={13} className="island-chevron" />
          </span>
          <span className="island-details" aria-hidden={!islandExpanded}>
            <span><small>SCENARIO</small><b>{scenario.replaceAll('_', ' ')}</b></span>
            <span><small>CYCLE</small><b>{liveEvent ? String(liveEvent.cycle).padStart(2, '0') : '—'}</b></span>
            <span><small>LAST SCAN</small><b>{liveEvent ? (liveEvent.detected ? 'HIT' : 'MISS') : '—'}</b></span>
          </span>
        </button>
        <div className="control-bar">
          <button type="button" className="control-button primary" onClick={() => sendCommand('start')} disabled={!liveConnected}><Play size={14} /> Start</button>
          <button type="button" className="control-button" onClick={() => sendCommand('pause')} disabled={!liveConnected}><Pause size={14} /> Pause</button>
          <button type="button" className="control-button" onClick={() => sendCommand('stop')} disabled={!liveConnected}><Square size={13} /> Stop</button>
          <button type="button" className="control-button" onClick={() => sendCommand('reset', { scenario })} disabled={!liveConnected}><RotateCcw size={14} /> Reset</button>
          <div
            className={`scenario-picker ${scenarioMenuOpen ? 'open' : ''}`}
            ref={scenarioPickerRef}
            onKeyDown={(event) => {
              if (event.key === 'Escape') {
                setScenarioMenuOpen(false)
                scenarioPickerRef.current?.querySelector('.scenario-trigger')?.focus()
              }
            }}
          >
            <button
              type="button"
              className="scenario-trigger"
              onClick={() => setScenarioMenuOpen((isOpen) => !isOpen)}
              disabled={!liveConnected}
              aria-haspopup="true"
              aria-expanded={scenarioMenuOpen}
              aria-label="Select RF scenario"
            >
              <Radio size={14} aria-hidden="true" />
              <span>{scenario.replaceAll('_', ' ')}</span>
              <ChevronDown size={13} className="scenario-chevron" aria-hidden="true" />
            </button>
            {scenarioMenuOpen && (
              <div className="scenario-menu" role="group" aria-label="RF scenarios">
                <small>SELECT SCENARIO</small>
                {[
                  ['stable', 'Stable emitter'],
                  ['bursty', 'Bursty signal'],
                  ['periodic', 'Periodic signal'],
                  ['frequency_agile', 'Frequency agile'],
                  ['multiple_emitters', 'Multiple emitters'],
                  ['weak', 'Weak emitter'],
                  ['noisy', 'Noisy environment'],
                  ['changing', 'Changing emitters'],
                ].map(([value, label]) => (
                  <button
                    type="button"
                    className={`scenario-option ${scenario === value ? 'selected' : ''}`}
                    key={value}
                    onClick={() => changeScenario(value)}
                    aria-pressed={scenario === value}
                  >
                    <span>{label}</span>
                    {scenario === value && <Check size={13} />}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </header>
      <section className="hero">
        <div>
          <p className="kicker">SPECTRAMIND / SYNTHETIC RF WORLD</p>
          <h1>Cognitive Spectrum<br /><em>Intelligence Console</em></h1>
          <p className="lede">Live receiver state, cognitive decisions, and held-out performance.</p>
        </div>
      </section>
      <section className="live-strip">
        <div className="live-label"><span className="live-dot" /> LIVE TELEMETRY <small>stateful scanner</small></div>
        <div className="live-reading"><span>current target</span><strong>{liveEvent ? `B${liveEvent.band}` : '—'}</strong></div>
        <div className="live-reading"><span>last result</span><strong className={liveEvent?.detected ? 'live-hit' : ''}>{liveEvent ? (liveEvent.detected ? 'HIT' : 'MISS') : '—'}</strong></div>
        <div className="live-reading"><span>scan clock</span><strong>{liveEvent ? `${String(Math.trunc(liveEvent.time)).padStart(2, '0')}s` : '—'}</strong></div>
        <div className="live-reading"><span>predicted activity</span><strong>{liveEvent ? `${(Number(liveEvent.prediction_score) * 100).toFixed(0)}%` : '—'}</strong></div>
      </section>
      <section className="process-panel">
        <div className="process-heading">
          <div><span className="section-index">01</span><strong>SCAN CYCLE</strong><small>frequency acquisition pipeline</small></div>
          <span className="cycle-count">{liveEvent ? `cycle ${String(liveEvent.cycle).padStart(2, '0')}` : 'standby'}</span>
        </div>
        <div className="process-rail">
          {processSteps.map((step, index) => (
            <div className={`process-step ${step.status}`} key={step.key}>
              <span className="process-marker">{step.status === 'complete' || step.status === 'active' ? <Check size={13} /> : index + 1}</span>
              <div><b>{step.label}</b><small>{step.status === 'active' ? 'processing now' : step.status}</small></div>
            </div>
          ))}
        </div>
      </section>
      {error ? <div className="loading error">{error}</div> : !mission ? <div className="loading">Initializing mission telemetry...</div> : <>
        <section className="grid">
          <article className="panel spectrum-panel">
            <div className="panel-head"><span>01 / SPECTRUM STATE</span><Activity size={17} /></div>
            <div className="spectrum-visual">
              <div className="power-label">SIGNAL POWER / LEARNED ACTIVITY</div>
              <div className="frequency-flow" aria-hidden="true" />
              <div className="bands">
              {spectrumBands.map(([band, state]) => {
                const bandId = Number(band)
                const power = Math.max(8, Math.min(100, (state.activity_probability || 0) * 100))
                return (
                  <button
                    type="button"
                    className={`band ${displayBand === bandId ? 'selected' : ''} ${state.activity_probability > 0.65 ? 'hot' : ''} ${liveSelection && displayBand === bandId && runtimeStatus === 'running' ? 'scanning' : ''}`}
                    key={band}
                    onClick={() => inspectBand(bandId)}
                      aria-pressed={displayBand === bandId}
                      title={`Band ${bandId}: ${(Number(state.activity_probability || 0) * 100).toFixed(0)}% learned activity, ${state.scan_count ?? 0} scans`}
                  >
                    <i style={{ height: `${power}%` }} />
                    {displayBand === bandId && <span className="tuning-cursor"><span /> RECEIVER</span>}
                    <span>B{band}</span>
                  </button>
                )
              })}
              </div>
              <div className="frequency-axis"><span>LOW FREQUENCY</span><span>{inspectMode === 'live' ? `LIVE RECEIVER: ${liveEvent ? `B${liveEvent.band}` : 'STANDBY'}` : `INSPECTING: B${displayBand}`}</span><span>HIGH FREQUENCY</span></div>
            </div>
            <div className="legend">
              <span><i className="dot hot-dot" /> learned activity</span>
              <span><i className="dot selected-dot" /> current target</span>
            </div>
          </article>
          <article className="panel decision-panel">
            <div className="panel-head"><span>02 / {inspectMode === 'live' ? 'NEXT DECISION' : inspectMode === 'band' ? 'BAND INSPECTION' : 'REPLAY DECISION'}</span><BrainCircuit size={17} /></div>
            {decision ? (
              <>
                <div className="target">
                  <small>SELECTED BAND</small>
                  <strong>B{decision.band}</strong>
                  <span>{inspectMode === 'band' ? 'band inspection' : (liveSelection ? `${Number(decision.dwell).toFixed(0)} ms dwell / live` : `${Number(decision.dwell).toFixed(0)} ms dwell / replay`)}</span>
                </div>
                <div className="readings">
                  {[
                    ['Future activity prediction', decision.prediction_score ?? decision.activity_score],
                    ['Activity', decision.activity_score],
                    ['Periodicity', decision.periodicity_score],
                    ['Uncertainty', decision.uncertainty],
                    ['Information gain', decision.information_gain],
                    ['Drift', decision.drift_score ?? (decision.drift ? 1 : 0)],
                  ].map(([label, value]) => (
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
            <div className="panel-head"><span>03 / {showingBandResult ? `BAND RESULT / B${focusedBand}` : (liveSelection ? 'LIVE RESULT' : 'MISSION RESULT')}</span><CircleDot size={17} /></div>
            <div className="metric-big">
              <strong>{((metrics?.detection_rate || 0) * 100).toFixed(1)}%</strong>
              <span>{showingBandResult ? `B${focusedBand} detection rate` : 'scan detection rate'}</span>
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
            <div className="panel-head">
              <span>04 / MISSION REPLAY</span>
              <div className="inspect-tabs" aria-label="Decision view">
                <button type="button" className={inspectMode === 'live' ? 'active' : ''} onClick={() => setInspectMode('live')}><Radio size={12} /> LIVE</button>
                <button type="button" className={inspectMode !== 'live' ? 'active' : ''} onClick={() => {
                  setSelected(Math.max(0, (mission?.decisions?.length || 1) - 1))
                  setFocusedBand(mission?.decisions?.at(-1)?.band ?? null)
                  setInspectMode('timeline')
                }}><History size={12} /> REPLAY</button>
              </div>
            </div>
            <div className="timeline">
              {mission.observations.map((item, index) => {
                const schedulerSelected = mission.decisions[index]?.band === item.band
                const repeatedBand = index > 0 && mission.observations[index - 1].band === item.band
                return (
                  <button
                    type="button"
                    className={`event ${index === eventIndex && inspectMode === 'timeline' ? 'active' : ''} ${repeatedBand ? 'repeated' : ''}`}
                    key={index}
                    onClick={() => inspectEvent(index)}
                    title={schedulerSelected ? `Smart scheduler selected band ${item.band} for this scan` : `Band ${item.band} scan`}
                  >
                    <span>{String(Math.trunc(item.time)).padStart(2, '0')}</span>
                    <b>B{item.band}</b>
                    <i className={item.detected ? 'hit' : 'miss'}>{item.detected ? 'HIT' : 'MISS'}</i>
                    <small>{schedulerSelected ? (repeatedBand ? 'SELECTED AGAIN' : 'SMART SELECTED') : 'SCAN'}</small>
                  </button>
                )
              })}
            </div>
          </article>
          <article className="panel explain-panel">
            <div className="panel-head"><span>05 / WHY THIS BAND?</span><span className="tag">AUDITABLE</span></div>
            {explanation ? (
              <>
                <h2>B{decision?.band ?? explanation.selected_band} was selected.</h2>
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
          <div className="panel-head"><span>06 / HELD-OUT BENCHMARK</span><span className="muted">unseen scenarios · rate is hits / scans</span></div>
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
  const appRoot = window.__spectramindRoot || createRoot(root)
  window.__spectramindRoot = appRoot
  appRoot.render(<App />)
}
