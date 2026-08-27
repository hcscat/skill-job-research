# 실행과 자동화 가이드

## 필요할 때 실행

Codex 또는 Claude Code에서 Skill을 설치한 뒤 채팅에서 `job-research-match를 사용해서 ... 조건의 공고를 찾아줘`라고 요청한다. 이력서나 경력기술서를 사용할 때는 현재 요청에 파일을 직접 태그한다.

## Codex 자동화

Codex 환경에 반복 자동화 기능이 노출되어 있으면 일정, 시간대, 작업 경로, 결과 저장 위치를 확인한 뒤 그 기능으로 작업을 생성한다. 자동화 프롬프트에는 Skill 이름, 로컬 프로필 이름, 로그인 실패 시 건너뛰기, 자동 지원 금지를 명시한다.

## Claude Code와 Linux cron

Claude Code 또는 Codex CLI를 cron에서 실행하려면 먼저 대화형 실행과 인증을 완료한다. 이후 `run_scheduled_search.sh`를 cron에 등록한다. 스크립트는 위험한 권한 우회 옵션을 사용하지 않는다.

```bash
JOB_RESEARCH_AGENT=codex \
  /path/to/job-research-match/scripts/run_scheduled_search.sh
```

cron 등록 도구는 기본적으로 등록할 내용을 출력만 한다. 실제 설치는 사용자가 일정을 확인한 뒤 `--install` 옵션을 붙여 실행한다.

## 자동 실행 제한

- 자동 지원, 이력서 업로드, 메시지 전송을 하지 않는다.
- 로그인 세션이 없으면 해당 사이트를 건너뛴다.
- 암호나 MFA를 자동 입력하지 않는다.
- 실행 결과는 Git 저장소가 아닌 로컬 상태 디렉터리에 저장한다.

## 수집 범위

- 1회 수집량은 기본적으로 제한하지 않는다. 사용자가 명시적으로 상한을 요청한 경우에만 적용한다.
- 선택한 각 플랫폼의 전체 페이지·커서·피드 구간을 순회하고, 모든 후보의 상세 화면을 검증한 뒤 점수와 정렬을 계산한다.
- 실행 요약에는 목록 후보 수, 순회한 페이지·커서, 상세 확인 수, 제외 사유, 플랫폼 내 중복 제거 수, 최종 저장 수를 기록한다.
- 인증·접근 제한·속도 제한 등으로 전수 확인이 불가능하면 중단 지점과 사유를 표시하고 `partial` 또는 `best-effort`로 보고한다.

## 공식 참고자료

- OpenAI, Codex Skill 작성: https://developers.openai.com/codex/skills
- Anthropic, Claude Code Skill: https://code.claude.com/docs/en/slash-commands
- Anthropic, Claude Code CLI 비대화형 실행: https://code.claude.com/docs/en/cli-usage
