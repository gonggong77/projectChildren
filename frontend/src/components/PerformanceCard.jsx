import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useFavorites } from '../favorites'

const STATE_CLASS_NAMES = {
  공연예정: 'status-badge--upcoming',
  공연중: 'status-badge--ongoing',
  공연완료: 'status-badge--ended',
}

function formatDate(value) {
  if (!value) return null
  return value.replaceAll('-', '.')
}

export default function PerformanceCard({ performance }) {
  const location = useLocation()
  const [imageFailed, setImageFailed] = useState(false)
  const { isFavorite, toggleFavorite } = useFavorites()
  const favorite = isFavorite(performance.mt20id)
  const periodStart = formatDate(performance.prfpdfrom)
  const periodEnd = formatDate(performance.prfpdto)
  const period =
    periodStart && periodEnd
      ? `${periodStart} ~ ${periodEnd}`
      : periodStart || periodEnd || '기간 정보 없음'
  const state = performance.prfstate || '상태 미정'
  const stateClassName = STATE_CLASS_NAMES[state] || 'status-badge--unknown'

  return (
    <article className="poster-card">
      <button
        type="button"
        className={`favorite-button poster-card__favorite ${
          favorite ? 'is-favorite' : ''
        }`}
        aria-label={
          favorite
            ? `${performance.prfnm} 즐겨찾기 삭제`
            : `${performance.prfnm} 즐겨찾기 추가`
        }
        aria-pressed={favorite}
        onClick={() => toggleFavorite(performance.mt20id)}
      >
        <span aria-hidden="true">{favorite ? '♥' : '♡'}</span>
      </button>
      <Link
        className="poster-card__link"
        to={`/performances/${encodeURIComponent(performance.mt20id)}`}
        state={{ from: `${location.pathname}${location.search}` }}
        aria-label={`${performance.prfnm} 상세 보기`}
      >
        <div className="poster-card__media">
          {performance.poster && !imageFailed ? (
            <img
              className="poster-card__image"
              src={performance.poster}
              alt={`${performance.prfnm} 포스터`}
              loading="lazy"
              onError={() => setImageFailed(true)}
            />
          ) : (
            <div className="poster-card__placeholder" role="img" aria-label="포스터 없음">
              <span aria-hidden="true">🎭</span>
              <span>포스터 준비 중</span>
            </div>
          )}
        </div>
        <div className="poster-card__body">
          <span className={`status-badge ${stateClassName}`}>{state}</span>
          <h2 className="poster-card__title">{performance.prfnm}</h2>
          <dl className="poster-card__details">
            <div>
              <dt>기간</dt>
              <dd>{period}</dd>
            </div>
            <div>
              <dt>시설</dt>
              <dd>{performance.fcltynm || '시설 정보 없음'}</dd>
            </div>
            <div>
              <dt>지역</dt>
              <dd>{performance.area || '지역 정보 없음'}</dd>
            </div>
          </dl>
        </div>
      </Link>
    </article>
  )
}
