#!/usr/bin/env python3
"""
图片合成模块
使用 Pillow 进行图文排版合成：参数表、卖点图、促销图等。
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path
from typing import Optional
import json
import textwrap

# 默认字体路径（系统中文字体）
FONT_PATHS = [
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
]

# 品牌配色默认值
DEFAULT_COLORS = {
    "bg_white": (255, 255, 255),
    "bg_light": (245, 245, 247),
    "text_primary": (33, 33, 33),
    "text_secondary": (102, 102, 102),
    "accent": (255, 107, 53),  # 橙色强调
    "accent_dark": (230, 81, 0),
    "gradient_start": (255, 255, 255),
    "gradient_end": (240, 240, 245),
}


def get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """获取字体"""
    for fp in FONT_PATHS:
        if Path(fp).exists():
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                continue
    # fallback
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except Exception:
        return ImageFont.load_default()


def find_chinese_font() -> Optional[str]:
    """查找系统中文字体"""
    for fp in FONT_PATHS:
        if Path(fp).exists():
            return fp
    return None


def create_gradient_bg(width: int, height: int, color_start: tuple, color_end: tuple) -> Image.Image:
    """创建渐变背景"""
    img = Image.new("RGB", (width, height), color_start)
    draw = ImageDraw.Draw(img)
    for y in range(height):
        ratio = y / height
        r = int(color_start[0] + (color_end[0] - color_start[0]) * ratio)
        g = int(color_start[1] + (color_end[1] - color_start[1]) * ratio)
        b = int(color_start[2] + (color_end[2] - color_start[2]) * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    return img


def compose_selling_point_image(
    title: str,
    subtitle: str,
    detail: str,
    output_path: str,
    size: tuple = (1080, 1080),
    bg_color: tuple = None,
    product_image: str = None,
    accent_color: tuple = None,
) -> str:
    """
    合成卖点图（图文排版）

    Args:
        title: 卖点标题
        subtitle: 副标题
        detail: 详细文案
        output_path: 输出路径
        size: 图片尺寸
        bg_color: 背景色
        product_image: 产品图路径（可选）
        accent_color: 强调色

    Returns:
        str: 输出图片路径
    """
    width, height = size
    bg_color = bg_color or DEFAULT_COLORS["bg_light"]
    accent_color = accent_color or DEFAULT_COLORS["accent"]

    # 创建背景
    img = create_gradient_bg(width, height, DEFAULT_COLORS["gradient_start"], DEFAULT_COLORS["gradient_end"])
    draw = ImageDraw.Draw(img)

    # 如果有产品图，放置在右侧或中间
    if product_image and Path(product_image).exists():
        try:
            prod_img = Image.open(product_image).convert("RGBA")
            # 缩放产品图
            max_prod_size = int(width * 0.5)
            prod_img.thumbnail((max_prod_size, max_prod_size), Image.LANCZOS)
            # 居中偏下放置
            prod_x = (width - prod_img.width) // 2
            prod_y = int(height * 0.35)
            img.paste(prod_img, (prod_x, prod_y), prod_img if prod_img.mode == 'RGBA' else None)
        except Exception:
            pass

    # 标题
    font_title = get_font(int(width * 0.055), bold=True)
    font_subtitle = get_font(int(width * 0.035))
    font_detail = get_font(int(width * 0.028))

    # 绘制强调色装饰条
    margin = int(width * 0.08)
    draw.rectangle([margin, int(height * 0.08), margin + 6, int(height * 0.08) + int(width * 0.05)], fill=accent_color)

    # 标题文字
    draw.text((margin + 20, int(height * 0.075)), title, font=font_title, fill=DEFAULT_COLORS["text_primary"])

    # 副标题
    if subtitle:
        draw.text((margin + 20, int(height * 0.075) + int(width * 0.065)), subtitle,
                  font=font_subtitle, fill=DEFAULT_COLORS["text_secondary"])

    # 详细文案（自动换行）
    if detail:
        max_chars = int(width * 0.84 / int(width * 0.028 * 0.5))
        lines = textwrap.wrap(detail, width=max_chars)
        y = int(height * 0.78)
        for line in lines:
            draw.text((margin, y), line, font=font_detail, fill=DEFAULT_COLORS["text_secondary"])
            y += int(width * 0.04)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path), "PNG", quality=95)
    return str(output_path)


def compose_spec_table(
    params: dict,
    title: str = "产品参数",
    output_path: str = None,
    size: tuple = (750, 700),
    bg_color: tuple = None,
) -> str:
    """
    合成参数规格表图片

    Args:
        params: 参数字典
        title: 表格标题
        output_path: 输出路径
        size: 图片尺寸
        bg_color: 背景色

    Returns:
        str: 输出路径
    """
    width, height = size
    bg_color = bg_color or DEFAULT_COLORS["bg_white"]

    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    margin = int(width * 0.08)
    content_width = width - 2 * margin

    font_title = get_font(int(width * 0.05), bold=True)
    font_label = get_font(int(width * 0.035))
    font_value = get_font(int(width * 0.035))

    # 标题
    draw.text((margin, int(height * 0.05)), title, font=font_title, fill=DEFAULT_COLORS["text_primary"])

    # 装饰线
    draw.line([(margin, int(height * 0.05) + int(width * 0.06)),
               (margin + 40, int(height * 0.05) + int(width * 0.06))],
              fill=DEFAULT_COLORS["accent"], width=4)

    # 参数表格
    y = int(height * 0.05) + int(width * 0.1)
    row_height = int(width * 0.07)
    col_label_width = int(content_width * 0.4)
    col_value_x = margin + col_label_width

    for key, value in params.items():
        # 交替背景
        if list(params.keys()).index(key) % 2 == 0:
            draw.rectangle([margin, y, margin + content_width, y + row_height],
                          fill=DEFAULT_COLORS["bg_light"])

        draw.text((margin + 15, y + 10), str(key), font=font_label, fill=DEFAULT_COLORS["text_secondary"])
        draw.text((col_value_x + 15, y + 10), str(value), font=font_value, fill=DEFAULT_COLORS["text_primary"])

        # 分隔线
        draw.line([(margin, y), (margin + content_width, y)],
                  fill=(224, 224, 224), width=1)
        y += row_height

    # 底部分隔线
    draw.line([(margin, y), (margin + content_width, y)], fill=(224, 224, 224), width=1)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path), "PNG", quality=95)
    return str(output_path)


def compose_promo_image(
    product_name: str,
    promo_text: str,
    cta: str,
    output_path: str,
    size: tuple = (1080, 1080),
    bg_color: tuple = None,
    product_image: str = None,
) -> str:
    """
    合成促销图

    Args:
        product_name: 产品名
        promo_text: 促销文案
        cta: 行动号召
        output_path: 输出路径
        size: 尺寸
        bg_color: 背景色
        product_image: 产品图

    Returns:
        str: 输出路径
    """
    width, height = size
    accent = DEFAULT_COLORS["accent"]

    # 渐变背景
    img = create_gradient_bg(width, height, (255, 248, 240), (255, 235, 210))
    draw = ImageDraw.Draw(img)

    # 如果有产品图
    if product_image and Path(product_image).exists():
        try:
            prod_img = Image.open(product_image).convert("RGBA")
            max_prod_size = int(width * 0.55)
            prod_img.thumbnail((max_prod_size, max_prod_size), Image.LANCZOS)
            prod_x = (width - prod_img.width) // 2
            prod_y = int(height * 0.15)
            img.paste(prod_img, (prod_x, prod_y), prod_img if prod_img.mode == 'RGBA' else None)
        except Exception:
            pass

    margin = int(width * 0.08)
    font_promo = get_font(int(width * 0.075), bold=True)
    font_cta = get_font(int(width * 0.045), bold=True)

    # 促销文案
    draw.text((margin, int(height * 0.68)), promo_text, font=font_promo, fill=accent)

    # CTA按钮
    cta_y = int(height * 0.82)
    cta_width = int(width * 0.5)
    cta_height = int(width * 0.1)
    cta_x = (width - cta_width) // 2
    draw.rounded_rectangle([cta_x, cta_y, cta_x + cta_width, cta_y + cta_height],
                          radius=int(cta_height * 0.2), fill=accent)
    # CTA文字居中
    cta_text_bbox = draw.textbbox((0, 0), cta, font=font_cta)
    cta_text_w = cta_text_bbox[2] - cta_text_bbox[0]
    cta_text_h = cta_text_bbox[3] - cta_text_bbox[1]
    draw.text((cta_x + (cta_width - cta_text_w) // 2, cta_y + (cta_height - cta_text_h) // 2 - 5),
              cta, font=font_cta, fill=(255, 255, 255))

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path), "PNG", quality=95)
    return str(output_path)


def compose_comparison_image(
    title: str,
    items: list,
    output_path: str,
    size: tuple = (1080, 1080),
    product_image: str = None,
) -> str:
    """
    合成对比图

    Args:
        title: 标题
        items: 对比项列表 [{"dimension": "", "ours": "", "competitor": ""}]
        output_path: 输出路径
        size: 尺寸
        product_image: 产品图

    Returns:
        str: 输出路径
    """
    width, height = size
    img = Image.new("RGB", (width, height), DEFAULT_COLORS["bg_white"])
    draw = ImageDraw.Draw(img)

    margin = int(width * 0.08)
    content_width = width - 2 * margin

    font_title = get_font(int(width * 0.05), bold=True)
    font_header = get_font(int(width * 0.032), bold=True)
    font_cell = get_font(int(width * 0.03))

    # 标题
    draw.text((margin, int(height * 0.05)), title, font=font_title, fill=DEFAULT_COLORS["text_primary"])
    draw.line([(margin, int(height * 0.05) + int(width * 0.06)),
               (margin + 40, int(height * 0.05) + int(width * 0.06))],
              fill=DEFAULT_COLORS["accent"], width=4)

    # 表格
    y = int(height * 0.18)
    col_w = content_width // 3

    # 表头
    headers = ["对比维度", "本产品", "普通产品"]
    for i, h in enumerate(headers):
        x = margin + i * col_w
        draw.rectangle([x, y, x + col_w, y + int(width * 0.06)], fill=DEFAULT_COLORS["accent"])
        draw.text((x + 15, y + 10), h, font=font_header, fill=(255, 255, 255))

    y += int(width * 0.06)

    # 数据行
    for item in items:
        cells = [item.get("dimension", ""), item.get("ours", ""), item.get("competitor", "")]
        for i, cell in enumerate(cells):
            x = margin + i * col_w
            bg = DEFAULT_COLORS["bg_light"] if i == 1 else DEFAULT_COLORS["bg_white"]
            draw.rectangle([x, y, x + col_w, y + int(width * 0.055)], fill=bg)
            color = DEFAULT_COLORS["accent_dark"] if i == 1 else DEFAULT_COLORS["text_secondary"]
            draw.text((x + 15, y + 8), str(cell), font=font_cell, fill=color)

        draw.line([(margin, y + int(width * 0.055)), (margin + content_width, y + int(width * 0.055))],
                  fill=(224, 224, 224), width=1)
        y += int(width * 0.055)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path), "PNG", quality=95)
    return str(output_path)
