# 공연예술통합전산망(KOPIS) OpenAPI 가이드

---

## 1. 공연목록 조회 서비스 (pblprfrService)

### 요청URL

- http://kopis.or.kr/openApi/restful/pblprfr

### 요청변수(Request Parameter)

| 항목명 | 샘플데이터 | 항목설명 |
|---|---|---|
| service | {서비스키} | 서비스키 (필수) |
| stdate | 20230101 | 공연시작일 (필수) |
| eddate | 20230630 | 공연종료일, 최대 31일 (필수) |
| cpage | 1 | 현재페이지 (필수) |
| rows | 10 | 페이지당 목록 수, 최대 100건 (필수) |
| shprfnm | 사랑(URLEncoding) | 공연명 |
| shprfnmfct | 예술의전당(URLEncoding) | 공연시설명 |
| shcate | AAAA | 장르코드 |
| prfplccd | FC000003-01 | 공연장코드 |
| signgucode | 11 | 지역(시도)코드 |
| signgucodesub | 1111 | 지역(구군)코드 |
| kidstate | Y | 아동공연여부 (지정 안하면 기본은 전체공연) |
| prfstate | 01 | 공연상태코드 |
| openrun | Y | 오픈런여부 |
| afterdate | 20230101 | 해당일자 이후 등록/수정된 항목만 출력 |

### 출력결과(Response Element)

| 항목명 | 샘플데이터 | 항목설명 |
|---|---|---|
| mt20id | PF178134 | 공연 ID |
| prfnm | 반짝반짝 인어공주 | 공연명 |
| prfpdfrom | 2021.08.21 | 공연시작일 |
| prfpdto | 2024.09.29 | 공연종료일 |
| fcltynm | 달밤엔씨어터 | 공연시설명(공연장명) |
| poster | http://www.kopis.or.kr/upload/pfmPoster/PF_PF178134_210809_125033.PNG | 공연포스터경로 |
| area | 서울특별시 | 공연지역 |
| genrenm | 뮤지컬 | 공연 장르명 |
| openrun | Y | 오픈런 |
| prfstate | 공연중 | 공연상태 |

---

## 2. 공연 상세 조회 서비스 (pblprfrService)

### 요청URL

- http://kopis.or.kr/openApi/restful/pblprfr

### 요청변수(Request Parameter)

| 항목명 | 샘플데이터 | 항목설명 |
|---|---|---|
| service | {서비스키} | 서비스키 (필수) |
| mt20id | PF132236 | 공연 ID (필수) |

### 출력결과(Response Element)

| 항목명 | 샘플데이터 | 항목설명 |
|---|---|---|
| mt20id | PF132236 | 공연 ID |
| prfnm | 우리연애할까 | 공연명 |
| mt10id | FC001431 | 공연시설 ID |
| mt13id | FC001431-01 | 공연장 ID |
| fcltynm | 피가로아트홀(구 훈아트홀) | 공연시설명(공연장명) |
| frstregdt | 2019-07-25 10:03:14 | 최초등록일 |
| prfpdfrom | 2016.05.12 | 공연시작일 |
| prfpdto | 2016.07.31 | 공연종료일 |
| prfcast | 김부연, 임정균, 최수영 | 공연출연진 |
| prfcrew | 천정민 | 공연제작진 |
| prfruntime | 1시간 30분 | 공연 런타임 |
| prfage | 만 12세 이상 | 공연 관람 연령 |
| entrpsnm | 극단 피에로(문화제작소) | 기획제작사 |
| entrpsnmP | 극단 피에로(문화제작소) | 제작사 |
| entrpsnmA | - | 기획사 |
| entrpsnmH | - | 주최 |
| entrpsnmS | - | 주관 |
| pcseguidance | 전석 30,000원 | 티켓가격 |
| poster | http://www.kopis.or.kr/upload/pfmPoster/PF_PF132236_160704_142630.gif | 포스터이미지경로 |
| sty | - | 줄거리 |
| area | 서울특별시 | 지역 |
| genrenm | 연극 | 공연장르명 |
| openrun | N | 오픈런 |
| visit | N | 내한 |
| child | N | 아동 |
| daehakro | Y | 대학로 |
| festival | N | 축제 |
| musicallicense | N | 뮤지컬 라이센스 |
| musicalcreate | N | 뮤지컬 창작 |
| updatedate | 2019-07-25 10:03:14 | 최종수정일 |
| prfstate | 공연중 | 공연상태 |
| dtguidance | 화요일~금요일(20:00), 토요일(16:00,19:00), 일요일(15:00,18:00) | 공연시간 |
| styurls > styurl | http://www.kopis.or.kr/upload/pfmIntroImage/PF_PF132236_160704_0226303.jpg 외 | 소개이미지목록(소개이미지 1~4) |
| relates > relatenm | 대학로티켓닷컴, 티켓링크 | 예매처명 목록 |
| relates > relateurl | http://www.ticketlink.co.kr/product/14015 외 | 예매처 URL 목록 |

---

## 3. 공연시설 목록 조회 서비스 (PrfplcService)

### 요청URL

- http://kopis.or.kr/openApi/restful/pblprfr

### 요청변수(Request Parameter)

| 항목명 | 샘플데이터 | 항목설명 |
|---|---|---|
| service | {서비스키} | 서비스키 (필수) |
| cpage | 1 | 현재페이지 (필수) |
| rows | 5 | 페이지당 목록 수, 최대 100건 (필수) |
| shprfnmfct | 예술의전당(URLEncoding) | 공연시설명 |
| fcltychartr | 1 | 공연시설특성코드 |
| signgucode | 11 | 지역(시도)코드 |
| signgucodesub | 1111 | 지역(구군)코드 |
| afterdate | 20230101 | 해당일자 이후 등록/수정된 항목만 출력 |

### 출력결과(Response Element)

| 항목명 | 샘플데이터 | 항목설명 |
|---|---|---|
| mt10id | FC000517 | 공연시설 ID |
| fcltynm | 경주예술의전당 | 공연시설명 |
| mt13cnt | 2 | 공연장 수 |
| fcltychartr | 문예회관 | 시설특성 |
| sidonm | 경북 | 지역(시도) |
| gugunnm | 경주시 | 지역(구군) |
| opende | 2010 | 개관연도 |

---

## 4. 공연시설 상세 조회 서비스 (prfplcService)

### 요청URL

- https://www.kopis.or.kr/openApi/restful/prfplc/{mt10id}

> 2026-07-24 실호출 검증: `FC001247` 조회 시 HTTP 200과 공연시설 상세
> (`mt10id`, 시설명, 위도·경도 포함) 1건이 정상 반환됨.

### 요청변수(Request Parameter)

| 항목명 | 샘플데이터 | 항목설명 |
|---|---|---|
| service | {서비스키} | 서비스키 (필수) |
| mt10id | FC001247 | 공연시설 ID (필수) |

### 출력결과(Response Element)

| 항목명 | 샘플데이터 | 항목설명 |
|---|---|---|
| mt10id | FC001247 | 공연시설 ID |
| fcltynm | 올림픽공원 | 공연시설명 |
| mt13cnt | 9 | 공연장 수 |
| fcltychartr | 기타(공공) | 시설특성 |
| opende | 1986 | 개관연도 |
| seatscale | 32349 | 객석 수 |
| telno | 02-410-1114 | 전화번호 |
| relateurl | http://www.olympicpark.co.kr/ | 홈페이지 |
| adres | 서울특별시 송파구 올림픽로 424 올림픽공원 | 주소 |
| la | 37.52112 | 위도 |
| lo | 127.12836360000005 | 경도 |
| restaurant | Y | 레스토랑 |
| cafe | Y | 카페 |
| store | Y | 편의점 |
| nolibang | N | 놀이방 |
| suyu | N | 수유실 |
| parkbarrier | N | 장애시설-주차장 |
| restbarrier | N | 장애시설-화장실 |
| runwbarrier | N | 장애시설-경사로 |
| elevbarrier | N | 장애시설-엘리베이터 |
| parkinglot | Y | 주차시설 |
| mt13s > mt13id | FC001247-01 | 공연장 ID |
| mt13s > prfplcnm | KSPO DOME(체조경기장) | 공연장명 |
| mt13s > seatscale | 15,000 | 좌석규모 |
| mt13s > stageorchat | N | 무대시설_오케스트라피트(Y/N/Z/0) |
| mt13s > stagepracat | Y | 무대시설_연습실 |
| mt13s > stagedresat | Y | 무대시설_분장실 |
| mt13s > stageoutdrat | N | 무대시설_야외공연장 |
| mt13s > disabledseatscale | 20 | 장애인시설_관객석(N/000) |
| mt13s > stagearea | 15.8X13.3X8.7 | 무대시설_무대넓이(000/0X0/00.00) |

---

## 5. 기획/제작사 목록 조회 서비스 (MnfctService)

### 요청URL

- http://kopis.or.kr/openApi/restful/pblprfr

### 요청변수(Request Parameter)

| 항목명 | 샘플데이터 | 항목설명 |
|---|---|---|
| service | {서비스키} | 서비스키 (필수) |
| cpage | 1 | 현재페이지 (필수) |
| rows | 10 | 페이지당 목록 수, 최대 100건 (필수) |
| entrpsnm | 국악단(URLEncoding) | 기획/제작사명 |
| shcate | AAAA | 장르코드 |
| afterdate | 20230101 | 해당일자 이후 등록/수정된 항목만 출력 |

### 출력결과(Response Element)

| 항목명 | 샘플데이터 | 항목설명 |
|---|---|---|
| mt30id | AG002086 | 기획/제작사 ID |
| entrpsnm | 락음국악단 | 기획/제작사명 |
| genrenm | 국악 | 장르 |
| telno | 031-829-0414 | 전화번호 |
| prfnm | 제2회 영재 국악회 | 최신작품 |
| relateurl | http://www.rageum.org/ | 홈페이지 |
| sidonm | AG002086 | 지역(시도) |

---

## 6. 수상작 목록 조회 서비스 (prfawadService)

### 요청URL

- http://kopis.or.kr/openApi/restful/pblprfr

### 요청변수(Request Parameter)

| 항목명 | 샘플데이터 | 항목설명 |
|---|---|---|
| service | {서비스키} | 서비스키 (필수) |
| stdate | 20190419 | 공연시작일 (필수) |
| eddate | 20190428 | 공연종료일, 최대 31일 (필수) |
| cpage | 1 | 현재페이지 (필수) |
| rows | 10 | 페이지당 목록 수, 최대 100건 (필수) |
| shprfnm | 사랑(URLEncoding) | 공연명 |
| shprfnmfct | 예술의전당(URLEncoding) | 공연시설명 |
| shcate | AAAA | 장르코드 |
| prfplccd | FC000001-01 | 공연장코드 |
| signgucode | 11 | 지역(시도)코드 |
| signgucodesub | 1111 | 지역(구군)코드 |
| kidstate | Y | 아동공연여부 (지정 안하면 기본은 전체공연) |
| prfstate | 01 | 공연상태코드 |
| afterdate | 20230101 | 해당일자 이후 등록/수정된 항목만 출력 |

### 출력결과(Response Element)

| 항목명 | 샘플데이터 | 항목설명 |
|---|---|---|
| mt20id | PF132236 | 공연 ID |
| prfnm | 우리연애할까 | 공연명 |
| prfpdfrom | 2016.05.12 | 공연시작일 |
| prfpdto | 2016.07.31 | 공연종료일 |
| fcltynm | 피가로아트홀(구 훈아트홀) | 공연시설명(공연장명) |
| poster | http://www.kopis.or.kr/upload/pfmPoster/PF_PF132236_160704_142630.gif | 공연포스터경로 |
| genrenm | 연극 | 공연 장르명 |
| prfstate | 공연중 | 공연 상태 |
| awards | 2017 대한민국 공감브랜드 대상 교육부문 대상 | 수상실적 |

---

## 7. 공연 목록 조회 서비스 (prffestService)

### 요청URL

- http://kopis.or.kr/openApi/restful/pblprfr

### 요청변수(Request Parameter)

| 항목명 | 샘플데이터 | 항목설명 |
|---|---|---|
| service | {서비스키} | 서비스키 (필수) |
| stdate | 20160101 | 공연시작일 (필수) |
| eddate | 20160630 | 공연종료일, 최대 31일 (필수) |
| cpage | 1 | 현재페이지 (필수) |
| rows | 10 | 페이지당 목록 수, 최대 100건 (필수) |
| shprfnm | 사랑(URLEncoding) | 공연명 |
| shprfnmfct | 예술의전당(URLEncoding) | 공연시설명 |
| shcate | AAAA | 장르코드 |
| prfplccd | FC000001-01 | 공연장코드 |
| signgucode | 11 | 지역(시도)코드 |
| signgucodesub | 1111 | 지역(구군)코드 |
| kidstate | Y | 아동공연여부 (지정 안하면 기본은 전체공연) |
| prfstate | 01 | 공연상태코드 |
| afterdate | 20230101 | 해당일자 이후 등록/수정된 항목만 출력 |

### 출력결과(Response Element)

| 항목명 | 샘플데이터 | 항목설명 |
|---|---|---|
| mt20id | PF132236 | 공연 ID |
| prfnm | 우리연애할까 | 공연명 |
| prfpdfrom | 2016.05.12 | 공연시작일 |
| prfpdto | 2016.07.31 | 공연종료일 |
| fcltynm | 피가로아트홀(구 훈아트홀) | 공연시설명(공연장명) |
| poster | http://www.kopis.or.kr/upload/pfmPoster/PF_PF132236_160704_142630.gif | 공연포스터경로 |
| genrenm | 연극 | 공연 장르명 |
| festival | Y | 축제 여부 |
| prfstate | 공연중 | 공연 상태 |

---

## 8. 원·창작자 목록 조회 서비스 (prferService)

### 요청URL

- http://kopis.or.kr/openApi/restful/pblprfr

### 요청변수(Request Parameter)

| 항목명 | 샘플데이터 | 항목설명 |
|---|---|---|
| service | {서비스키} | 서비스키 (필수) |
| stdate | 20160101 | 공연시작일 (필수) |
| eddate | 20160630 | 공연종료일, 최대 31일 (필수) |
| cpage | 1 | 현재페이지 (필수) |
| rows | 10 | 페이지당 목록 수, 최대 100건 (필수) |
| shprfnm | 사랑(URLEncoding) | 공연명 |
| shprfnmfct | 예술의전당(URLEncoding) | 공연시설명 |
| shcate | AAAA | 장르코드 |
| prfplccd | FC000001-01 | 공연장코드 |
| signgucode | 11 | 지역(시도)코드 |
| signgucodesub | 1111 | 지역(구군)코드 |
| kidstate | Y | 아동공연여부 (지정 안하면 기본은 전체공연) |
| prfstate | 01 | 공연상태코드 |
| afterdate | 20230101 | 해당일자 이후 등록/수정된 항목만 출력 |

### 출력결과(Response Element)

| 항목명 | 샘플데이터 | 항목설명 |
|---|---|---|
| mt20id | PF132236 | 공연 ID |
| prfnm | 우리연애할까 | 공연명 |
| prfpdfrom | 2016.05.12 | 공연시작일 |
| prfpdto | 2016.07.31 | 공연종료일 |
| fcltynm | 피가로아트홀(구 훈아트홀) | 공연시설명(공연장명) |
| poster | http://www.kopis.or.kr/upload/pfmPoster/PF_PF132236_160704_142630.gif | 포스터이미지경로 |
| genrenm | 연극 | 공연 장르명 |
| prfstate | 공연중 | 공연 상태 |
| author | 김민수, 변성현 | 원작자 |
| creator | 정세혁(각색) | 창작자 |

---

## 9. 예매상황판 조회 서비스 (boxofficeService)

### 요청URL

- http://kopis.or.kr/openApi/restful/pblprfr

### 요청변수(Request Parameter)

| 항목명 | 샘플데이터 | 항목설명 |
|---|---|---|
| service | {서비스키} | 서비스키 (필수) |
| stdate | 20230108 | 시작날짜 (필수) |
| eddate | 20230112 | 종료날짜, 최대 31일 (필수) |
| date | 20171219 | 날짜 (필수) |
| catecode | AAAA | 장르구분코드 |
| area | 11 | 지역코드 |
| srchseatscale | 100 | 좌석수 (0:미상, 100:1~300석 미만, 300:300~500석 미만, 500:500~1000석 미만, 1000:1000~5000석 미만, 5000:5000~10000석 미만, 10000:10000석 이상) |

### 출력결과(Response Element)

| 항목명 | 샘플데이터 | 항목설명 |
|---|---|---|
| basedate | 2017-12-12~2017-12-18 | 기준일 |
| cate | 연극 | 장르 |
| rnum | 1 | 순위 |
| prfnm | 셜록홈즈 [울산] | 공연명 |
| prfpd | 2016.06.07~2016.07.24 | 공연기간 |
| prfplcnm | 소공연장 | 공연장 |
| seatcnt | 212 | 좌석수 |
| prfdtcnt | 4 | 상연횟수 |
| area | 울산 | 지역 |
| poster | http://www.kopis.or.kr/upload/pfmPoster/PF_PF131793_160603_140415.jpg | 포스터이미지 |
| mt20id | PF131793 | 공연 ID |

---

## 10. 예매통계 기간별 조회 서비스 (boxStatsService)

### 요청URL

- http://kopis.or.kr/openApi/restful/pblprfr

### 요청변수(Request Parameter)

| 항목명 | 샘플데이터 | 항목설명 |
|---|---|---|
| service | {서비스키} | 서비스키 (필수) |
| ststype | day | 요청형태, day(일별)/dayWeek(주별). 조회기간은 일별/주별 동일 최대 31일이며, 주별 요청 시 요일별 기준으로 합계되어 표기 (필수) |
| stdate | 20230108 | 시작날짜 (필수) |
| eddate | 20230112 | 종료날짜, 최대 31일 (필수) |

### 출력결과(Response Element)

| 항목명 | 샘플데이터 | 항목설명 |
|---|---|---|
| prfdt | 2023-01-08 | 날짜 |
| prfcnt | 1058 | 공연건수 |
| prfdtcnt | 4600 | 상연횟수 |
| ntssnmrssm | 53253 | 예매수 |
| cancelnmrssm | 20682 | 취소수 |
| totnmrssm | 32571 | 총 티켓판매수 |
| ntssamountsm | 1973067860 | 총 티켓판매액 |

---

## 11. 예매통계 장르별 조회 서비스 (boxStatsCateService)

### 요청URL

- http://kopis.or.kr/openApi/restful/pblprfr

### 요청변수(Request Parameter)

| 항목명 | 샘플데이터 | 항목설명 |
|---|---|---|
| service | {서비스키} | 서비스키 (필수) |
| stdate | 20230108 | 시작날짜 (필수) |
| eddate | 20230112 | 종료날짜, 최대 31일 (필수) |
| catecode | AAAA | 장르 구분 코드 (예: AAAA\|BBBB\|CCCA) |

### 출력결과(Response Element)

| 항목명 | 샘플데이터 | 항목설명 |
|---|---|---|
| catenm | 연극 | 장르 |
| prfcnt | 190 | 공연건수 |
| prfdtcnt | 26730 | 상연횟수 |
| ntssnmrssm | 76368 | 예매수 |
| cancelnmrssm | 19093 | 취소수 |
| totnmrssm | 57275 | 총 티켓판매수 |
| ntssamountsm | 14983960901 | 총 티켓판매액 |

---

## 12. 예매통계 시간대별 조회 서비스 (boxStatsTimeService)

### 요청URL

- http://kopis.or.kr/openApi/restful/pblprfr

### 요청변수(Request Parameter)

| 항목명 | 샘플데이터 | 항목설명 |
|---|---|---|
| service | {서비스키} | 서비스키 (필수) |
| stdate | 20230108 | 시작날짜 (필수) |
| eddate | 20230112 | 종료날짜, 최대 31일 (필수) |

### 출력결과(Response Element)

| 항목명 | 샘플데이터 | 항목설명 |
|---|---|---|
| timename | 00:00 ~ 2:59 | 시간대 |
| prfcnt | 16 | 공연건수 |
| prfdtcnt | 16 | 상연횟수 |
| ntssnmrssm | 82 | 예매수 |
| cancelnmrssm | 23 | 취소수 |
| totnmrssm | 59 | 총 티켓판매수 |
| ntssamountsm | -989500 | 총 티켓판매액 |

---

## 13. 예매통계 가격대별 조회 서비스 (boxStatsPriceService)

### 요청URL

- http://kopis.or.kr/openApi/restful/pblprfr

### 요청변수(Request Parameter)

| 항목명 | 샘플데이터 | 항목설명 |
|---|---|---|
| service | {ServiceKey} | 서비스키 (필수) |
| stdate | 20230108 | 시작날짜 (필수) |
| eddate | 20230112 | 종료날짜, 최대 31일 (필수) |

### 출력결과(Response Element)

| 항목명 | 샘플데이터 | 항목설명 |
|---|---|---|
| catenm | 연극 | 장르 |
| price | 0원 | 가격대 |
| ntssnmrssm | 16861 | 예매수 |
| cancelnmrssm | 7366 | 취소수 |
| totnmrssm | 9495 | 총 티켓판매수 |
| pertotnmrssm | 17 | 총 티켓판매수 장르별 비중 |
| ntssamountsm | 75848000 | 총 티켓판매액 |

---

## 14. 공연통계 기간별 통계 목록 조회 서비스 (prfstsTotalService)

### 요청URL

- http://kopis.or.kr/openApi/restful/pblprfr

### 요청변수(Request Parameter)

| 항목명 | 샘플데이터 | 항목설명 |
|---|---|---|
| service | {서비스키} | 서비스키 (필수) |
| ststype | dayWeek | 날짜코드, day(일별:최대 31일)/dayWeek(요일별:최대 7일) (필수) |
| stdate | 20160101 | 시작검색기간 (필수) |
| eddate | 20160630 | 종료검색기간, 최대 31일 (필수) |

### 출력결과(Response Element)

| 항목명 | 샘플데이터 | 항목설명 |
|---|---|---|
| prfdt | 20160101(일별) / 수요일(요일별) | 년월일 |
| prfprocnt | 14 | 개막편수 |
| prfdtcnt | 61 | 상연횟수 |
| amount | 39526200 | 매출액 |
| nmrs | 34576 | 총 티켓판매수 |
| prfcnt | 53 | 공연건수 |
| ntssnmrs | 7323 | 판매수 |
| cancelnmrs | 1390 | 취소수 |

---

## 15. 지역별 통계 목록 조회 서비스 (prfstsAreaService)

### 요청URL

- http://kopis.or.kr/openApi/restful/pblprfr

### 요청변수(Request Parameter)

| 항목명 | 샘플데이터 | 항목설명 |
|---|---|---|
| service | {서비스키} | 서비스키 (필수) |
| stdate | 20160101 | 시작검색기간 (필수) |
| eddate | 20160107 | 종료검색기간, 최대 31일 (필수) |

### 출력결과(Response Element)

| 항목명 | 샘플데이터 | 항목설명 |
|---|---|---|
| area | 서울 | 지역 |
| fcltycnt | 1085 | 공연시설수 |
| prfplccnt | 1353 | 공연장수 |
| seatcnt | 551638 | 총좌석수 |
| prfcnt | 68 | 공연건수 |
| prfprcnt | 19 | 개막편수 |
| prfdtcnt | 103 | 상연횟수 |
| nmrs | 17058 | 판매수 |
| nmrcancl | 1996 | 취소수 |
| totnmrs | 15062 | 총 티켓판매수 |
| amount | 85917000 | 총 티켓판매액 |

---

## 16. 장르별 통계 목록 조회 서비스 (prfstsCateService)

### 요청URL

- http://kopis.or.kr/openApi/restful/pblprfr

### 요청변수(Request Parameter)

| 항목명 | 샘플데이터 | 항목설명 |
|---|---|---|
| service | {서비스키} | 서비스키 (필수) |
| stdate | 20160101 | 시작검색기간 (필수) |
| eddate | 20160102 | 종료검색기간, 최대 31일 (필수) |

### 출력결과(Response Element)

| 항목명 | 샘플데이터 | 항목설명 |
|---|---|---|
| cate | 연극 | 장르 |
| prfprocnt | 6 | 개막편수 |
| prfdtcnt | 64 | 상연횟수 |
| amount | 10364600 | 매출액 |
| amountshr | 9.9 | 매출액점유율 |
| nmrs | 1080 | 관객수 |
| nmrsshr | 6.8 | 관객점유율 |

---

## 17. 공연별 통계 목록 조회 서비스 (prfstsPrfByService)

### 요청URL

- http://kopis.or.kr/openApi/restful/pblprfr

### 요청변수(Request Parameter)

| 항목명 | 샘플데이터 | 항목설명 |
|---|---|---|
| service | {서비스키} | 서비스키 (필수) |
| cpage | 1 | 현재페이지 (필수) |
| rows | 10 | 페이지당 목록 수, 최대 100건 (필수) |
| stdate | 20160601 | 시작검색기간 (필수) |
| eddate | 20160630 | 종료검색기간, 최대 31일 (필수) |
| shcate | AAAA | 장르코드 |
| shprfnm | 아들(URLEncoding) | 공연명 |

### 출력결과(Response Element)

| 항목명 | 샘플데이터 | 항목설명 |
|---|---|---|
| prfnm | 아들 | 공연명 |
| cate | 연극 | 장르 |
| mt20id | PF131558 | 공연 ID |
| fcltynm | 대학로아트원씨어터 | 공연시설명 |
| entrpsnm | (주)티앤비컴퍼니 | 기획/제작사 |
| prfpdfrom | 2016.06.07 | 공연시작일 |
| prfpdto | 2016.07.24 | 공연종료일 |
| prfdtcnt | 31 | 상연횟수 |

---

## 18. 공연시설별 통계 목록 조회 서비스 (prfstsPrfByFctService)

### 요청URL

- http://kopis.or.kr/openApi/restful/pblprfr

### 요청변수(Request Parameter)

| 항목명 | 샘플데이터 | 항목설명 |
|---|---|---|
| service | {서비스키} | 서비스키 (필수) |
| stdate | 20160601 | 시작검색기간 (필수) |
| eddate | 20160630 | 종료검색기간, 최대 31일 (필수) |
| sharea | 11 | 지역(시도)코드 |
| shprfnmfct | 예술의전당(URLEncoding) | 공연시설명 |

### 출력결과(Response Element)

| 항목명 | 샘플데이터 | 항목설명 |
|---|---|---|
| prfnmfct | 예술의전당 | 공연시설명 |
| prfnmplc | CJ 토월극장 | 공연장명 |
| seatcnt | 1004 | 좌석수 |
| prfcnt | 1 | 공연건수 |
| prfprocnt | 1 | 개막편수 |
| prfdtcnt | 1 | 상연횟수 |
| totnmrs | 480 | 총 티켓판매수 |

---

## 19. 가격대별 통계 목록 조회 서비스 (prfstsPriceService)

### 요청URL

- http://kopis.or.kr/openApi/restful/pblprfr

### 요청변수(Request Parameter)

| 항목명 | 샘플데이터 | 항목설명 |
|---|---|---|
| service | {서비스키} | 서비스키 (필수) |
| stdate | 20190625 | 시작검색기간 (필수) |
| eddate | 20190626 | 종료검색기간, 최대 31일 (필수) |
| shcate | AAAA | 장르코드 (필수) |

### 출력결과(Response Element)

| 항목명 | 샘플데이터 | 항목설명 |
|---|---|---|
| nmrs | 3 | 예매수 |
| amount | 2365000 | 예매액 |
| nmrcancl | 0 | 취소수 |
| cate | 연극 | 장르 |
| price | 15만원이상 | 가격대 |
| amountsmratio | 0.1 | 예매액 비중 |
| totnmrs | 3 | 총 티켓판매수 |

---

> 참고: 본 문서는 「공연예술통합전산망 OpenAPI 개발가이드」(v5.0, 배포일자 2026.04.23)를 기준으로 작성되었습니다. 상세 코드값(장르코드, 지역코드, 공연상태코드 등)은 kopis_openapi_code_v3.7 문서를 참조하시기 바랍니다. 원본 PDF에는 서비스별 에러코드 표가 포함되어 있지 않아 별도로 작성하지 않았습니다.