/**
 * 빈 결과 공통 UI
 * @param {{ title: string, description?: string, actionLabel?: string, onAction?: () => void }} props
 */
export default function EmptyState({
  title,
  description,
  actionLabel,
  onAction,
}) {
  return (
    <div className="state-panel empty-state" role="status">
      <p className="state-panel__title">{title}</p>
      {description ? (
        <p className="state-panel__desc">{description}</p>
      ) : null}
      {actionLabel && onAction ? (
        <button type="button" className="btn btn--secondary" onClick={onAction}>
          {actionLabel}
        </button>
      ) : null}
    </div>
  )
}
