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
import urllib.request
import ssl

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from pyppeteer import launch

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from backend.parsers import get_food_image_by_category

DATA_FILE = BASE_DIR / "data" / "places.json"
FRONTEND_FILE = BASE_DIR / "frontend" / "places.json"
ROOT_FILE = BASE_DIR / "places.json"


def is_image_url_valid(url: str, timeout: float = 3.5) -> bool:
    """Kiểm tra xem URL ảnh có hoạt động và trả về HTTP 200 hay không"""
    if not url or not url.startswith('http'):
        return False
    try:
        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://www.google.com/'
            }
        )
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            ct = resp.headers.get('Content-Type', '')
            return resp.status == 200 and ct.startswith('image')
    except Exception:
        return False


def save_places_sync(places):
    for fpath in [DATA_FILE, FRONTEND_FILE, ROOT_FILE]:
        fpath.parent.mkdir(parents=True, exist_ok=True)
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(places, f, ensure_ascii=False, indent=2)


async def fetch_photos_for_url(page, url, max_photos=4):
    collected = []

    def on_response(response):
        r_url = response.url
        if ('googleusercontent.com/p/' in r_url or 'googleusercontent.com/gps-cs-s/' in r_url or 'googleusercontent.com/gps-proxy/' in r_url) and ('=w' in r_url or '=s' in r_url):
            collected.append(r_url)

    listener = on_response
    page.on('response', listener)

    try:
        await page.goto(url, {'waitUntil': 'domcontentloaded', 'timeout': 14000})
        await asyncio.sleep(1.5)

        # Thử click nút xem ảnh album nếu có
        photo_btn = await page.querySelector('button[aria-label*="ảnh"], button[aria-label*="Ảnh"], button[aria-label*="Photo"], button[aria-label*="Photos"]')
        if photo_btn:
            try:
                await photo_btn.click()
                await asyncio.sleep(1.5)
            except Exception:
                pass

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
            if ('googleusercontent.com/p/' in s or 'googleusercontent.com/gps-cs-s/' in s or 'googleusercontent.com/gps-proxy/' in s) and ('=w' in s or '=s' in s):
                collected.append(s)

    except Exception:
        pass
    finally:
        try:
            page.remove_listener('response', listener)
        except Exception:
            pass

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
    print(f"📸 BẮT ĐẦU KIỂM TRA & CẬP NHẬT ẢNH THỰC TẾ CHO {len(places)} QUÁN ĂN")
    print("=" * 70)

    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    browser = await launch(
        executablePath=chrome_path,
        headless=True,
        args=['--no-sandbox', '--disable-setuid-sandbox', '--lang=vi-VN', '--disable-gpu']
    )

    semaphore = asyncio.Semaphore(3)
    lock = asyncio.Lock()
    updated_count = 0
    skipped_count = 0

    async def process_single(idx, place):
        nonlocal updated_count, skipped_count
        name = place.get("name", f"Quán {idx}")
        current_img = place.get("image_url", "")
        gallery = place.get("photo_gallery", [])
        
        # 1. Kiểm tra ảnh hiện tại: nếu đã là ảnh Google Maps hợp lệ và còn sống (200 OK) thì bỏ qua để tiết kiệm thời gian
        current_ok = await asyncio.to_thread(is_image_url_valid, current_img)
        if current_ok and len(gallery) >= 3 and "googleusercontent.com" in current_img:
            print(f"[{idx}/{len(places)}] ⚡ {name}: Ảnh hiện tại đã hoạt động tốt (200 OK), bỏ qua.")
            async with lock:
                skipped_count += 1
            return

        url = place.get("original_url") or place.get("expanded_url")
        if not url:
            print(f"[{idx}/{len(places)}] ⚠️ {name}: Không có URL Google Maps.")
            return

        print(f"[{idx}/{len(places)}] 🔄 Đang cào ảnh mới cho: {name}...")
        
        async with semaphore:
            page = None
            photos = []
            try:
                page = await browser.newPage()
                await page.setUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
                await page.setViewport({'width': 1280, 'height': 800})
                photos = await fetch_photos_for_url(page, url, max_photos=4)
            except Exception as e:
                print(f"[{idx}/{len(places)}] ⚠️ Lỗi khi mở tab: {e}")
            finally:
                if page:
                    try:
                        await page.close()
                    except Exception:
                        pass

        # Kiểm tra tính hợp lệ của các ảnh vừa cào
        valid_photos = []
        for p in photos:
            ok = await asyncio.to_thread(is_image_url_valid, p)
            if ok:
                valid_photos.append(p)

        async with lock:
            if valid_photos:
                place["image_url"] = valid_photos[0]
                place["photo_gallery"] = valid_photos
                updated_count += 1
                print(f"  ✅ [{idx}] {name}: Thành công {len(valid_photos)} ảnh Google Maps!")
            else:
                # Nếu không cào được ảnh Google Maps sống, fallback về Unsplash chuẩn danh mục
                cat = place.get("category", "Ẩm thực")
                fb_img = get_food_image_by_category(cat, name)
                place["image_url"] = fb_img
                place["photo_gallery"] = [fb_img]
                updated_count += 1
                print(f"  📌 [{idx}] {name}: Dùng ảnh Unsplash theo danh mục ({cat})")

            # Lưu định kỳ
            save_places_sync(places)

    # Chạy đồng thời với semaphore 3
    tasks = [process_single(idx, place) for idx, place in enumerate(places, 1)]
    await asyncio.gather(*tasks)

    await browser.close()

    # Lưu lần cuối
    save_places_sync(places)

    print("\n" + "=" * 70)
    print(f"🎉 HOÀN TẤT! ĐÃ CẬP NHẬT {updated_count} QUÁN, GIỮ NGUYÊN {skipped_count} QUÁN")
    print(f"[*] Đã lưu đồng bộ vào:\n    - {DATA_FILE}\n    - {FRONTEND_FILE}\n    - {ROOT_FILE}")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(process_all_places())
