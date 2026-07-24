import { useEffect, useState } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'
import { fetchNearbyPlaygrounds, fetchPerformanceDetail } from '../api'
import ErrorState from '../components/ErrorState'
import PlaygroundAccordion from '../components/PlaygroundAccordion'
import { ContentSkeleton } from '../components/Skeleton'
import VenueMap from '../components/VenueMap'
import { useFavorites } from '../favorites'

const STATE_CLASS_NAMES = {
  공연예정: 'status-badge--upcoming',
  공연중: 'status-badge--ongoing',
  공연완료: 'status-badge--ended',
}

const CONVENIENCES = [
  ['parkinglot', '🅿️', '주차'],
  ['suyu', '🍼', '수유실'],
  ['nolibang', '🧸', '놀이방'],
  ['restaurant', '🍽️', '식당'],
  ['cafe', '☕', '카페'],
  ['store', '🛍️', '매점'],
]

const ACCESSIBILITIES = [
  ['elevbarrier', '엘리베이터'],
  ['parkbarrier', '장애인 주차장'],
  ['restbarrier', '장애인 화장실'],
  ['runwbarrier', '경사로'],
]

function formatDate(value) {
  return value ? value.replaceAll('-', '.') : null
}

function isAvailable(value) {
  if (!value) return false
  return ['Y', '예', '있음', '가능'].includes(value.trim())
}

function DetailPoster({ performance }) {
  const [imageFailed, setImageFailed] = useState(false)

  if (!performance.poster || imageFailed) {
    return (
      <div className="detail-hero__poster-placeholder" role="img" aria-label="포스터 없음">
        <span aria-hidden="true">🎭</span>
        <span>포스터 준비 중</span>
      </div>
    )
  }

  return (
    <img
      className="detail-hero__poster"
      src={performance.poster}
      alt={`${performance.prfnm} 포스터`}
      onError={() => setImageFailed(true)}
    />
  )
}

function IntroImage({ image, performanceName }) {
  const [failed, setFailed] = useState(false)
  if (failed) return null

  return (
    <img
      src={image.styurl}
      alt={`${performanceName} 소개 이미지`}
      loading="lazy"
      onError={() => setFailed(true)}
    />
  )
}

export default function PerformanceDetailPage() {
  const { mt20id } = useParams()
  const location = useLocation()
  const { isFavorite, toggleFavorite } = useFavorites()
  const [performance, setPerformance] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)
  const [retryCount, setRetryCount] = useState(0)
  const [isStoryExpanded, setIsStoryExpanded] = useState(false)
  const [playgrounds, setPlaygrounds] = useState([])
  const [playgroundsStatus, setPlaygroundsStatus] = useState('idle')
  const [playgroundsRetryCount, setPlaygroundsRetryCount] = useState(0)
  const [selectedPlaygroundRadius, setSelectedPlaygroundRadius] = useState(1000)
  const [playgroundRadius, setPlaygroundRadius] = useState(1000)
  const [allowAutomaticRadiusExpansion, setAllowAutomaticRadiusExpansion] =
    useState(true)
  const [wasRadiusAutomaticallyExpanded, setWasRadiusAutomaticallyExpanded] =
    useState(false)
  const [playgroundFallbackUsed, setPlaygroundFallbackUsed] = useState(false)
  const [selectedPlaygroundId, setSelectedPlaygroundId] = useState(null)

  useEffect(() => {
    const controller = new AbortController()

    async function loadPerformance() {
      setIsLoading(true)
      setError(null)
      setPerformance(null)

      try {
        const result = await fetchPerformanceDetail(mt20id, {
          signal: controller.signal,
        })
        setPerformance(result)
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

    loadPerformance()
    return () => controller.abort()
  }, [mt20id, retryCount])

  useEffect(() => {
    const lat = performance?.venue?.la
    const lng = performance?.venue?.lo

    if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
      setPlaygrounds([])
      setPlaygroundsStatus('idle')
      setSelectedPlaygroundRadius(1000)
      setPlaygroundRadius(1000)
      setAllowAutomaticRadiusExpansion(true)
      setWasRadiusAutomaticallyExpanded(false)
      setPlaygroundFallbackUsed(false)
      setSelectedPlaygroundId(null)
      return undefined
    }

    const controller = new AbortController()

    async function loadPlaygrounds() {
      setPlaygroundsStatus('loading')
      setPlaygrounds([])
      setPlaygroundRadius(selectedPlaygroundRadius)
      setWasRadiusAutomaticallyExpanded(false)
      setPlaygroundFallbackUsed(false)
      setSelectedPlaygroundId(null)

      try {
        let radius = selectedPlaygroundRadius
        let result = await fetchNearbyPlaygrounds(
          { lat, lng, radius, limit: 20 },
          { signal: controller.signal },
        )
        if (
          result.total === 0 &&
          radius === 1000 &&
          allowAutomaticRadiusExpansion
        ) {
          radius = 3000
          result = await fetchNearbyPlaygrounds(
            { lat, lng, radius, limit: 20 },
            { signal: controller.signal },
          )
          setWasRadiusAutomaticallyExpanded(true)
        }
        setPlaygrounds(result.items)
        setPlaygroundRadius(radius)
        setPlaygroundFallbackUsed(result.fallback_used)
        setPlaygroundsStatus('success')
      } catch (requestError) {
        if (requestError.name !== 'AbortError') {
          setPlaygroundsStatus('error')
        }
      }
    }

    loadPlaygrounds()
    return () => controller.abort()
  }, [
    allowAutomaticRadiusExpansion,
    performance?.venue?.la,
    performance?.venue?.lo,
    playgroundsRetryCount,
    selectedPlaygroundRadius,
  ])

  function changePlaygroundRadius(radius) {
    setAllowAutomaticRadiusExpansion(false)
    setWasRadiusAutomaticallyExpanded(false)
    setSelectedPlaygroundRadius(radius)
    setPlaygroundRadius(radius)
    setPlaygroundsRetryCount((count) => count + 1)
  }

  function selectPlaygroundFromMap(playgroundId) {
    setSelectedPlaygroundId(playgroundId)
    window.requestAnimationFrame(() => {
      const listItem = document.getElementById(`playground-${playgroundId}`)
      const reduceMotion = window.matchMedia(
        '(prefers-reduced-motion: reduce)',
      ).matches
      listItem?.scrollIntoView({
        behavior: reduceMotion ? 'auto' : 'smooth',
        block: 'center',
      })
      listItem?.querySelector('button')?.focus({ preventScroll: true })
    })
  }

  function showPlaygroundOnMap(playgroundId) {
    setSelectedPlaygroundId(playgroundId)
    window.requestAnimationFrame(() => {
      const map = document.getElementById('venue-playground-map')
      const reduceMotion = window.matchMedia(
        '(prefers-reduced-motion: reduce)',
      ).matches
      map?.scrollIntoView({
        behavior: reduceMotion ? 'auto' : 'smooth',
        block: 'center',
      })
    })
  }

  const backTo =
    typeof location.state?.from === 'string' ? location.state.from : '/'

  if (isLoading && !performance) {
    return (
      <section className="page performance-detail-page">
        <ContentSkeleton />
      </section>
    )
  }

  if (error && !performance) {
    return (
      <section className="page performance-detail-page">
        <ErrorState
          message={
            error.status === 404
              ? '공연 정보를 찾을 수 없습니다.'
              : error.message
          }
          onRetry={
            error.status === 404
              ? undefined
              : () => setRetryCount((count) => count + 1)
          }
        />
        <Link className="detail-back-link" to={backTo}>
          ← 공연 목록으로
        </Link>
      </section>
    )
  }

  if (!performance) return null

  const state = performance.prfstate || '상태 미정'
  const stateClassName = STATE_CLASS_NAMES[state] || 'status-badge--unknown'
  const fromDate = formatDate(performance.prfpdfrom)
  const toDate = formatDate(performance.prfpdto)
  const period =
    fromDate && toDate
      ? `${fromDate} ~ ${toDate}`
      : fromDate || toDate || '정보 없음'
  const venue = performance.venue
  const conveniences = CONVENIENCES.filter(([key]) =>
    isAvailable(venue?.[key]),
  )
  const accessibilities = ACCESSIBILITIES.filter(([key]) =>
    isAvailable(venue?.[key]),
  )
  const relates = performance.relates.filter(
    (relate) => relate.relatenm && relate.relateurl,
  )
  const images = performance.images.filter((image) => image.styurl)
  const hasCoordinates =
    Number.isFinite(venue?.la) && Number.isFinite(venue?.lo)
  const favorite = isFavorite(performance.mt20id)

  return (
    <article className="page performance-detail-page">
      <Link className="detail-back-link" to={backTo}>
        ← 공연 목록으로
      </Link>

      <header className="detail-hero">
        <div className="detail-hero__media">
          <DetailPoster performance={performance} />
        </div>
        <div className="detail-hero__content">
          <div className="detail-badges">
            {performance.genrenm ? (
              <span className="genre-badge">{performance.genrenm}</span>
            ) : null}
            <span className={`status-badge ${stateClassName}`}>{state}</span>
          </div>
          <h1 className="detail-hero__title">{performance.prfnm}</h1>
          <button
            type="button"
            className={`favorite-button detail-hero__favorite ${
              favorite ? 'is-favorite' : ''
            }`}
            aria-pressed={favorite}
            onClick={() => toggleFavorite(performance.mt20id)}
          >
            <span aria-hidden="true">{favorite ? '♥' : '♡'}</span>
            {favorite ? '즐겨찾기 삭제' : '즐겨찾기 추가'}
          </button>
          <p className="detail-hero__period">📅 {period}</p>
          <p className="detail-hero__venue">
            📍 {performance.fcltynm || venue?.fcltynm || '공연장 정보 없음'}
          </p>
        </div>
      </header>

      <section className="detail-section detail-section--core" aria-labelledby="core-title">
        <h2 id="core-title" className="detail-section__title">관람 핵심 정보</h2>
        <dl className="core-info">
          <div>
            <dt>👶 관람 연령</dt>
            <dd>{performance.prfage || '정보 없음'}</dd>
          </div>
          <div>
            <dt>⏱️ 러닝타임</dt>
            <dd>{performance.prfruntime || '정보 없음'}</dd>
          </div>
          <div>
            <dt>💰 티켓 가격</dt>
            <dd>{performance.pcseguidance || '정보 없음'}</dd>
          </div>
          <div>
            <dt>📅 공연 기간</dt>
            <dd>{period}</dd>
          </div>
          <div className="core-info__wide">
            <dt>🕐 공연 시간</dt>
            <dd>{performance.dtguidance || '정보 없음'}</dd>
          </div>
        </dl>
      </section>

      {relates.length > 0 ? (
        <section className="detail-section" aria-labelledby="booking-title">
          <h2 id="booking-title" className="detail-section__title">예매</h2>
          <div className="booking-links">
            {relates.map((relate, index) => (
              <a
                key={`${relate.relatenm}-${index}`}
                className="btn btn--primary"
                href={relate.relateurl}
                target="_blank"
                rel="noreferrer"
              >
                {relate.relatenm}에서 예매하기
                <span aria-hidden="true">↗</span>
              </a>
            ))}
          </div>
        </section>
      ) : null}

      <section className="detail-section" aria-labelledby="venue-title">
        <h2 id="venue-title" className="detail-section__title">공연장 정보</h2>
        <dl className="venue-info">
          <div>
            <dt>공연장</dt>
            <dd>{performance.fcltynm || venue?.fcltynm || '정보 없음'}</dd>
          </div>
          <div>
            <dt>공연시설</dt>
            <dd>{venue?.fcltynm || '정보 없음'}</dd>
          </div>
          <div>
            <dt>주소</dt>
            <dd>{venue?.adres || '주소 정보 없음'}</dd>
          </div>
          <div>
            <dt>전화</dt>
            <dd>
              {venue?.telno ? (
                <a className="text-link" href={`tel:${venue.telno.replaceAll(' ', '')}`}>
                  {venue.telno}
                </a>
              ) : (
                '전화번호 정보 없음'
              )}
            </dd>
          </div>
        </dl>

        <h3 className="detail-section__subtitle">편의시설</h3>
        {conveniences.length > 0 ? (
          <ul className="facility-badges" aria-label="이용 가능한 편의시설">
            {conveniences.map(([key, icon, label]) => (
              <li key={key}>
                <span aria-hidden="true">{icon}</span> {label}
              </li>
            ))}
          </ul>
        ) : (
          <p className="detail-muted">제공된 편의시설 정보가 없습니다.</p>
        )}

        <h3 className="detail-section__subtitle">무장애 시설</h3>
        {accessibilities.length > 0 ? (
          <ul className="facility-badges" aria-label="이용 가능한 무장애 시설">
            {accessibilities.map(([key, label]) => (
              <li key={key}>♿ {label}</li>
            ))}
          </ul>
        ) : (
          <p className="detail-muted">제공된 무장애 시설 정보가 없습니다.</p>
        )}

        {!hasCoordinates ? (
          <div className="location-notice" role="note">
            <strong>위치 정보가 제공되지 않는 공연장입니다.</strong>
            <span>지도와 주변 놀이시설은 표시할 수 없습니다.</span>
            <span>{venue.adres || '주소 정보 없음'}</span>
          </div>
        ) : null}
      </section>

      {hasCoordinates ? (
        <section className="detail-section" aria-labelledby="location-title">
          <h2 id="location-title" className="detail-section__title">
            위치 및 주변 놀이시설
          </h2>
          <div id="venue-playground-map">
            <VenueMap
              venue={venue}
              playgrounds={playgrounds}
              selectedPlaygroundId={selectedPlaygroundId}
              onPlaygroundSelect={selectPlaygroundFromMap}
            />
          </div>
          <div className="map-legend" aria-label="지도 마커 안내">
            <span><span aria-hidden="true">🎭</span> 공연장</span>
            <span><span aria-hidden="true">🛝</span> 놀이시설</span>
          </div>
          <div
            className="playground-radius-toggle"
            role="group"
            aria-label="놀이시설 검색 반경"
          >
            <span>검색 반경</span>
            {[1000, 3000].map((radius) => (
              <button
                key={radius}
                type="button"
                className={
                  playgroundRadius === radius ? 'is-selected' : undefined
                }
                aria-pressed={playgroundRadius === radius}
                disabled={playgroundsStatus === 'loading'}
                onClick={() => changePlaygroundRadius(radius)}
              >
                {radius / 1000}km
              </button>
            ))}
          </div>

          {playgroundsStatus === 'loading' ? (
            <p className="detail-muted map-status">주변 놀이시설을 불러오는 중입니다.</p>
          ) : null}
          {playgroundsStatus === 'error' ? (
            <div className="playground-section-error" role="alert">
              <p>
                주변 놀이시설을 불러오지 못했습니다. 공연 상세와 공연장 지도는
                계속 확인할 수 있습니다.
              </p>
              <button
                type="button"
                className="btn btn--secondary"
                onClick={() => setPlaygroundsRetryCount((count) => count + 1)}
              >
                다시 시도
              </button>
            </div>
          ) : null}
          {playgroundsStatus === 'success' && playgrounds.length === 0 ? (
            <p className="playground-empty">
              반경 {playgroundRadius === 1000 ? '1km' : '3km'} 안에 확인할 수
              있는 놀이시설이 없습니다.
            </p>
          ) : null}
          {playgroundsStatus === 'success' && playgrounds.length > 0 ? (
            <div className="playground-results">
              <p className="playground-results__summary">
                반경 {playgroundRadius === 1000 ? '1km' : '3km'} 내 놀이시설{' '}
                <strong>{playgrounds.length}곳</strong>
              </p>
              {wasRadiusAutomaticallyExpanded ? (
                <p className="playground-results__notice">
                  1km 내 결과가 없어 반경을 3km로 넓혔습니다.
                </p>
              ) : null}
              {playgroundFallbackUsed ? (
                <p className="playground-results__notice">
                  공공 개방 시설이 없어 주변 다른 놀이시설을 표시합니다. 방문 전
                  이용 가능 여부를 확인해 주세요.
                </p>
              ) : null}
              <PlaygroundAccordion
                playgrounds={playgrounds}
                expandedId={selectedPlaygroundId}
                onToggle={(playgroundId) =>
                  setSelectedPlaygroundId(
                    playgroundId === selectedPlaygroundId
                      ? null
                      : playgroundId,
                  )
                }
                onShowOnMap={showPlaygroundOnMap}
              />
            </div>
          ) : null}
        </section>
      ) : null}

      {(performance.sty || images.length > 0 || performance.prfcast) ? (
        <section className="detail-section" aria-labelledby="intro-title">
          <h2 id="intro-title" className="detail-section__title">작품 소개</h2>
          {performance.sty ? (
            <div className="story">
              <p className={isStoryExpanded ? '' : 'story__text--collapsed'}>
                {performance.sty}
              </p>
              <button
                type="button"
                className="story__toggle"
                aria-expanded={isStoryExpanded}
                onClick={() => setIsStoryExpanded((expanded) => !expanded)}
              >
                {isStoryExpanded ? '접기' : '더보기'}
              </button>
            </div>
          ) : null}

          {images.length > 0 ? (
            <div className="intro-images" aria-label="공연 소개 이미지">
              {images.map((image, index) => (
                <IntroImage
                  key={`${image.styurl}-${index}`}
                  image={image}
                  performanceName={performance.prfnm}
                />
              ))}
            </div>
          ) : null}

          {performance.prfcast ? (
            <dl className="cast-info">
              <dt>출연진</dt>
              <dd>{performance.prfcast}</dd>
            </dl>
          ) : null}
        </section>
      ) : null}
    </article>
  )
}
