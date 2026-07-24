import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchPerformancesBatch } from '../api'
import EmptyState from '../components/EmptyState'
import ErrorState from '../components/ErrorState'
import PerformanceCard from '../components/PerformanceCard'
import { PosterSkeleton } from '../components/Skeleton'
import { useFavorites } from '../favorites'

const BATCH_SIZE = 100

function chunkIds(ids) {
  return Array.from(
    { length: Math.ceil(ids.length / BATCH_SIZE) },
    (_, index) => ids.slice(index * BATCH_SIZE, (index + 1) * BATCH_SIZE),
  )
}

export default function FavoritesPage() {
  const navigate = useNavigate()
  const { ids, removeFavorites } = useFavorites()
  const [items, setItems] = useState([])
  const [isLoading, setIsLoading] = useState(ids.length > 0)
  const [error, setError] = useState(null)
  const [retryCount, setRetryCount] = useState(0)
  const [toast, setToast] = useState('')
  const idsKey = ids.join('\u0000')

  useEffect(() => {
    const controller = new AbortController()

    async function loadFavorites() {
      if (ids.length === 0) {
        setItems([])
        setError(null)
        setIsLoading(false)
        return
      }

      setIsLoading(true)
      setError(null)
      setItems([])

      try {
        const results = await Promise.all(
          chunkIds(ids).map((chunk) =>
            fetchPerformancesBatch(chunk, { signal: controller.signal }),
          ),
        )
        const fetchedItems = results.flatMap((result) => result.items)
        const itemById = new Map(
          fetchedItems.map((performance) => [performance.mt20id, performance]),
        )
        const missingIds = ids.filter((id) => !itemById.has(id))

        setItems(ids.flatMap((id) => (itemById.has(id) ? [itemById.get(id)] : [])))
        if (missingIds.length > 0) {
          removeFavorites(missingIds)
          setToast(
            `더 이상 제공되지 않는 공연 ${missingIds.length}개를 즐겨찾기에서 정리했어요.`,
          )
        }
      } catch (requestError) {
        if (requestError.name !== 'AbortError') {
          setError(requestError)
        }
      } finally {
        if (!controller.signal.aborted) {
          setIsLoading(false)
        }
      }
    }

    loadFavorites()
    return () => controller.abort()
  }, [idsKey, retryCount])

  const visibleItems = useMemo(() => {
    const activeIds = new Set(ids)
    return items.filter((item) => activeIds.has(item.mt20id))
  }, [ids, items])

  return (
    <section className="page favorites-page">
      <div className="favorites-page__heading">
        <h1 className="page__title">즐겨찾기</h1>
        <p className="page__lead">저장한 공연의 최신 정보를 확인하세요.</p>
        <p className="favorites-page__notice">
          즐겨찾기는 이 브라우저에만 저장되며 다른 브라우저나 기기와 동기화되지
          않습니다.
        </p>
      </div>

      {toast ? (
        <div className="toast" role="status" aria-live="polite">
          <span>{toast}</span>
          <button type="button" onClick={() => setToast('')} aria-label="알림 닫기">
            ×
          </button>
        </div>
      ) : null}

      {isLoading && items.length === 0 ? <PosterSkeleton count={4} /> : null}

      {!isLoading && error ? (
        <ErrorState
          message={error.message}
          onRetry={() => setRetryCount((count) => count + 1)}
        />
      ) : null}

      {!isLoading && !error && visibleItems.length === 0 ? (
        <EmptyState
          title="저장한 공연이 없어요"
          description="관심 있는 공연을 하트 버튼으로 저장해보세요."
          actionLabel="공연 둘러보기"
          onAction={() => navigate('/')}
        />
      ) : null}

      {visibleItems.length > 0 ? (
        <>
          <p className="favorites-page__total">
            저장한 공연 <strong>{visibleItems.length}개</strong>
          </p>
          <div className="poster-grid">
            {visibleItems.map((performance) => (
              <PerformanceCard
                key={performance.mt20id}
                performance={performance}
              />
            ))}
          </div>
        </>
      ) : null}
    </section>
  )
}
