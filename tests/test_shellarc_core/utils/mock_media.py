"""
byteのIO経路（添付 -> アップロード -> Mockストレージへの書き込み）を確認するための、
超軽量な疑似メディアファイルを生成するモジュール。

実装方針（判断事項）:
- PNG / GIF は「本物として正しく開ける」最小限のバイナリを実際に組み立てている
  （1x1ピクセルの本物のPNG/GIF）。画像ビューアで開いても壊れない。
- JPEG / MP4 は完全な仕様準拠エンコーダを書くコストが高いため、
  「ファイル先頭のマジックバイト（シグネチャ）とコンテナ構造の形だけ」を正しくした
  軽量なダミーにしている。実際の画像/動画としては開けない可能性が高いが、
  「拡張子を選んだらそれらしいバイナリが添付される」というテストの目的には十分。
  この制限はコード内コメントにも明記している。
"""

import base64
import struct
import zlib


def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    chunk = chunk_type + data
    crc = zlib.crc32(chunk) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + chunk + struct.pack(">I", crc)


def make_fake_png() -> bytes:
    """本物として開ける、1x1ピクセル(赤)の正真正銘のPNGバイナリを生成する。"""
    signature = b"\x89PNG\r\n\x1a\n"
    width, height = 1, 1
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)  # 8bit, RGB
    ihdr_chunk = _png_chunk(b"IHDR", ihdr)
    raw_scanline = b"\x00" + bytes([255, 0, 0])  # filter byte + 赤ピクセル
    idat_chunk = _png_chunk(b"IDAT", zlib.compress(raw_scanline))
    iend_chunk = _png_chunk(b"IEND", b"")
    return signature + ihdr_chunk + idat_chunk + iend_chunk


# 1x1の透明GIF(89a) - 広く使われている既知の最小構成をそのままデコードして使う。
_MINIMAL_GIF_B64 = "R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=="


def make_fake_gif() -> bytes:
    """本物として開ける、1x1ピクセルの透明GIFバイナリを生成する。"""
    return base64.b64decode(_MINIMAL_GIF_B64)


def make_fake_jpg() -> bytes:
    """
    JPEGのマジックバイト(SOI/EOI)とAPP0(JFIF)セグメントの形だけを持つ軽量ダミー。
    正しくレンダリングできる本物のJPEGではない点に注意。
    """
    soi = bytes.fromhex("FFD8")
    app0 = bytes.fromhex("FFE0000A4A46494600010100")  # JFIFマーカーの雛形
    fake_payload = b"MOCKJPEGDATA-not-a-real-image"
    eoi = bytes.fromhex("FFD9")
    return soi + app0 + fake_payload + eoi


def make_fake_mp4() -> bytes:
    """
    MP4コンテナのbox構造(ftyp + mdat)だけを持つ軽量ダミー。
    正しく再生できる本物の動画ではない点に注意。
    """
    ftyp_body = b"isom" + struct.pack(">I", 0) + b"isom"
    ftyp_box = struct.pack(">I", 8 + len(ftyp_body)) + b"ftyp" + ftyp_body
    mdat_payload = b"MOCKVIDEODATA-not-a-real-video"
    mdat_box = struct.pack(">I", 8 + len(mdat_payload)) + b"mdat" + mdat_payload
    return ftyp_box + mdat_box


# 拡張子 -> (生成関数, デフォルトファイル名)
MOCK_MEDIA_GENERATORS = {
    "png": (make_fake_png, "mock_image.png"),
    "gif": (make_fake_gif, "mock_image.gif"),
    "jpg": (make_fake_jpg, "mock_image.jpg"),
    "mp4": (make_fake_mp4, "mock_video.mp4"),
}


def generate_mock_file(ext: str) -> tuple[str, bytes]:
    """指定した拡張子の疑似メディアファイルの (ファイル名, バイト列) を返す。"""
    ext = ext.lower().lstrip(".")
    if ext not in MOCK_MEDIA_GENERATORS:
        raise ValueError(f"Unsupported mock media extension: {ext}")
    generator, filename = MOCK_MEDIA_GENERATORS[ext]
    return filename, generator()
