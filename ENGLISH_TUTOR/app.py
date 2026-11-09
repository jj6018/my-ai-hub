import json
import os
from google import genai
import streamlit as st

st.set_page_config(page_title="AI 영어 회화 튜터", page_icon="✍️", layout="wide")

# 1. API 키 불러오기 (Streamlit Secrets)
api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("⚠️ GEMINI_API_KEY가 설정되지 않았습니다. Secrets를 확인해주세요.")
    st.stop()

client = genai.Client(api_key=api_key)

# 2. 로컬 저장소 JSON 관리
DATA_FILE = "vocab_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"vocab_list": []}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if "db" not in st.session_state:
    st.session_state.db = load_data()

if "current_question" not in st.session_state:
    st.session_state.current_question = "🎲 하단의 버튼을 눌러 첫 대화 질문을 받아보세요!"

# 3. AI 호출 함수 (gemini-3.8-flash)
def generate_ai_response(prompt_text):
    try:
        return client.models.generate_content(
            model="gemini-3.8-flash", 
            contents=prompt_text
        ).text
    except Exception as e:
        err_msg = str(e)
        if "429" in err_msg:
            raise Exception("⚠️ 무료 API 호출 한도를 초과했습니다. 잠시 후 시도해 주세요.")
        elif "503" in err_msg:
            raise Exception("⚠️ AI 서버 트래픽이 일시적으로 급증했습니다.")
        else:
            raise Exception(f"AI 호출 오류: {err_msg}")

# 4. 메뉴 및 화면 구성
st.sidebar.title("✍️ AI English Tutor")
menu = st.sidebar.radio("메뉴 선택", ["🎯 회화 질문 받기 & 답변 교정", "📚 나만의 단어장 (Vocab Vault)"])

if menu == "🎯 회화 질문 받기 & 답변 교정":
    st.title("🎯 AI 회화 스타터 & 영작 튜터")
    st.caption("AI가 던져주는 질문에 대답하며 자연스러운 영어 표현과 어휘를 익혀보세요.")

    col_q1, col_q2 = st.columns([3, 1])
    with col_q1:
        st.info(f"**[AI 연습 질문]**\n\n{st.session_state.current_question}")
    with col_q2:
        if st.button("🎲 새 질문 받기"):
            with st.spinner("질문 생성 중..."):
                q_prompt = '''
                영어 회화 및 작문 연습용 대화 시작 질문 1개를 만들어라.
                - ❓ **Question:** (친근한 일상 주제의 영어 질문 1개)
                - 🇰🇷 **한글 번역:** (질문 뜻)
                - 💡 **답변 아이디어/키워드 힌트:** (사용하면 좋은 영어 단어 2~3개 및 한국어 뜻)
                '''
                try:
                    st.session_state.current_question = generate_ai_response(q_prompt)
                    st.rerun()
                except Exception as err:
                    st.error(str(err))

    st.markdown("---")
    user_text = st.text_area("위 질문에 대한 답변을 영어로 작성해보세요", height=150, placeholder="Write your answer here in English...")

    if st.button("내 답변 교정받기", type="primary"):
        if user_text.strip():
            with st.spinner("검토 중..."):
                prompt = f'''
                너는 원어민 영작/회화 튜터다. 사용자의 답변을 검토하여 작성해라.
                1. ✨ Natural Revision (자연스러운 교정본)
                2. 💡 Better Expressions (더 세련된 표현 2~3가지)
                3. 📌 Key Vocabulary & Phrases (주요 단어 및 뜻)

                [질문 Context]
                {st.session_state.current_question}

                [사용자 답변]
                {user_text}
                '''
                try:
                    feedback = generate_ai_response(prompt)
                    st.subheader("💡 AI 튜터 피드백 결과")
                    st.markdown(feedback)
                except Exception as err:
                    st.error(str(err))
        else:
            st.warning("답변을 입력해 주세요.")

    st.markdown("---")
    st.subheader("📥 단어장에 빠르게 추가하기")
    col1, col2 = st.columns(2)
    with col1:
        w_input = st.text_input("저장할 단어/표현")
    with col2:
        m_input = st.text_input("뜻 및 예문")

    if st.button("단어장에 저장"):
        if w_input and m_input:
            st.session_state.db["vocab_list"].append({"word": w_input, "meaning": m_input})
            save_data(st.session_state.db)
            st.success(f"'{w_input}' 저장 완료!")
        else:
            st.warning("단어와 뜻을 모두 입력해 주세요.")

elif menu == "📚 나만의 단어장 (Vocab Vault)":
    st.title("📚 나만의 단어장 (Vocab Vault)")
    vocab = st.session_state.db.get("vocab_list", [])

    if vocab:
        st.write(f"현재 총 **{len(vocab)}개**의 표현이 저장되어 있습니다.")
        
        search_query = st.text_input("🔍 단어 검색", "")
        filtered_vocab = [
            item for item in vocab 
            if search_query.lower() in item['word'].lower() or search_query.lower() in item['meaning'].lower()
        ]

        st.markdown("---")
        for idx, item in enumerate(reversed(filtered_vocab)):
            cols = st.columns([4, 1])
            with cols[0]:
                st.info(f"**{item['word']}** : {item['meaning']}")
            with cols[1]:
                if st.button("삭제", key=f"del_{idx}"):
                    st.session_state.db["vocab_list"].remove(item)
                    save_data(st.session_state.db)
                    st.rerun()
    else:
        st.info("저장된 단어가 없습니다. 회화 메뉴에서 단어를 저장해 보세요!")
