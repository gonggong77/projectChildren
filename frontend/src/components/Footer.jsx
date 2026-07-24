import { useEffect, useState } from 'react'
import { fetchHealth } from '../api'

function formatIngestedAt(value) {
  if (!value) return null
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

export default function Footer() {
  const [lastIngestedAt, setLastIngestedAt] = useState(null)

  useEffect(() => {
    let cancelled = false
    fetchHealth()
      .then((data) => {
        if (!cancelled) setLastIngestedAt(data.last_ingested_at ?? null)
      })
      .catch(() => {
        if (!cancelled) setLastIngestedAt(null)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const formatted = formatIngestedAt(lastIngestedAt)

  return (
    <footer className="site-footer">
      <div className="site-footer__inner">
        <p>
          공연 정보: 공연예술통합전산망(KOPIS) / 놀이시설 정보: 행정안전부
        </p>
        <p className="site-footer__meta">
          {formatted
            ? `최종 갱신일: ${formatted}`
            : '최종 갱신일: 확인 중…'}
        </p>
      </div>
    </footer>
  )
}
