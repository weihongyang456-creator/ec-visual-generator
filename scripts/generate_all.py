#!/usr/bin/env python3
"""
电商产品视觉内容自动化生成工具 — 主调度脚本

使用方式:
    python3 generate_all.py \
      --product-name "TESNA GT-EA16" \
      --product-type "3C数码-耳机" \
      --images /root/uploads/product1.jpg \
      --params '{"brand": "TESNA", "model": "GT-EA16", "bluetooth": "5.3", "battery": "36h"}' \
      --brand-style "科技感/简约/黑金配色"

输出:
    /workspace/ec-visual-generator/output/{product_name}_{timestamp}/
"""

import argparse
import json
import sys
import os
from pathlib import Path
from datetime import datetime

# 添加脚本目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from prompt_builder import PromptBuilder
from file_organizer import FileOrganizer
from ai_image_gen import generate_image, generate_external_prompt
from image_compose import (
    compose_selling_point_image,
    compose_spec_table,
    compose_promo_image,
    compose_comparison_image,
)


def parse_args():
    parser = argparse.ArgumentParser(description="电商产品视觉内容自动化生成工具")
    parser.add_argument("--product-name", required=True, help="产品名称")
    parser.add_argument("--product-type", required=True, help="产品类型（如：3C数码-耳机）")
    parser.add_argument("--images", nargs="*", default=[], help="产品图片路径列表")
    parser.add_argument("--params", default="{}", help="产品参数JSON字符串")
    parser.add_argument("--brand-style", default="", help="品牌调性描述")
    parser.add_argument("--output-dir", default="/workspace/ec-visual-generator/output", help="输出目录")
    parser.add_argument("--skip-ai-gen", action="store_true", help="跳过AI生图，仅生成指令和文案")
    parser.add_argument("--api-key", default=None, help="Gemini API Key")
    return parser.parse_args()


def main():
    args = parse_args()

    # 解析参数
    try:
        params = json.loads(args.params) if isinstance(args.params, str) else args.params
    except json.JSONDecodeError:
        print("⚠️ 参数JSON解析失败，使用空字典")
        params = {}

    print(f"\n{'='*60}")
    print(f"  电商视觉内容生成器")
    print(f"  产品: {args.product_name}")
    print(f"  类型: {args.product_type}")
    print(f"{'='*60}\n")

    # 初始化模块
    builder = PromptBuilder(args.product_name, args.product_type, params, args.brand_style)
    organizer = FileOrganizer(args.product_name, args.output_dir)
    organizer.create_dirs()

    # 记录生成结果
    gen_results = {
        "product_name": args.product_name,
        "product_type": args.product_type,
        "brand_style": args.brand_style or builder.brand_style,
        "params": params,
        "main_1_1": [],
        "main_3_4": [],
        "detail": [],
        "ad": [],
    }

    # ========== STEP 1: 文案生成 ==========
    print("📝 STEP 1: 生成卖点与文案...")
    selling_md = builder.generate_selling_points_md()
    pain_md = builder.generate_pain_points_md()
    detail_md = builder.generate_detail_copy_md()
    organizer.save_copywriting(selling_md, pain_md, detail_md)
    print(f"   ✅ 卖点提炼、痛点场景、详情页文案已生成")

    # 获取产品描述
    product_desc = builder.get_product_desc()
    matched_points = builder.get_matched_selling_points()

    # ========== STEP 2: 主图生成 ==========
    print("\n📸 STEP 2: 生成主图（1:1 + 3:4）...")

    main_layout = builder.main_layout
    product_image = args.images[0] if args.images else None

    for size_key, size_label, dims in [("square_1_1", "1-1", (1080, 1080)),
                                        ("portrait_3_4", "3-4", (1080, 1440))]:
        print(f"\n   📐 处理 {size_label} 尺寸...")

        # 映射 size_key 到 gen_results 的 key
        results_key = "main_1_1" if size_key == "square_1_1" else "main_3_4"
        # 映射 size_key 到 organizer.dirs 的 key
        dir_key = "main_1_1" if size_key == "square_1_1" else "main_3_4"

        for slide in main_layout.get("slides", []):
            slide_num = slide["slide_num"]
            name = slide["name"]
            purpose = slide["purpose"]
            method = slide["gen_method"]
            filename = f"{slide_num:02d}_{name}.png"

            print(f"   → [{slide_num}/5] {name} ({method})...", end=" ")

            item = {"name": name, "purpose": purpose, "success": False, "path": ""}

            if method == "user_original" and product_image:
                # 使用用户原图，缩放为目标尺寸
                from PIL import Image as PILImage
                try:
                    img = PILImage.open(product_image).convert("RGB")
                    img = img.resize(dims, PILImage.LANCZOS)
                    out_path = organizer.dirs[dir_key] / filename
                    img.save(str(out_path), "PNG", quality=95)
                    item["success"] = True
                    item["path"] = str(out_path)
                    print("✅ 使用原图")
                except Exception as e:
                    print(f"⚠️ 原图处理失败: {e}")
                    item["error"] = str(e)

            elif method == "user_original" and not product_image:
                # 无原图，用Pillow合成首图
                try:
                    out_path = organizer.dirs[dir_key] / filename
                    point = matched_points[0] if matched_points else {}
                    compose_selling_point_image(
                        title=args.product_name,
                        subtitle=point.get("description", "产品展示"),
                        detail=builder.fill_selling_point_template(point) if point else "",
                        output_path=str(out_path), size=dims
                    )
                    item["success"] = True
                    item["path"] = str(out_path)
                    print("✅ 合成首图（无原图）")
                except Exception as e:
                    print(f"⚠️ 合成失败: {e}")
                    item["error"] = str(e)

            elif method == "pillow_compose":
                # Pillow 合成
                try:
                    out_path = organizer.dirs[dir_key] / filename

                    if slide_num == 2 and matched_points:
                        # 卖点图1
                        point = matched_points[0]
                        detail = builder.fill_selling_point_template(point)
                        compose_selling_point_image(
                            title=point["title"], subtitle=point["description"],
                            detail=detail, output_path=str(out_path), size=dims,
                            product_image=product_image
                        )
                    elif slide_num == 4:
                        # 对比图
                        compare_items = [
                            {"dimension": "续航", "ours": params.get("battery", "长续航"), "competitor": "普通"},
                            {"dimension": "连接", "ours": params.get("bluetooth", "蓝牙5.3"), "competitor": "蓝牙5.0"},
                            {"dimension": "重量", "ours": params.get("weight", "轻量"), "competitor": "较重"},
                        ]
                        compose_comparison_image(title="实力对比", items=compare_items,
                                                 output_path=str(out_path), size=dims, product_image=product_image)
                    elif slide_num == 5:
                        # 促销图
                        compose_promo_image(
                            product_name=args.product_name, promo_text="限时特惠",
                            cta="立即抢购", output_path=str(out_path), size=dims,
                            product_image=product_image
                        )
                    else:
                        # 默认卖点图
                        point = matched_points[min(slide_num - 2, len(matched_points) - 1)] if matched_points else {}
                        compose_selling_point_image(
                            title=point.get("title", name), subtitle=point.get("description", ""),
                            detail=builder.fill_selling_point_template(point) if point else "",
                            output_path=str(out_path), size=dims, product_image=product_image
                        )

                    item["success"] = True
                    item["path"] = str(out_path)
                    print("✅ 合成完成")
                except Exception as e:
                    print(f"⚠️ 合成失败: {e}")
                    item["error"] = str(e)

            elif method == "ai_generate":
                # AI 生图（场景图）
                if args.skip_ai_gen:
                    # 仅输出指令
                    prompt_md = generate_external_prompt(
                        image_name=f"主图{slide_num}_{name}",
                        product_desc=product_desc,
                        scene_desc=slide.get("design_logic", ""),
                        brand_style=builder.brand_style,
                        gen_purpose=f"主图{slide_num}：{purpose}",
                    )
                    prompt_file = organizer.dirs["prompts"] / f"main_{size_label}_{slide_num}_{name}.md"
                    organizer.save_external_prompt(prompt_file.name, prompt_md)
                    item["prompt_file"] = prompt_file.name
                    print("📋 已输出指令")
                else:
                    # 尝试AI生图
                    prompt = builder.build_image_prompt(slide, product_desc)
                    out_path = organizer.dirs[dir_key] / filename
                    result = generate_image(prompt, str(out_path), resolution="2K", api_key=args.api_key)
                    if result["success"]:
                        item["success"] = True
                        item["path"] = result["path"]
                        print("✅ AI生成完成")
                    else:
                        # 失败则输出指令
                        prompt_md = generate_external_prompt(
                            image_name=f"主图{slide_num}_{name}",
                            product_desc=product_desc,
                            scene_desc=slide.get("design_logic", ""),
                            brand_style=builder.brand_style,
                            gen_purpose=f"主图{slide_num}：{purpose}",
                        )
                        prompt_file = organizer.dirs["prompts"] / f"main_{size_label}_{slide_num}_{name}.md"
                        organizer.save_external_prompt(prompt_file.name, prompt_md)
                        item["prompt_file"] = prompt_file.name
                        print(f"📋 AI生图失败，已输出指令 ({result['error'][:50]})")

            gen_results[results_key].append(item)

    # ========== STEP 3: 详情页生成 ==========
    print("\n📄 STEP 3: 生成详情页图片...")

    detail_layout = builder.detail_layout

    for slide in detail_layout.get("slides", []):
        slide_num = slide["slide_num"]
        name = slide["name"]
        purpose = slide["purpose"]
        method = slide["gen_method"]
        height = slide.get("height", 800)
        filename = f"{slide_num:02d}_{name}.png"
        dims = (750, height)

        print(f"   → [{slide_num}/13] {name} ({method})...", end=" ")

        item = {"name": name, "purpose": purpose, "success": False, "path": ""}

        if method == "pillow_compose":
            try:
                out_path = organizer.dirs["detail"] / filename

                if slide_num == 2:
                    # 卖点总览
                    points = matched_points[:4]
                    title = "核心卖点"
                    subtitle = " | ".join([p["title"] for p in points]) if points else ""
                    detail = "；".join([p["description"] for p in points]) if points else ""
                    compose_selling_point_image(title, subtitle, detail, str(out_path), dims)

                elif slide_num == 3 and matched_points:
                    point = matched_points[0]
                    compose_selling_point_image(
                        title=point["title"], subtitle=point["description"],
                        detail=builder.fill_selling_point_template(point),
                        output_path=str(out_path), size=dims, product_image=product_image
                    )

                elif slide_num == 4 and len(matched_points) > 1:
                    point = matched_points[1]
                    compose_selling_point_image(
                        title=point["title"], subtitle=point["description"],
                        detail=builder.fill_selling_point_template(point),
                        output_path=str(out_path), size=dims, product_image=product_image
                    )

                elif slide_num == 9:
                    # 参数表
                    compose_spec_table(params, "产品参数", str(out_path), dims)

                elif slide_num == 11:
                    # 品牌故事
                    brand = params.get("brand", args.product_name)
                    compose_selling_point_image(
                        title="品牌故事", subtitle=brand,
                        detail=f"{brand}致力于为用户带来{builder.category}领域的优质体验。好产品不仅是工具，更是生活方式的表达。",
                        output_path=str(out_path), size=dims
                    )

                elif slide_num == 12:
                    # 售后保障
                    compose_selling_point_image(
                        title="售后保障", subtitle="无忧购物",
                        detail="7天无理由退换 | 15天质量问题免费换新 | 1年质保 | 全国联保",
                        output_path=str(out_path), size=dims
                    )

                elif slide_num == 13:
                    # 行动号召
                    compose_promo_image(
                        product_name=args.product_name, promo_text="限时优惠",
                        cta="立即下单", output_path=str(out_path), size=dims
                    )

                else:
                    # 默认
                    compose_selling_point_image(
                        title=name, subtitle=purpose, detail="",
                        output_path=str(out_path), size=dims
                    )

                item["success"] = True
                item["path"] = str(out_path)
                print("✅ 合成完成")

            except Exception as e:
                print(f"⚠️ 合成失败: {e}")
                item["error"] = str(e)

        elif method == "ai_generate":
            if args.skip_ai_gen:
                prompt_md = generate_external_prompt(
                    image_name=f"详情页{slide_num}_{name}",
                    product_desc=product_desc,
                    scene_desc=slide.get("design_logic", ""),
                    brand_style=builder.brand_style,
                    gen_purpose=f"详情页{slide_num}：{purpose}",
                )
                prompt_file = organizer.dirs["prompts"] / f"detail_{slide_num}_{name}.md"
                organizer.save_external_prompt(prompt_file.name, prompt_md)
                item["prompt_file"] = prompt_file.name
                print("📋 已输出指令")
            else:
                prompt = builder.build_image_prompt(slide, product_desc)
                out_path = organizer.dirs["detail"] / filename
                result = generate_image(prompt, str(out_path), resolution="2K", api_key=args.api_key)
                if result["success"]:
                    item["success"] = True
                    item["path"] = result["path"]
                    print("✅ AI生成完成")
                else:
                    prompt_md = generate_external_prompt(
                        image_name=f"详情页{slide_num}_{name}",
                        product_desc=product_desc,
                        scene_desc=slide.get("design_logic", ""),
                        brand_style=builder.brand_style,
                        gen_purpose=f"详情页{slide_num}：{purpose}",
                    )
                    prompt_file = organizer.dirs["prompts"] / f"detail_{slide_num}_{name}.md"
                    organizer.save_external_prompt(prompt_file.name, prompt_md)
                    item["prompt_file"] = prompt_file.name
                    print(f"📋 AI生图失败，已输出指令")

        gen_results["detail"].append(item)

    # ========== STEP 4: 广告图生成 ==========
    print("\n📢 STEP 4: 生成广告图...")

    ad_layout = builder.ad_layout

    for ad in ad_layout.get("ad_types", []):
        ad_num = ad["ad_num"]
        name = ad["name"]
        purpose = ad["purpose"]
        method = ad["gen_method"]
        dims = tuple(ad["dimensions"])
        filename = f"{ad_num:02d}_{name}.png"

        print(f"   → [{ad_num}] {name} ({method})...", end=" ")

        item = {"name": name, "purpose": purpose, "success": False, "path": ""}

        if "pillow_compose" in method:
            try:
                out_path = organizer.dirs["ad"] / filename

                if ad_num == 1:
                    # 信息流广告 — AI生图+合成
                    if args.skip_ai_gen:
                        prompt_md = generate_external_prompt(
                            image_name=f"广告图{ad_num}_{name}",
                            product_desc=product_desc,
                            scene_desc="信息流广告场景，产品突出展示",
                            brand_style=builder.brand_style,
                            gen_purpose=f"广告图{ad_num}：{purpose}",
                        )
                        prompt_file = organizer.dirs["prompts"] / f"ad_{ad_num}_{name}.md"
                        organizer.save_external_prompt(prompt_file.name, prompt_md)
                        item["prompt_file"] = prompt_file.name
                        print("📋 已输出指令")
                    else:
                        prompt = builder.build_image_prompt(
                            {"purpose": purpose, "prompt_keywords": ad.get("prompt_keywords", [])},
                            product_desc
                        )
                        result = generate_image(prompt, str(out_path), resolution="2K", api_key=args.api_key)
                        if result["success"]:
                            item["success"] = True
                            item["path"] = result["path"]
                            print("✅ AI生成完成")
                        else:
                            prompt_md = generate_external_prompt(
                                image_name=f"广告图{ad_num}_{name}",
                                product_desc=product_desc,
                                scene_desc="信息流广告场景，产品突出展示",
                                brand_style=builder.brand_style,
                                gen_purpose=f"广告图{ad_num}：{purpose}",
                            )
                            prompt_file = organizer.dirs["prompts"] / f"ad_{ad_num}_{name}.md"
                            organizer.save_external_prompt(prompt_file.name, prompt_md)
                            item["prompt_file"] = prompt_file.name
                            print("📋 已输出指令")

                elif ad_num == 2:
                    # 搜索广告 — 合成
                    compose_promo_image(
                        product_name=args.product_name,
                        promo_text=args.product_name,
                        cta="立即抢购", output_path=str(out_path), size=dims,
                        product_image=product_image
                    )
                    item["success"] = True
                    item["path"] = str(out_path)
                    print("✅ 合成完成")

            except Exception as e:
                print(f"⚠️ 失败: {e}")
                item["error"] = str(e)

        gen_results["ad"].append(item)

    # ========== STEP 5: 生成索引 ==========
    print("\n📊 STEP 5: 生成索引文件...")
    organizer.save_generation_log(gen_results)
    index_path = organizer.generate_index(gen_results)

    print(f"\n{'='*60}")
    print(f"  ✅ 全部完成！")
    print(f"  📂 输出目录: {organizer.output_dir}")
    print(f"  📋 索引文件: {index_path}")
    print(f"{'='*60}\n")

    # 统计
    total = sum(len(gen_results[k]) for k in ["main_1_1", "main_3_4", "detail", "ad"])
    success = sum(1 for k in ["main_1_1", "main_3_4", "detail", "ad"]
                  for item in gen_results[k] if item.get("success"))
    prompts = sum(1 for k in ["main_1_1", "main_3_4", "detail", "ad"]
                  for item in gen_results[k] if item.get("prompt_file"))

    print(f"  📊 统计:")
    print(f"     - 图片总数: {total}")
    print(f"     - 已生成: {success}")
    print(f"     - 外部指令: {prompts}")
    print(f"     - 文案文件: 3个（卖点/痛点/详情页）\n")


if __name__ == "__main__":
    main()
