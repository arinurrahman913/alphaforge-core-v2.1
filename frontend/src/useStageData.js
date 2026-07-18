import { useEffect, useState } from 'react'

// Fetches once per mount via the given api function, returns {data, error}.
export function useStageData(fetcher, deps = []) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    setData(null)
    setError(null)
    fetcher()
      .then((d) => {
        if (!cancelled) setData(d)
      })
      .catch((e) => {
        if (!cancelled) setError(String(e))
      })
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  return { data, error }
}

export function generatedMeta(data) {
  if (!data?.generated_at) return ''
  return `generated ${data.generated_at.slice(0, 19).replace('T', ' ')}Z`
}
