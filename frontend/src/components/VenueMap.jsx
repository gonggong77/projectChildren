import { useEffect } from 'react'
import L from 'leaflet'
import {
  MapContainer,
  Marker,
  Popup,
  TileLayer,
  useMap,
} from 'react-leaflet'

const venueIcon = L.divIcon({
  className: 'map-marker map-marker--venue',
  html: '<span aria-hidden="true">🎭</span>',
  iconAnchor: [22, 44],
  iconSize: [44, 44],
  popupAnchor: [0, -40],
})

const playgroundIcon = L.divIcon({
  className: 'map-marker map-marker--playground',
  html: '<span aria-hidden="true">🛝</span>',
  iconAnchor: [18, 36],
  iconSize: [36, 36],
  popupAnchor: [0, -32],
})

function SelectedPlaygroundController({ playground }) {
  const map = useMap()

  useEffect(() => {
    if (playground) {
      map.panTo([playground.lat, playground.lng])
    }
  }, [map, playground])

  return null
}

export default function VenueMap({
  venue,
  playgrounds,
  selectedPlaygroundId,
  onPlaygroundSelect,
}) {
  const center = [venue.la, venue.lo]
  const selectedPlayground = playgrounds.find(
    (playground) => playground.pfct_sn === selectedPlaygroundId,
  )

  return (
    <MapContainer
      className="venue-map"
      center={center}
      zoom={15}
      scrollWheelZoom={false}
      aria-label={`${venue.fcltynm || '공연장'} 위치 지도`}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <Marker position={center} icon={venueIcon} zIndexOffset={1000}>
        <Popup>
          <strong>{venue.fcltynm || '공연장'}</strong>
          {venue.adres ? <><br />{venue.adres}</> : null}
        </Popup>
      </Marker>
      {playgrounds.map((playground) => (
        <Marker
          key={playground.pfct_sn}
          position={[playground.lat, playground.lng]}
          icon={playgroundIcon}
          eventHandlers={{
            click: () => onPlaygroundSelect(playground.pfct_sn),
          }}
        >
          <Popup>
            <strong>{playground.pfct_nm}</strong>
            <br />
            공연장에서 {playground.distance_m.toLocaleString('ko-KR')}m
          </Popup>
        </Marker>
      ))}
      <SelectedPlaygroundController playground={selectedPlayground} />
    </MapContainer>
  )
}
