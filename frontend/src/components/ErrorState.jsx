/**
 * 서버 오류·재시도 공통 UI
 * @param {{ message?: string, onRetry?: () => void }} props
 */
export default function ErrorState({
  message = '잠시 후 다시 시도해주세요',
  onRetry,
}) {
  return (
    <div className="state-panel error-state" role="alert">
      <p className="state-panel__title">{message}</p>
      {onRetry ? (
        <button type="button" className="btn btn--primary" onClick={onRetry}>
          다시 시도
        </button>
      ) : null}
    </div>
  )
}
