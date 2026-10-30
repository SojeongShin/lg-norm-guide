# LG 규범 가이드 챗봇

## 실행
```bash
source .venv/bin/activate          # 또는 python3 -m venv .venv 후 활성화
pip install -r requirements.txt
streamlit run app.py                 # 키 없이 실행하면 데모 모드(무료)
# 실제 Claude 답변: export ANTHROPIC_API_KEY=sk-ant-... 후 실행 (키는 코드/슬라이드에 넣지 말 것)
```

데모 모드: 샘플 6개는 PDF 조항 근거로 사전 작성된 답변(`demo.py`), 그 외 입력은 검색된 조항 원문을 카드로 보여줌.

## 구성
- `app.py` : Streamlit 화면 (입력·샘플 6개·우선순위·규범 카드·체크리스트·후속 질문·면책 문구)
- `demo.py` : 데모 모드 답변
- `rag.py` : 문서 청크 분할, 검색(문자 bigram TF-IDF + 우선순위 가중치), Claude API 호출
- `corpus/*.txt` : `데이터/*.pdf`에서 추출한 텍스트 (pdftotext)

환경변수 `CLAUDE_MODEL`(기본 claude-opus-5-5), `CLAUDE_EFFORT`(기본 low)로 조정 가능.
