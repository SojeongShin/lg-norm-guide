"""LENS (LG Employee Norm Support) - 문서 적재/청크/검색/생성 로직.

PRD 1안: 규범 문서 4종 전체를 청크 단위(출처 표기 포함)로 시스템 프롬프트에 적재하고
프롬프트 캐싱을 건다. 질의마다 선택 카테고리에서 상위 3개 청크를 검색(문자 bigram TF-IDF,
우선순위 가중치)해 '우선 참고 근거'로 함께 전달한다.
"""

from __future__ import annotations

import json
import math
import os
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

try:
    import anthropic
except ImportError:  # 브라우저(stlite) 배포본은 데모 모드 전용
    anthropic = None

BASE_DIR = Path(__file__).parent
CORPUS_DIR = BASE_DIR / "corpus"

MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-5-5")
EFFORT = os.environ.get("CLAUDE_EFFORT", "low")  # 시연 응답 시간(15초) 목표로 low 기본

CATEGORIES = {
    "anticorruption": "뇌물수수 및 부패방지 규정",
    "ethics": "윤리규범",
    "conduct": "행동강령",
    "tax": "세무 정책",
}
DEFAULT_ORDER = ["anticorruption", "ethics", "conduct", "tax"]
PRIORITY_WEIGHT = [1.3, 1.15, 1.05, 1.0]

DISCLAIMER = "본 답변은 규범 문서 기반 참고 자료이며 최종 판단은 담당 부서(준법사무국 등) 확인이 필요합니다."


@dataclass
class Chunk:
    id: str
    category: str
    citation: str  # PRD 표기 형식의 출처
    text: str
    summary_ko: str = ""  # 세무 정책(영문) 한글 요약
    tf: Counter = field(default_factory=Counter, repr=False)


# ---------------------------------------------------------------- 전처리 ---

NAV_TOKENS = {"목차", "들어가기에 앞서", "프린트", "앞장", "다음장", "이해관계자를 위한 가치창조", "LG전자(주)"}


def _clean_lines(text: str) -> list[str]:
    out = []
    for line in text.splitlines():
        s = line.strip()
        if not s:
            out.append("")
            continue
        if s in NAV_TOKENS or s.isdigit() or s.startswith("APCPCWM_"):
            continue
        if set(s.split()) <= NAV_TOKENS:  # "목차 들어가기에 앞서 프린트 앞장 다음장"
            continue
        if " : " in s and len(s) < 40:  # 행동강령 페이지 꼬리말 "고객에 대한 정직과 성실 : 제품 안전"
            continue
        out.append(s)
    return out


def _join(lines: list[str]) -> str:
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def _load_anticorruption() -> list[Chunk]:
    lines = _clean_lines((CORPUS_DIR / "anticorruption.txt").read_text(encoding="utf-8"))
    chunks: list[Chunk] = []
    cur_title, cur_lines, in_addenda = None, [], False

    def flush():
        if cur_title:
            chunks.append(Chunk(f"ac-{len(chunks)}", "anticorruption", cur_title, _join(cur_lines)))

    for s in lines:
        if s == "부칙":
            flush()
            cur_title, cur_lines, in_addenda = None, [], True
            continue
        if re.match(r"^제\s*\d+\s*장", s) or s in {"총", "칙"}:
            continue
        m = re.match(r"^제\s*(\d+)\s*조\s*\((.+?)\)", s)
        if m:
            flush()
            prefix = "부칙 " if in_addenda else ""
            cur_title = f"부패방지 규정 {prefix}제{m.group(1)}조({m.group(2)})"
            cur_lines = []
            continue
        cur_lines.append(s)
    flush()

    # 제4조 용어 정의 9개를 별도 청크로 분리
    art4 = next((c for c in chunks if c.citation.startswith("부패방지 규정 제4조")), None)
    if art4:
        parts = re.split(r"(?m)^(\d)\. (.+)$", art4.text)
        for i in range(1, len(parts) - 2, 3):
            num, term, body = parts[i], parts[i + 1].strip(), parts[i + 2]
            chunks.append(Chunk(f"ac-def{num}", "anticorruption",
                                f"부패방지 규정 제4조 {num}호({term})", f"{term}\n{body.strip()}"))
    return chunks


def _load_ethics() -> list[Chunk]:
    lines = _clean_lines((CORPUS_DIR / "ethics.txt").read_text(encoding="utf-8"))
    chunks: list[Chunk] = []
    chapter, title, buf = None, "윤리규범 전문", []

    def flush():
        if title and _join(buf):
            chunks.append(Chunk(f"et-{len(chunks)}", "ethics", title, _join(buf)))

    for s in lines:
        if s == "LG 윤리규범":
            continue
        m = re.match(r"^제(\d)장\s*(.+)$", s)
        if m:
            flush()
            chapter = f"제{m.group(1)}장"
            title, buf = f"윤리규범 {chapter} {m.group(2)}(총론)", []
            continue
        m = re.match(r"^(\d)\.\s*(.+)$", s)
        if m and chapter and len(s) < 25:
            flush()
            title, buf = f"윤리규범 {chapter} {m.group(1)}.{m.group(2)}", []
            continue
        buf.append(s)
    flush()
    return chunks


# 행동강령 항목별 인쇄 페이지 시작/끝 (PDF 쪽 = 인쇄 쪽 + 2)
CONDUCT_ITEMS = [
    ("들어가기에 앞서", 8, 9),
    ("신뢰할 수 있는 마케팅", 12, 14), ("제품 안전", 15, 17), ("제품규격", 18, 20),
    ("고객의 개인정보 보호", 21, 23),
    ("공평한 인사관리", 26, 28), ("상호 존중의 조직문화", 29, 31), ("건강하고 안전한 근무환경", 32, 35),
    ("경쟁 정보의 수집", 38, 40), ("제3자 정보의 올바른 사용", 41, 42), ("공정거래", 43, 44),
    ("경쟁사와의 관계", 45, 47), ("협력업체와의 관계", 48, 50), ("올바른 커뮤니케이션", 51, 53),
    ("타인 지적재산권의 존중", 54, 55), ("뇌물수수 금지", 56, 59),
    ("환경보호", 62, 64), ("국제거래질서의 존중", 65, 67),
    ("정보보안과 기밀 유지", 70, 72), ("회사 지적재산의 보호", 73, 75),
    ("정보통신수단 이용시 유의사항", 76, 78), ("기록 관리 및 보존", 79, 81),
    ("내부자 정보", 82, 84), ("공시", 85, 87),
]
CONDUCT_SUBHEADS = ["사례", "우리의 원칙", "기본지식", "정도의 실천", "유의사항", "바람직한 대처방식"]


def _load_conduct() -> list[Chunk]:
    pages = (CORPUS_DIR / "conduct.txt").read_text(encoding="utf-8").split("\f")
    chunks: list[Chunk] = []
    for item, start, end in CONDUCT_ITEMS:
        lines = _clean_lines("\n".join(pages[start + 1: end + 2]))
        sub, buf = "개요", []

        def flush():
            body = _join(buf)
            if body:
                chunks.append(Chunk(f"cd-{len(chunks)}", "conduct", f"행동강령 '{item}' > {sub}", body))

        for s in lines:
            if s in CONDUCT_SUBHEADS:
                flush()
                sub, buf = s, []
                continue
            buf.append(s)
        flush()
    return chunks


TAX_SECTIONS = [
    (r"^LG ELECTRONICS TAX POLICY", "Tax Policy 서문(Preamble)",
     "세무정책 서문: 사업 국가의 세법을 준수하고 사회적 의무를 다한다. 5가지 약속 - 세법 취지까지 이해·준수, "
     "가치창출에 따라 각 과세관할에 적정 세금 인식, 세무 정보 적시 작성·제출·보관, 유능한 세무 전문가 고용, "
     "복잡·불확실·중요한 세무 이슈는 외부 자문 적극 활용."),
    (r"^1\. Approach to tax risk", "Tax Policy 1. Approach to tax risk management and compliance",
     "세무 리스크 관리와 준수: 세무 신고의 무결성을 위한 정책·절차 수립, 내부 세무관리팀이 세무 리스크를 관리."),
    (r"^1\) Global Compliance", "Tax Policy 1-1) Global Compliance",
     "글로벌 준수: 각 사업 국가의 세법에 따라 신고·납부 의무를 이행하고 세무당국이 요구하는 자료를 제출."),
    (r"^2\) Transparent Trade", "Tax Policy 1-2) Transparent Trade",
     "투명한 거래: OECD 가이드라인에 따른 정상가격 원칙(arm's length principle) 기반의 투명한 이전가격 정책, "
     "각 과세관할에 적정 세금 납부. 해외 법인 간 거래가격, 이전가격."),
    (r"^2\. Perspective towards tax planning", "Tax Policy 2. Perspective towards tax planning",
     "세무 계획 관점: 조세회피처(tax haven)·저세율 등 조세회피 구조를 남용하지 않음, 신의성실 원칙, "
     "계열사 간 거래(내부거래)는 정상가격 원칙에 따라 수행. 세금 줄이기, 절세, 탈세."),
    (r"^3\. Affordable level", "Tax Policy 3. Affordable level of tax risk management",
     "감내 가능한 세무 리스크 수준: 중요한 세무 리스크를 식별·모니터링, 불명확하거나 논쟁적인 세법 이슈는 "
     "외부 세무 자문과 협력하고 세무당국과 협의."),
    (r"^4\. Attitude towards Tax Authorities", "Tax Policy 4. Attitude towards Tax Authorities",
     "세무당국에 대한 태도: 투명·정직·전문적으로 협력, 요청 시 글로벌 세무회계 책임자 통제하의 현지 회계 "
     "담당자를 통해 적시에 정보 제공."),
]


def _load_tax() -> list[Chunk]:
    lines = [l for l in (CORPUS_DIR / "tax.txt").read_text(encoding="utf-8").replace("\f", "\n").splitlines()]
    chunks: list[Chunk] = []
    idx, buf = None, []

    def flush():
        if idx is not None:
            _, cite, summ = TAX_SECTIONS[idx]
            chunks.append(Chunk(f"tx-{idx}", "tax", cite, _join(buf), summary_ko=summ))

    for line in lines:
        s = line.strip()
        hit = next((i for i, (pat, _, _) in enumerate(TAX_SECTIONS) if re.match(pat, s)), None)
        if hit is not None:
            flush()
            idx, buf = hit, ([] if hit else [s])
            continue
        if s:
            buf.append(s)
    flush()
    return chunks


# ---------------------------------------------------------------- 검색 ---

# 일상어 → 규범 문서 용어 (세무 정책은 영문이라 영어 키워드도 함께)
SYNONYMS = {
    "선물": "선물 접대 금품 뇌물 공정한 직무수행 이해관계자 금전적 이익",
    "명절": "선물 금품", "접대": "접대 향응 금품", "식사": "접대 향응",
    "통관": "통관 급행료 대리인 컨설턴트 뇌물", "컨설턴트": "대리인 외부전문가 급행료",
    "급행": "급행료", "공무원": "공직자", "기부": "기부금",
    "친척": "친인척 이해충돌 이해상충 특수관계", "가족": "친인척 이해충돌 이해상충",
    "지인": "이해충돌 특수관계", "협력사": "협력업체 거래선 선정",
    "미공개": "기밀 비밀 대외비 정보보안 내부자 정보", "일정": "기밀 정보보안",
    "기밀": "기밀 정보보안 영업비밀", "전 직장": "경쟁 정보 비밀유지", "동료": "정보보안 기밀",
    "세금": "세무 조세 tax", "법인 간": "계열사 intercompany arm length transparent trade 이전가격",
    "거래가격": "정상가격 arm length transfer pricing", "절세": "tax planning", "탈세": "tax evasion haven",
    "영수증": "증빙 영수증 회계서류 기록", "경비": "경비 증빙", "회식": "경비 접대",
    "기자": "공시 홍보부서 언론", "루머": "공시 소문", "이사회": "내부자 정보",
    "경쟁사": "경쟁사 담합 경쟁 정보", "가격": "가격 담합",
    "법인카드": "회사의 재산 무단사용 이해상충", "회사 돈": "회사의 재산 무단사용", "개인적": "개인의 이익 이해상충",
    "성희롱": "성희롱 괴롭힘 상호 존중", "괴롭힘": "괴롭힘 상호 존중 보고", "폭언": "괴롭힘 상호 존중",
    "차별": "차별 공평한 인사관리", "채용": "채용 공평한 인사관리", "승진": "진급 공평한 인사관리",
    "개인정보": "개인정보 고객의 개인정보 보호", "고객 정보": "고객의 개인정보 보호",
    "광고": "마케팅 광고 과장", "과장": "허위 과장 마케팅", "안전": "제품 안전 안전성",
    "주식": "내부자 정보 유가증권", "보복": "보복 인사부서 보고", "제보": "신고 신문고 보고",
    "폐기물": "환경보호 협력업체", "저작권": "지적재산권 라이선스", "특허": "지적재산 특허",
}


def expand_query(query: str) -> str:
    extra = [v for k, v in SYNONYMS.items() if k in query]
    return query + " " + " ".join(extra)


def _bigrams(text: str) -> Counter:
    s = re.sub(r"[^0-9A-Za-z가-힣]+", " ", text.lower())
    grams = Counter()
    for tok in s.split():
        if len(tok) == 1:
            continue
        grams.update(tok[i:i + 2] for i in range(len(tok) - 1))
    return grams


class Corpus:
    def __init__(self):
        self.chunks: list[Chunk] = (_load_anticorruption() + _load_ethics() + _load_conduct() + _load_tax())
        for c in self.chunks:
            # 출처(제목)는 가중치를 높이기 위해 3번 반영
            c.tf = _bigrams((c.citation + " ") * 3 + c.text + " " + c.summary_ko)
        n = len(self.chunks)
        df = Counter(g for c in self.chunks for g in c.tf)
        self.idf = {g: math.log((n + 1) / (d + 1)) + 1 for g, d in df.items()}
        self.norms = {c.id: math.sqrt(sum((tf * self.idf[g]) ** 2 for g, tf in c.tf.items())) or 1.0
                      for c in self.chunks}
        self._norm_cite = {_norm(c.citation): c for c in self.chunks}

    def by_category(self, cat: str) -> list[Chunk]:
        return [c for c in self.chunks if c.category == cat]

    def search(self, query: str, categories: list[str], k: int = 3) -> list[tuple[Chunk, float]]:
        q = _bigrams(expand_query(query))
        results = []
        for rank, cat in enumerate(categories):
            scored = []
            for c in self.by_category(cat):
                dot = sum(qtf * self.idf.get(g, 0) * c.tf.get(g, 0) * self.idf.get(g, 0) for g, qtf in q.items())
                if dot:
                    scored.append((c, dot / self.norms[c.id] * PRIORITY_WEIGHT[rank]))
            scored.sort(key=lambda x: -x[1])
            results.extend(scored[:k])
        return results

    def match_source(self, source: str) -> Chunk | None:
        """모델이 인용한 출처 문자열을 실제 청크와 대조 (원문 확인용)."""
        ns = _norm(source)
        if ns in self._norm_cite:
            return self._norm_cite[ns]
        for nc, c in sorted(self._norm_cite.items(), key=lambda x: -len(x[0])):
            if nc in ns or ns in nc:
                return c
        m = re.search(r"제\s*(\d+)\s*조\s*(\d+)\s*호", source)
        if m and "부패" in source:
            return next((c for c in self.chunks if c.citation.startswith(f"부패방지 규정 제{m.group(1)}조 {m.group(2)}호")), None)
        m = re.search(r"(부칙\s*)?제\s*(\d+)\s*조", source)
        if m and "부패" in source:
            pre = "부칙 " if m.group(1) else ""
            return next((c for c in self.chunks if c.citation.startswith(f"부패방지 규정 {pre}제{m.group(2)}조(")), None)
        m = re.search(r"['‘’\"]([^'‘’\"]+)['‘’\"]", source)
        if m and "행동강령" in source:
            item = m.group(1).strip()
            sub = next((s for s in CONDUCT_SUBHEADS if s in source), None)
            cands = [c for c in self.chunks if c.category == "conduct" and f"'{item}'" in c.citation]
            return next((c for c in cands if sub and c.citation.endswith(sub)), cands[0] if cands else None)
        m = re.search(r"제\s*(\d)\s*장\s*(\d)\.", source)
        if m and "윤리" in source:
            return next((c for c in self.chunks if c.citation.startswith(f"윤리규범 제{m.group(1)}장 {m.group(2)}.")), None)
        return None


def _norm(s: str) -> str:
    return re.sub(r"[\s'‘’\"“”·()（）]", "", s).replace("뇌물수수및", "")


# ---------------------------------------------------------------- 생성 ---

SYSTEM_RULES = """당신은 LG전자 임직원을 위한 '규범 가이드' 어시스턴트입니다. 직원이 자신의 상황을 설명하면, 아래 <규범문서>에 있는 조항만 근거로 지금 무엇을 해야 하는지 안내합니다.

# 답변 원칙
1. 답변은 <규범문서>에 제공된 청크 안에서만 생성한다. 청크에 없는 수치·금액 한도·기한·절차는 쓰지 않는다. 청탁금지법의 금액 기준(예: 3만/5만/10만 원)처럼 문서 밖 숫자를 끌어오지 않는다. 부패방지 규정은 금액 한도 없이 "소액이거나 합리적인 수준"으로만 정한다.
2. 카드의 sources에는 반드시 청크 머리글 [[출처: ...]]에 적힌 표기를 글자 그대로 복사해 넣는다. 존재하지 않는 조항을 만들지 않는다.
3. 사용자가 지정한 카테고리만, 지정한 우선순위 순서대로 카드를 만든다. 1순위 카테고리를 가장 자세히 다룬다.
4. 같은 주제를 두 문서가 다룰 때(뇌물·접대·선물은 부패방지 규정과 행동강령 모두에 있음) 부패방지 규정을 우선 인용하고 행동강령은 보조로 붙인다(부패방지 규정 제3조 4항: 규정이 하위 기준에 우선).
5. 보고·문의 경로는 문서에 적힌 대로만 안내한다: 부패방지 위반은 부서의 장 또는 신문고(부패방지 규정 제13조), 규정 해석·판단이 어려울 때는 준법사무국(부칙 제2조, 제11조 3항), 이해충돌은 관련 업무 배제 후 인사부서 또는 준법사무국 신고(제10조), 행동강령 일반 위반은 조직책임자 → Compliance Manager, 보복 우려는 인사부서, 경쟁정보·기밀 노출은 법무부서, 언론 문의는 홍보부서. 문서마다 경로가 다르면 문서별로 구분해 보여준다.
6. checklist는 3~5개의 짧은 명령문(예: "선물을 정중히 반환하세요")으로, 행동강령 '바람직한 대처방식' 문단의 톤을 따른다.
7. 세무 정책 관련 내용은 한국어로 쓰되 원문 섹션명을 영문으로 병기한다(예: 정상가격 원칙(Transparent Trade)).
8. 근거가 약하면 단정하지 않고 담당 부서 확인을 권한다.

# 근거가 없는 경우
- 선택된 카테고리 문서 어디에도 상황을 직접 다루는 조항이 없으면 has_basis=false로 하고, no_basis_message에 "명확하게 알 수 없음 - 규범 문서에 직접 규정이 없습니다. 담당 부서(예: 재무·회계팀) 문의를 권장합니다."와 같은 취지로 쓴다. 이때 조항을 억지로 끼워 맞추지 않는다. 세무 정책은 회사 차원의 조세 원칙 문서이며 개인 경비·영수증·증빙 처리 규정은 없다.
- 특정 카테고리만 관련 조항이 없으면 그 카드의 relevance를 "none"으로 하고 summary에 "이 문서에는 직접 관련된 조항이 없습니다"라고 쓰며 sources는 빈 배열로 둔다.

# 출력
지정된 JSON 스키마로만 답한다. situation_summary는 입력 상황을 한 줄로 재진술한다(예: "거래처로부터 고가 명절 선물을 받은 상황"). 후속 질문에도 같은 형식으로 답하되, 앞선 대화 맥락을 반영한다.
"""

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "situation_summary": {"type": "string"},
        "has_basis": {"type": "boolean"},
        "no_basis_message": {"type": "string"},
        "cards": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "category": {"type": "string", "enum": list(CATEGORIES)},
                    "relevance": {"type": "string", "enum": ["direct", "indirect", "none"]},
                    "clause_title": {"type": "string"},
                    "summary": {"type": "string"},
                    "action": {"type": "string"},
                    "sources": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["category", "relevance", "clause_title", "summary", "action", "sources"],
                "additionalProperties": False,
            },
        },
        "checklist": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["situation_summary", "has_basis", "no_basis_message", "cards", "checklist"],
    "additionalProperties": False,
}


def build_system(corpus: Corpus) -> list[dict]:
    parts = []
    for cat in DEFAULT_ORDER:
        body = []
        for c in corpus.by_category(cat):
            extra = f"\n(한글 요약: {c.summary_ko})" if c.summary_ko else ""
            body.append(f"[[출처: {c.citation}]]\n{c.text}{extra}")
        parts.append(f'<문서 category="{cat}" name="{CATEGORIES[cat]}">\n' + "\n\n".join(body) + "\n</문서>")
    docs = "<규범문서>\n" + "\n\n".join(parts) + "\n</규범문서>"
    # 규칙 + 문서 전체는 매 요청 동일 → 1시간 TTL 캐시로 비용·지연 절감
    return [{"type": "text", "text": SYSTEM_RULES + "\n\n" + docs,
             "cache_control": {"type": "ephemeral", "ttl": "1h"}}]


def build_user_turn(text: str, categories: list[str], retrieved: list[tuple[Chunk, float]], followup: bool) -> str:
    order = "\n".join(f"{i + 1}순위: {CATEGORIES[c]} (category={c})" for i, c in enumerate(categories))
    hits = "\n".join(f"- {c.citation}" for c, _ in retrieved) or "- (검색 결과 없음)"
    label = "후속 질문" if followup else "상황"
    return (f"<참고 카테고리_우선순위>\n{order}\n</참고 카테고리_우선순위>\n"
            f"<검색된_관련_청크 설명=\"키워드 검색 상위 결과. 우선 검토하되 더 적합한 조항이 문서에 있으면 그것을 인용\">\n"
            f"{hits}\n</검색된_관련_청크>\n<{label}>\n{text}\n</{label}>")


class GuideBot:
    def __init__(self, corpus: Corpus):
        self.corpus = corpus
        self._client = None  # 데모 모드에서는 생성하지 않음
        self.system = build_system(corpus)

    @property
    def client(self):
        if self._client is None:
            self._client = anthropic.Anthropic()
        return self._client

    def ask(self, history: list[dict], user_text: str, on_progress=None) -> tuple[dict, list[dict], object]:
        """history + 새 user 턴으로 호출. (파싱된 결과, assistant content 블록, usage) 반환."""
        messages = history + [{"role": "user", "content": user_text}]
        try:
            return self._call(messages, on_progress)
        except anthropic.BadRequestError:
            if not history:
                raise
            # 이전 턴의 사고 블록 재전송이 거부되면 텍스트만 남겨 재시도
            slim = [m if m["role"] == "user" else
                    {"role": "assistant", "content": [b for b in m["content"] if b.get("type") == "text"]}
                    for m in history]
            return self._call(slim + [{"role": "user", "content": user_text}], on_progress)

    def _call(self, messages, on_progress):
        with self.client.beta.messages.stream(
            model=MODEL,
            max_tokens=16000,
            system=self.system,
            messages=messages,
            output_config={"effort": EFFORT, "format": {"type": "json_schema", "schema": RESPONSE_SCHEMA}},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",  # 안전 분류기 거절 시 서버 측에서 권장 모델로 재시도
        ) as stream:
            n = 0
            for text in stream.text_stream:
                n += len(text)
                if on_progress:
                    on_progress(n)
            msg = stream.get_final_message()

        if msg.stop_reason == "refusal":
            raise RuntimeError("모델이 이 요청에 대한 답변을 거절했습니다. 표현을 바꿔 다시 시도해 주세요.")
        if msg.stop_reason == "max_tokens":
            raise RuntimeError("답변이 너무 길어 중간에 잘렸습니다. 상황을 조금 더 짧게 입력해 주세요.")
        text = next((b.text for b in msg.content if b.type == "text"), "")
        data = json.loads(text)
        content = [b.model_dump(exclude_none=True) for b in msg.content]
        return data, content, msg.usage
