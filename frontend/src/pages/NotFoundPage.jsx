import { Link } from 'react-router-dom'

export default function NotFoundPage() {
  return (
    <div className="page page--center">
      <h1 className="page__title">페이지를 찾을 수 없어요</h1>
      <p className="page__lead">요청한 주소가 올바른지 확인해주세요.</p>
      <Link to="/" className="btn btn--primary">
        공연 목록으로 돌아가기
      </Link>
    </div>
  )
}
