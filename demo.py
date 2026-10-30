"""데모 모드 (API 미사용).

- 샘플 상황 6개: PDF 원문 조항을 근거로 미리 작성한 답변을 반환
- 그 외 입력: Claude 호출 없이 검색된 조항 원문을 카드로 반환
"""

import rag

C_INTRO = "행동강령 '들어가기에 앞서' > 개요"

CANNED = [
    {  # 1. 명절 고가 선물
        "situation_summary": "거래처 담당자로부터 20만 원 상당의 고가 명절 선물을 받은 상황",
        "has_basis": True, "no_basis_message": "",
        "cards": [
            {"category": "anticorruption", "relevance": "direct",
             "clause_title": "제5조 원칙적 금지 · 제6조 선물 및 접대",
             "summary": "임직원은 부정한 사업상 이익을 목적으로 금품 등을 수수하거나 요구해서는 안 됩니다(제5조). "
                        "선물·접대는 소액이거나 합리적인 수준이어야 하고, 호화롭거나 관련 상황에 비추어 이례적인 수준, "
                        "공개될 경우 난처할 수 있는 선물은 허용되지 않습니다. 주는 쪽과 받는 쪽 모두 뇌물로 의도하지 "
                        "않았더라도 뇌물 목적으로 간주될 수 있습니다(제6조 2항). 규정은 금액 한도를 따로 두지 않습니다.",
             "action": "거래 관계에 있는 담당자가 보낸 고가 선물은 '소액·합리적 수준'을 넘어 부정한 대가로 오해받을 수 "
                       "있으므로 받지 말고 반환하세요. 위반이 의심되면 부서의 장 또는 신문고에 알리고(제13조), "
                       "허용 여부 판단이 어려우면 준법사무국의 해석을 받으세요(부칙 제2조).",
             "sources": ["부패방지 규정 제5조(원칙적 금지)", "부패방지 규정 제6조(선물 및 접대)",
                         "부패방지 규정 제13조(위반행위에 대한 신고)", "부패방지 규정 부칙 제2조(해석)"]},
            {"category": "ethics", "relevance": "direct",
             "clause_title": "제4장 4. 공정한 직무수행",
             "summary": "직무와 관련하여 판단의 공정성을 저해할 수 있는 어떠한 형태의 금전적 이익도 이해관계자로부터 "
                        "취하지 않는다.",
             "action": "거래처는 직무상 이해관계자이므로, 선물을 받는 것 자체가 판단의 공정성을 해칠 수 있습니다. "
                       "받지 않는 것이 원칙입니다.",
             "sources": ["윤리규범 제4장 4.공정한 직무수행"]},
            {"category": "conduct", "relevance": "indirect",
             "clause_title": "'뇌물수수 금지' · 위반 보고 경로",
             "summary": "'유가물'에는 선물·식사·접대가 모두 포함되며, 허용되는 것은 소액의 판촉물과 누가 보더라도 "
                        "합리적인 수준의 식사·접대뿐입니다. 행동강령 위반이 의심되면 조직책임자와 먼저 상의하고, "
                        "해결되지 않으면 Compliance Manager에게 보고합니다.",
             "action": "부패방지 규정(상위 규정)을 우선 따르고, 처리 과정은 조직책임자와 공유하세요.",
             "sources": ["행동강령 '뇌물수수 금지' > 정도의 실천", C_INTRO]},
        ],
        "checklist": ["선물을 받지 말고 정중히 반환하세요",
                      "받은 사실과 반환 내역을 기록으로 남기세요",
                      "부서의 장에게 알리세요 (위반 의심 시 신문고 신고 가능)",
                      "허용 여부가 애매하면 준법사무국에 문의하세요"],
    },
    {  # 2. 통관 급행료
        "situation_summary": "통관 지연 중 '통관 컨설턴트'가 소액 지급을 조건으로 신속 통관을 제안한 상황",
        "has_basis": True, "no_basis_message": "",
        "cards": [
            {"category": "anticorruption", "relevance": "direct",
             "clause_title": "제4조 7호 급행료 · 제8조 급행료 금지 · 제5조 제3자를 통한 제공 금지",
             "summary": "급행료는 통관·비자 발급 같은 일상적 조치를 보장받거나 촉진하기 위해 공무원 또는 담당자에게 "
                        "제공하는 상대적으로 적은 규모의 금품입니다(제4조 7호). 대부분의 국가에서 뇌물로 간주되므로 "
                        "회사는 급행료 지급을 원칙적으로 금지합니다(제8조). 직접이든 제3자를 통해서든 공직자 등에게 "
                        "금품을 제공·제안·약속하는 행위도 금지됩니다(제5조).",
             "action": "'소액이면 내일 풀어준다'는 제안은 컨설턴트를 통한 급행료 지급에 해당할 수 있으므로 거절하세요. "
                       "이런 제안을 받은 사실은 부서의 장 또는 신문고에 신고하세요(제13조).",
             "sources": ["부패방지 규정 제4조 7호(급행료)", "부패방지 규정 제8조(급행료)",
                         "부패방지 규정 제5조(원칙적 금지)", "부패방지 규정 제13조(위반행위에 대한 신고)"]},
            {"category": "conduct", "relevance": "direct",
             "clause_title": "'뇌물수수 금지' (동일 사례)",
             "summary": "행동강령에 같은 사례가 실려 있습니다. 외부 브로커·컨설턴트 등 제3자가 회사 이익을 위해 뇌물을 "
                        "공여해도 회사가 책임을 집니다. 컨설턴트가 담당공직자의 지인이라는 것 외에 별다른 자격이 없거나, "
                        "과도한 수임료·현금 등 추적 불가능한 지급을 요구하면 부정한 방법을 의심해야 합니다.",
             "action": "해당 컨설턴트를 선임하지 마세요. 통관 서류·절차에 의문이 있으면 조직책임자나 수출입업무 "
                       "담당자에게 조언을 구하세요.",
             "sources": ["행동강령 '뇌물수수 금지' > 사례", "행동강령 '뇌물수수 금지' > 바람직한 대처방식",
                         "행동강령 '뇌물수수 금지' > 유의사항", "행동강령 '국제거래질서의 존중' > 정도의 실천"]},
        ],
        "checklist": ["컨설턴트의 '소액 지급' 제안을 거절하세요",
                      "정식 절차로 통관 지연 사유를 확인하도록 수출입업무 담당자와 상의하세요",
                      "제안받은 사실을 부서의 장 또는 신문고에 신고하세요",
                      "외부전문가 선임 시 공직자와의 특수관계·보수의 합리성을 확인하세요"],
    },
    {  # 3. 법인 간 거래가격
        "situation_summary": "세금을 줄이기 위해 해외 법인 간 거래가격을 조정하자는 제안을 받은 상황",
        "has_basis": True, "no_basis_message": "",
        "cards": [
            {"category": "tax", "relevance": "direct",
             "clause_title": "정상가격 원칙(Transparent Trade) · 세무 계획 관점(Perspective towards tax planning)",
             "summary": "회사는 OECD 가이드라인을 따르는 정상가격 원칙(arm's length principle)에 기반한 투명한 가격 정책을 "
                        "수립하고, 사업이 이루어지는 각 과세관할에 적정한 세금을 납부합니다(1-2). LG 계열사 간 거래는 "
                        "정상가격 원칙에 따라 수행하며, 조세회피처(tax haven)·저세율 등 조세회피 구조를 남용하지 "
                        "않습니다(2).",
             "action": "세금 감소를 목적으로 정상가격에서 벗어나게 거래가격을 조정하는 것은 회사 세무 정책에 반하므로 "
                       "따르지 마세요. 내부 세무관리팀(1. Approach to tax risk management)과 상의하고, 불명확하거나 "
                       "중요한 이슈는 외부 세무 자문을 활용하세요(3. Affordable level of tax risk management).",
             "sources": ["Tax Policy 1-2) Transparent Trade", "Tax Policy 2. Perspective towards tax planning",
                         "Tax Policy 1. Approach to tax risk management and compliance",
                         "Tax Policy 3. Affordable level of tax risk management"]},
            {"category": "ethics", "relevance": "direct",
             "clause_title": "제6장 3. 사회발전에 기여 · 제2장 2. 법규의 준수",
             "summary": "고용의 창출과 조세의 성실한 납부로 국가발전에 기여한다. 국내외 모든 사업활동은 해당 국가의 "
                        "제반 법규를 준수하여 수행한다.",
             "action": "조세를 성실히 납부하는 것이 윤리규범상 회사의 책임입니다. 제안에 동의하지 마세요.",
             "sources": ["윤리규범 제6장 3.사회발전에 기여", "윤리규범 제2장 2.법규의 준수"]},
        ],
        "checklist": ["세금 감소 목적의 가격 조정안에 동의하거나 실행하지 마세요",
                      "거래가격이 정상가격 원칙에 맞는지 근거를 확인하세요",
                      "내부 세무관리팀과 상의하세요",
                      "판단이 어려운 중요 이슈는 외부 세무 자문을 받으세요"],
    },
    {  # 4. 미공개 제품 일정
        "situation_summary": "전 직장 동료가 회사의 미공개 제품 출시 일정을 문의한 상황",
        "has_basis": True, "no_basis_message": "",
        "cards": [
            {"category": "conduct", "relevance": "direct",
             "clause_title": "'정보보안과 기밀 유지'",
             "summary": "일상 업무에서 발생하는 모든 산출물은 일차적으로 '대외비'로 분류되며, 사외에 공유하려면 "
                        "정보보안 담당자의 승인과 적절한 법적 보호조치가 필요합니다. 회사기밀이나 업무와 관련된 민감한 "
                        "정보는 친구나 가족에게도 발설하면 안 됩니다.",
             "action": "미공개 제품 일정은 사외 공유 대상이 아니므로 답하지 마세요. 의문사항이 있으면 조직책임자나 "
                       "정보보안 담당자와 상의하세요.",
             "sources": ["행동강령 '정보보안과 기밀 유지' > 기본지식", "행동강령 '정보보안과 기밀 유지' > 정도의 실천",
                         "행동강령 '정보보안과 기밀 유지' > 바람직한 대처방식"]},
            {"category": "ethics", "relevance": "direct",
             "clause_title": "제4장 2. 사명의 완수",
             "summary": "회사의 재산을 잘 유지관리하고, 업무상 취득한 회사의 비밀을 보호한다.",
             "action": "친분과 관계없이 업무상 알게 된 회사 비밀을 지키는 것이 임직원의 기본 의무입니다.",
             "sources": ["윤리규범 제4장 2.사명의 완수"]},
        ],
        "checklist": ["미공개 일정에 대해 답하지 마세요",
                      "회사 기밀이라 공유할 수 없다고 정중히 밝히세요",
                      "메신저·이메일 등 어떤 경로로도 공유하지 마세요",
                      "요청이 반복되거나 의심스러우면 조직책임자·정보보안 담당자와 상의하세요"],
    },
    {  # 5. 친척 회사 지원
        "situation_summary": "본인이 맡은 협력사 선정 심사에 친척이 운영하는 회사가 지원한 상황",
        "has_basis": True, "no_basis_message": "",
        "cards": [
            {"category": "ethics", "relevance": "direct",
             "clause_title": "제4장 5. 회사와의 이해상충 회피 · 제3장 1. 평등한 기회",
             "summary": "회사와 개인의 이해가 상충되는 어떠한 행위나 관계도 회피한다. 거래선 등록 및 선정은 객관적이고 "
                        "공정한 심사기준에 따라 합리적인 방법으로 수행한다.",
             "action": "친척 회사에 대한 심사는 이해상충 관계에 해당하므로 직접 맡지 마세요.",
             "sources": ["윤리규범 제4장 5.회사와의 이해상충 회피", "윤리규범 제3장 1.평등한 기회"]},
            {"category": "anticorruption", "relevance": "direct",
             "clause_title": "제10조 이해충돌 등",
             "summary": "임직원이 거래상대방의 주요임원과 친인척 관계인 경우 등은 이해충돌에 해당합니다. 이해충돌이 "
                        "불가피하면 원칙적으로 관련 업무에서 배제되어야 하며, 인사부서 또는 준법사무국에 신고한 뒤 "
                        "회사의 결정에 따라야 합니다.",
             "action": "심사 업무에서 빠지고, 인사부서 또는 준법사무국에 이해충돌 사실을 신고하세요.",
             "sources": ["부패방지 규정 제10조(이해충돌 등)", "부패방지 규정 제4조 9호(이해충돌)"]},
            {"category": "conduct", "relevance": "indirect",
             "clause_title": "'협력업체와의 관계'",
             "summary": "모든 협력업체는 성실하고 공정하게 대해야 하며, 거래 관련 의사결정은 객관적이고 공정한 기준에 "
                        "따르고 이를 뒷받침할 근거 자료를 남겨야 합니다.",
             "action": "심사가 객관적 기준과 근거 자료에 따라 진행되도록 하세요.",
             "sources": ["행동강령 '협력업체와의 관계' > 우리의 원칙", "행동강령 '협력업체와의 관계' > 정도의 실천"]},
        ],
        "checklist": ["해당 심사 업무에서 회피(배제)를 요청하세요",
                      "인사부서 또는 준법사무국에 이해충돌 사실을 신고하세요",
                      "신고 후 회사의 결정에 따르세요",
                      "심사는 객관적 기준과 근거 자료로 진행되도록 하세요"],
    },
    {  # 6. 규정 없음
        "situation_summary": "팀 회식비를 개인 카드로 결제한 뒤 영수증을 분실한 상황",
        "has_basis": False,
        "no_basis_message": "규범 문서에 직접 규정이 없습니다. 선택한 세무 정책(Tax Policy)은 회사 차원의 조세 원칙"
                            "(정상가격, 세무당국 협력 등)을 다루는 문서로, 개인 경비 정산이나 영수증 분실 처리 절차는 "
                            "포함하지 않습니다. 재무·회계팀에 문의하시기를 권장합니다.",
        "cards": [
            {"category": "tax", "relevance": "none", "clause_title": "직접 관련 조항 없음",
             "summary": "이 문서에는 직접 관련된 조항이 없습니다.", "action": "", "sources": []},
        ],
        "checklist": ["이 답변을 근거로 임의 처리하지 마세요",
                      "재무·회계팀에 경비 처리 방법을 문의하세요",
                      "처리 기준이 확인되면 그에 따라 정산하세요"],
    },
]


def _similar(a: str, b: str) -> float:
    ga, gb = rag._bigrams(a), rag._bigrams(b)
    inter = sum((ga & gb).values())
    return inter / max(1, min(sum(ga.values()), sum(gb.values())))


def answer(corpus: rag.Corpus, question: str, samples: list[str], categories: list[str],
           retrieved: list[tuple[rag.Chunk, float]], followup: bool, sample_idx: int | None = None) -> dict:
    """샘플(또는 샘플의 대표 후속 질문)과 비슷하면 사전 작성 답변, 아니면 검색 결과 카드를 반환."""
    if not followup:
        best = match_sample(question, samples)
        if best is not None:
            canned = _filtered(CANNED[best], categories)
            if canned:
                return canned
    elif sample_idx is not None and _matches_followup(question, sample_idx):
        canned = _filtered(FOLLOWUPS[sample_idx][1], categories)
        if canned:
            return canned
    return _from_retrieval(question, categories, retrieved)


def match_sample(question: str, samples: list[str]) -> int | None:
    best = max(range(len(samples)), key=lambda i: _similar(question, samples[i]))
    return best if _similar(question, samples[best]) > 0.7 else None


# 샘플별 대표 후속 질문으로 인식할 핵심 표현 (해당 샘플로 시작한 상담에서만 적용)
FOLLOWUP_KEYWORDS = [
    ["뜯", "개봉", "사용했", "써버", "먹었", "이미 받"],
    ["줬", "줘버", "주었", "드렸", "지급", "냈", "송금", "건넸", "이미"],
    ["이미", "벌써", "진행됐", "적용", "거래했", "반영"],
    ["말해", "말했", "알려줬", "얘기했", "언급", "흘렸"],
    ["이미", "벌써", "점수", "매겼", "평가했", "심사했", "진행했"],
    ["카드", "명세", "결제 내역", "대체", "대신"],
]


def _matches_followup(question: str, idx: int) -> bool:
    q = question.replace(" ", "")
    return question.strip() == FOLLOWUPS[idx][0] or any(k.replace(" ", "") in q for k in FOLLOWUP_KEYWORDS[idx])


def _filtered(canned: dict, categories: list[str]) -> dict | None:
    cards = [c for c in canned["cards"] if c["category"] in categories]
    return {**canned, "cards": cards} if cards else None


def _from_retrieval(question, categories, retrieved) -> dict:
    cards = []
    for cat in categories:
        hits = [c for c, s in retrieved if c.category == cat and s > 0.4]
        if not hits:
            cards.append({"category": cat, "relevance": "none", "clause_title": "검색된 관련 조항 없음",
                          "summary": "이 문서에서 키워드가 일치하는 조항을 찾지 못했습니다.", "action": "", "sources": []})
            continue
        top = hits[0]
        excerpt = top.text.replace("\n", " ")
        cards.append({"category": cat, "relevance": "indirect", "clause_title": top.citation,
                      "summary": excerpt[:220] + ("…" if len(excerpt) > 220 else ""),
                      "action": "데모 모드에서는 AI 해석 없이 검색된 조항 원문만 보여줍니다. 아래 출처를 펼쳐 원문을 확인하세요.",
                      "sources": [c.citation for c in hits]})
    has = any(c["relevance"] != "none" for c in cards)
    return {
        "situation_summary": question if len(question) < 80 else question[:80] + "…",
        "has_basis": has,
        "no_basis_message": "" if has else "검색된 근거 조항이 없습니다. 담당 부서에 문의하시기를 권장합니다.",
        "cards": cards,
        "checklist": ["검색된 조항 원문을 확인하세요",
                      "판단하기 어려우면 조직책임자와 먼저 상의하세요",
                      "부패방지 규정 해석이 필요하면 준법사무국에 문의하세요"],
    }


# 샘플별 대표 후속 질문과 사전 작성 답변 (CANNED와 같은 순서)
FOLLOWUPS = [
    ("이미 포장을 뜯었거나 일부 사용했다면 어떻게 해야 하나요?", {
        "situation_summary": "고가 명절 선물을 이미 개봉·일부 사용한 뒤 처리 방법을 묻는 상황",
        "has_basis": True, "no_basis_message": "",
        "cards": [
            {"category": "anticorruption", "relevance": "direct",
             "clause_title": "제13조 위반행위 신고 · 부칙 제2조 해석",
             "summary": "규정에는 '이미 개봉한 선물'의 처리 절차가 따로 적혀 있지 않습니다. 다만 위반이 의심되거나 우려가 "
                        "있는 사실을 인지하면 즉시 부서의 장 또는 신문고에 알려야 하고(제13조 1항), 신고자는 비밀이 "
                        "보장되며 불이익을 받지 않습니다(제13조 3항). 규정에 없거나 판단이 어려운 사항은 준법사무국의 "
                        "해석에 따릅니다(부칙 제2조).",
             "action": "개봉했다는 이유로 숨기거나 그대로 사용하지 말고, 받은 사실과 현재 상태를 있는 그대로 부서의 장에게 "
                       "알리세요. 반환·처리 방법은 준법사무국의 해석을 받아 결정하세요.",
             "sources": ["부패방지 규정 제13조(위반행위에 대한 신고)", "부패방지 규정 부칙 제2조(해석)",
                         "부패방지 규정 제6조(선물 및 접대)"]},
            {"category": "ethics", "relevance": "indirect",
             "clause_title": "제4장 1. 기본윤리",
             "summary": "임직원은 항상 정직하고 공정한 자세를 견지한다.",
             "action": "이미 받은 사실을 감추지 않고 정직하게 공유하는 것이 원칙입니다.",
             "sources": ["윤리규범 제4장 1.기본윤리"]},
            {"category": "conduct", "relevance": "direct",
             "clause_title": "'들어가기에 앞서' – 임직원의 의무",
             "summary": "판단하기 어려운 상황에서는 상사나 관련부서에 자문을 구한 후 조치하고, 행동강령이나 회사정책 위반으로 "
                        "의심되는 행위는 반드시 보고해야 합니다. 먼저 조직책임자와 상의하고, 해결되지 않으면 Compliance "
                        "Manager에게 보고합니다.",
             "action": "혼자 판단해 처리하지 말고 조직책임자와 먼저 상의하세요.",
             "sources": [C_INTRO]},
        ],
        "checklist": ["개봉·사용 사실을 숨기지 마세요",
                      "받은 사실과 현재 상태를 부서의 장에게 알리세요",
                      "처리 방법은 준법사무국의 해석을 받으세요",
                      "결정된 처리 내용을 기록으로 남기세요"],
    }),
    ("이미 컨설턴트에게 돈을 줬다면 어떻게 해야 하나요?", {
        "situation_summary": "통관 컨설턴트에게 이미 금품을 지급한 뒤 대응 방법을 묻는 상황",
        "has_basis": True, "no_basis_message": "",
        "cards": [
            {"category": "anticorruption", "relevance": "direct",
             "clause_title": "제13조 신고 · 제14조 위반행위에 대한 조치 · 제12조 조사",
             "summary": "위반사실이나 위반이 의심되는 사실을 인지하면 즉시 부서의 장 또는 신문고에 신고해야 하며, 신고자의 "
                        "비밀은 보장되고 불이익을 주어서는 안 됩니다(제13조). 위반하거나 위반을 발견하고도 합리적인 조치를 "
                        "취하지 않으면 회사는 대신 책임지지 않고 징계할 수 있으며, 민·형사 책임에 대한 지원 의무도 지지 "
                        "않습니다(제14조). 회사의 조사에는 적극 협조해야 합니다(제12조).",
             "action": "추가 지급을 멈추고, 지급 사실을 즉시 부서의 장 또는 신문고에 신고하세요. 이후 회사 조사에 협조하세요.",
             "sources": ["부패방지 규정 제13조(위반행위에 대한 신고)", "부패방지 규정 제14조(위반행위에 대한 조치)",
                         "부패방지 규정 제12조(조사 및 모니터링)"]},
            {"category": "conduct", "relevance": "direct",
             "clause_title": "'뇌물수수 금지' · 위반 시 보고",
             "summary": "대리인 등이 회사를 대신해 뇌물을 줘도 그 사실을 알았거나 알 수 있었다면 회사가 책임을 집니다. "
                        "'상사가 시켜서', '회사 목표 달성을 위해' 같은 변명은 용납되지 않으며, 보고 후 보복이 우려되면 즉시 "
                        "인사부서에 알릴 수 있습니다.",
             "action": "숨기거나 사후에 정당화하지 말고 바로 보고하세요. 보복이 걱정되면 인사부서에 알리세요.",
             "sources": ["행동강령 '뇌물수수 금지' > 정도의 실천", C_INTRO]},
        ],
        "checklist": ["추가 지급이나 연락을 멈추세요",
                      "지급 사실을 즉시 부서의 장 또는 신문고에 신고하세요",
                      "지급 내역 등 관련 자료를 그대로 보존하세요",
                      "회사 조사에 협조하고, 보복이 우려되면 인사부서에 알리세요"],
    }),
    ("이미 조정된 가격으로 거래가 진행됐다면 어떻게 하나요?", {
        "situation_summary": "세금 감소 목적으로 조정된 법인 간 거래가격이 이미 적용된 상황",
        "has_basis": True, "no_basis_message": "",
        "cards": [
            {"category": "tax", "relevance": "direct",
             "clause_title": "감내 가능한 세무 리스크 관리(Affordable level of tax risk management) · "
                             "세무당국에 대한 태도(Attitude towards Tax Authorities)",
             "summary": "회사는 불확실한 세무 이슈를 가능한 한 이른 시점에 식별·모니터링하고, 사업에 중대한 영향을 줄 수 있는 "
                        "불명확한 이슈는 외부 세무 자문과 협력해 세무당국과 협의합니다(3). 세무당국과는 투명하고 정직하며 "
                        "전문적으로 협력하고, 요청 시 글로벌 세무회계 책임자 통제하의 현지 회계 담당자를 통해 정보를 "
                        "제공합니다(4).",
             "action": "이미 적용된 거래 내역을 내부 세무관리팀에 즉시 공유하세요. 정상가격 원칙(Transparent Trade) 위반 "
                       "여부와 대응 방안은 세무팀과 외부 세무 자문을 통해 판단하세요.",
             "sources": ["Tax Policy 3. Affordable level of tax risk management",
                         "Tax Policy 4. Attitude towards Tax Authorities", "Tax Policy 1-2) Transparent Trade"]},
            {"category": "ethics", "relevance": "indirect",
             "clause_title": "제6장 3. 사회발전에 기여",
             "summary": "조세의 성실한 납부로 국가발전에 기여한다.",
             "action": "문제를 덮지 말고 성실 납부 원칙에 따라 바로잡는 방향으로 대응해야 합니다.",
             "sources": ["윤리규범 제6장 3.사회발전에 기여"]},
        ],
        "checklist": ["같은 방식의 가격 조정을 더 진행하지 마세요",
                      "적용된 거래 내역을 내부 세무관리팀에 즉시 공유하세요",
                      "관련 계약서·송장 등 기록을 그대로 보존하세요",
                      "대응 방안은 세무팀·외부 세무 자문을 거쳐 결정하세요"],
    }),
    ("이미 대략적인 출시 시기를 말해버렸다면 어떻게 하나요?", {
        "situation_summary": "전 직장 동료에게 미공개 제품의 출시 시기를 이미 언급한 상황",
        "has_basis": True, "no_basis_message": "",
        "cards": [
            {"category": "conduct", "relevance": "direct",
             "clause_title": "'정보보안과 기밀 유지' · '내부자 정보'",
             "summary": "회사기밀이나 업무상 민감한 정보는 외부에 발설하면 안 되며, 의문사항은 조직책임자나 정보보안 담당자와 "
                        "상의해야 합니다. 내부자 정보가 무단 공개된 사실을 알게 되면 즉시 법무담당 부서에 보고해야 하고, "
                        "정보를 전달받은 상대에게도 다시 언급하지 않도록 주의를 줘야 합니다.",
             "action": "더 이상 말하지 말고, 언급한 내용을 조직책임자·정보보안 담당자에게 바로 알리세요. 출시 일정이 내부자 "
                       "정보에 해당할 수 있으면 법무담당 부서에도 보고하세요.",
             "sources": ["행동강령 '정보보안과 기밀 유지' > 정도의 실천",
                         "행동강령 '정보보안과 기밀 유지' > 바람직한 대처방식",
                         "행동강령 '내부자 정보' > 정도의 실천", "행동강령 '내부자 정보' > 바람직한 대처방식"]},
            {"category": "ethics", "relevance": "direct",
             "clause_title": "제4장 2. 사명의 완수",
             "summary": "업무상 취득한 회사의 비밀을 보호한다.",
             "action": "이미 말한 내용이 더 퍼지지 않도록 즉시 조치하는 것도 비밀 보호 의무에 포함됩니다.",
             "sources": ["윤리규범 제4장 2.사명의 완수"]},
        ],
        "checklist": ["추가 정보는 말하지 마세요",
                      "상대에게 들은 내용을 공유하지 말아 달라고 요청하세요",
                      "조직책임자·정보보안 담당자에게 언급한 내용을 알리세요",
                      "내부자 정보에 해당할 수 있으면 법무담당 부서에 보고하세요"],
    }),
    ("이미 심사를 진행해서 점수를 매겼다면 어떻게 하나요?", {
        "situation_summary": "친척 회사에 대한 협력사 심사를 이미 일부 진행한 상황",
        "has_basis": True, "no_basis_message": "",
        "cards": [
            {"category": "ethics", "relevance": "direct",
             "clause_title": "제4장 5. 회사와의 이해상충 회피",
             "summary": "회사와 개인의 이해가 상충되는 어떠한 행위나 관계도 회피한다.",
             "action": "지금 시점부터라도 해당 심사에서 빠지는 것이 원칙입니다.",
             "sources": ["윤리규범 제4장 5.회사와의 이해상충 회피"]},
            {"category": "anticorruption", "relevance": "direct",
             "clause_title": "제10조 이해충돌 등",
             "summary": "이해충돌이 불가피한 경우 원칙적으로 관련 업무에서 배제되어야 하며, 인사부서 또는 준법사무국에 신고한 뒤 "
                        "회사의 결정에 따라야 합니다. 이미 진행한 심사를 어떻게 처리할지는 규정에 따로 적혀 있지 않으므로 "
                        "회사의 결정을 따릅니다.",
             "action": "남은 심사 업무에서 즉시 빠지고, 이미 심사에 참여한 사실까지 포함해 인사부서 또는 준법사무국에 "
                       "신고하세요.",
             "sources": ["부패방지 규정 제10조(이해충돌 등)", "부패방지 규정 부칙 제2조(해석)"]},
            {"category": "conduct", "relevance": "indirect",
             "clause_title": "'협력업체와의 관계'",
             "summary": "협력업체 관련 의사결정은 객관적이고 공정한 기준에 따르고, 이를 뒷받침할 근거 자료를 남겨야 합니다.",
             "action": "이미 작성한 심사 점수와 근거 자료는 고치지 말고 그대로 제출해 회사가 판단할 수 있게 하세요.",
             "sources": ["행동강령 '협력업체와의 관계' > 정도의 실천"]},
        ],
        "checklist": ["남은 심사 업무에서 즉시 빠지세요",
                      "심사 참여 사실까지 포함해 인사부서 또는 준법사무국에 신고하세요",
                      "작성한 점수·근거 자료를 수정하지 말고 그대로 제출하세요",
                      "재심사 여부 등은 회사의 결정에 따르세요"],
    }),
    ("카드 결제 내역으로 영수증을 대신할 수 있나요?", {
        "situation_summary": "분실한 영수증 대신 카드 결제 내역을 증빙으로 쓸 수 있는지 묻는 상황",
        "has_basis": False,
        "no_basis_message": "규범 문서에 직접 규정이 없습니다. 세무 정책(Tax Policy)은 회사 차원의 조세 원칙 문서로, 개인 "
                            "경비의 증빙 대체 기준은 다루지 않습니다. 대체 증빙 인정 여부는 재무·회계팀에 문의하시기를 "
                            "권장합니다.",
        "cards": [
            {"category": "tax", "relevance": "none", "clause_title": "직접 관련 조항 없음",
             "summary": "이 문서에는 직접 관련된 조항이 없습니다.", "action": "", "sources": []},
        ],
        "checklist": ["대체 증빙 인정 여부를 재무·회계팀에 문의하세요",
                      "확인 전에는 임의로 정산하지 마세요",
                      "안내받은 기준에 따라 처리하세요"],
    }),
]
