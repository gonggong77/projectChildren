function formatDistance(distance) {
  return `${distance.toLocaleString('ko-KR')}m`
}

function walkingMinutes(distance) {
  return Math.max(1, Math.round(distance / 67))
}

function waterPlayLabel(code) {
  if (code === 'X001') return '포함'
  if (code === 'X002') return '미포함'
  return '정보 없음'
}

function indoorLabel(value) {
  if (value === 'Y') return '실내'
  if (value === 'N') return '실외'
  return '정보 없음'
}

export default function PlaygroundAccordion({
  playgrounds,
  expandedId,
  onToggle,
  onShowOnMap,
}) {
  return (
    <ul className="playground-accordion" aria-label="인근 놀이시설 목록">
      {playgrounds.map((playground) => {
        const isExpanded = playground.pfct_sn === expandedId
        const panelId = `playground-panel-${playground.pfct_sn}`
        const buttonId = `playground-button-${playground.pfct_sn}`
        const address =
          playground.road_addr ||
          playground.lotno_addr ||
          '주소 정보 없음'

        return (
          <li
            id={`playground-${playground.pfct_sn}`}
            key={playground.pfct_sn}
            className={isExpanded ? 'is-expanded' : ''}
          >
            <button
              id={buttonId}
              type="button"
              className="playground-accordion__trigger"
              aria-expanded={isExpanded}
              aria-controls={panelId}
              onClick={() => onToggle(playground.pfct_sn)}
            >
              <span className="playground-accordion__chevron" aria-hidden="true">
                {isExpanded ? '▼' : '▶'}
              </span>
              <span className="playground-accordion__name">
                {playground.pfct_nm}
              </span>
              <span className="playground-place-badge">
                {playground.instl_place_nm || '유형 미상'}
              </span>
              <strong>{formatDistance(playground.distance_m)}</strong>
            </button>

            <div
              id={panelId}
              className={`playground-accordion__panel${
                isExpanded ? ' is-expanded' : ''
              }`}
              role="region"
              aria-labelledby={buttonId}
              aria-hidden={!isExpanded}
              inert={!isExpanded}
            >
              <dl className="playground-detail">
                <div>
                  <dt>주소</dt>
                  <dd>{address}</dd>
                </div>
                <div>
                  <dt>물놀이형 놀이기구</dt>
                  <dd>{waterPlayLabel(playground.wowa_styl_ride_cd)}</dd>
                </div>
                <div>
                  <dt>실내외</dt>
                  <dd>{indoorLabel(playground.indoor_yn)}</dd>
                </div>
                <div>
                  <dt>거리</dt>
                  <dd>
                    {formatDistance(playground.distance_m)} · 도보 약{' '}
                    {walkingMinutes(playground.distance_m)}분
                    <span className="playground-detail__approx">
                      (직선거리 기준 근사치)
                    </span>
                  </dd>
                </div>
              </dl>
              <button
                type="button"
                className="btn btn--secondary playground-map-button"
                onClick={() => onShowOnMap(playground.pfct_sn)}
              >
                지도에서 보기
              </button>
            </div>
          </li>
        )
      })}
    </ul>
  )
}
