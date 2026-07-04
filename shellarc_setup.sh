#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "export SHELLARC_PROJECT_CTX=\"${SCRIPT_DIR}/project_ctx\"" >> ~/.zshrc

VENV_DIR="${SCRIPT_DIR}/venv"
python3 -m venv "${VENV_DIR}"
"${VENV_DIR}/bin/python3" -m pip install --upgrade pip
"${VENV_DIR}/bin/python3" -m pip install -e "${SCRIPT_DIR}"

echo "alias shellarc='${VENV_DIR}/bin/python3 ${SCRIPT_DIR}/shellarc_desktop/shellarc_desktop.py'" >> ~/.zshrc

echo "設定を反映するには: source ~/.zshrc を実行してください"
echo "以降は、shellarc コマンドでバックアップを実行できます"
read -p "デスクトップにショートカットを登録しますか? (Y/n): " confirmation

function set_shortcut(){
    mkdir -p ~/Desktop/ShellArc_Desktop.app/Contents/MacOS
    mkdir -p ~/Desktop/ShellArc_Desktop.app/Contents/Resources

    cat << EOF > ~/Desktop/ShellArc_Desktop.app/Contents/MacOS/ShellArc_Desktop
#!/bin/bash
"${VENV_DIR}/bin/python3" "${SCRIPT_DIR}/shellarc_desktop/shellarc_desktop.py"
EOF

    if [ -f "${SCRIPT_DIR}/null_logo.png" ]; then
        sips -s format icns "${SCRIPT_DIR}/null_logo.png" --out ~/Desktop/ShellArc_Desktop.app/Contents/Resources/icon.icns 2>/dev/null
    fi

    cat << EOF > ~/Desktop/ShellArc_Desktop.app/Contents/Info.plist
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>ShellArc_Desktop</string>
    <key>CFBundleIconFile</key>
    <string>icon</string>
</dict>
</plist>
EOF

    chmod +x ~/Desktop/ShellArc_Desktop.app/Contents/MacOS/ShellArc_Desktop
    echo "デスクトップにショートカットを作成しました。"
}

if [ "$confirmation" = "Y" ] || [ "$confirmation" = "y" ]; then
    set_shortcut
else
    :
fi