import { useEffect, useRef } from 'react'

const EASE_OUT_QUART = 'cubic-bezier(0.25, 1, 0.5, 1)'
const STAR_COLORS = ['#ffeb54', '#ff641e', '#34b96f', '#ffffff', '#ff8fbd']
const STAR_COUNT = 8

function getClickPosition(event) {
  if (event.clientX || event.clientY) {
    return { x: event.clientX, y: event.clientY }
  }

  const target = event.target instanceof Element ? event.target : null
  const rect = target?.getBoundingClientRect()

  return rect
    ? { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 }
    : { x: window.innerWidth / 2, y: window.innerHeight / 2 }
}

export default function ClickStarBurst() {
  const layerRef = useRef(null)

  useEffect(() => {
    function burst(event) {
      const layer = layerRef.current
      if (!layer) return

      const { x, y } = getClickPosition(event)

      Array.from({ length: STAR_COUNT }, (_, index) => {
        const star = document.createElement('span')
        const angle = (Math.PI * 2 * index) / STAR_COUNT + (Math.random() - 0.5) * 0.35
        const distance = 38 + Math.random() * 56
        const dx = Math.cos(angle) * distance
        const dy = Math.sin(angle) * distance
        const size = 13 + Math.random() * 12
        const rotation = Math.random() * 50 - 25
        const duration = 520 + Math.random() * 180

        star.className = 'click-star'
        star.textContent = '★'
        star.style.left = `${x}px`
        star.style.top = `${y}px`
        star.style.fontSize = `${size}px`
        star.style.color = STAR_COLORS[index % STAR_COLORS.length]
        layer.appendChild(star)

        const animation = star.animate(
          [
            {
              opacity: 0,
              transform: `translate(-50%, -50%) scale(0.2) rotate(${rotation}deg)`,
            },
            {
              opacity: 1,
              transform: `translate(calc(-50% + ${dx * 0.28}px), calc(-50% + ${dy * 0.28}px)) scale(1.18) rotate(${rotation + 35}deg)`,
              offset: 0.18,
            },
            {
              opacity: 0,
              transform: `translate(calc(-50% + ${dx}px), calc(-50% + ${dy}px)) scale(0.55) rotate(${rotation + 95}deg)`,
            },
          ],
          {
            duration,
            easing: EASE_OUT_QUART,
            fill: 'forwards',
          },
        )

        animation.addEventListener('finish', () => star.remove(), { once: true })
        window.setTimeout(() => star.remove(), duration + 100)
        return star
      })
    }

    document.addEventListener('click', burst)
    return () => document.removeEventListener('click', burst)
  }, [])

  return <div ref={layerRef} className="click-star-layer" aria-hidden="true" />
}
