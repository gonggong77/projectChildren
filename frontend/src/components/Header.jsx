import { Link, NavLink } from 'react-router-dom'
import { useFavorites } from '../favorites'

export default function Header() {
  const { ids } = useFavorites()

  return (
    <header className="site-header">
      <div className="site-header__inner">
        <Link to="/" className="site-logo" aria-label="키즈스테이지 홈">
          키즈스테이지
        </Link>
        <nav className="site-nav" aria-label="주요 메뉴">
          <NavLink
            to="/favorites"
            className={({ isActive }) =>
              isActive ? 'site-nav__link is-active' : 'site-nav__link'
            }
          >
            <span aria-hidden="true">♥</span>
            즐겨찾기
            <span
              className="site-nav__count"
              aria-label={`${ids.length}개`}
            >
              {ids.length}
            </span>
          </NavLink>
        </nav>
      </div>
    </header>
  )
}
