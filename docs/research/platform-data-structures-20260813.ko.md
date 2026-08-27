# 채용 플랫폼 공개 데이터 구조 검토 (한국어 부가 번역)

영문 문서 [`platform-data-structures-20260813.md`](platform-data-structures-20260813.md)가
주요 문서이며, 이 파일은 읽기 편의를 위한 부가 번역이다.

## 범위와 한계

이번 검토는 플랫폼의 공식 문서와 로그인 없이 접근 가능한 공개 GET 응답의 상태 코드·응답 헤더·HTML·SSR/Next.js·RSC·JSON-LD·직렬화 객체를 확인한 결과다. 인앱 브라우저 네트워크 패널을 사용할 수 없었으므로 인증 세션의 비공개 패킷, 내부 검색 API, 계정별 요청은 검사하지 않았다. 아래 내용은 관찰된 공개 페이지 계약이며, undocumented endpoint의 안정성을 보장하지 않는다. 수집기에서는 실행 시 응답을 다시 확인하고, 쿠키·인증 헤더·외부 앱 키·연락처·인증 페이지 전문을 저장하지 않는다.

공통 정규화 키는 `source`, `posting_id`, `canonical_url`, `title`, `company`, `responsibilities`, `requirements`, `experience_min_years`, `experience_max_years`, `location`, `employment_type`, `posted_at`, `deadline`, `active_status`, `transport_evidence`다. 사람인·잡코리아는 `query_path=region`과 `query_path=subway`를 따로 기록하고 상세 확인 후 ID/URL로 합친다.

### 공개 요청·응답 운반 요약

| 플랫폼 | 공개 요청/응답에서 확인한 운반 | 실행 시 주의 |
|---|---|---|
| 사람인 | 공식 API `GET`, `Accept`로 XML/JSON 선택; 공개 상세 셸은 리디렉션(이번 확인에서는 307) 후 HTML로 이어질 수 있음 | API 자격을 저장하지 않고, 상세·마감 상태를 다시 확인 |
| 잡코리아 | 상세 GET은 200 HTML, `X-Powered-By: Next.js`와 RSC 관련 `Vary` 헤더; 본문에 SSR/RSC·JSON-LD·iframe | 내부 RSC 요청을 undocumented API로 고정하지 않음 |
| 원티드 | 공개 상세 GET은 200 HTML, `__NEXT_DATA__` 초기 JSON과 렌더링 본문 병존 | 초기 JSON의 status/close와 화면 문구를 교차 검증 |
| 점핏 | 공개 상세 GET은 200 HTML, Next.js/RSC 및 dehydrated state | 접근 가능해도 게시·마감일이 과거일 수 있음 |
| CATCH | 공개 상세 GET은 200 HTML, SSR 직렬화 객체와 상세 본문 | 종료 시각·종료 코드를 우선 확인 |
| 그룹바이 | 공개 목록·상세 GET은 200 HTML, Next.js `__NEXT_DATA__`와 JSON-LD | 공개 개발자 API를 추정하지 않고 상세 `dueDate`와 화면 상태를 재확인 |
| Work24 | 공식 API는 XML 목록/상세; 공개 상세 GET은 200 HTML 폼·표 | API 자격 없이 공개 상세로 확인할 때도 상태를 검증 |

위 표의 상태 코드와 헤더는 2026-08-13 공개 GET 점검의 관찰값이다. 인증 세션의 요청·응답, 브라우저 네트워크 패널, 쿠키·인증 헤더는 범위에서 제외했다.

## 사용자 프로필과의 결합 규칙

- 이 문서는 플랫폼의 공개 데이터 구조만 설명하며 특정 사용자의 검색 조건을 기본값으로 두지 않는다.
- 역할·경력·지역·역·고용형태·연봉·최신성·제외어·저장점수는 설치 후 승인된 프로필 또는 실행 직전 읽은 설정에서 가져온다.
- `job_type`, `salary`, `salary_min`, `salary_max`, 전체 경력 필드와 상세 본문을 원문 그대로 보존하고, 사용자 조건에 맞게 정규화한 뒤 판정한다.
- 입력되지 않은 조건은 제한으로 사용하지 않는다. 점수는 정렬·저장 보조값이며 자동지원 또는 자동판정을 수행하지 않는다.

## 사람인 (Saramin)

- 공식 검색 API 안내: [Job Search API](https://oapi.saramin.co.kr/guide/job-search)
- 공식 엔드포인트는 `GET https://oapi.saramin.co.kr/job-search`이며 `Accept: application/xml` 또는 `application/json`을 사용한다. 외부 애플리케이션의 접근 자격이 필요하므로 공유 설정 파일에는 실제 값이나 계정을 넣지 않는다.
- 확인 가능한 필터는 `keywords`, `loc_cd`, `loc_mcd`, `loc_bcd`, `ind_cd`, `job_mid_cd`, `job_cd`, `job_type`, `edu_lv`, `published`, `updated`, `deadline`, `start`, `count`(최대 110), `sort`다. 지역 경로와 역세권 경로는 UI 검색 조건으로 각각 실행한다.
- API의 `sr=directhire`는 헤드헌팅·파견업체 공고를 제외하는 옵션이다. 사용자의 고용형태 정책을 확인한 뒤 사용 여부를 정하고, `job_type`과 상세 본문을 보존한다.
- 응답은 `job-search/jobs/job` 배열 형태이며 공고 ID·URL·`active`, 게시/수정 시각, 마감 유형, 회사, 포지션, 지역, 고용형태, 산업·직무 코드가 핵심 필드다.
- `salary`는 코드·표시명으로 내려오거나 없을 수 있다. 미제공 허용 여부와 표시 금액 하한은 사용자 프로필로 후검증한다.
- 공개 상세 링크는 실행 시 리디렉션·동적 본문 여부를 확인한다. 목록의 활성 플래그만으로 추천하지 않고 상세 페이지의 마감 문구와 날짜를 재검증한다.

## 잡코리아 (JobKorea)

- 데스크톱 상세 URL 형식은 `https://www.jobkorea.co.kr/Recruit/GI_Read/<id>`다. 이번 검토에서 별도의 공개 개발자 API는 확인하지 못했다.
- 공개 상세 응답은 HTML과 Next.js/RSC 페이로드가 함께 내려오며 JSON-LD도 포함될 수 있다. 관찰한 구조의 예시는 `jobId`, `jobSubId`, `careers[]`(전체 경력 범위), `locationAttributes`, `nearbySubwayAttributes`, `experienceRequirements`, `educationRequirements`, 직무·기술 코드다.
- 본문 일부는 `GI_Read_Comt_Ifrm?Gno=<id>` 임베디드 프레임으로 제공될 수 있다. 프레임에서 업무·요건을 확인하되, 응답에 섞인 인사 담당자 연락처는 정규화하거나 보고하지 않는다.
- 사용자가 지정한 지역 검색과 역세권 검색을 분리 실행한다. 검색 UI의 내부 쿼리 파라미터는 변경될 수 있으므로 실행 시 새로 확인한다.

## 원티드 (Wanted)

- 공개 상세 페이지 예: [Wanted position](https://www.wanted.co.kr/wd/267268)
- HTML과 `__NEXT_DATA__.props.pageProps.initialData`에서 ID, 회사, 주소, 포지션, 주요 업무, 자격요건, 경력, 고용형태, 카테고리, 마감·상태 필드를 관찰할 수 있다.
- 렌더링된 문구와 초기 데이터의 상태가 다를 수 있다. 검토한 샘플은 화면에 상시채용 문구가 있어도 초기 데이터에 `status=close`, 과거 `close_time`, `hidden=true`가 함께 있었다. 따라서 상태·마감·숨김 필드를 같은 실행 시점에 재조정한다.
- 페이지의 무단 재배포·재처리 금지 문구를 존중하고, 공개 상세를 근거 확인에만 사용한다. 내부 API를 추정해 대량 수집하지 않는다.

## 점핏 (Jumpit)

- 공개 상세 URL 형식은 `https://jumpit.saramin.co.kr/position/<id>`다.
- Next.js/RSC와 dehydrated state에서 `queryKey=["position","view","<id>"]`, `techStacks`, `responsibility`, `qualifications`, `preferredRequirements`, `minCareer`, `maxCareer`, `publishedAt`, `closedAt`, `location`, `educationName`, `jobCategories`, `positionStatus`를 관찰했다.
- 과거 게시일·마감일이 있는 페이지도 접근될 수 있으므로 `closedAt`, 현재 상태, 상세 본문을 함께 확인한다. 기술 스택은 정규화하되 원문 표기와 코드가 있으면 분리 보존한다.

## CATCH

- 공개 상세 URL 형식은 `https://www.catch.co.kr/NCS/RecruitInfoDetails/<id>`다.
- 서버 렌더링 HTML 안에 직렬화된 객체가 포함될 수 있으며 관찰 키는 `RecruitID`, `ApplyStartDatetime`, `ApplyEndDatetime`, `ApplyEndCode`, `RecruitTitle`, `CompName`, `workAreas`, `careerGubun`, `careerGubunNames`, `JsonData`다.
- 시작·종료 시각과 종료 코드가 현재 상태 판단의 우선 근거다. 목록의 카테고리만으로 직무·지역·경력 적합성을 확정하지 않고 공식 상세에서 재확인한다.

## 고용24/Work24

- 공식 Open API 안내: [고용24 Open API](https://www.work24.go.kr/cm/e/a/0110/selectOpenApiIntro.do)
- 공식 API는 XML(UTF-8) 응답이며 인증된 외부 애플리케이션 키와 `callTp=L|D`, `returnType=XML`, 시작 페이지·표시 건수, 지역·직종 조건을 사용한다. 목록과 상세를 분리해 호출할 수 있다.
- 공개 상세 페이지는 `wantedAuthNo`를 포함한 HTML 폼과 표 형태의 직무·자격·업무·지역 필드를 제공한다. 공개 상세만으로 확인할 때도 마감·상태를 다시 검사한다.
- 공공·중소기업 보조 소스로 유지하되, IT 신호가 약하면 저장 점수와 증거 품질로 걸러낸다.

## 그룹바이 (Groupby) — 2026-08-17 추가 점검

- 공개 목록은 `https://groupby.kr/jobs/engineering` 및 직무별 목록에서 확인할 수 있고, 공식 상세 URL은 `https://groupby.kr/positions/<id>` 형식이다.
- 목록의 `__NEXT_DATA__.props.pageProps.positions`에서 `id`, `name`, `careerType`, `positionTypes`, `techStacks`, `experienceRange`, `publishedAt`, `updatedAt`, `location`, `address`, `startup` 등을 관찰했다.
- 상세의 직렬화 데이터에서 `task`, `qualification`, `preferred`, `hiringProcess`, `dueDate`, `careerType`, `experienceRange`, `positionTypes`, `techStacks`, `location`, `address`, `startup`을 확인할 수 있다. 화면 본문과 함께 업무·요건·경력·지역·마감 상태를 재검증한다.
- 공개 필터 UI는 포지션, 경력 유형·연차, 스킬, 근무지, 서비스/비즈니스 모델, 기업 규모, 키워드 축을 제공한다. 필터 값과 쿼리 파라미터는 실행 시 갱신하며, 역·지하철 필터는 확인되지 않았으므로 별도 경로를 만들지 않는다.
- 문서화된 공개 개발자 API는 확인하지 못했다. 공개 HTML·Next.js 초기 데이터만 관찰 계약으로 기록하고 비공개 엔드포인트를 추정하거나 고정하지 않는다.

## 공식 기업/ATS, LinkedIn·Indeed, 프로그래머스

- 공식 기업/ATS는 사이트별 HTML·JSON-LD·XML 계약이 다르므로 canonical URL, 업무·요건·지역·경력·마감·상태를 확인할 수 있을 때 우선한다. 로그인 전용이나 URL이 안정적이지 않은 경우 `manual-only`로 표시한다.
- LinkedIn·Indeed는 공개 목록·검색 결과만 보조 근거로 사용하고, 로그인·지역 제한·재배포 조건이 있는 상세는 사용자 승인 없이 자동 수집하지 않는다.
- 프로그래머스는 현재 공개 상세 필드와 URL 계약을 실행 시점에 다시 확인한 뒤 사용한다. 확인 전에는 `deferred`로 기록한다.

## 검색·검증·저장 매핑

| 공통 값 | 우선 관찰 필드 | 없을 때 처리 |
|---|---|---|
| 공고 ID | `id`, `jobId`, `jobSubId`, `RecruitID`, `wantedAuthNo` | canonical URL을 대체 키로 사용 |
| 회사·제목 | `company`, `CompName`, `position`, `RecruitTitle`, JSON-LD | `미제공`, 수동 검토 |
| 업무·요건 | `responsibility`, `responsibilities`, `qualifications`, 상세 본문/iframe | 목록만 있으면 evidence cap |
| 총경력 | `careers[]`, `minCareer/maxCareer`, `careerGubun` | 총경력 미확인, 세부 연차는 메모 |
| 지역·역세권 | `location`, `workAreas`, `locationAttributes`, `nearbySubwayAttributes` | 허용 지역 매칭 보류 |
| 마감·활성 | `active`, `ApplyEndDatetime`, `closedAt`, `status`, `deadline` | `unknown`, 추천 금지·최대 79점 |
| 운반 구조 | official API, HTML, SSR/Next.js, RSC, JSON-LD, XML | `mixed` 또는 `unknown` |

이 매핑은 검색조건 시트와 설정 예시 파일의 설명용 기준이다. 실제 수집 때마다 응답 시각과 공개 근거를 기록하고, 같은 회사·제목이라도 플랫폼이 다르면 플랫폼별 공고를 보존한다.
