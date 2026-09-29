# vMix Output 설정 한눈에 정리: Fullscreen, Output 1~4, NDI·SRT, MultiView

<!--
발행 전 확인할 것
1. [직접 경험] 표시된 곳에 실제 현장에서 쓰는 구성을 한두 줄 넣어 주세요.
2. OMT 설명과 Source 목록은 사용 중인 vMix 버전 기준으로 한 번 확인해 주세요.
확인이 끝나면 이 주석은 지워도 됩니다.
-->

slug: vmix-output-settings
description: vMix의 Settings > Outputs / NDI / OMT / SRT 화면을 항목별로 설명합니다. Fullscreen 출력, Output 1~4의 역할, 오버레이 on/off, NDI·SRT 송출, MultiView 레이아웃까지 현장에서 쓰는 기준으로 정리했습니다.
tags: vMix, vMix설정, NDI, SRT, 라이브방송, 방송송출

---

vMix에서 "화면을 어디로, 어떤 모습으로 내보낼지"는 모두 **Settings → Outputs / NDI / OMT / SRT** 한 화면에서 정합니다. 처음 보면 칸이 많아 복잡해 보이지만, 구조는 단순합니다. **각 줄마다 "무엇을(Source) → 자막을 얹을지(Overlays) → 어디로(NDI·OMT·SRT, 모니터, 녹화·송출)"** 를 고르는 방식입니다.

![vMix Settings의 Outputs / NDI / OMT / SRT 화면](/images/vmix-output-settings.png)

## 1. Fullscreen 1·2: 모니터로 내보내기

PC에 연결된 **두 번째·세 번째 모니터(또는 프로젝터, 현장 LED)** 에 화면을 전체 화면으로 띄우는 출력입니다. 오른쪽 Description의 Display 1, Display 2가 각각 어떤 모니터인지는 **Display** 메뉴에서 지정합니다.

- **Source**: 보통 `Output`(방송 화면)을 고르지만, 현장 스크린에는 특정 입력(예: 발표 PPT)만 따로 띄울 수도 있습니다.
- **Overlays**: 방송용 자막을 현장 스크린에서는 빼고 싶다면 여기서 끕니다.

## 2. Output 1~4: 녹화·송출·외부 출력의 출발점

vMix 안에서 만들어지는 화면을 최대 4개까지 따로 정의할 수 있는 칸입니다.

| 출력 | 기본 용도(Description) | 이렇게 씁니다 |
| --- | --- | --- |
| Output 1 | Record / Stream / External | 녹화·유튜브 송출·기본 외부 출력에 쓰이는 메인 화면 |
| Output 2 | External 2 | 자막 없는 클린 화면, 별도 녹화용 |
| Output 3 | External 3 | 현장 모니터용, 프리뷰 화면 등 |
| Output 4 | External 4 | 다른 PC·장비로 보내는 추가 화면 |

**Output 1이 가장 중요합니다.** 녹화(Record)와 송출(Stream)이 이 줄의 Source를 따라가기 때문에, 여기를 `Output`이 아닌 다른 것으로 바꾸면 방송에 전혀 다른 화면이 나갈 수 있습니다.

### Source 고르기
드롭다운에서 방송 화면(`Output`) 외에 `Preview`, `MultiView`, 개별 입력 등을 고를 수 있습니다. 예를 들어 Output 2의 Source를 특정 카메라로 두면, 그 카메라 화면만 따로 다른 곳으로 보낼 수 있습니다.

### Overlays: 클린 피드 만들기
`All On`이면 오버레이 채널(자막, 로고 등)이 모두 얹힌 화면이 나가고, 드롭다운에서 오버레이를 끄면 **자막이 없는 "클린 피드"** 가 됩니다. 방송에는 자막을 넣고, 편집용 녹화본은 자막 없이 따로 남기고 싶을 때 가장 많이 쓰는 설정입니다.

[직접 경험] 예: "저는 Output 1은 자막 포함 송출용, Output 2는 오버레이를 끈 클린 피드로 NDI 녹화 PC에 보냅니다." 같은 실제 구성

## 3. NDI · OMT · SRT: 네트워크로 내보내기

각 Output 줄 오른쪽의 버튼을 `On`으로 바꾸면 그 화면이 네트워크로 나갑니다.

- **NDI**: 같은 내부망(LAN)의 다른 PC·장비에서 바로 입력으로 받을 수 있습니다. 녹화 PC, 다른 vMix·OBS, NDI 모니터로 보낼 때 씁니다.
- **OMT**: vMix 쪽에서 내놓은 개방형 IP 영상 전송 방식입니다. NDI처럼 내부망에서 영상을 주고받는 용도이며, 받는 쪽 장비·프로그램이 지원하는지 확인하고 쓰세요.
- **SRT**: 인터넷을 거쳐 멀리 보낼 때 쓰는 방식입니다. 패킷 손실에 강해 원격지 송출, 중계차·스튜디오 간 전송에 적합합니다.
- **톱니바퀴(⚙)**: NDI·SRT 세부 설정입니다. SRT는 여기서 Caller/Listener 모드, 주소·포트, 지연(Latency), 인코딩 품질을 정합니다.

> 네트워크 출력은 켤수록 CPU·GPU와 네트워크 부담이 늘어납니다. 실제로 받는 곳이 있는 출력만 켜 두세요.

## 4. Additional Outputs: 입력과 오디오를 따로 내보내기

- **Cameras / Calls / Audio Inputs**: 방송 화면이 아니라 **카메라, vMix Call 게스트, 오디오 입력 각각**을 NDI·OMT로 따로 내보냅니다. 다른 PC에서 카메라별 원본을 녹화하거나 다른 스위처에서 받아 쓸 때 유용합니다.
- **Audio Outputs**: vMix의 오디오 버스(Master, A~G)를 네트워크 오디오로 내보냅니다.

## 5. MultiView Layout: 감독용 모니터 화면

여러 입력과 프리뷰·프로그램을 한 화면에 모아 보는 **멀티뷰 화면의 배치**를 정합니다.

- **MultiView 1 / 2**: 서로 다른 배치의 멀티뷰를 두 개까지 만들어 둘 수 있습니다.
- 배치 버튼: 큰 화면 2개 + 작은 화면 여러 개, 작은 화면 격자, 4분할, 1화면 등에서 고릅니다. `Legacy`는 예전 버전 방식 배치입니다.
- **Customise Layout**: 칸마다 어떤 입력을 보여 줄지 직접 지정합니다.

만든 멀티뷰는 위의 Fullscreen이나 Output의 Source에서 `MultiView`를 골라 **감독 모니터나 NDI로 내보내면** 됩니다.

## 6. Show Advanced Settings

왼쪽 아래 체크박스를 켜면 출력별 해상도·프레임 등 추가 옵션이 나타납니다. 기본 설정으로 문제없이 돌아간다면 처음에는 건드리지 않는 편이 안전합니다.

## 자주 쓰는 구성 예시

| 목적 | 설정 |
| --- | --- |
| 유튜브 송출 + 녹화 | Output 1 = Output, Overlays All On |
| 자막 없는 편집용 녹화 | Output 2 = Output, Overlays 끔 → NDI On → 녹화 PC에서 수신 |
| 현장 스크린에 발표 자료만 | Fullscreen 1 = PPT 입력, Overlays 끔 |
| 감독 모니터 | Fullscreen 2 = MultiView |
| 원격지로 방송 화면 전송 | Output 1 또는 2 → SRT On → ⚙에서 주소·포트 설정 |

## 핵심 요약

- 이 화면은 **"무엇을 → 자막 포함 여부 → 어디로"** 를 줄마다 정하는 곳입니다.
- **Output 1은 녹화·송출의 기준**이므로 함부로 Source를 바꾸지 마세요.
- **Overlays를 끄면 클린 피드**가 되어 편집용 녹화에 좋습니다.
- 내부망은 **NDI(또는 OMT)**, 인터넷 너머는 **SRT**로 보냅니다.
- 멀티뷰는 여기서 배치를 정하고, Fullscreen·Output으로 내보내 감독 모니터로 씁니다.

## 자주 묻는 질문

**Q1. Output 1을 바꿨더니 유튜브에 다른 화면이 나가요.**
녹화와 송출은 Output 1의 Source를 따라갑니다. Output 1은 `Output`으로 두고, 다른 화면이 필요하면 Output 2~4를 쓰세요.

**Q2. NDI를 켰는데 다른 PC에서 안 보여요.**
두 PC가 같은 네트워크 대역인지, 윈도우 방화벽이 vMix와 NDI를 막고 있지 않은지 확인하세요. 와이파이보다 유선 기가비트 연결이 훨씬 안정적입니다.

**Q3. 방송에는 자막을 넣고, 녹화는 자막 없이 하고 싶어요.**
Output 2의 Source를 `Output`으로 두고 Overlays를 끈 뒤, 그 출력을 NDI로 다른 PC에서 녹화하거나 External Output으로 녹화 장비에 보내면 됩니다.
