import os
import platform
import glob
import shutil

# 主要な2D・3Dデザイン・DCCツールの定義
# 各ツールの実行ファイル名（PATH用）と、代表的なインストールパス（ワイルドカード対応）を指定
DCC_TOOLS = {
    # 3D DCC Tools
    "Blender": {
        "executables": ["blender"],
        "paths": [r"C:\Program Files\Blender Foundation\Blender *", "/Applications/Blender.app"]
    },
    "Maya": {
        "executables": ["maya"],
        "paths": [r"C:\Program Files\Autodesk\Maya*", "/Applications/Autodesk/maya*"]
    },
    "3ds Max": {
        "executables": ["3dsmax"],
        "paths": [r"C:\Program Files\Autodesk\3ds Max*"]
    },
    "Cinema 4D": {
        "executables": ["Cinema 4D"],
        "paths": [r"C:\Program Files\Maxon Cinema 4D*", "/Applications/Maxon Cinema 4D*"]
    },
    "Houdini": {
        "executables": ["houdini"],
        "paths": [r"C:\Program Files\Side Effects Software\Houdini*", "/Applications/Houdini*"]
    },
    "ZBrush": {
        "executables": ["ZBrush"],
        "paths": [r"C:\Program Files\Maxon ZBrush*", r"C:\Program Files\Pixologic\ZBrush*", "/Applications/ZBrush*"]
    },
    "Rhino": {
        "executables": ["rhino"],
        "paths": [r"C:\Program Files\Rhino *", "/Applications/Rhino*.app"]
    },
    "SketchUp": {
        "executables": ["SketchUp"],
        "paths": [r"C:\Program Files\SketchUp\SketchUp *", "/Applications/SketchUp *"]
    },

    # 2D Design Tools
    "Photoshop": {
        "executables": ["photoshop"],
        "paths": [r"C:\Program Files\Adobe\Adobe Photoshop *", "/Applications/Adobe Photoshop *"]
    },
    "Illustrator": {
        "executables": ["illustrator"],
        "paths": [r"C:\Program Files\Adobe\Adobe Illustrator *", "/Applications/Adobe Illustrator *"]
    },
    "GIMP": {
        "executables": ["gimp", "gimp-2.10"],
        "paths": [r"C:\Program Files\GIMP 2\bin\gimp-*", "/Applications/GIMP*.app"]
    },
    "Krita": {
        "executables": ["krita"],
        "paths": [r"C:\Program Files\Krita\bin\krita.exe", "/Applications/Krita.app"]
    },
    "Inkscape": {
        "executables": ["inkscape"],
        "paths": [r"C:\Program Files\Inkscape\bin\inkscape.exe", "/Applications/Inkscape.app"]
    },
    "Affinity Designer": {
        "executables": [],
        "paths": [r"C:\Program Files\Affinity\Designer*", "/Applications/Affinity Designer*.app"]
    },
    "Affinity Photo": {
        "executables": [],
        "paths": [r"C:\Program Files\Affinity\Photo*", "/Applications/Affinity Photo*.app"]
    },
    "Clip Studio Paint": {
        "executables": [],
        "paths": [r"C:\Program Files\CELSYS\CLIP STUDIO 1.5\CLIP STUDIO PAINT\CLIPStudioPaint.exe", "/Applications/CLIP STUDIO PAINT.app"]
    }
}

def _check_tool_exists(tool_info):
    # 1. 環境変数のPATHから実行ファイルを検索
    for exe in tool_info.get("executables", []):
        if shutil.which(exe):
            return True
            
    # 2. 定番のインストールパスを glob でパターンマッチ検索
    for path_pattern in tool_info.get("paths", []):
        expanded_pattern = os.path.expandvars(path_pattern)
        if glob.glob(expanded_pattern):
            return True
            
    return False

def find_design_tools():
    """
    システム上の2D/3Dデザイン・DCCツールを検索し、
    存在する場合は辞書を返し、ない場合は None を返す。
    """
    found_tools = {}
    
    for tool_name, info in DCC_TOOLS.items():
        if _check_tool_exists(info):
            found_tools[tool_name] = "Installed"
            
    # 一つも検出されなかった場合は None を返す
    if not found_tools:
        return None
        
    return found_tools

if __name__ == "__main__":
    result = find_design_tools()
    
    if result is None:
        print(None)
    else:
        print("検出されたデザイン・DCCツール:")
        for tool in result:
            print(f"- {tool}")
