import streamlit as st
from PIL import Image
import io
import base64

# ライブラリの存在チェックとインポート
try:
    import google.generativeai as genai
except ImportError:
    st.error("Geminiライブラリが見つかりません。`pip install google-generativeai` を実行してください。")
    st.stop()
try:
    import openai
except ImportError:
    st.error("OpenAIライブラリが見つかりません。`pip install openai` を実行してください。")
    st.stop()


# --- 1. アプリの基本設定 ---
st.set_page_config(
    page_title="計測器数値読み取りアプリ",
    page_icon="🔎",
    layout="centered"
)

st.title("🔎 計測器数値読み取りアプリ")
st.write("サイドバーでAIモデルを選択し、画像をアップロードして解析します。")

# --- 2. セッションステートの初期化 ---
# APIキーは設定ページで読み込まれるが、直接このページにアクセスした場合のために初期化しておく
if 'gemini_api_key' not in st.session_state:
    st.session_state.gemini_api_key = ""
if 'openrouter_api_key' not in st.session_state:
    st.session_state.openrouter_api_key = ""
if 'rotation_angle' not in st.session_state:
    st.session_state.rotation_angle = 0
if 'last_uploaded_file_id' not in st.session_state:
    st.session_state.last_uploaded_file_id = None


# --- 3. サイドバー ---
with st.sidebar:
    st.header("⚙️ モデル設定")
    selected_model_option = st.selectbox(
        "使用するAIモデルを選択",
        ("Gemini 1.5 Flash (Google)", "Llama 4 Maverick (OpenRouter)")
    )
    st.info("APIキーは左のメニューから「APIキー設定」ページで入力・管理できます。")


# --- 4. APIキーの存在チェック ---
active_api_key = None
if selected_model_option == "Gemini 1.5 Flash (Google)":
    active_api_key = st.session_state.get("gemini_api_key")
    if not active_api_key:
        st.warning("APIキーが設定されていません。左のナビゲーションから「APIキー設定」ページに移動してキーを入力してください。")
        st.stop()
else: # Llama 4 Maverick (OpenRouter)
    active_api_key = st.session_state.get("openrouter_api_key")
    if not active_api_key:
        st.warning("APIキーが設定されていません。左のナビゲーションから「APIキー設定」ページに移動してキーを入力してください。")
        st.stop()

# --- 5. プロンプトテンプレート ---
PROMPT_TEMPLATE = """
あなたは工業用計測器の読み取りに特化した専門家です。提供された画像の中から、圧力計、温度計、流量計、デジタルメーターなどの計測器をすべて特定してください。特定した各計測器について、以下の情報をMarkdownの表形式で出力してください。
- **計測器の種類**: (例: 圧力計, デジタル温度計)
- **読み取った数値**: 可能な限り正確な数値を読み取ってください。針が指している値を推定してください。
- **単位**: (例: MPa, °C, L/min, V)
もし数値や単位が不鮮明で読み取れない場合は、その旨を記載してください。画像内に計測器が見つからない場合は、「画像内に計測器は見つかりませんでした。」と明確に報告してください。
"""
OPTION_PROMPT_ADDITION = "\n**追加指示:**\n画像内に黄色い円やマーカーで囲まれている箇所があります。その囲まれている内部にある計測器の数値だけを読み取ってください。"

# --- 6. 解析関数の定義 ---
def analyze_with_gemini(api_key, image_part, final_prompt):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        response = model.generate_content([final_prompt, image_part])
        return response.text
    except Exception as e: return f"Geminiでの解析中にエラー: {e}"

def analyze_with_openrouter_vision(api_key, model_name, image_bytes, final_prompt):
    try:
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        client = openai.OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1", default_headers={"HTTP-Referer": "http://localhost:8501", "X-Title": "Gauge Reader App"})
        response = client.chat.completions.create(model=model_name, messages=[{"role": "user", "content": [{"type": "text", "text": final_prompt}, {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}]}])
        return response.choices[0].message.content
    except Exception as e: return f"OpenRouter ({model_name}) での解析中にエラー: {e}"

# --- 7. メインのUIとロジック ---
uploaded_file = st.file_uploader("計測器の画像をアップロードしてください", type=['jpg', 'jpeg', 'png'])
if uploaded_file:
    if st.session_state.last_uploaded_file_id != uploaded_file.file_id:
        st.session_state.rotation_angle = 0
        st.session_state.last_uploaded_file_id = uploaded_file.file_id
    original_image = Image.open(io.BytesIO(uploaded_file.getvalue()))
    st.subheader("🔧 画像の調整とオプション")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("画像を90度回転 🔄"): st.session_state.rotation_angle = (st.session_state.rotation_angle + 90) % 360
    with col2:
        is_option_enabled = st.checkbox("🟡 黄色い丸の中のみ解析")
    rotated_image = original_image.rotate(-st.session_state.rotation_angle, expand=True)
    st.image(rotated_image, caption=f'アップロードされた画像 (回転角度: {st.session_state.rotation_angle}°)', use_container_width=True)
    if st.button('この画像の数値を解析する', type="primary"):
        with st.spinner(f'{selected_model_option}が解析中です...'):
            final_prompt = PROMPT_TEMPLATE
            if is_option_enabled: final_prompt += OPTION_PROMPT_ADDITION
            img_byte_arr = io.BytesIO()
            rotated_image.save(img_byte_arr, format='PNG')
            image_bytes_for_api = img_byte_arr.getvalue()
            analysis_result = ""
            if selected_model_option == "Gemini 1.5 Flash (Google)":
                image_part = {"mime_type": "image/png", "data": image_bytes_for_api}
                analysis_result = analyze_with_gemini(active_api_key, image_part, final_prompt)
            else:
                analysis_result = analyze_with_openrouter_vision(api_key=active_api_key, model_name="meta-llama/llama-4-maverick", image_bytes=image_bytes_for_api, final_prompt=final_prompt)
        st.subheader("📊 解析結果")
        st.markdown(analysis_result if analysis_result else "解析結果を取得できませんでした。")