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
           retrieved: list[tuple[rag.Chunk, float]], followup: bool) -> dict:
    if not followup:
        best = max(range(len(samples)), key=lambda i: _similar(question, samples[i]))
        if _similar(question, samples[best]) > 0.7:
            canned = dict(CANNED[best])
            canned["cards"] = [c for c in canned["cards"] if c["category"] in categories]
            if canned["cards"]:
                return canned
    return _from_retrieval(question, categories, retrieved)


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
