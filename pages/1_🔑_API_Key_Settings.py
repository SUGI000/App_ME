import streamlit as st
import os
from dotenv import load_dotenv

# .envファイルのフルパスを決定 (プロジェクトルートに作成)
# __file__ は現在のファイルパス、'..'で一つ上の階層に移動
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')

st.set_page_config(page_title="APIキー設定", page_icon="🔑")
st.title("🔑 APIキー設定")
st.markdown("---")

st.write("Google AI Studioで取得したAPIキーを設定・保存します。")
st.info(
    "ここで設定したAPIキーは、お使いのPCのプロジェクトフォルダ内に `.env` という名前のファイルとして保存されます。"
    "次回以降アプリを起動する際は、このファイルから自動でキーが読み込まれます。"
)

# 現在保存されているキーを読み込んで表示（セキュリティのため一部をマスク）
load_dotenv(dotenv_path=dotenv_path)
current_key = os.getenv("GOOGLE_API_KEY")

if current_key:
    # キーの一部をマスクして表示
    masked_key = current_key[:4] + "••••••••••••" + current_key[-4:]
    st.write(f"**現在設定中のAPIキー:** `{masked_key}`")
else:
    st.write("**現在設定中のAPIキー:** `未設定`")

# 新しいAPIキーを入力するフォーム
new_api_key = st.text_input(
    "新しいAPIキーを入力、または上書きしてください",
    type="password",
    help="入力されたキーはローカルの.envファイルに保存されます。"
)

if st.button("このAPIキーを保存する"):
    if new_api_key and new_api_key.strip():
        try:
            # .envファイルにキーを書き込む (ファイルがなければ新規作成)
            with open(dotenv_path, "w") as f:
                f.write(f'GOOGLE_API_KEY="{new_api_key}"\n')
            
            # 保存が成功したことをユーザーに通知
            st.success("APIキーを保存しました！")
            st.info("ページを再読み込みして、設定が反映されたことを確認してください。")
            
            # Streamlitに即時再読み込みを促す
            st.rerun()

        except Exception as e:
            st.error(f"ファイルの保存中にエラーが発生しました: {e}")
    else:
        st.warning("APIキーが入力されていません。")

st.markdown("---")
st.warning(
    "**注意：** `.env` ファイルには重要なAPIキーが記録されます。"
    "このフォルダやファイルを、Gitリポジトリに含めたり他者と共有したりしないでください。",
    icon="⚠️"
)