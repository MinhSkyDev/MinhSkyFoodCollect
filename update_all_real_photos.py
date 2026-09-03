"""
Update All Places with Real Google Maps Photos
==============================================
Tự động lấy ảnh chụp thực tế (Mặt tiền quán, không gian, món ăn thật)
từ album Google Maps của từng quán ăn và cập nhật vào database & web tĩnh.
"""

import sys
import json
import asyncio
import re
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from pyppeteer import launch

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "places.json"
FRONTEND_FILE = BASE_DIR / "frontend" / "places.json"


async def fetch_photos_for_url(page, url, max_photos=4):
    collected = []

    def on_response(response):
        r_url = response.url
        if ('googleusercontent.com/p/' in r_url or 'googleusercontent.com/gps-cs-s/' in r_url or 'googleusercontent.com/gps-proxy/' in r_url) and ('=w' in r_url or '=s' in r_url):
            collected.append(r_url)

    # Đăng ký listener tạm thời
    listener = on_response
    page.on('response', listener)

    try:
        await page.goto(url, {'waitUntil': 'domcontentloaded', 'timeout': 14000})
        await asyncio.sleep(1.5)

        # Thử click nút xem ảnh album
        photo_btn = await page.querySelector('button[aria-label*="ảnh"], button[aria-label*="Ảnh"], button[aria-label*="Photo"], button[aria-label*="Photos"]')
        if photo_btn:
            await photo_btn.click()
            await asyncio.sleep(1.5)

        # Thu thập từ DOM
        dom_srcs = await page.evaluate('''() => {
            const imgs = Array.from(document.querySelectorAll('img, [style*="background-image"]'));
            const list = [];
            imgs.forEach(el => {
                if (el.tagName === 'IMG' && el.src) list.push(el.src);
                const style = el.getAttribute('style') || '';
                const match = style.match(/url\\(["']?([^"']+)["']?\\)/);
                if (match && match[1]) list.push(match[1]);
            });
            return list;
        }''')
        for s in dom_srcs:
            if ('googleusercontent.com/p/' in s or 'googleusercontent.com/gps-cs-s/' in s) and ('=w' in s or '=s' in s):
                collected.append(s)

    except Exception as e:
        pass
    finally:
        page.remove_listener('response', listener)

    unique_photos = []
    seen = set()
    for p in collected:
        base = p.split('=')[0]
        if base not in seen and not base.endswith('/default-user'):
            seen.add(base)
            unique_photos.append(f"{base}=w800-h600-k-no")
            if len(unique_photos) >= max_photos:
                break

    return unique_photos


async def process_all_places():
    if not DATA_FILE.exists():
        print(f"Không tìm thấy {DATA_FILE}")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        places = json.load(f)

    print("=" * 70)
    print(f"📸 BẮT ĐẦU CẬP NHẬT ẢNH THỰC TẾ TỪ GOOGLE MAPS CHO {len(places)} QUÁN ĂN")
    print("=" * 70)

    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    browser = await launch(
        executablePath=chrome_path,
        headless=True,
        args=['--no-sandbox', '--disable-setuid-sandbox', '--lang=vi-VN', '--disable-gpu']
    )
    page = await browser.newPage()
    await page.setUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    await page.setViewport({'width': 1280, 'height': 800})

    updated_count = 0
    for idx, place in enumerate(places, 1):
        name = place.get("name", f"Quán {idx}")
        url = place.get("original_url") or place.get("expanded_url")
        print(f"\n[{idx}/{len(places)}] Đang lấy ảnh thực tế cho: {name}...")

        photos = []
        if url:
            photos = await fetch_photos_for_url(page, url, max_photos=4)

        if photos:
            place["image_url"] = photos[0]
            place["photo_gallery"] = photos
            updated_count += 1
            print(f"  ✅ Thành công: Tìm thấy {len(photos)} ảnh thật từ Google Maps!")
            print(f"     Preview: {photos[0][:80]}...")
        else:
            print("  ⚠️ Không tìm thấy ảnh trực tiếp, giữ nguyên ảnh hiện tại.")

        # Lưu trung gian mỗi 5 quán
        if idx % 5 == 0 or idx == len(places):
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(places, f, ensure_ascii=False, indent=2)
            with open(FRONTEND_FILE, "w", encoding="utf-8") as f:
                json.dump(places, f, ensure_ascii=False, indent=2)

    await browser.close()

    print("\n" + "=" * 70)
    print(f"🎉 HOÀN TẤT! ĐÃ CẬP NHẬT {updated_count}/{len(places)} QUÁN ĂN VỚI ẢNH THẬT GOOGLE MAPS")
    print(f"[*] Đã lưu đồng bộ vào: {DATA_FILE} & {FRONTEND_FILE}")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(process_all_places())
