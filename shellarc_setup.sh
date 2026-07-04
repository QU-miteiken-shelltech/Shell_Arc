#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v python3 &> /dev/null; then
    echo "ShellArc を使うのに、Pythonをインストールする必要があります"
    echo "Pythonをインストールしてください"
    read -p "Pythonインストールのチュートリアルが必要ですか? (Y/n): " has_tutorial
    if [ "$has_tutorial" = "Y" ] || [ "$has_tutorial" = "y" ] || [ -z "$has_tutorial" ]; then
        if [ -f "${SCRIPT_DIR}/python_install_tutorial.txt" ]; then
            cat "${SCRIPT_DIR}/python_install_tutorial.txt"
        else
            echo "チュートリアルファイル（python_install_tutorial.txt）が見つかりません。"
        fi
    fi
    exit 1 
fi

ZSHRC="${HOME}/.zshrc"
ENV_LINE="export SHELLARC_PROJECT_CTX=\"${SCRIPT_DIR}/project_ctx\""
VENV_DIR="${SCRIPT_DIR}/venv"
ALIAS_LINE="alias shellarc='${VENV_DIR}/bin/python3 ${SCRIPT_DIR}/shellarc_desktop/shellarc_desktop.py'"

echo "環境設定を追記中..."
echo "#Appended by ShellArc :" >> "$ZSHRC"
grep -qxF "$ENV_LINE" "$ZSHRC" || echo "$ENV_LINE" >> "$ZSHRC"
grep -qxF "$ALIAS_LINE" "$ZSHRC" || echo "$ALIAS_LINE" >> "$ZSHRC"
echo "#ShellArc END" >> "$ZSHRC"

echo "Python仮想環境を作成中..."
python3 -m venv "${VENV_DIR}"

echo "pipをアップグレード中..."
"${VENV_DIR}/bin/python3" -m pip install --upgrade pip

echo "ディペンデンシーをインストール中..."
"${VENV_DIR}/bin/python3" -m pip install -e "${SCRIPT_DIR}"

read -p "秘密鍵を入力してください: " secret_key
export EXPORT_SECRET_KEY="$secret_key"
export EXPORT_SCRIPT_DIR="$SCRIPT_DIR"

${VENV_DIR}/bin/python3 << 'EOF'
import os
from cryptography.fernet import Fernet
script_dir = os.environ.get("EXPORT_SCRIPT_DIR")
secret_key = os.environ.get("EXPORT_SECRET_KEY", "")
bin_path = os.path.join(script_dir, "project_ctx", ".env.bin")
env_path = os.path.join(script_dir, "project_ctx", ".env")
with open(bin_path, "rb") as f:
    token = f.read()
key = secret_key.encode("utf-8")
decrypted_data = Fernet(key).decrypt(token).decode("utf-8")
with open(env_path, "w", encoding="utf-8") as f:
    f.write(decrypted_data)
EOF

unset EXPORT_SECRET_KEY
unset EXPORT_SCRIPT_DIR

echo "--------------------------------------------------"
echo "設定を反映するには: source ~/.zshrc を実行してください"
echo "以降は、ターミナルから 'shellarc' コマンドで起動できます"
echo "--------------------------------------------------"


function set_shortcut(){
    APP_DIR="${HOME}/Desktop/ShellArc_Desktop.app"
    mkdir -p "${APP_DIR}/Contents/MacOS"
    mkdir -p "${APP_DIR}/Contents/Resources"

    cat << EOF > "${APP_DIR}/Contents/MacOS/ShellArc_Desktop"
#!/bin/bash
export SHELLARC_PROJECT_CTX="${SCRIPT_DIR}/project_ctx"
"${VENV_DIR}/bin/python3" "${SCRIPT_DIR}/shellarc_desktop/shellarc_desktop.py"
EOF

    if [ -f "${SCRIPT_DIR}/null_logo.png" ] && command -v iconutil &> /dev/null; then
        echo "アイコンを生成中..."
        mkdir -p "${SCRIPT_DIR}/tmp.iconset"
        sips -z 512 512 "${SCRIPT_DIR}/null_logo.png" --out "${SCRIPT_DIR}/tmp.iconset/icon_256x256@2x.png" &> /dev/null
        iconutil -c icns "${SCRIPT_DIR}/tmp.iconset" -o "${APP_DIR}/Contents/Resources/icon.icns" &> /dev/null
    fi

    cat << EOF > "${APP_DIR}/Contents/Info.plist"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>ShellArc_Desktop</string>
    <key>CFBundleIconFile</key>
    <string>icon</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
</dict>
</plist>
EOF

    chmod +x "${APP_DIR}/Contents/MacOS/ShellArc_Desktop"
    
    touch "${APP_DIR}"
    
    echo "デスクトップにショートカットを作成しました。"
}

read -p "デスクトップにショートカットを登録しますか? (Y/n): " confirmation
if [ "$confirmation" = "Y" ] || [ "$confirmation" = "y" ] || [ -z "$confirmation" ]; then
    set_shortcut
fi