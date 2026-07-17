#!/usr/bin/env python3
"""
Prompt 构建器
根据产品信息、图片类型、品牌调性，构建各类图片的生图指令和文案。
"""

import json
from pathlib import Path
from typing import Optional

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


class PromptBuilder:
    """根据产品信息和模板，构建图片生成指令和文案内容。"""

    def __init__(self, product_name: str, product_type: str, params: dict, brand_style: str = ""):
        self.product_name = product_name
        self.product_type = product_type
        self.params = params
        self.brand_style = brand_style or "现代简约，专业商业风格"

        # 加载卖点库和痛点库
        self.selling_points = self._load_json(TEMPLATES_DIR / "selling_points.json")
        self.pain_points = self._load_json(TEMPLATES_DIR / "pain_points.json")

        # 加载排版模板
        self.main_layout = self._load_json(TEMPLATES_DIR / "main_image_layout.json")
        self.detail_layout = self._load_json(TEMPLATES_DIR / "detail_page_layout.json")
        self.ad_layout = self._load_json(TEMPLATES_DIR / "ad_layout.json")

        # 匹配品类
        self.category = self._match_category()

    def _load_json(self, path: Path) -> dict:
        """加载JSON文件"""
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _match_category(self) -> str:
        """根据产品类型匹配卖点库品类"""
        for cat_name, cat_data in self.selling_points.get("categories", {}).items():
            subcats = cat_data.get("subcategories", [])
            for sub in subcats:
                if sub.lower() in self.product_type.lower() or self.product_type.lower() in sub.lower():
                    return cat_name
            if cat_name in self.product_type:
                return cat_name
        # 默认返回第一个品类
        return list(self.selling_points.get("categories", {}).keys())[0] if self.selling_points else ""

    def get_matched_selling_points(self) -> list:
        """获取匹配的卖点列表"""
        cat_data = self.selling_points.get("categories", {}).get(self.category, {})
        points = cat_data.get("selling_points", [])

        # 根据产品参数过滤适用卖点
        matched = []
        for point in points:
            applicable = point.get("applicable_params", [])
            if not applicable:
                # 无参数依赖，直接加入
                matched.append(point)
            else:
                # 检查是否有匹配的参数
                if any(p in self.params for p in applicable):
                    matched.append(point)
        return matched

    def get_matched_pain_points(self) -> list:
        """获取匹配的痛点列表"""
        cat_data = self.pain_points.get("categories", {}).get(self.category, {})
        return cat_data.get("pain_points", [])

    def fill_selling_point_template(self, point: dict) -> str:
        """填充卖点模板"""
        template = point.get("detail_template", "")
        applicable = point.get("applicable_params", [])
        for param_key in applicable:
            placeholder = "{" + param_key + "}"
            value = self.params.get(param_key, "")
            if value:
                template = template.replace(placeholder, str(value))
            else:
                template = template.replace(placeholder, "")
        # 清理未填充的占位符
        import re
        template = re.sub(r'\{[^}]+\}', '', template)
        return template

    def generate_selling_points_md(self) -> str:
        """生成卖点提炼Markdown"""
        points = self.get_matched_selling_points()

        md = f"""# {self.product_name} 卖点提炼

## 产品信息
- 产品名称：{self.product_name}
- 产品类型：{self.product_type}
- 匹配品类：{self.category}

## 核心卖点

| 序号 | 卖点 | 描述 | 详细文案 |
|------|------|------|---------|
"""
        for i, p in enumerate(points, 1):
            detail = self.fill_selling_point_template(p)
            md += f"| {i} | {p['title']} | {p['description']} | {detail} |\n"

        md += f"""
## 卖点优先级建议（电商主图/详情页使用顺序）

1. **第一梯队**（主图首图+详情页首屏）：{points[0]['title'] if points else '核心卖点'}
2. **第二梯队**（主图2-3+详情页详解）：{points[1]['title'] if len(points) > 1 else '功能亮点'}, {points[2]['title'] if len(points) > 2 else '使用场景'}
3. **第三梯队**（详情页补充）：{', '.join([p['title'] for p in points[3:]]) if len(points) > 3 else '其他卖点'}
"""
        return md

    def generate_pain_points_md(self) -> str:
        """生成痛点场景Markdown"""
        points = self.get_matched_pain_points()

        md = f"""# {self.product_name} 痛点场景分析

## 痛点场景

| 序号 | 场景 | 用户痛点 | 解决方案 | 目标人群 |
|------|------|---------|---------|---------|
"""
        for i, p in enumerate(points, 1):
            md += f"| {i} | {p['scenario']} | {p['pain']} | {p['solution']} | {p['target_audience']} |\n"

        md += """
## 痛点营销建议

- 详情页"使用场景"板块优先展示Top3痛点场景
- 主图场景图选择覆盖最广人群的痛点
- 广告图文案直击核心痛点，一句话引发共鸣
"""
        return md

    def generate_detail_copy_md(self) -> str:
        """生成详情页文案Markdown"""
        points = self.get_matched_selling_points()
        pains = self.get_matched_pain_points()

        # 提取品牌名
        brand = self.params.get("brand", self.product_name)

        md = f"""# {self.product_name} 详情页文案

## 1. 品牌首屏
**Slogan**: {brand} · {points[0]['description'] if points else '品质之选'}
**副标题**: {self.fill_selling_point_template(points[0]) if points else ''}

## 2. 卖点总览
"""
        for i, p in enumerate(points[:4], 1):
            md += f"**卖点{i}**: {p['title']} — {p['description']}\n\n"

        md += f"""
## 3-4. 卖点详解
"""
        for i, p in enumerate(points[:2], 1):
            detail = self.fill_selling_point_template(p)
            md += f"""### 卖点详解{i}: {p['title']}
{detail}

**用户价值**: {p['description']}

---

"""
        # 场景文案
        md += "## 5-6. 使用场景\n\n"
        for i, pain in enumerate(pains[:2], 1):
            md += f"""### 场景{i}: {pain['scenario']}
**痛点**: {pain['pain']}
**解决方案**: {pain['solution']}
**目标人群**: {pain['target_audience']}

"""

        # 参数表
        md += "## 9. 参数规格表\n\n"
        md += "| 参数 | 数值 |\n|------|------|\n"
        for key, value in self.params.items():
            md += f"| {key} | {value} |\n"

        md += f"""
## 11. 品牌故事
{brand}致力于为用户带来{self.category}领域的优质体验。
我们相信，好的产品不仅是工具，更是生活方式的表达。

## 12. 售后保障
- 7天无理由退换
- 15天质量问题免费换新
- 1年质保
- 全国联保

## 13. 行动号召
限时优惠 立即下单
{brand} · 品质保证 · 售后无忧
"""
        return md

    def build_image_prompt(self, slide_config: dict, extra_context: str = "") -> str:
        """
        构建单张图片的生图Prompt。

        Args:
            slide_config: 排版模板中的单张配置
            extra_context: 额外上下文（如具体卖点文案）

        Returns:
            str: 生图Prompt
        """
        keywords = ", ".join(slide_config.get("prompt_keywords", []))
        purpose = slide_config.get("purpose", "")

        prompt = f"""
E-commerce product image generation.
Product: {self.product_name}
Type: {self.product_type}
Purpose: {purpose}
Brand style: {self.brand_style}
Context: {extra_context}
Keywords: {keywords}
Requirements:
- Professional commercial photography quality
- Clean and modern design
- High detail and sharp focus
- Suitable for e-commerce platform
"""
        return prompt.strip()

    def get_product_desc(self) -> str:
        """生成产品描述摘要"""
        brand = self.params.get("brand", "")
        model = self.params.get("model", "")
        desc_parts = []
        if brand:
            desc_parts.append(brand)
        if model:
            desc_parts.append(model)
        if self.product_type:
            desc_parts.append(self.product_type)

        # 加入关键参数
        key_params = []
        for k in ["bluetooth", "battery", "driver_size", "anc_db", "material", "weight"]:
            if k in self.params:
                key_params.append(f"{k}: {self.params[k]}")

        desc = " ".join(desc_parts)
        if key_params:
            desc += " (" + ", ".join(key_params) + ")"
        return desc
