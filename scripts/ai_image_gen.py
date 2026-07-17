#!/usr/bin/env python3
"""
AI 图片生成封装模块
封装 nano-banana-pro 生图能力，提供统一的图片生成接口。
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Optional

# nano-banana-pro 脚本路径
NANO_BANANA_SCRIPT = "/root/.codebuddy/plugins/cache/codebuddy-plugins-official/hot-skills/8ae4a251815a/skills/nano-banana-pro/scripts/generate_image.py"


def generate_image(
    prompt: str,
    output_path: str,
    input_image: Optional[str] = None,
    resolution: str = "2K",
    api_key: Optional[str] = None,
) -> dict:
    """
    使用 nano-banana-pro 生成图片。

    Args:
        prompt: 图片描述/生图指令
        output_path: 输出图片路径
        input_image: 输入图片路径（用于图片编辑/变换）
        resolution: 分辨率 1K/2K/4K
        api_key: Gemini API Key

    Returns:
        dict: {"success": bool, "path": str, "error": str}
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = ["uv", "run", NANO_BANANA_SCRIPT,
           "--prompt", prompt,
           "--filename", str(output_path),
           "--resolution", resolution]

    if input_image:
        cmd.extend(["--input-image", input_image])
    if api_key:
        cmd.extend(["--api-key", api_key])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(output_path.parent)
        )

        if result.returncode == 0 and output_path.exists():
            return {"success": True, "path": str(output_path), "error": ""}
        else:
            return {"success": False, "path": "", "error": result.stderr or result.stdout}
    except subprocess.TimeoutExpired:
        return {"success": False, "path": "", "error": "生图超时（120s）"}
    except Exception as e:
        return {"success": False, "path": "", "error": str(e)}


def generate_product_scene(
    product_desc: str,
    scene_desc: str,
    brand_style: str,
    output_path: str,
    resolution: str = "2K",
) -> dict:
    """
    生成产品场景图。

    Args:
        product_desc: 产品描述
        scene_desc: 场景描述
        brand_style: 品牌调性
        output_path: 输出路径
        resolution: 分辨率

    Returns:
        dict: 生成结果
    """
    prompt = f"""
    Product photography: {product_desc}
    Scene: {scene_desc}
    Style: {brand_style}
    Requirements:
    - Professional commercial photography quality
    - Natural lighting, soft shadows
    - High detail, sharp focus
    - Clean and modern composition
    - Suitable for e-commerce use
    """
    return generate_image(prompt.strip(), output_path, resolution=resolution)


def generate_external_prompt(
    image_name: str,
    product_desc: str,
    scene_desc: str,
    brand_style: str,
    gen_purpose: str,
    recommended_tools: list = None,
) -> str:
    """
    生成外部生图工具的结构化Prompt指令（当AI无法直接生成时使用）。

    Args:
        image_name: 图片名称
        product_desc: 产品描述
        scene_desc: 场景描述
        brand_style: 品牌调性
        gen_purpose: 用途说明
        recommended_tools: 推荐工具列表

    Returns:
        str: Markdown格式的生图指令
    """
    if recommended_tools is None:
        recommended_tools = ["Midjourney V6", "即梦 AI", "可灵 AI", "Stable Diffusion XL"]

    prompt_en = f"""
Professional e-commerce product photography.
Product: {product_desc}
Scene: {scene_desc}
Style: {brand_style}
Requirements: commercial quality, studio lighting, high detail, sharp focus, clean composition.
""".strip()

    prompt_zh = f"""
专业电商产品摄影。
产品：{product_desc}
场景：{scene_desc}
风格：{brand_style}
要求：商业级画质，影棚光效，高细节，锐利对焦，干净构图，适合电商使用。
""".strip()

    md = f"""# 生图指令：{image_name}

## 用途
{gen_purpose}

## 推荐工具
"""
    for tool in recommended_tools:
        md += f"- {tool}\n"

    md += f"""

## 英文 Prompt（适用于 Midjourney / Stable Diffusion）

```
{prompt_en}
```

### Midjourney 参数建议
```
--ar 1:1 --v 6 --style raw --quality 2
```

### Stable Diffusion 参数建议
- 采样器：DPM++ 2M Karras
- 步数：30-40
- CFG Scale：7-8
- 尺寸：1024×1024

## 中文 Prompt（适用于即梦/可灵）

```
{prompt_zh}
```

### 即梦 AI 参数建议
- 模式：精细模式
- 尺寸：1:1 或 3:4
- 风格：摄影风格

### 可灵 AI 参数建议
- 画质：高清
- 风格：商业摄影

## 注意事项
1. 实物产品图建议使用 **图生图** 模式，上传产品白底图作为参考
2. 保持产品外观一致性，避免AI擅自修改产品形态
3. 生成后建议用 Photoshop 进行最终排版和文字叠加
4. 如需添加文字，建议在AI生成图片后用 Pillow/PS 后期合成
"""
    return md
