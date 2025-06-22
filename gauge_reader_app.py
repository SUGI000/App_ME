import streamlit as st
import google.generativeai as genai
from PIL import Image
import os
from dotenv import load_dotenv

# --- アプリの基本設定 ---
st.set_page_config(
    page_title="工業用計測器 数値読み取りアプリ",
    page_icon="🤖",
    layout="centered"
)

st.title("🤖 工業用計測器 数値読み取りアプリ")
st.write("工業用のメーターやゲージの画像をアップロードすると、AI(Gemini)が数値を読み取ります。")

# --- APIキーの読み込み処理 ---
# .envファイルのフルパスを決定
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=dotenv_path)
api_key = os.getenv("GOOGLE_API_KEY")

# APIキーが設定されているかチェック
if not api_key:
    st.warning("APIキーが設定されていません。")
    st.info("左のサイドバーから「🔑 APIキー設定」ページに移動して、キーを登録してください。")
    st.stop() # APIキーがない場合はここで処理を停止

# Geminiクライアントの設定
try:
    genai.configure(api_key=api_key)
except Exception as e:
    st.error(f"APIキーの設定中にエラーが発生しました。キーが正しいか確認してください。エラー: {e}")
    st.stop()

# --- Geminiに渡すプロンプトのテンプレート ---
PROMPT_TEMPLATE = """
あなたは工業用計測器の読み取りに特化した専門家です。
提供された画像の中から、圧力計、温度計、流量計、デジタルメーターなどの計測器をすべて特定してください。

特定した各計測器について、以下の情報をMarkdownの表形式で出力してください。

- **計測器の種類**: (例: 圧力計, デジタル温度計)
- **読み取った数値**: 可能な限り正確な数値を読み取ってください。針が指している値を推定してください。
- **単位**: (例: MPa, °C, L/min, V)

もし数値や単位が不鮮明で読み取れない場合は、その旨を記載してください。

---
**解析結果**

| 計測器の種類 | 読み取った数値 | 単位 |
| :--- | :--- | :--- |
| (ここに結果を記入) | (ここに結果を記入) | (ここに結果を記入) |
"""

def analyze_gauge_image(image_data, prompt):
    """画像をGeminiに送信して解析結果を取得する関数"""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        response = model.generate_content([prompt, image_data])
        return response.text
    except Exception as e:
        st.error(f"解析中にエラーが発生しました: {e}")
        return None

# --- ファイルアップローダー ---
uploaded_file = st.file_uploader(
    "計測器の画像をアップロードしてください",
    type=['jpg', 'jpeg', 'png']
)

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption='アップロードされた画像', use_container_width=True)

    if st.button('この画像の数値を解析する'):
        with st.spinner('AIが画像を解析中です... しばらくお待ちください。'):
            img_byte_arr = uploaded_file.getvalue()
            image_parts = [{"mime_type": uploaded_file.type, "data": img_byte_arr}]
            analysis_result = analyze_gauge_image(image_parts[0], PROMPT_TEMPLATE)
            st.subheader("📊 解析結果")
            if analysis_result:
                st.markdown(analysis_result)
            else:
                st.write("解析結果を取得できませんでした。")