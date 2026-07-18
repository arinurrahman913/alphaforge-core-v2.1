import { useMemo, useState } from 'react'

// columns: [{ key, label, render(row) => node, sortValue(row) => comparable }]
// rows: array of plain objects, each expected to have a `.ticker` field for search.
export default function DataTable({ columns, rows, onRowClick, searchPlaceholder = 'Cari ticker…' }) {
  const [search, setSearch] = useState('')
  const [sortKey, setSortKey] = useState(null)
  const [sortDir, setSortDir] = useState('asc')

  const filtered = useMemo(() => {
    if (!search.trim()) return rows
    const q = search.toUpperCase()
    return rows.filter((r) => String(r.ticker ?? '').toUpperCase().includes(q))
  }, [rows, search])

  const sorted = useMemo(() => {
    if (!sortKey) return filtered
    const col = columns.find((c) => c.key === sortKey)
    if (!col) return filtered
    const getVal = col.sortValue || ((r) => r[sortKey])
    const copy = [...filtered]
    copy.sort((a, b) => {
      const va = getVal(a)
      const vb = getVal(b)
      if (va === null || va === undefined) return 1
      if (vb === null || vb === undefined) return -1
      if (typeof va === 'string') return va.localeCompare(vb)
      return va - vb
    })
    if (sortDir === 'desc') copy.reverse()
    return copy
  }, [filtered, sortKey, sortDir, columns])

  function toggleSort(key) {
    if (sortKey !== key) {
      setSortKey(key)
      setSortDir('asc')
    } else if (sortDir === 'asc') {
      setSortDir('desc')
    } else {
      setSortKey(null)
    }
  }

  return (
    <>
      <div className="controls">
        <input
          className="search"
          placeholder={searchPlaceholder}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              {columns.map((c) => (
                <th key={c.key} onClick={() => toggleSort(c.key)}>
                  {c.label}
                  {sortKey === c.key && (
                    <span className="sort-arrow">{sortDir === 'asc' ? '▲' : '▼'}</span>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.length === 0 ? (
              <tr>
                <td className="empty" colSpan={columns.length}>
                  Tidak ada data
                </td>
              </tr>
            ) : (
              sorted.map((row, i) => (
                <tr key={row.ticker ?? i} onClick={() => onRowClick?.(row)}>
                  {columns.map((c) => (
                    <td key={c.key}>{c.render(row)}</td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </>
  )
}
