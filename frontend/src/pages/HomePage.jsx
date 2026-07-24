import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { fetchPerformances, fetchRankings, fetchRegions } from '../api'
import EmptyState from '../components/EmptyState'
import ErrorState from '../components/ErrorState'
import PerformanceCard from '../components/PerformanceCard'
import RankingCard from '../components/RankingCard'
import { PosterSkeleton } from '../components/Skeleton'
import { SHCATE_OPTIONS, isValidShcate } from '../constants/shcate'

const PAGE_SIZE = 20
const RANKING_LIMIT = 10

function parsePage(value) {
  const parsed = Number.parseInt(value ?? '1', 10)
  return Number.isInteger(parsed) && parsed > 0 ? parsed : 1
}

export default function HomePage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const query = searchParams.get('q')?.trim() ?? ''
  const sido = /^\d{2}$/.test(searchParams.get('sido') ?? '')
    ? searchParams.get('sido')
    : ''
  const gugun =
    sido && /^\d{4}$/.test(searchParams.get('gugun') ?? '')
      ? searchParams.get('gugun')
      : ''
  const prfstate = ['공연예정', '공연중'].includes(searchParams.get('prfstate'))
    ? searchParams.get('prfstate')
    : ''
  const shcate = isValidShcate(searchParams.get('shcate') ?? '')
    ? searchParams.get('shcate')
    : ''
  const sort = searchParams.get('sort') === 'name' ? 'name' : 'soon'
  const page = parsePage(searchParams.get('page'))

  const [searchInput, setSearchInput] = useState(query)
  const [regions, setRegions] = useState([])
  const [isRegionsLoading, setIsRegionsLoading] = useState(true)
  const [regionsError, setRegionsError] = useState(null)
  const [rankings, setRankings] = useState([])
  const [isRankingsLoading, setIsRankingsLoading] = useState(true)
  const [rankingsError, setRankingsError] = useState(null)
  const [rankingsRetryCount, setRankingsRetryCount] = useState(0)
  const [items, setItems] = useState([])
  const [total, setTotal] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)
  const [retryCount, setRetryCount] = useState(0)

  const selectedRegion = regions.find((region) => region.code === sido)
  const guguns = selectedRegion?.guguns ?? []

  useEffect(() => {
    setSearchInput(query)
  }, [query])

  useEffect(() => {
    const controller = new AbortController()

    async function loadRegions() {
      setIsRegionsLoading(true)
      setRegionsError(null)

      try {
        const result = await fetchRegions({ signal: controller.signal })
        setRegions(result.items)
      } catch (requestError) {
        if (requestError.name !== 'AbortError') {
          setRegionsError(requestError)
        }
      } finally {
        if (!controller.signal.aborted) {
          setIsRegionsLoading(false)
        }
      }
    }

    loadRegions()
    return () => controller.abort()
  }, [])

  useEffect(() => {
    const controller = new AbortController()

    async function loadRankings() {
      setIsRankingsLoading(true)
      setRankingsError(null)

      try {
        const result = await fetchRankings(
          { limit: RANKING_LIMIT },
          { signal: controller.signal },
        )
        setRankings(result.items)
      } catch (requestError) {
        if (requestError.name !== 'AbortError') {
          setRankingsError(requestError)
          setRankings([])
        }
      } finally {
        if (!controller.signal.aborted) {
          setIsRankingsLoading(false)
        }
      }
    }

    loadRankings()
    return () => controller.abort()
  }, [rankingsRetryCount])

  useEffect(() => {
    const controller = new AbortController()

    async function loadPerformances() {
      setIsLoading(true)
      setError(null)
      if (page === 1) {
        setItems([])
        setTotal(0)
      }

      try {
        const results = await Promise.all(
          Array.from({ length: page }, (_, index) =>
            fetchPerformances(
              {
                q: query,
                sido,
                gugun,
                prfstate,
                shcate,
                sort,
                page: index + 1,
                size: PAGE_SIZE,
              },
              { signal: controller.signal },
            ),
          ),
        )
        setItems(results.flatMap((result) => result.items))
        setTotal(results[0]?.total ?? 0)
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

    loadPerformances()
    return () => controller.abort()
  }, [gugun, page, prfstate, query, retryCount, shcate, sido, sort])

  function updateUrl(changes) {
    const nextParams = new URLSearchParams(searchParams)

    Object.entries(changes).forEach(([key, value]) => {
      const isDefault =
        value === '' ||
        value === null ||
        value === undefined ||
        (key === 'page' && value === 1) ||
        (key === 'sort' && value === 'soon')

      if (isDefault) {
        nextParams.delete(key)
      } else {
        nextParams.set(key, String(value))
      }
    })

    setSearchParams(nextParams)
  }

  function resetList(changes) {
    setItems([])
    setTotal(0)
    updateUrl({ ...changes, page: 1 })
  }

  function handleSearch(event) {
    event.preventDefault()
    const nextQuery = searchInput.trim()
    if (nextQuery === query && page === 1) {
      setRetryCount((count) => count + 1)
      return
    }
    resetList({ q: nextQuery })
  }

  function handleSortChange(event) {
    resetList({ sort: event.target.value })
  }

  function handleSidoChange(event) {
    resetList({ sido: event.target.value, gugun: '' })
  }

  function handleGugunChange(event) {
    resetList({ gugun: event.target.value })
  }

  function handleStateChange(event) {
    resetList({ prfstate: event.target.value })
  }

  function handleShcateChange(event) {
    resetList({ shcate: event.target.value })
  }

  function handleReset() {
    setSearchInput('')
    resetList({
      q: '',
      sido: '',
      gugun: '',
      prfstate: '',
      shcate: '',
      sort: 'soon',
    })
  }

  const isInitialLoading = isLoading && items.length === 0
  const hasMore = items.length < total
  const rankingPeriod =
    rankings[0]?.stdate && rankings[0]?.eddate
      ? `${rankings[0].stdate} ~ ${rankings[0].eddate}`
      : null

  return (
    <section className="page performance-list-page">
      <section className="home-hero" aria-labelledby="home-title">
        <div className="home-hero__copy">
          <p className="home-hero__eyebrow">KIDSSTAGE · FAMILY DAY OUT</p>
          <h1 id="home-title" className="home-hero__title">
            아이와 만드는
            <span>반짝이는 하루</span>
          </h1>
          <p className="home-hero__lead">
            재미있는 공연부터 근처 놀이터까지,
            <br />
            우리 가족의 특별한 외출을 한 번에 찾아보세요.
          </p>
          <a className="btn home-hero__cta" href="#performance-search">
            공연 찾으러 가기 <span aria-hidden="true">→</span>
          </a>
        </div>
        <div className="home-hero__scene" aria-hidden="true">
          <span className="home-hero__star home-hero__star--one">★</span>
          <span className="home-hero__star home-hero__star--two">★</span>
          <span className="home-hero__star home-hero__star--three">★</span>
          <div className="home-mascot home-mascot--rabbit">🐰</div>
          <div className="home-mascot home-mascot--bear">🐻</div>
          <div className="home-mascot home-mascot--chick">🐥</div>
          <div className="home-hero__stage" />
        </div>
      </section>

      <section className="ranking-section" aria-labelledby="ranking-heading">
        <div className="ranking-section__heading">
          <div>
            <p className="section-kicker">이번 주 인기 친구들</p>
            <h2 id="ranking-heading" className="ranking-section__title">
              지금 가장 사랑받는 공연
            </h2>
          </div>
          {rankingPeriod ? (
            <p className="ranking-section__period">기준 {rankingPeriod}</p>
          ) : null}
        </div>

        {isRankingsLoading ? <PosterSkeleton count={5} /> : null}

        {!isRankingsLoading && rankingsError ? (
          <ErrorState
            message={rankingsError.message}
            onRetry={() => setRankingsRetryCount((count) => count + 1)}
          />
        ) : null}

        {!isRankingsLoading && !rankingsError && rankings.length === 0 ? (
          <EmptyState
            title="인기 공연 정보가 없어요"
            description="데이터 적재 후 다시 확인해주세요."
          />
        ) : null}

        {!isRankingsLoading && !rankingsError && rankings.length > 0 ? (
          <div className="ranking-grid">
            {rankings.map((ranking) => (
              <RankingCard
                key={`${ranking.rnum}-${ranking.mt20id ?? ranking.prfnm}`}
                ranking={ranking}
              />
            ))}
          </div>
        ) : null}
      </section>

      <section className="catalog-section" aria-labelledby="catalog-heading">
        <div className="catalog-section__heading">
          <p className="section-kicker">어디로 떠나볼까요?</p>
          <h2 id="catalog-heading">우리 가족 공연 찾기</h2>
          <span aria-hidden="true">★</span>
        </div>

        <form className="search-form" role="search" onSubmit={handleSearch}>
        <label className="visually-hidden" htmlFor="performance-search">
          공연명 검색
        </label>
        <input
          id="performance-search"
          className="search-form__input"
          type="search"
          value={searchInput}
          onChange={(event) => setSearchInput(event.target.value)}
          placeholder="공연명을 검색하세요"
          maxLength={100}
        />
        <button type="submit" className="btn btn--primary">
          검색
        </button>
        </form>

        <div className="region-filters" aria-label="목록 필터">
        <label className="filter-control">
          <span>시도</span>
          <select
            value={sido}
            disabled={isRegionsLoading || Boolean(regionsError)}
            onChange={handleSidoChange}
          >
            <option value="">
              {isRegionsLoading ? '지역 불러오는 중…' : '전국'}
            </option>
            {regions.map((region) => (
              <option key={region.code} value={region.code}>
                {region.name}
              </option>
            ))}
          </select>
        </label>

        <label className="filter-control">
          <span>구군</span>
          <select
            value={gugun}
            disabled={!sido || isRegionsLoading || Boolean(regionsError)}
            onChange={handleGugunChange}
          >
            <option value="">{sido ? '전체 구군' : '시도를 먼저 선택하세요'}</option>
            {guguns.map((regionGugun) => (
              <option key={regionGugun.code} value={regionGugun.code}>
                {regionGugun.name}
              </option>
            ))}
          </select>
        </label>

        <label className="filter-control">
          <span>공연상태</span>
          <select value={prfstate} onChange={handleStateChange}>
            <option value="">전체</option>
            <option value="공연예정">공연예정</option>
            <option value="공연중">공연중</option>
          </select>
        </label>

        <label className="filter-control">
          <span>장르</span>
          <select value={shcate} onChange={handleShcateChange}>
            <option value="">전체</option>
            {SHCATE_OPTIONS.map((option) => (
              <option key={option.code} value={option.code}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        {regionsError ? (
          <p className="region-filters__error" role="alert">
            지역 목록을 불러오지 못했어요. 새로고침 후 다시 시도해주세요.
          </p>
        ) : null}
        </div>

        <div className="list-toolbar">
        <p className="list-toolbar__total" aria-live="polite">
          총 <strong>{total.toLocaleString()}</strong>개의 공연
        </p>
        <label className="sort-control">
          <span className="visually-hidden">정렬 기준</span>
          <select value={sort} onChange={handleSortChange}>
            <option value="soon">임박순</option>
            <option value="name">공연명순</option>
          </select>
        </label>
        </div>

        {isInitialLoading ? <PosterSkeleton count={8} /> : null}

        {!isInitialLoading && error && items.length === 0 ? (
        <ErrorState
          message={error.message}
          onRetry={() => setRetryCount((count) => count + 1)}
        />
        ) : null}

        {!isInitialLoading && !error && items.length === 0 ? (
        <EmptyState
          title="조건에 맞는 공연이 없어요"
          description="검색어를 바꾸거나 조건을 초기화해보세요."
          actionLabel="필터 초기화"
          onAction={handleReset}
        />
        ) : null}

        {items.length > 0 ? (
        <>
          <div className="poster-grid">
            {items.map((performance) => (
              <PerformanceCard
                key={performance.mt20id}
                performance={performance}
              />
            ))}
          </div>

          {error ? (
            <div className="load-more-state">
              <ErrorState
                message={error.message}
                onRetry={() => setRetryCount((count) => count + 1)}
              />
            </div>
          ) : null}

          {hasMore && !error ? (
            <div className="load-more">
              <button
                type="button"
                className="btn btn--secondary load-more__button"
                disabled={isLoading}
                onClick={() => updateUrl({ page: page + 1 })}
              >
                {isLoading ? '불러오는 중…' : '더 보기'}
              </button>
            </div>
          ) : null}
        </>
        ) : null}
      </section>
    </section>
  )
}
