# vMix 강의 시리즈 작성 브리프 (서브에이전트용)

Source outline: `drafts/vMix 강의 주제 20개.md` (read it first; each numbered section is one post).
Blog: https://warrendc50-gif.github.io · author is an experienced vMix/broadcast-audio engineer and office worker.
Today: 2026-10-07. Do NOT commit or touch git. Write ONLY the JSON files assigned to you.

## Series slugs, titles, dates (use exactly)

| N | slug | date (UTC) |
|---|---|---|
| 1 | vmix-lecture-01-first-setup | 2026-10-07T14:00:00+00:00 |
| 2 | vmix-lecture-02-input-sources | 2026-10-07T14:05:00+00:00 |
| 3 | vmix-lecture-03-audio-mixer | 2026-10-07T14:10:00+00:00 |
| 4 | vmix-lecture-04-transitions-switching | 2026-10-07T14:15:00+00:00 |
| 5 | vmix-lecture-05-gt-title-designer | 2026-10-07T14:20:00+00:00 |
| 6 | vmix-lecture-06-overlay-multiview-layout | 2026-10-07T14:25:00+00:00 |
| 7 | vmix-lecture-07-outputs-streaming | 2026-10-07T14:30:00+00:00 |
| 8 | vmix-lecture-08-recording-strategy | 2026-10-07T14:35:00+00:00 |
| 9 | vmix-lecture-09-ndi | 2026-10-07T14:40:00+00:00 |
| 10 | vmix-lecture-10-srt | 2026-10-07T14:45:00+00:00 |
| 11 | vmix-lecture-11-vmix-call | 2026-10-07T14:50:00+00:00 |
| 12 | vmix-lecture-12-instant-replay | 2026-10-07T14:55:00+00:00 |
| 13 | vmix-lecture-13-shortcuts-control-surfaces | 2026-10-07T15:00:00+00:00 |
| 14 | vmix-lecture-14-triggers-scripting-api | 2026-10-07T15:05:00+00:00 |
| 15 | vmix-lecture-15-chroma-key-virtual-sets | 2026-10-07T15:10:00+00:00 |
| 16 | vmix-lecture-16-lecture-seminar-church-package | 2026-10-07T15:15:00+00:00 |
| 17 | vmix-lecture-17-performance-troubleshooting | 2026-10-07T15:20:00+00:00 |
| 18 | vmix-lecture-18-presets-redundancy | 2026-10-07T15:25:00+00:00 |
| 19 | vmix-lecture-19-multi-platform-vertical | 2026-10-07T15:30:00+00:00 |
| 20 | vmix-lecture-20-live-operations-checklist | 2026-10-07T15:35:00+00:00 |

Post URL pattern: `https://warrendc50-gif.github.io/posts/<slug>/`

Title format: `vMix 강의 N편 | <outline 제목>` — e.g. `vMix 강의 3편 | vMix 오디오 믹서 완전 정복: 게인, 버스, EQ, 컴프레서`. Keep under 70 chars; shorten the outline title if needed.

## File format

Write `content/posts/2026-10-07_<slug>.json` with Python (`json.dump(..., ensure_ascii=False, indent=2)` + trailing newline), keys exactly:
```
{"title", "slug", "description" (≤150자), "tags" (5–6, always include "vMix" and "vMix강의"),
 "topic": "vMix 강의 시리즈 N편: <짧은 주제>", "category": "broadcast", "date", "products": [], "body_markdown"}
```

## Writing rules

- Korean, 합니다체, first person 저 where natural. The author teaches from experience: write as a practitioner, not a manual. No emoji, no clickbait, no "# Title" heading in the body.
- Length: 3,000–4,500 Korean characters of body (not counting links). Expand the outline: every 목차 item becomes a `##` or `###` section with concrete steps (which window/tab/option in vMix), why it matters, and what goes wrong. Keep the outline's 실습 and 자주 하는 실수 as their own sections (`## 실습 과제`, `## 자주 하는 실수`). Do NOT include the `▶ 현장 메모` placeholder.
- Open with 2–3 sentences: what the reader can do after this lesson, then one line `이 글은 vMix 강의 시리즈 N편입니다. 이전 편: [제목](url) · 다음 편: [제목](url)` (omit 이전 for N=1, 다음 for N=20). Use the slugs table for URLs and the outline titles for link text.
- End with `## 핵심 요약` (3–5 bullets) and `## FAQ` (2–3 Q&A), then a final line: `질문이나 다른 현장 경험은 [Threads](https://www.threads.net/@warrendc502026)로 알려 주세요. 다음 편에 반영하겠습니다.`
- Accuracy: use real vMix UI names (Settings → Display, Audio Mixer, Overlay 1–4, GT Title Designer, Multi View, Shortcuts, Triggers, Activators, Data Sources, MultiCorder, Instant Replay, vMix Call, Second Recorder, Fault Tolerant, New File Every, Web Controller, Virtual Sets…). If unsure about an option name or an edition limit, verify in the vMix 29 user guide. **WebFetch on www.vmix.com redirect-loops; fetch with Bash instead:**
  `curl -sL -A "Mozilla/5.0" https://www.vmix.com/help29/<Page>.html | python -c "import re,html,sys;t=sys.stdin.buffer.read().decode('utf-8','ignore');t=re.sub(r'<script.*?</script>|<style.*?</style>','',t,flags=re.S);t=re.sub(r'<[^>]+>',' ',t);print(html.unescape(re.sub(r'\s+',' ',t))[:6000])"`
  Useful pages: Setup.html (recording setup), Settings.html, Display.html, Performance.html, AudioMixer.html, Outputs.html, Streaming.html, StreamingQuality.html, Overlay.html, MultiView.html, Titles.html, GTTitleDesigner.html, DataSources.html, Shortcuts.html, Triggers.html, Activators.html, Scripting.html, NDI.html, SRT.html, vMixCall.html, InstantReplay.html, MultiCorder.html, VirtualSets.html, ChromaKey.html, PowerPoint.html, WebController.html, Presets.html, FaultTolerantRecordings.html, SecondRecorder.html, vMixVideoCodec.html. Page names are guesses: if one 404s, open https://www.vmix.com/help29/ index with the same curl and find the right name. Edition comparison: https://www.vmix.com/software/pricing.aspx (same curl).
  Never invent numbers (bitrates, limits, prices). If you can't verify, phrase generally ("에디션에 따라 다릅니다. 구매 페이지에서 확인하세요").
- Internal links: where the outline lists 관련 글, link them in context (not just at the end). Posts 7, 8, 10 overlap with existing posts (vMix Output 설정, vMix 녹화 화질·용량, SRT 장비 비교): summarize and link rather than repeating; spend the words on the lecture angle (how to teach/practice it).
- Where a short table helps (comparisons, settings), use one.

## Final report

For each post: title, body length (Korean chars), and any vMix fact you could not verify (so the author can double-check before publishing).
