# -*- coding: utf-8 -*-
# Eyes Blink Boxes (Two synced squares)
# Works fullscreen, optimized for Raspberry Pi Zero
# 3 states: open -> half -> closed -> half -> open

import os, time, platform
import pygame

# ---------------- إعدادات عامة ----------------
RENDER_W, RENDER_H = 480, 320     # حجم الشاشة
BG_COLOR  = (0, 0, 0)             # خلفية سوداء
EYE_COLOR = (255, 255, 255)       # لون المربعات (العينين)
EYE_SIZE  = 120                   # طول ضلع المربع الأساسي
BLINK_DELAY = 0.25                # زمن الانتقال بين الحالات
BLINK_PAUSE = 2.5                 # زمن بقاء العين مفتوحة بين كل رمشة

# ---------------- تفعيل KMSDRM للراسبيري ----------------
def is_pi():
    m = platform.machine().lower()
    return ("arm" in m) or ("aarch64" in m) or ("raspberry" in platform.platform().lower())

if is_pi() and not os.environ.get("DISPLAY"):
    os.environ.setdefault("SDL_VIDEODRIVER", "kmsdrm")

# ---------------- تهيئة الشاشة ----------------
pygame.init()
screen = pygame.display.set_mode((RENDER_W, RENDER_H), pygame.FULLSCREEN, 32)
pygame.mouse.set_visible(False)

# ---------------- دالة رسم العينين ----------------
def draw_eyes(state):
    """
    state: 0 = مفتوحة / 1 = نصف مغلقة / 2 = مغلقة
    """
    screen.fill(BG_COLOR)

    # مواضع العينين
    spacing = 60
    total_width = (EYE_SIZE * 2) + spacing
    start_x = (RENDER_W - total_width) // 2
    y_center = RENDER_H // 2

    # حساب ارتفاع المربع حسب الحالة
    if state == 0:      # مفتوحة
        h_factor = 1.0
    elif state == 1:    # نصف مغلقة
        h_factor = 0.5
    else:               # مغلقة
        h_factor = 0.1

    new_h = int(EYE_SIZE * h_factor)
    y_top = y_center - new_h // 2

    # رسم العين اليسرى
    pygame.draw.rect(screen, EYE_COLOR, (start_x, y_top, EYE_SIZE, new_h))
    # رسم العين اليمنى
    pygame.draw.rect(screen, EYE_COLOR, (start_x + EYE_SIZE + spacing, y_top, EYE_SIZE, new_h))

    pygame.display.flip()

# ---------------- الحلقة الرئيسية ----------------
def run():
    blink_sequence = [0, 1, 2, 1, 0]  # فتح → نصف → غلق → نصف → فتح
    running = True
    last_blink = time.time()

    try:
        while running:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running = False
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    running = False

            # نفّذ دورة رمش كل فترة محددة
            now = time.time()
            if now - last_blink >= BLINK_PAUSE:
                for state in blink_sequence:
                    draw_eyes(state)
                    time.sleep(BLINK_DELAY)
                last_blink = time.time()
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    pygame.quit()



# ==========================================
# MAIN
# ==========================================

if __name__ == "__main__":
    run()