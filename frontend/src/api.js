// 프론트엔드는 FastAPI `/api/*`만 호출한다.
// KOPIS·공공데이터포털 등 외부 API는 절대 직접 호출하지 않는다.
const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

export class ApiError extends Error {
  constructor(message, { status, code } = {}) {
    super(message)
    this.name = 'ApiError'
    this.status = status ?? null
    this.code = code ?? null
  }
}

function buildUrl(path, params) {
  const url = new URL(path, BASE_URL)
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value === undefined || value === null || value === '') return
      url.searchParams.set(key, String(value))
    })
  }
  return url
}

async function request(path, { params, signal } = {}) {
  if (!path.startsWith('/api/')) {
    throw new Error('프론트엔드는 /api/* 경로만 호출할 수 있습니다.')
  }

  const res = await fetch(buildUrl(path, params), {
    headers: { Accept: 'application/json' },
    signal,
  })

  let body = null
  try {
    body = await res.json()
  } catch {
    body = null
  }

  if (!res.ok) {
    const detail = body?.detail
    const message =
      (typeof detail === 'object' && detail?.message) ||
      body?.message ||
      '잠시 후 다시 시도해주세요'
    const code =
      (typeof detail === 'object' && detail?.code) || body?.code || null
    throw new ApiError(message, { status: res.status, code })
  }

  return body
}

/** 헬스체크 + 최종 적재 시각 */
export function fetchHealth(options) {
  return request('/api/health', options)
}

/** 시도·구군 행정표준코드 목록 */
export function fetchRegions(options) {
  return request('/api/regions', options)
}

/**
 * 공연 목록
 * @param {{ q?, sido?, gugun?, prfstate?, shcate?, from?, to?, sort?, page?, size? }} params
 */
export function fetchPerformances(params = {}, options) {
  return request('/api/performances', { ...options, params })
}

/** 공연 상세(+공연장 병합) */
export function fetchPerformanceDetail(mt20id, options) {
  return request(`/api/performances/${encodeURIComponent(mt20id)}`, options)
}

/** 즐겨찾기용 일괄 조회 (ids 배열, 최대 100) */
export function fetchPerformancesBatch(ids, options) {
  return request('/api/performances/batch', {
    ...options,
    params: { ids: ids.join(',') },
  })
}

/**
 * 인기 어린이 공연 랭킹
 * @param {{ limit? }} params
 */
export function fetchRankings(params = {}, options) {
  return request('/api/rankings', { ...options, params })
}

/**
 * 인근 놀이시설
 * @param {{ lat, lng, radius?, limit? }} params
 */
export function fetchNearbyPlaygrounds(params, options) {
  return request('/api/playgrounds/nearby', { ...options, params })
}
