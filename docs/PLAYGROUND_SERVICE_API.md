# 요청URL

- https://apis.data.go.kr/1741000/pfc3/getPfctInfo3

> 2026-07-24 실호출 검증: 1건 조회 시 HTTP 200 및 정상 응답 코드(`00`)를
> 확인했으며, `latCrtsVl`(위도)과 `lotCrtsVl`(경도)이 숫자 형태로 반환됨.
> 따라서 PRD D2의 1차 방안인 API 응답 좌표를 사용할 수 있음.
>
> 2026-07-24 페이지 크기 실호출 검증: `recordCountPerPage=1,000` 요청은
> 응답값과 항목 수가 모두 1,000건이었고, `10,000` 요청은 응답값과 항목 수가
> 모두 1,000건으로 제한됨. 따라서 API의 페이지당 최대 조회 건수는 1,000건임.
>
> 2026-07-24 전국 적재 호출량 산정: 실호출의 `totalCnt=85,211`과 페이지당
> 최대 1,000건을 기준으로 `ceil(85,211 / 1,000) = 86회`가 필요함.
> 개발계정 일 한도 10,000회 중 0.86%이므로 전국 전량 적재가 가능함
> (재시도 호출은 별도 여유분으로 관리).

## 요청변수 (Request Parameters)

| 변수명 | 필수여부 | 설명 |
|---|---|---|
| serviceKey | 필수 | 공공데이터포털에서 받은 인증키 |
| pageIndex | 필수 | 페이지번호 |
| recordCountPerPage | 필수 | 한 페이지 결과 수 |
| instlPlaceCd | 선택 | 설치장소코드 (A001:목욕장업소, A002:도로휴게시설, A003:도시공원, A004:식품접객업소, A005:아동복지시설, A006:어린이집, A007:유치원, A008:대규모점포, A009:의료기관, A010:주택단지, A011:학교, A012:학원, A013:놀이제공영업소, A020:주상복합, A022:박물관, A023:종교시설, A030:자연휴양림, A031:하천, A032:야영장, A033:공공도서관, A092:육아종합지원센터, A093:유아교육진흥원) |
| pfctNm | 선택 | 놀이시설명 |
| pfctSn | 선택 | 놀이시설번호 |
| wowaStylRideCd | 선택 | 물놀이유형놀이기구 포함여부 (X001:포함, X002:미포함) |

## 응답 구조 (Response Model)

```
response
├─ header
│   ├─ resultCode: string
│   └─ resultMsg: string
└─ body
    ├─ pageIndex: string
    ├─ recordCountPerPage: string
    ├─ totalCnt: string
    ├─ totalPageCnt: string
    └─ items: [ ... ]
```

items의 각 항목에는 시설번호(pfctSn), 시설명(pfctNm), 우편번호(zip), 지번/도로명 주소(lotnoAddr, lotnoDaddr, ronaAddr, ronaDaddr), 설치일자(instlYmd), 설치장소코드(instlPlaceCd/Nm), 의무여부(dutyCd/Nm), 민간/공공여부(prvtPblcYnCd/Nm), 운영여부(operYnCd/Nm), 실내외구분(idrodrCd/Nm), 지역코드(rgnCd/Nm), 위경도(latCrtsVl, lotCrtsVl), 물놀이기구포함여부(wowaStylRideCd/Nm) 등의 필드가 포함됩니다.

### items 필드 상세

| 필드명 | 설명 |
|---|---|
| pfctSn | 시설번호 |
| pfctNm | 시설명 |
| zip | 우편번호 |
| lotnoAddr | 지번주소 |
| lotnoDaddr | 지번상세주소 |
| ronaAddr | 도로명주소 |
| ronaDaddr | 도로명상세주소 |
| instlYmd | 설치일자 |
| clsgYmd | 폐쇄일자 |
| acptnYmd | 검사(인수)일자 |
| etcSufa | 기타 부대시설 |
| exfcYn | 설치검사 효력여부 |
| fcar | 설치면적 |
| instlPlaceCd / instlPlaceCdNm | 설치장소코드 / 설치장소명 |
| dutyCd / dutyCdNm | 의무코드 / 의무여부명 |
| prvtPblcYnCd / prvtPblcYnCdNm | 민간/공공 구분코드 / 구분명 |
| operYnCd / operYnCdNm | 운영여부코드 / 운영여부명 |
| idrodrCd / idrodrCdNm | 실내외구분코드 / 실내외구분명 |
| exfcDsgnYmd | 효력지정일자 |
| rgnCd / rgnCdNm | 지역코드 / 지역명 |
| latCrtsVl | 위도 |
| lotCrtsVl | 경도 |
| wowaStylRideCd / wowaStylRideCdNm | 물놀이유형놀이기구 포함여부코드 / 포함여부명 |

### 수집 매핑 (2026-07-24 실호출 검증)

`recordCountPerPage=1` 응답의 전체 필드명을 확인해 다음과 같이 매핑한다.

| DB 필드 | API 필드 | 변환 규칙 |
|---|---|---|
| `pfct_sn` | `pfctSn` | 문자열로 저장 |
| `pfct_nm` | `pfctNm` | 그대로 저장 |
| `instl_place_cd` | `instlPlaceCd` | 그대로 저장 |
| `instl_place_nm` | `instlPlaceCdNm` | 그대로 저장 |
| `road_addr` | `ronaAddr`, `ronaDaddr` | 두 필드의 비어 있지 않은 값을 공백으로 결합 |
| `lotno_addr` | `lotnoAddr`, `lotnoDaddr` | 두 필드의 비어 있지 않은 값을 공백으로 결합 |
| `zip` | `zip` | 그대로 저장 |
| `lat` | `latCrtsVl` | 실수로 변환 |
| `lng` | `lotCrtsVl` | 실수로 변환 |
| `wowa_styl_ride_cd` | `wowaStylRideCd` | `X001` 포함 / `X002` 미포함 |
| `indoor_yn` | `idrodrCd`, `idrodrCdNm` | 원본 코드·라벨 기준으로 정규화 |
| `is_public_access` | `instlPlaceCd` | PRD 부록 B 화이트리스트로 파생 |
| `updated_at` | 제공 필드 없음 | 적재 시각 기록 |

## 출력결과 예시 (Response Example)

```json
{
  "response": {
    "header": {
      "resultCode": "00",
      "resultMsg": "NORMAL SERVICE"
    },
    "body": {
      "recordCountPerPage": 10,
      "pageIndex": 1,
      "totalPageCnt": 8521,
      "totalCnt": 85210,
      "items": [
        {
          "pfctSn": "1008026",
          "pfctNm": "황간초등학교 놀이시설",
          "zip": "29115",
          "lotnoAddr": null,
          "lotnoDaddr": null,
          "ronaAddr": "충북 영동군 황간면 남성1길 25",
          "ronaDaddr": "(황간초등학교)",
          "instlYmd": "20260714",
          "clsgYmd": null,
          "acptnYmd": " ",
          "etcSufa": "",
          "exfcYn": "N",
          "fcar": "82",
          "instlPlaceCd": "A011",
          "instlPlaceCdNm": "학교",
          "dutyCd": "Q001",
          "dutyCdNm": "의무",
          "prvtPblcYnCd": "C002",
          "prvtPblcYnCdNm": "공공",
          "operYnCd": "B001",
          "operYnCdNm": "운영",
          "idrodrCd": "O002",
          "idrodrCdNm": "실외",
          "exfcDsgnYmd": null,
          "rgnCd": "4374032000",
          "rgnCdNm": "충청북도 영동군 황간면",
          "latCrtsVl": "36.2273960",
          "lotCrtsVl": "127.9130288",
          "wowaStylRideCd": "X002",
          "wowaStylRideCdNm": "미포함"
        }
      ]
    }
  }
}
```

## 응답 코드

| Code | 설명 |
|---|---|
| 70 | aop 에러 |
| 200 | 성공 |


# 에러코드 에러 메시지 설명

22 LIMITED_NUMBER_OF_SERVICE_REQUESTS_EXCEEDS_ERROR 서비스 요청제한횟수 초과에러
00 NORMAL_CODE 정상
01 APPLICATION_ERROR 어플리케이션 에러
02 DB_ERROR 데이터베이스 에러
03 NODATA_ERROR 데이터없음 에러
04 HTTP_ERROR HTTP 에러
05 SERVICETIMEOUT_ERROR 서비스 연결실패 에러
10 INVALID_REQUEST_PARAMETER_ERROR 잘못된 요청 파라메터 에러
11 NO_MANDATORY_REQUEST_PARAMETERS_ERROR 필수요청 파라메터가 없음
12 NO_OPENAPI_SERVICE_ERROR 해당 오픈API서비스가 없거나 폐기됨
20 SERVICE_ACCESS_DENIED_ERROR 서비스 접근거부
21 TEMPORARILY_DISABLE_THE_SERVICEKEY_ERROR 일시적으로 사용할 수 없는 서비스 키
22 LIMITED_NUMBER_OF_SERVICE_REQUESTS_EXCEEDS_ERROR 서비스 요청제한횟수 초과에러
30 SERVICE_KEY_IS_NOT_REGISTERED_ERROR 등록되지 않은 서비스키
31 DEADLINE_HAS_EXPIRED_ERROR 기한만료된 서비스키
32 UNREGISTERED_IP_ERROR 등록되지 않은 IP
33 UNSIGNED_CALL_ERROR 서명되지 않은 호출
99 UNKNOWN_ERROR 기타에러
