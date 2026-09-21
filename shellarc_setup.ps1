$ScriptDir = Split-Path -Parent$MyInvocation.MyCommand.Definition

# Python の存在確認
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "ShellArc を使うのに、Pythonをインストールする必要があります"
    Write-Host "Pythonをインストールしてください"
    $hasTutorial = Read-Host "Pythonインストールのチュートリアルが必要ですか? (Y/n)"
    if ($hasTutorial -eq "Y" -or $hasTutorial -eq "y" -or [string]::IsNullOrWhiteSpace($hasTutorial)) {
        $tutorialPath = Join-Path$ScriptDir "python_install_tutorial.txt"
        if (Test-Path $tutorialPath) {
            Get-Content $tutorialPath
        } else {
            Write-Host "チュートリアルファイル（python_install_tutorial.txt）が見つかりません。"
        }
    }
    exit 1
}

$VenvDir = Join-Path$ScriptDir "venv"
$VenvPython = Join-Path$VenvDir "Scripts\python.exe"

# PowerShell プロファイルに環境変数・エイリアス関数を追記
$ProfilePath =$PROFILE
if (-not (Test-Path $ProfilePath)) {
    New-Item -Type File -Path $ProfilePath -Force | Out-Null
}

$EnvLine = "`$env:SHELLARC_PROJECT_CTX = `"$ScriptDir\project_ctx`""
$FunctionLine = "function shellarc { & `"$VenvPython`" `"$ScriptDir\shellarc_desktop\shellarc_desktop.py`" `$args }"

Write-Host "環境設定を追記中..."
Add-Content -Path $ProfilePath -Value "`n# Appended by ShellArc"
if (-not (Select-String -Path $ProfilePath -Pattern [regex]::Escape($EnvLine) -Quiet)) {
    Add-Content -Path $ProfilePath -Value $EnvLine
}
if (-not (Select-String -Path $ProfilePath -Pattern [regex]::Escape("function shellarc") -Quiet)) {
    Add-Content -Path $ProfilePath -Value $FunctionLine
}
Add-Content -Path $ProfilePath -Value "# ShellArc END"

Write-Host "Python仮想環境を作成中..."
python -m venv $VenvDir

Write-Host "pipをアップグレード中..."
& $VenvPython -m pip install --upgrade pip

Write-Host "ディペンデンシーをインストール中..."
& $VenvPython -m pip install -e $ScriptDir

$SecretKey = Read-Host "秘密鍵を入力してください"
$env:EXPORT_SECRET_KEY = $SecretKey
$env:EXPORT_SCRIPT_DIR = $ScriptDir

# Python スクリプトの実行（復号処理）
$pythonCode = @"
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
"@

& $VenvPython -c $pythonCode

Remove-Item Env:\EXPORT_SECRET_KEY
Remove-Item Env:\EXPORT_SCRIPT_DIR

Write-Host "--------------------------------------------------"
Write-Host "設定を反映するには PowerShell を再起動するか、以下を実行してください:"
Write-Host ". `$PROFILE"
Write-Host "以降は、ターミナルから 'shellarc' コマンドで起動できます"
Write-Host "--------------------------------------------------"

# デスクトップショートカット登録関数
function Set-Shortcut {
    $DesktopPath = [Environment]::GetFolderPath("Desktop")
    $ShortcutPath = Join-Path$DesktopPath "ShellArc Desktop.lnk"
    
    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut =$WshShell.CreateShortcut($ShortcutPath)$Shortcut.TargetPath = $VenvPython$Shortcut.Arguments = "`"$ScriptDir\shellarc_desktop\shellarc_desktop.py`""
    $Shortcut.WorkingDirectory =$ScriptDir
    
    # ロゴ画像が存在する場合はアイコンに設定
    $LogoPath = Join-Path$ScriptDir "null_logo.png"
    if (Test-Path $LogoPath) {
        # 注: 通常のWindowsショートカットアイコンには .ico ファイル指定が推奨されます
        $Shortcut.IconLocation =$LogoPath
    }
    
    $Shortcut.Save()
    Write-Host "デスクトップにショートカットを作成しました。"
}

$Confirmation = Read-Host "デスクトップにショートカットを登録しますか? (Y/n)"
if ($Confirmation -eq "Y" -or $Confirmation -eq "y" -or [string]::IsNullOrWhiteSpace($Confirmation)) {
    Set-Shortcut
}
