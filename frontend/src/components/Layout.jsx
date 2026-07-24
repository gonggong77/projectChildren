import { Outlet } from 'react-router-dom'
import ClickStarBurst from './ClickStarBurst'
import Header from './Header'
import Footer from './Footer'

export default function Layout() {
  return (
    <div className="app-shell">
      <ClickStarBurst />
      <Header />
      <main className="app-main">
        <Outlet />
      </main>
      <Footer />
    </div>
  )
}
