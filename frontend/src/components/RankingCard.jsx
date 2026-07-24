import { Link, useLocation } from 'react-router-dom'
import { useState } from 'react'

export default function RankingCard({ ranking }) {
  const location = useLocation()
  const [posterFailed, setPosterFailed] = useState(false)
  const from = `${location.pathname}${location.search}`
  const hasDetailLink = Boolean(ranking.mt20id)

  const body = (
    <>
      <div className="ranking-card__media">
        <span className="ranking-card__rank" aria-hidden="true">
          {ranking.rnum}
        </span>
        {ranking.poster && !posterFailed ? (
          <img
            src={ranking.poster}
            alt=""
            loading="lazy"
            onError={() => setPosterFailed(true)}
          />
        ) : (
          <div className="poster-placeholder" aria-hidden="true">
            No Image
          </div>
        )}
      </div>
      <div className="ranking-card__body">
        <h3 className="ranking-card__title">{ranking.prfnm || '제목 없음'}</h3>
        {ranking.prfpd ? (
          <p className="ranking-card__meta">{ranking.prfpd}</p>
        ) : null}
        {ranking.prfplcnm || ranking.area ? (
          <p className="ranking-card__meta">
            {[ranking.prfplcnm, ranking.area].filter(Boolean).join(' · ')}
          </p>
        ) : null}
      </div>
    </>
  )

  if (!hasDetailLink) {
    return (
      <article className="ranking-card ranking-card--static">{body}</article>
    )
  }

  return (
    <Link
      to={`/performances/${encodeURIComponent(ranking.mt20id)}`}
      state={{ from }}
      className="ranking-card"
    >
      {body}
    </Link>
  )
}
