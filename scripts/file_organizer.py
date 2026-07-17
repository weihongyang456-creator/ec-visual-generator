#!/usr/bin/env python3
"""
文件整理模块
负责创建输出目录结构、整理生成文件、生成索引文件。
"""

import os
import json
from pathlib import Path
from datetime import datetime


class FileOrganizer:
    """管理输出文件的目录结构和索引。"""

    def __init__(self, product_name: str, base_output_dir: str = "/workspace/ec-visual-generator/output"):
        self.product_name = product_name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # 清理产品名用于目录名
        safe_name = "".join(c for c in product_name if c.isalnum() or c in "-_").replace(" ", "-")
        self.output_dir = Path(base_output_dir) / f"{safe_name}_{timestamp}"

        self.dirs = {
            "main_1_1": self.output_dir / "01_main_images" / "1-1",
            "main_3_4": self.output_dir / "01_main_images" / "3-4",
            "detail": self.output_dir / "02_detail_page",
            "ad": self.output_dir / "03_ad_images",
            "copy": self.output_dir / "04_copywriting",
            "prompts": self.output_dir / "05_external_prompts",
        }

    def create_dirs(self):
        """创建所有输出目录"""
        for d in self.dirs.values():
            d.mkdir(parents=True, exist_ok=True)

    def save_copywriting(self, selling_md: str, pain_md: str, detail_md: str):
        """保存文案文件"""
        copy_dir = self.dirs["copy"]
        (copy_dir / "selling_points.md").write_text(selling_md, encoding="utf-8")
        (copy_dir / "pain_points.md").write_text(pain_md, encoding="utf-8")
        (copy_dir / "detail_copy.md").write_text(detail_md, encoding="utf-8")

    def save_external_prompt(self, filename: str, prompt_md: str):
        """保存外部生图指令"""
        prompt_path = self.dirs["prompts"] / filename
        prompt_path.write_text(prompt_md, encoding="utf-8")

    def save_generation_log(self, log_data: dict):
        """保存生成日志"""
        log_path = self.output_dir / "generation_log.json"
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)

    def generate_index(self, gen_results: dict) -> str:
        """
        生成总索引文件 00_index.md

        Args:
            gen_results: 生成结果汇总

        Returns:
            str: 索引文件路径
        """
        md = f"""# {self.product_name} — 电商视觉素材包

> 生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## 一、产品信息概览

| 项目 | 内容 |
|------|------|
| 产品名称 | {gen_results.get('product_name', '')} |
| 产品类型 | {gen_results.get('product_type', '')} |
| 品牌调性 | {gen_results.get('brand_style', '')} |
| 产品参数 | {json.dumps(gen_results.get('params', {}), ensure_ascii=False, indent=2)} |

---

## 二、素材清单总览

| 板块 | 数量 | 状态 |
|------|------|------|
| 主图（1:1） | 5张 | {self._status_label(gen_results.get('main_1_1', []))} |
| 主图（3:4） | 5张 | {self._status_label(gen_results.get('main_3_4', []))} |
| 详情页 | 11-13张 | {self._status_label(gen_results.get('detail', []))} |
| 广告图 | 1-2张 | {self._status_label(gen_results.get('ad', []))} |

---

## 三、主图（1:1）

"""
        md += self._list_images("01_main_images/1-1", gen_results.get("main_1_1", []))

        md += "\n## 四、主图（3:4）\n\n"
        md += self._list_images("01_main_images/3-4", gen_results.get("main_3_4", []))

        md += "\n## 五、详情页图片\n\n"
        md += self._list_images("02_detail_page", gen_results.get("detail", []))

        md += "\n## 六、广告图\n\n"
        md += self._list_images("03_ad_images", gen_results.get("ad", []))

        md += """
## 七、文案文件

| 文件 | 路径 |
|------|------|
| 卖点提炼 | [selling_points.md](04_copywriting/selling_points.md) |
| 痛点场景 | [pain_points.md](04_copywriting/pain_points.md) |
| 详情页文案 | [detail_copy.md](04_copywriting/detail_copy.md) |

---

## 八、外部生图指令

"""
        prompts_dir = self.dirs["prompts"]
        if prompts_dir.exists():
            prompt_files = sorted(prompts_dir.glob("*.md"))
            if prompt_files:
                md += "| 序号 | 指令文件 | 用途 |\n|------|---------|------|\n"
                for i, pf in enumerate(prompt_files, 1):
                    md += f"| {i} | [{pf.name}](05_external_prompts/{pf.name}) | {pf.stem.replace('_', ' ')} |\n"
            else:
                md += "暂无外部生图指令（所有图片已直接生成）。\n"
        else:
            md += "暂无外部生图指令。\n"

        md += f"""
---

## 九、使用说明

1. **已生成图片**：直接可用于电商平台上架
2. **外部生图指令**：复制Prompt到对应AI工具（Midjourney/即梦/可灵）生成，建议使用图生图模式保持产品一致性
3. **文案文件**：可直接用于详情页文案、卖点提炼参考
4. **生成日志**：查看 `generation_log.json` 了解详细生成过程

---

## 十、目录结构

```
{self.product_name}/
├── 00_index.md              ← 本文件
├── 01_main_images/
│   ├── 1-1/                 ← 1:1 主图（5张）
│   └── 3-4/                 ← 3:4 主图（5张）
├── 02_detail_page/          ← 详情页图片（11-13张）
├── 03_ad_images/            ← 广告图（1-2张）
├── 04_copywriting/          ← 文案汇总
│   ├── selling_points.md
│   ├── pain_points.md
│   └── detail_copy.md
├── 05_external_prompts/     ← 外部生图指令
└── generation_log.json      ← 生成日志
```
"""
        index_path = self.output_dir / "00_index.md"
        index_path.write_text(md, encoding="utf-8")
        return str(index_path)

    def _status_label(self, items: list) -> str:
        """生成状态标签"""
        if not items:
            return "未生成"
        success = sum(1 for i in items if i.get("success"))
        total = len(items)
        if success == total:
            return f"全部生成（{total}张）"
        elif success > 0:
            return f"部分生成（{success}/{total}张）"
        else:
            return "待生成（已输出指令）"

    def _list_images(self, rel_dir: str, items: list) -> str:
        """生成图片清单表格"""
        if not items:
            return "暂无图片\n\n"

        md = "| 序号 | 图片名称 | 用途 | 状态 | 路径 |\n|------|---------|------|------|------|\n"
        for i, item in enumerate(items, 1):
            name = item.get("name", f"图片{i}")
            purpose = item.get("purpose", "")
            status = "已生成" if item.get("success") else "需外部生成"
            path = item.get("path", item.get("prompt_file", ""))
            if path:
                rel_path = Path(path).name
                md += f"| {i} | {name} | {purpose} | {'已生成' if item.get('success') else '见指令'} | `{rel_path}` |\n"
            else:
                md += f"| {i} | {name} | {purpose} | {status} | - |\n"
        return md + "\n"
