import { useSyncExternalStore } from 'react'

export const FAVORITES_STORAGE_KEY = 'kidsstage:favorites'

const EMPTY_IDS = []
const listeners = new Set()
let snapshot = readFavorites()

function normalizeIds(value) {
  const ids = Array.isArray(value) ? value : value?.ids
  if (!Array.isArray(ids)) return []

  return [
    ...new Set(
      ids.filter((id) => typeof id === 'string' && id.trim()).map((id) => id.trim()),
    ),
  ]
}

function readFavorites() {
  if (typeof window === 'undefined') return []

  try {
    const rawValue = window.localStorage.getItem(FAVORITES_STORAGE_KEY)
    return rawValue ? normalizeIds(JSON.parse(rawValue)) : []
  } catch {
    return []
  }
}

function notify() {
  listeners.forEach((listener) => listener())
}

function persist(ids) {
  snapshot = normalizeIds(ids)

  if (typeof window !== 'undefined') {
    try {
      window.localStorage.setItem(
        FAVORITES_STORAGE_KEY,
        JSON.stringify({
          ids: snapshot,
          saved_at: new Date().toISOString(),
        }),
      )
    } catch {
      // 저장 공간 제한 등으로 실패해도 현재 화면의 낙관적 상태는 유지한다.
    }
  }

  notify()
}

function subscribe(listener) {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

function getSnapshot() {
  return snapshot
}

function getServerSnapshot() {
  return EMPTY_IDS
}

if (typeof window !== 'undefined') {
  window.addEventListener('storage', (event) => {
    if (event.key !== FAVORITES_STORAGE_KEY) return
    snapshot = readFavorites()
    notify()
  })
}

export function useFavorites() {
  const ids = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot)

  return {
    ids,
    isFavorite: (mt20id) => ids.includes(mt20id),
    toggleFavorite: (mt20id) => {
      persist(
        snapshot.includes(mt20id)
          ? snapshot.filter((id) => id !== mt20id)
          : [...snapshot, mt20id],
      )
    },
    removeFavorites: (removedIds) => {
      const removed = new Set(removedIds)
      persist(snapshot.filter((id) => !removed.has(id)))
    },
  }
}
