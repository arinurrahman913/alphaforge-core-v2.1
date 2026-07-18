import { useState } from 'react'
import Sidebar from './components/Sidebar'
import TickerModal from './components/TickerModal'
import Layer1View from './views/Layer1View'
import ScreeningView from './views/ScreeningView'
import EvidenceView from './views/EvidenceView'
import KnowledgeView from './views/KnowledgeView'
import PeerView from './views/PeerView'
import ConfidenceView from './views/ConfidenceView'
import RiskView from './views/RiskView'
import ReasoningView from './views/ReasoningView'
import AggregatorView from './views/AggregatorView'
import HistoricalView from './views/HistoricalView'

const TITLES = {
  layer1: ['Layer 1 — Market Context', '12 komponen makro, membaca data/layer1_context.json'],
  screening: ['Screening', 'Filter kandidat dari universe mentah — data/screening.json'],
  evidence: ['Evidence', 'Fakta terverifikasi per ticker (price, fundamental, ownership, news, SEC filings)'],
  knowledge: ['Knowledge', '7-section profile per ticker, hasil sintesis Evidence'],
  peer: ['Peer Comparison', 'Posisi percentile terhadap peer group'],
  confidence: ['Confidence Scoring', 'Skor kualitas data 0-100 per 6 kategori'],
  risk: ['Risk / Red Flags', 'Deteksi anomali governance, financial, momentum, valuation'],
  reasoning: ['Reasoning Pipeline', '3 lensa independen: Quality, Speculative, Multibagger'],
  aggregator: ['Aggregator', 'Rekomendasi final gabungan Confidence + Risk + Reasoning'],
  historical: ['Historical Tracking', 'Pelacakan hasil rekomendasi vs actual return'],
}

const VIEWS = {
  layer1: Layer1View,
  screening: ScreeningView,
  evidence: EvidenceView,
  knowledge: KnowledgeView,
  peer: PeerView,
  confidence: ConfidenceView,
  risk: RiskView,
  reasoning: ReasoningView,
  aggregator: AggregatorView,
  historical: HistoricalView,
}

export default function App() {
  const [activeView, setActiveView] = useState('layer1')
  const [modalTicker, setModalTicker] = useState(null)

  const ActiveView = VIEWS[activeView]
  const [title, desc] = TITLES[activeView]

  return (
    <div className="app">
      <Sidebar activeView={activeView} onSelect={setActiveView} />

      <div className="main">
        <div className="topbar">
          <div>
            <h1>{title}</h1>
            <p>{desc}</p>
          </div>
        </div>

        <div className="content">
          <ActiveView onSelectTicker={setModalTicker} />
        </div>
      </div>

      {modalTicker && <TickerModal ticker={modalTicker} onClose={() => setModalTicker(null)} />}
    </div>
  )
}
