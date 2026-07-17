---
name: ec-visual-generator
description: "电商产品视觉内容自动化生成工具。输入产品图+参数+类型，自动生成主图5张×2尺寸、详情页11-13张、广告图1-2张，含卖点文案和外部生图指令。关键词：电商主图、详情页、广告图、产品图、卖点提炼、生图指令"
version: "1.0.0"
author: "WorkBuddy"
created: "2026-07-17"
---

# 电商产品视觉内容自动化生成工具

> **Goal**: 输入产品图+参数+类型，一键生成完整电商视觉素材包（主图+详情页+广告图+文案+生图指令）。

## When to Use

用户需要批量生成电商产品视觉素材时触发：
- "帮我生成产品主图和详情页"
- "我有产品白底图，需要做电商图"
- "生成TESNA GT-EA16的电商素材"
- "我需要主图5张+详情页+广告图"

## When NOT to Use

- 仅需要文案生成（用 ecommerce-copywriter）
- 仅需要单张图片生成（用 nano-banana-pro）
- 产品摄影/精修需求（用专业设计工具）

---

## 使用方式

### 基本用法

```bash
python3 /workspace/ec-visual-generator/scripts/generate_all.py \
  --product-name "TESNA GT-EA16" \
  --product-type "3C数码-耳机" \
  --images /root/uploads/product1.jpg /root/uploads/product2.jpg \
  --params '{"brand": "TESNA", "model": "GT-EA16", "bluetooth": "5.3", "battery": "36h", "anc_db": "42", "driver_size": "13mm", "weight": "4.5g", "waterproof": "5"}' \
  --brand-style "科技感/简约/黑金配色"
```

### 仅生成文案+指令（不调用AI生图）

```bash
python3 /workspace/ec-visual-generator/scripts/generate_all.py \
  --product-name "产品名" \
  --product-type "3C数码-耳机" \
  --params '{"brand": "XX", "model": "XX"}' \
  --skip-ai-gen
```

### 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--product-name` | ✅ | 产品名称 |
| `--product-type` | ✅ | 产品类型（格式：`品类-子类`，如 `3C数码-耳机`） |
| `--images` | ❌ | 产品图片路径（白底图/角度图） |
| `--params` | ❌ | 产品参数JSON字符串 |
| `--brand-style` | ❌ | 品牌调性描述 |
| `--output-dir` | ❌ | 输出目录（默认 `/workspace/ec-visual-generator/output`） |
| `--skip-ai-gen` | ❌ | 跳过AI生图，仅生成文案和外部指令 |
| `--api-key` | ❌ | Gemini API Key |

---

## 支持品类

| 品类 | 子类 |
|------|------|
| 3C数码 | 耳机/音箱/充电器/手机配件/智能穿戴/键盘鼠标 |
| 家居生活 | 小家电/收纳整理/厨具/床上用品/灯具/装饰 |
| 美妆个护 | 护肤/彩妆/美容工具/口腔护理/身体护理 |
| 服饰鞋包 | 男装/女装/童装/鞋履/箱包/配饰 |
| 潮玩收藏 | vinyl figures/毛绒玩具/手办/盲盒/收藏品 |
| 食品饮料 | 零食/饮品/保健品/茶叶/烘焙 |

---

## 输出结构

```
output/{产品名}_{时间戳}/
├── 00_index.md                    # 总索引文件
├── 01_main_images/
│   ├── 1-1/                       # 1:1 主图（5张）
│   │   ├── 01_首图.png
│   │   ├── 02_卖点图1.png
│   │   ├── 03_场景图.png
│   │   ├── 04_对比图.png
│   │   └── 05_促销图.png
│   └── 3-4/                       # 3:4 主图（5张）
│       └── （同上5张）
├── 02_detail_page/                # 详情页（11-13张）
│   ├── 01_品牌首屏.png
│   ├── 02_卖点总览.png
│   ├── ...
│   └── 13_行动号召.png
├── 03_ad_images/                  # 广告图（1-2张）
│   ├── 01_信息流广告图.png
│   └── 02_搜索广告图.png
├── 04_copywriting/                # 文案汇总
│   ├── selling_points.md          # 卖点提炼
│   ├── pain_points.md             # 痛点场景
│   └── detail_copy.md             # 详情页文案
├── 05_external_prompts/           # 外部生图指令
│   ├── main_3-4_03_场景图.md
│   ├── detail_05_使用场景1.md
│   └── ...
└── generation_log.json            # 生成日志
```

---

## 主图5张逻辑

| 序号 | 名称 | 用途 | 生成方式 |
|------|------|------|---------|
| 1 | 首图 | 产品白底展示 | 用户原图/缩放 |
| 2 | 卖点图1 | 核心功能亮点 | Pillow合成 |
| 3 | 场景图 | 使用场景化 | AI生图/外部指令 |
| 4 | 对比图 | 竞品对比 | Pillow合成 |
| 5 | 促销图 | 优惠+行动号召 | Pillow合成 |

**尺寸版本**：1:1（1080×1080）+ 3:4（1080×1440）

## 详情页11-13张逻辑

| 序号 | 名称 | 生成方式 |
|------|------|---------|
| 1 | 品牌首屏 | AI生图 |
| 2 | 卖点总览 | Pillow合成 |
| 3 | 卖点详解1 | Pillow合成 |
| 4 | 卖点详解2 | Pillow合成 |
| 5 | 使用场景1 | AI生图 |
| 6 | 使用场景2 | AI生图 |
| 7 | 产品细节1 | AI生图 |
| 8 | 产品细节2 | AI生图 |
| 9 | 参数规格表 | Pillow合成 |
| 10 | 包装清单 | AI生图 |
| 11 | 品牌故事 | Pillow合成 |
| 12 | 售后保障 | Pillow合成 |
| 13 | 行动号召 | Pillow合成 |

---

## 图片生成分层策略

| 类型 | 方式 | 说明 |
|------|------|------|
| 白底产品图 | 用户原图 | 直接缩放使用 |
| 图文排版图 | Python Pillow | 文字/参数表/对比图合成 |
| 场景/细节图 | nano-banana-pro AI | 调用Gemini 3 Pro Image |
| 实物一致性图 | 外部指令 | 输出Prompt供Midjourney/即梦/可灵使用 |

**AI生图失败时自动降级**为输出外部生图指令。

---

## 外部生图指令格式

每条指令包含：
- 英文Prompt（Midjourney/SD用）
- 中文Prompt（即梦/可灵用）
- 推荐工具及参数建议
- 注意事项（图生图建议、后处理建议）

---

## 技术依赖

- Python 3.11+
- Pillow（图片合成）
- nano-banana-pro（AI生图，可选）
- 中文字体（Noto Sans CJK）
