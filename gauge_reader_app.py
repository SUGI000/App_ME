import streamlit as st
import google.generativeai as genai
from PIL import Image
import os
from dotenv import load_dotenv
import io

# --- 1. アプリの基本設定 ---
st.set_page_config(
    page_title="工業用計測器 数値読み取りアプリ (高機能版)",
    page_icon="🤖",
    layout="centered"
)

st.title("🤖 工業用計測器 数値読み取りアプリ (高機能版)")
st.write("工業用のメーター画像を解析します。画像の回転や、特定箇所の読み取りも可能です。")

# --- 2. セッションステートの初期化 ---
# st.session_stateに値がない場合のみ初期値を設定
if 'api_key' not in st.session_state:
    st.session_state.api_key = None
if 'rotation_angle' not in st.session_state:
    st.session_state.rotation_angle = 0
if 'last_uploaded_file_id' not in st.session_state:
    st.session_state.last_uploaded_file_id = None

# --- 3. サイドバーとAPIキー管理 ---
with st.sidebar:
    st.header("🔑 API設定")
    # APIキーのリセットボタン
    if st.button("APIキーをリセット"):
        st.session_state.api_key = None
        # ページを再実行してAPIキーの再読み込みを促す
        st.rerun()

    # APIキーの読み込みロジック (st.session_stateを活用)
    if not st.session_state.api_key:
        try:
            # 優先: Streamlitのsecretsから読み込み (デプロイ環境)
            st.session_state.api_key = st.secrets["GOOGLE_API_KEY"]
            st.success("APIキーをデプロイ環境から読み込みました。")
        except (st.errors.StreamlitAPIException, KeyError):
            # 次善: .envファイルから読み込み (ローカル環境)
            dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
            if os.path.exists(dotenv_path):
                load_dotenv(dotenv_path=dotenv_path)
                st.session_state.api_key = os.getenv("GOOGLE_API_KEY")
                if st.session_state.api_key:
                    st.success("APIキーを.envファイルから読み込みました。")

# --- 4. APIキーの存在チェックとGeminiクライアント設定 ---
if not st.session_state.api_key:
    st.warning("APIキーが設定されていません。")
    st.info("デプロイ環境ではSecretsに、ローカルでは`.env`ファイルに`GOOGLE_API_KEY`を設定してください。")
    st.stop()

try:
    genai.configure(api_key=st.session_state.api_key)
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
except Exception as e:
    st.error(f"APIキーの設定またはモデルの初期化中にエラーが発生しました。: {e}")
    st.stop()

# --- 5. プロンプトテンプレート ---
BASE_PROMPT = """
あなたは工業用計測器の読み取りに特化した専門家です。
提供された画像の中から、圧力計、温度計、流量計、デジタルメーターなどの計測器をすべて特定してください。

特定した各計測器について、以下の情報をMarkdownの表形式で出力してください。

- **計測器の種類**: (例: 圧力計, デジタル温度計)
- **読み取った数値**: 可能な限り正確な数値を読み取ってください。針が指している値を推定してください。
- **単位**: (例: MPa, °C, L/min, V)

もし数値や単位が不鮮明で読み取れない場合は、その旨を記載してください。
画像内に計測器が見つからない場合は、「画像内に計測器は見つかりませんでした。」と明確に報告してください。
"""

OPTION_PROMPT_ADDITION = """
**追加指示:**
画像内に黄色い円やマーカーで囲まれている箇所があります。その囲まれている内部にある計測器の数値だけを読み取ってください。それ以外の計測器は無視してください。
"""

def analyze_gauge_image(image_part, final_prompt):
    """画像をGeminiに送信して解析結果を取得する関数"""
    try:
        response = model.generate_content([final_prompt, image_part])
        return response.text
    except Exception as e:
        st.error(f"AIによる解析中にエラーが発生しました。: {e}")
        return None

# --- 6. メインのファイルアップローダーと画像処理 ---
uploaded_file = st.file_uploader(
    "計測器の画像をアップロードしてください",
    type=['jpg', 'jpeg', 'png']
)

if uploaded_file is not None:
    # 新しいファイルがアップロードされたら回転角度をリセット
    if st.session_state.last_uploaded_file_id != uploaded_file.file_id:
        st.session_state.rotation_angle = 0
        st.session_state.last_uploaded_file_id = uploaded_file.file_id

    img_bytes = uploaded_file.getvalue()
    original_image = Image.open(io.BytesIO(img_bytes))

    st.subheader("🔧 画像の調整とオプション")
    
    # 2列レイアウトでボタンを配置
    col1, col2 = st.columns(2)
    with col1:
        # 画像回転ボタン
        if st.button("画像を90度回転 🔄"):
            st.session_state.rotation_angle = (st.session_state.rotation_angle + 90) % 360
    
    with col2:
        # オプション解析のチェックボックス
        is_option_enabled = st.checkbox("🟡 黄色い丸の中のみ解析")

    # 画像を回転させる
    # PILのrotateは反時計回りなので、-をつけて時計回りにする
    rotated_image = original_image.rotate(-st.session_state.rotation_angle, expand=True)
    
    st.image(rotated_image, caption=f'アップロードされた画像 (回転角度: {st.session_state.rotation_angle}°)', use_container_width=True)

    # 解析実行ボタン
    if st.button('この画像の数値を解析する', type="primary"):
        with st.spinner('AIが画像を解析中です... しばらくお待ちください。'):
            # 解析用のプロンプトを決定
            final_prompt = BASE_PROMPT
            if is_option_enabled:
                final_prompt += "\n\n" + OPTION_PROMPT_ADDITION

            # 回転後の画像をバイトデータに変換してAPIに渡す
            img_byte_arr = io.BytesIO()
            # MIMEタイプに合わせてフォーマットを指定 (PNGが品質劣化なく無難)
            image_format = 'PNG' if uploaded_file.type == 'image/png' else 'JPEG'
            rotated_image.save(img_byte_arr, format=image_format)
            img_bytes_for_api = img_byte_arr.getvalue()
            
            image_part = {"mime_type": uploaded_file.type, "data": img_bytes_for_api}
            
            analysis_result = analyze_gauge_image(image_part, final_prompt)
            
            st.subheader("📊 解析結果")
            if analysis_result:
                st.markdown(analysis_result)
            else:
                st.write("解析結果を取得できませんでした。")