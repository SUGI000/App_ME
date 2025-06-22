import streamlit as st
from streamlit_local_storage import LocalStorage

# ページの設定
st.set_page_config(
    page_title="APIキー設定 (デバイス保存対応)",
    page_icon="🔑",
    layout="centered"
)

st.title("🔑 APIキー設定 (デバイス保存対応)")
st.write("ここで入力したAPIキーは、お使いのブラウザのローカルストレージに保存されます。")

# セキュリティに関する重要な警告
st.error(
    """
    **セキュリティに関する重要な注意**

    APIキーは金銭的価値を持つ非常に重要な秘密情報です。
    - **絶対に**、学校や職場などの共有PCでAPIキーを入力・保存しないでください。
    - **絶対に**、信頼できないネットワーク（例: 公共のWi-Fi）では使用しないでください。
    - このアプリケーションの作者は、APIキーの漏洩によって生じたいかなる損害についても責任を負いかねます。
    """
)

# LocalStorageの初期化
try:
    localS = LocalStorage()
except Exception as e:
    st.error(f"LocalStorageコンポーネントの読み込みに失敗しました: {e}")
    st.info("ブラウザのシークレットモードでは動作しないことがあります。")
    st.stop()


# --- セッションステートの初期化 ---
# ページロード時に一度だけ、LocalStorageから読み込みを試みる
if 'keys_loaded' not in st.session_state:
    st.session_state.gemini_api_key = localS.getItem("gemini_api_key") or ""
    st.session_state.openrouter_api_key = localS.getItem("openrouter_api_key") or ""
    st.session_state.keys_loaded = True # 読み込み完了フラグ


# --- UIの定義とコールバック関数 ---
def save_key(key_name, widget_key):
    """入力値をセッションステートとLocalStorageに保存する関数"""
    new_value = st.session_state[widget_key]
    st.session_state[key_name] = new_value
    localS.setItem(key_name, new_value)
    st.success(f"{key_name.replace('_', ' ').title()} がブラウザに保存されました。")

def clear_key(key_name, widget_key):
    """セッションステートとLocalStorageからキーを削除する関数"""
    st.session_state[key_name] = ""
    st.session_state[widget_key] = ""
    localS.removeItem(key_name)
    st.info(f"{key_name.replace('_', ' ').title()} がクリアされました。")


# --- Gemini APIキーのセクション ---
st.subheader("Google Gemini")
st.text_input(
    "Gemini APIキーを入力・更新",
    key="gemini_input_widget", # ウィジェットに一意のキー
    type="password",
    on_change=save_key, # 値が変更されたら保存関数を呼び出す
    args=("gemini_api_key", "gemini_input_widget")
)
if st.button("Geminiキーをクリア"):
    clear_key("gemini_api_key", "gemini_input_widget")
    st.rerun()

# --- OpenRouter APIキーのセクション ---
st.subheader("OpenRouter (Llama 4)")
st.text_input(
    "OpenRouter APIキーを入力・更新",
    key="openrouter_input_widget", # ウィジェットに一意のキー
    type="password",
    on_change=save_key, # 値が変更されたら保存関数を呼び出す
    args=("openrouter_api_key", "openrouter_input_widget")
)
if st.button("OpenRouterキーをクリア"):
    clear_key("openrouter_api_key", "openrouter_input_widget")
    st.rerun()

st.divider()

# --- 現在の設定状況 ---
st.subheader("現在の設定状況")
if st.session_state.get("gemini_api_key"):
    st.success("Gemini APIキーは現在設定されています。")
else:
    st.warning("Gemini APIキーは未設定です。")

if st.session_state.get("openrouter_api_key"):
    st.success("OpenRouter APIキーは現在設定されています。")
else:
    st.warning("OpenRouter APIキーは未設定です。")