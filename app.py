"""LG 규범 가이드 챗봇 - Streamlit 단일 화면.

실행: streamlit run app.py
ANTHROPIC_API_KEY가 없으면 데모 모드(API 미사용)로 동작한다.
"""

import html
import os
import sys
import time

import streamlit as st

try:
    import anthropic
except ImportError:  # 브라우저(stlite) 배포본은 데모 모드 전용
    anthropic = None

import demo
import rag

st.set_page_config(page_title="LG 규범 가이드", page_icon="⚖️", layout="wide")

CAT_COLOR = {"anticorruption": "#A50034", "ethics": "#5B4BD6", "conduct": "#D9730D", "tax": "#0F7B8A"}

SAMPLES = [
    ("🎁 명절 고가 선물", "거래처 담당자가 명절에 20만 원 상당의 고가 선물을 집으로 보냈어요. 받아도 되나요?",
     ["anticorruption", "ethics", "conduct"]),
    ("🛃 통관 급행료", "해외 통관이 몇 주째 막혀 있는데, '통관 컨설턴트'라는 사람이 소액만 주면 내일 바로 풀어준다고 합니다.",
     ["anticorruption", "conduct"]),
    ("💱 법인 간 거래가격", "해외 법인 간 거래가격을 세금을 줄이는 쪽으로 조정하자는 제안을 받았습니다.",
     ["tax", "ethics"]),
    ("🔒 미공개 제품 일정", "전 직장 동료가 우리 회사 미공개 제품의 출시 일정을 물어봅니다.",
     ["conduct", "ethics"]),
    ("🤝 친척 회사 지원", "제가 협력사 선정 심사를 맡았는데, 친척이 운영하는 회사가 지원했습니다.",
     ["ethics", "anticorruption", "conduct"]),
    ("🧾 영수증 분실 (규정 없음)", "팀 회식비를 개인 카드로 결제했는데 영수증을 잃어버렸어요. 어떻게 처리하나요?",
     ["tax"]),
]

st.markdown("""
<style>
.block-container {padding-top: 2rem; padding-bottom: 5rem;}
.norm-card {border:1px solid #e6e6e6; border-left:6px solid var(--c); border-radius:10px;
            padding:14px 18px; margin:10px 0; background:var(--bg, #fff);}
.norm-card.none {opacity:.65}
.badge {display:inline-block; padding:2px 10px; border-radius:999px; color:#fff; font-size:.78rem;
        font-weight:600; background:var(--c); margin-right:6px}
.rel {font-size:.75rem; color:#666; border:1px solid #ccc; border-radius:999px; padding:1px 8px}
.clause {font-size:1.08rem; font-weight:700; margin:8px 0 4px}
.label {font-size:.78rem; font-weight:700; color:#666; margin-top:8px}
.action {background:#fff6f8; border-radius:8px; padding:8px 12px; margin-top:4px}
.summary-line {font-size:1.05rem; padding:10px 14px; background:#f4f4f6; border-radius:8px; margin:6px 0 4px}
.disclaimer-bar {position:fixed; left:0; right:0; bottom:0; z-index:999; background:#2b2b2b; color:#fff;
                 font-size:.82rem; text-align:center; padding:7px 12px}
@media (prefers-color-scheme: dark) {
  .norm-card {border-color:#333; --bg:#1b1b1f} .summary-line {background:#26262b}
  .action {background:#3a1f28} .label, .rel {color:#aaa}
}
</style>
""", unsafe_allow_html=True)
st.markdown(f'<div class="disclaimer-bar">⚠️ {rag.DISCLAIMER}</div>', unsafe_allow_html=True)


@st.cache_resource
def load_bot():
    return rag.GuideBot(rag.Corpus())


bot = load_bot()
corpus = bot.corpus

ss = st.session_state
ss.setdefault("turns", [])     # [{"question", "result", "retrieved", "meta"}]
ss.setdefault("history", [])   # Claude messages (user/assistant 교대)
ss.setdefault("active_cats", [])
ss.setdefault("situation", "")
ss.setdefault("cats", [])


def apply_sample(i):
    _, text, cats = SAMPLES[i]
    ss.situation, ss.cats = text, list(cats)


def reset():
    ss.turns, ss.history, ss.active_cats = [], [], []


# ---------------------------------------------------------------- 사이드바 ---
with st.sidebar:
    st.subheader("📚 규범 문서 4종")
    for cat, name in rag.CATEGORIES.items():
        st.markdown(f"<span class='badge' style='--c:{CAT_COLOR[cat]}'>{name}</span> "
                    f"{len(corpus.by_category(cat))}개 청크", unsafe_allow_html=True)
    st.caption("부패방지 규정(2024.6 개정) · 윤리규범 · 행동강령(2011) · Tax Policy(2022)")
    st.divider()
    has_key = anthropic is not None and bool(os.environ.get("ANTHROPIC_API_KEY"))
    st.toggle("데모 모드 (API 미사용·무료)", key="demo_mode", value=True,
              help="샘플 6개는 미리 작성된 답변, 그 외 입력은 검색된 조항 원문을 보여줍니다. "
                   "끄면 Claude API를 호출합니다(유료).")
    if not has_key:
        st.caption("ANTHROPIC_API_KEY가 없어 데모 모드로만 동작합니다.")
    st.caption(f"모델: `{rag.MODEL}` · effort: `{rag.EFFORT}`")
    st.caption("문서 전체를 시스템 프롬프트에 적재(프롬프트 캐싱) + 카테고리별 상위 3개 청크 검색")
    st.button("🔄 새 상담 시작", on_click=reset)

# ---------------------------------------------------------------- 입력 ---
st.title("⚖️ LG 규범 가이드")
st.markdown("내 상황을 말하면 **행동강령 · 윤리규범 · 부패방지 규정 · 세무 정책**에서 해당 조항을 찾아 "
            "**지금 어떻게 해야 하는지** 알려드립니다.")

st.markdown("**샘플 상황** (클릭하면 입력창과 우선순위가 채워집니다)")
cols = st.columns(len(SAMPLES))
for i, (label, _, _) in enumerate(SAMPLES):
    cols[i].button(label, key=f"s{i}", on_click=apply_sample, args=(i,))

left, right = st.columns([3, 2])
with left:
    st.text_area("나의 상황", key="situation", height=120,
                 placeholder="예: 거래처 담당자가 명절에 20만 원 상당의 선물을 보냈어요")
with right:
    st.multiselect("참고할 규범 (선택한 순서 = 우선순위)", options=list(rag.CATEGORIES),
                   format_func=lambda c: rag.CATEGORIES[c], key="cats",
                   help="미선택 시 4종 전체를 기본 순서로 참고합니다. 순서를 바꾸려면 지웠다가 다시 선택하세요.")
    chosen = ss.cats or rag.DEFAULT_ORDER
    st.markdown(" ".join(f"<span class='badge' style='--c:{CAT_COLOR[c]}'>{i + 1}순위 · {rag.CATEGORIES[c]}</span>"
                         for i, c in enumerate(chosen)), unsafe_allow_html=True)
    submit = st.button("🔍 규범 확인하기", type="primary")


# ---------------------------------------------------------------- 처리 ---
def run_query(question: str, followup: bool):
    cats = ss.active_cats
    retrieved = corpus.search(question if not followup else ss.turns[0]["question"] + " " + question, cats)
    user_turn = rag.build_user_turn(question, cats, retrieved, followup)
    status = st.empty()
    t0 = time.time()

    def run_demo(note=""):
        with st.spinner("관련 조항을 검색하고 분석하는 중…"):
            if sys.platform != "emscripten":  # 브라우저(Pyodide)에서는 대기 생략
                time.sleep(1.2)
            result = demo.answer(corpus, question, [s[1] for s in SAMPLES], cats, retrieved, followup)
        ss.turns.append({"question": question, "result": result, "retrieved": retrieved, "followup": followup,
                         "meta": f"🧪 데모 모드 · API 미호출 (샘플은 사전 작성 답변, 그 외는 검색 결과){note}"})

    if ss.demo_mode or not has_key:
        run_demo()
        return

    def progress(n):
        status.info(f"⏳ 조항을 대조해 답변을 작성하는 중… ({n:,}자 생성, {time.time() - t0:.0f}초)")

    status.info("⏳ 관련 조항을 검색하고 분석하는 중…")
    try:
        result, content, usage = bot.ask(ss.history, user_turn, progress)
    except anthropic.AuthenticationError:
        status.empty()
        run_demo(" · ⚠ API 키가 올바르지 않아 데모 답변으로 대체")
        return
    except anthropic.RateLimitError:
        status.error("요청이 많아 잠시 제한되었습니다. 잠시 후 다시 시도해 주세요.")
        return
    except anthropic.APIConnectionError:
        status.error("네트워크 오류로 Claude API에 연결하지 못했습니다.")
        return
    except anthropic.APIStatusError as e:
        status.error(f"API 오류 ({e.status_code}): {e.message}")
        return
    except Exception as e:  # 파싱 실패·거절 등
        status.error(f"답변 생성 실패: {e}")
        return
    status.empty()
    ss.history += [{"role": "user", "content": user_turn}, {"role": "assistant", "content": content}]
    cache_read = getattr(usage, "cache_read_input_tokens", 0) or 0
    ss.turns.append({"question": question, "result": result, "retrieved": retrieved, "followup": followup,
                     "meta": f"응답 {time.time() - t0:.1f}초 · 캐시 읽기 {cache_read:,} 토큰 · "
                             f"입력 {usage.input_tokens:,} · 출력 {usage.output_tokens:,}"})


if submit:
    if not ss.situation.strip():
        st.warning("상황을 입력해 주세요.")
    else:
        reset()
        ss.active_cats = list(chosen)
        run_query(ss.situation.strip(), followup=False)


# ---------------------------------------------------------------- 결과 ---
def render_source(src: str, key: str):
    chunk = corpus.match_source(src)
    if chunk:
        with st.expander(f"📄 {src}  ✓ 원문 대조됨"):
            st.caption(f"원문 출처: {chunk.citation}")
            st.text(chunk.text)
            if chunk.summary_ko:
                st.caption(f"한글 요약: {chunk.summary_ko}")
    else:
        st.markdown(f"<span class='rel'>📄 {html.escape(src)} · ⚠ 원문 자동 대조 실패 – 직접 확인 필요</span>",
                    unsafe_allow_html=True)


def render_turn(ti: int, turn: dict):
    r = turn["result"]
    if turn["followup"]:
        st.markdown(f"#### 💬 후속 질문: {html.escape(turn['question'])}")
    st.markdown(f"<div class='summary-line'>📝 <b>상황 요약</b> · {html.escape(r['situation_summary'])}</div>",
                unsafe_allow_html=True)
    st.caption(turn["meta"])

    if not r["has_basis"]:
        st.warning(f"**명확하게 알 수 없음** — {r['no_basis_message']}")

    order = {c: i for i, c in enumerate(ss.active_cats)}
    cards = sorted(r["cards"], key=lambda c: order.get(c["category"], 99))
    for ci, c in enumerate(cards):
        color = CAT_COLOR.get(c["category"], "#888")
        rank = order.get(c["category"])
        rank_txt = f"{rank + 1}순위 · " if rank is not None else ""
        rel = {"direct": "직접 관련", "indirect": "간접 관련", "none": "관련 조항 없음"}[c["relevance"]]
        none_cls = " none" if c["relevance"] == "none" else ""
        action = (f"<div class='label'>✅ 이 상황에서의 대처</div><div class='action'>{html.escape(c['action'])}</div>"
                  if c["action"].strip() and c["relevance"] != "none" else "")
        st.markdown(
            f"<div class='norm-card{none_cls}' style='--c:{color}'>"
            f"<span class='badge' style='--c:{color}'>{rank_txt}{rag.CATEGORIES.get(c['category'], c['category'])}</span>"
            f"<span class='rel'>{rel}</span>"
            f"<div class='clause'>{html.escape(c['clause_title'])}</div>"
            f"<div class='label'>핵심 내용</div><div>{html.escape(c['summary'])}</div>{action}</div>",
            unsafe_allow_html=True)
        for si, src in enumerate(c["sources"]):
            render_source(src, f"{ti}-{ci}-{si}")

    if r["checklist"]:
        st.markdown("##### 🧭 지금 해야 할 행동")
        for i, item in enumerate(r["checklist"]):
            st.checkbox(item, key=f"chk-{ti}-{i}")

    with st.expander("🔎 검색된 근거 조항 (카테고리별 상위 3개, 우선순위 가중치 반영)"):
        for ch, score in turn["retrieved"]:
            st.markdown(f"- `{score:.2f}` {ch.citation}")


if ss.turns:
    st.divider()
    st.subheader("📋 결과")
    for ti, turn in enumerate(ss.turns):
        render_turn(ti, turn)
        if ti < len(ss.turns) - 1:
            st.divider()

    follow = st.chat_input("후속 질문을 입력하세요 (예: 이미 받아버렸으면 어떻게 하나요?)")
    if follow:
        run_query(follow, followup=True)
        st.rerun()
