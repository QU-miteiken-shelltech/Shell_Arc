import requests

headers = {
    "Content-Type": "application/json",
    "Authorization": "xxxxxx"
}

data = {
    "input": {
        # 1. 送信する画像データのリスト
        "images": [
            {
                "name": "test.png",
                "image": (
                    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAIAAAD8GO2jAAAAMklEQVR4nGI5ZdXAQEvARFPTRy0YtWDUglELRi0YtWDUglELRi0YtWDUAioCQAAAAP//E24Bx3jUKuYAAAAASUVORK5CYII="
                ),
            }
        ],
        "workflow": {
            # ノード6: ポジティブプロンプト
            "6": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": "anime cat with massive fluffy fennec ears...",
                    "clip": ["30", 1],
                },
                "_meta": {"title": "CLIP Text Encode (Positive Prompt)"},
            },
            # ノード8: VAEデコード（潜在表現を画像に戻す）
            "8": {
                "class_type": "VAEDecode",
                "inputs": {"samples": ["31", 0], "vae": ["30", 2]},
                "_meta": {"title": "VAE Decode"},
            },
            # ノード9: 画像保存
            "9": {
                "class_type": "SaveImage",
                "inputs": {"filename_prefix": "ComfyUI", "images": ["8", 0]},
                "_meta": {"title": "Save Image"},
            },
            # ノード27: 空のLatent画像生成（サイズやバッチ数）
            "27": {
                "class_type": "EmptySD3LatentImage",
                "inputs": {"width": 512, "height": 512, "batch_size": 1},
                "_meta": {"title": "EmptySD3LatentImage"},
            },
            # ノード30: チェックポイント（モデル）の読み込み
            "30": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": "flux1-dev-fp8.safetensors"},
                "_meta": {"title": "Load Checkpoint"},
            },
            # ノード31: サンプラー（生成のメイン処理）
            "31": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": 243057879077961,
                    "steps": 10,
                    "cfg": 1,
                    "sampler_name": "euler",
                    "scheduler": "simple",
                    "denoise": 1,
                    "model": ["30", 0],
                    "positive": ["35", 0],
                    "negative": ["33", 0],
                    "latent_image": ["27", 0],
                },
                "_meta": {"title": "KSampler"},
            },
            # ノード33: ネガティブプロンプト
            "33": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": "", "clip": ["30", 1]},
                "_meta": {"title": "CLIP Text Encode (Negative Prompt)"},
            },
            # ノード35: Flux専用ガイダンス
            "35": {
                "class_type": "FluxGuidance",
                "inputs": {"guidance": 3.5, "conditioning": ["6", 0]},
                "_meta": {"title": "FluxGuidance"},
            },
            # ノード38: 画像プレビュー
            "38": {
                "class_type": "PreviewImage",
                "inputs": {"images": ["8", 0]},
                "_meta": {"title": "Preview Image"},
            },
            # ノード40: 画像保存（重複）
            "40": {
                "class_type": "SaveImage",
                "inputs": {"filename_prefix": "ComfyUI", "images": ["8", 0]},
                "_meta": {"title": "Save Image"},
            },
        },
    }
}

response = requests.post('https://api.runpod.ai/v2/2720l0arwhwpvj/runsync', headers=headers, json=data)