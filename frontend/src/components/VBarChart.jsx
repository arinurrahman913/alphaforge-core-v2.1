// Vertical pillar chart dengan bubble cap + gradien emas→cyan per peringkat.
// data: [{ label, count }] — diasumsikan sudah terurut (peringkat 0 = tertinggi).
const lerp = (a, b, t) => Math.round(a + (b - a) * t)
// gold rgb(232,184,75) -> cyan rgb(79,209,224)
const ramp = (t) => `rgb(${lerp(232, 79, t)},${lerp(184, 209, t)},${lerp(75, 224, t)})`
const rampHi = (t) => `rgb(${lerp(255, 150, t)},${lerp(226, 236, t)},${lerp(150, 245, t)})`

const MAX_BAR_PX = 150

export default function VBarChart({ title, data }) {
  const max = Math.max(...data.map((d) => d.count), 1)
  const n = data.length

  return (
    <div className="chart-card">
      <div className="chart-title">{title}</div>
      <div className="vbars">
        {data.map((d, i) => {
          const t = n > 1 ? i / (n - 1) : 0
          const c = ramp(t)
          const chi = rampHi(t)
          const h = (d.count / max) * MAX_BAR_PX
          return (
            <div className="vbar" key={d.label} title={`${d.full || d.label}: ${d.count}`}>
              <div className="vbar-area">
                <div className="vbar-bub" style={{ background: `radial-gradient(circle at 35% 30%, ${chi}, ${c})` }}>
                  {d.count}
                </div>
                <div
                  className="vbar-pil"
                  style={{ height: `${h}px`, background: `linear-gradient(180deg, ${chi}, ${c})`, '--vi': i }}
                />
              </div>
              <div className="vbar-lab">{d.label}</div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
