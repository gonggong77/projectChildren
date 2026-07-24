/** 포스터 카드 스켈레톤 (비율 3:4 고정 — CLS 방지) */
export function PosterSkeleton({ count = 8 }) {
  return (
    <div className="poster-grid" aria-busy="true" aria-label="불러오는 중">
      {Array.from({ length: count }, (_, index) => (
        <div key={index} className="poster-card skeleton-card">
          <div className="poster-card__media skeleton-block" />
          <div className="poster-card__body">
            <div className="skeleton-line skeleton-line--short" />
            <div className="skeleton-line" />
            <div className="skeleton-line skeleton-line--medium" />
          </div>
        </div>
      ))}
    </div>
  )
}

/** 상세/일반 콘텐츠용 블록 스켈레톤 */
export function ContentSkeleton() {
  return (
    <div className="content-skeleton" aria-busy="true" aria-label="불러오는 중">
      <div className="skeleton-block content-skeleton__hero" />
      <div className="skeleton-line" />
      <div className="skeleton-line skeleton-line--medium" />
      <div className="skeleton-line skeleton-line--short" />
    </div>
  )
}
