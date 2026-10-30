# War Shooter Mobile - نسخة بأزرار لمس للموبايل
# في Pydroid 3 ثبّت pygame من Pip ثم افتح الملف واضغط Run.

import random
import sys
import pygame

pygame.init()

# اللعبة لا تحتاج إلى كتابة نصوص؛ أوقف إدخال النصوص حتى لا تظهر لوحة المفاتيح.
try:
    pygame.key.stop_text_input()
except Exception:
    pass

def hide_android_keyboard():
    try:
        from jnius import autoclass
        Activity = autoclass("org.kivy.android.PythonActivity")
        activity = Activity.mActivity
        InputMethodManager = autoclass("android.view.inputmethod.InputMethodManager")
        imm = activity.getSystemService(activity.INPUT_METHOD_SERVICE)
        view = activity.getWindow().getDecorView()
        token = view.getWindowToken()
        if token is not None:
            imm.hideSoftInputFromWindow(token, 0)
    except Exception:
        # بعض نسخ Pydroid لا تتيح واجهة Java هذه؛ نكمل بدون تعطيل اللعبة.
        pass

# حاول طلب الوضع الأفقي على أندرويد إذا كانت واجهة Java متاحة.
# لو مش متاحة في Pydroid، نطلب من SDL شاشة عريضة (Landscape) كخطة بديلة.
def request_landscape():
    try:
        from jnius import autoclass
        # قد لا تكون هذه الفئة متاحة داخل Pydroid؛ لذلك نستخدم try/except.
        Activity = autoclass("org.kivy.android.PythonActivity")
        activity = Activity.mActivity
        activity.setRequestedOrientation(0)  # SCREEN_ORIENTATION_LANDSCAPE
    except Exception:
        pass

request_landscape()

# نسبة العرض أكبر من الارتفاع لتطلب اللعبة في الوضع الأفقي.
try:
    screen = pygame.display.set_mode((900, 560), pygame.FULLSCREEN)
except pygame.error:
    screen = pygame.display.set_mode((900, 560), pygame.RESIZABLE)

# أعد طلب الاتجاه بعد إنشاء نافذة SDL، لأنها قد تغيّر طلب الاتجاه بنفسها.
request_landscape()
hide_android_keyboard()

SCREEN_W, SCREEN_H = screen.get_size()
WIDTH, HEIGHT = 900, 560  # إحداثيات اللعبة الداخلية
pygame.display.set_caption("War Shooter Mobile")
clock = pygame.time.Clock()
canvas = pygame.Surface((WIDTH, HEIGHT))
# ارسم كل عناصر اللعبة على اللوحة الداخلية من أول إطار، ثم كبّرها للشاشة الفعلية.
screen = canvas
SCALE_X, SCALE_Y = SCREEN_W / WIDTH, SCREEN_H / HEIGHT

FONT = pygame.font.Font(None, 27)
BIG = pygame.font.Font(None, 54)

SKY = (85, 155, 210)
WHITE = (245, 245, 245)
RED = (220, 55, 55)
GREEN = (65, 190, 85)
YELLOW = (255, 210, 65)
DARK = (20, 29, 38)

GROUND_Y = 430
player = pygame.Rect(110, GROUND_Y - 48, 38, 48)
health, max_health, ammo, max_ammo, score = 100, 100, 30, 30, 0
player_damage = 1
level = 0
game_mode = 1
selected_map = 0
menu_page = "main"
store_open = False
money = 0
armor_helmet = armor_chest = weapon_level = 0
auto_weapon = False
shooting_requested = False
last_reward_score = 0
zombie_kills = 0
boss_kills = 0
enemies, bullets, enemy_bullets, acid_bullets = [], [], [], []
last_spawn = 0
last_shot = 0
game_over = False
paused = False
main_menu = True
move_left = move_right = shooting = False
# حالات أزرار اللمس المتعددة: تسمح بضغط أكثر من زر في نفس الوقت.
active_touch_buttons = set()
last_menu_tap_pos = None
last_menu_tap_time = -1000
jump_height = 0
jump_velocity = 0
on_ground = True

# أزرار كبيرة مناسبة للمس
left_btn = pygame.Rect(20, 465, 92, 76)
right_btn = pygame.Rect(125, 465, 92, 76)
shoot_btn = pygame.Rect(760, 455, 118, 88)
reload_btn = pygame.Rect(655, 475, 88, 62)
jump_btn = pygame.Rect(545, 455, 100, 82)
pause_btn = pygame.Rect(820, 12, 62, 50)
restart_btn = pygame.Rect(300, 315, 300, 60)
start_btn = pygame.Rect(180, 215, 540, 110)
mode1_btn = pygame.Rect(35, 280, 255, 48)
mode2_btn = pygame.Rect(323, 280, 255, 48)
mode3_btn = pygame.Rect(605, 270, 260, 48)
mode_back_btn = pygame.Rect(385, 445, 130, 44)
map_back_btn = pygame.Rect(35, 475, 150, 48)
map_cards = [pygame.Rect(35 + i*142, 150, 128, 235) for i in range(6)]
pause_home_btn = pygame.Rect(310, 330, 280, 48)
gameover_home_btn = pygame.Rect(300, 385, 300, 48)
store_btn = pygame.Rect(700, 12, 105, 50)
store_back_btn = pygame.Rect(300, 465, 300, 32)
shop_health_btn = pygame.Rect(170, 205, 270, 65)
shop_weapon_btn = pygame.Rect(460, 205, 270, 65)
shop_helmet_btn = pygame.Rect(170, 290, 270, 65)
shop_chest_btn = pygame.Rect(460, 290, 270, 65)
shop_special_btn = pygame.Rect(170, 375, 560, 58)
menu_quit_btn = pygame.Rect(300, 395, 300, 58)
menu_help_btn = pygame.Rect(300, 325, 300, 58)

def event_position(event):
    """حوّل إحداثيات اللمس/الماوس إلى مساحة اللعبة الداخلية."""
    if event.type in (pygame.FINGERDOWN, pygame.FINGERUP, getattr(pygame, "FINGERMOTION", -999)):
        return (max(0, min(WIDTH - 1, int(event.x * WIDTH))),
                max(0, min(HEIGHT - 1, int(event.y * HEIGHT))))
    # استخدم أبعاد نافذة SDL الحالية؛ هذا أكثر أمانًا على شاشات أندرويد المختلفة.
    display = pygame.display.get_surface()
    dw, dh = display.get_size() if display else (SCREEN_W, SCREEN_H)
    x, y = event.pos
    return (max(0, min(WIDTH - 1, int(x * WIDTH / max(1, dw)))),
            max(0, min(HEIGHT - 1, int(y * HEIGHT / max(1, dh)))))

def text(msg, x, y, color=WHITE, font=FONT, center=False):
    surf = font.render(msg, True, color)
    rect = surf.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    screen.blit(surf, rect)

def button(rect, label, color=(35, 48, 60), font=FONT):
    pygame.draw.rect(screen, color, rect, border_radius=15)
    pygame.draw.rect(screen, (210, 220, 225), rect, 2, border_radius=15)
    text(label, rect.centerx, rect.centery, WHITE, font, center=True)

def draw_panel(rect, fill=(10, 15, 20), border=(177, 129, 43), radius=12, width=2):
    """Dark military UI panel with a warm metallic edge."""
    pygame.draw.rect(screen, (4, 7, 10), (rect.x + 3, rect.y + 4, rect.width, rect.height), border_radius=radius)
    pygame.draw.rect(screen, fill, rect, border_radius=radius)
    pygame.draw.rect(screen, border, rect, width, border_radius=radius)
    inner = rect.inflate(-8, -8)
    if inner.width > 0 and inner.height > 0:
        pygame.draw.rect(screen, (34, 35, 31), inner, 1, border_radius=max(2, radius - 4))

def draw_gold_button(rect, label, active=False, font=FONT):
    base = (107, 70, 19) if active else (28, 30, 29)
    edge = (255, 194, 66) if active else (157, 119, 52)
    pygame.draw.rect(screen, (5, 7, 9), rect.move(2, 3), border_radius=9)
    pygame.draw.rect(screen, base, rect, border_radius=9)
    pygame.draw.rect(screen, edge, rect, 2, border_radius=9)
    pygame.draw.line(screen, (218, 167, 62), (rect.x + 10, rect.y + 5), (rect.right - 10, rect.y + 5), 1)
    text(label, rect.centerx, rect.centery, (255, 224, 153) if active else (229, 229, 218), font, center=True)

def draw_menu_backdrop():
    # Layered dusk sky, ruined skyline, smoke and embers; no external assets required.
    for y in range(HEIGHT):
        t = y / HEIGHT
        col = (int(11 + 20*t), int(17 + 18*t), int(23 + 15*t))
        pygame.draw.line(screen, col, (0, y), (WIDTH, y))
    # distant skyline silhouettes
    buildings = [(0,130,210),(105,95,255),(185,120,185),(315,100,230),(425,120,170),(560,105,245),(690,100,200),(790,110,270)]
    for x,w,h in buildings:
        top = 385-h//2
        pygame.draw.rect(screen, (25,31,34), (x,top,w,h))
        pygame.draw.line(screen, (70,61,44), (x,top), (x+w,top), 2)
        for wx in range(x+12,x+w-8,23):
            for wy in range(top+15,390,27):
                if random.random() < 0.52:
                    pygame.draw.rect(screen, random.choice([(115,82,38),(65,74,74),(142,87,38)]),(wx,wy,7,10))
    # burning horizon and broken ground
    pygame.draw.ellipse(screen, (67,38,20), (180,300,560,135))
    pygame.draw.rect(screen, (13,17,17), (0,405,WIDTH,HEIGHT-405))
    for i in range(75):
        ex=random.randint(0,WIDTH-1); ey=random.randint(285,HEIGHT-12)
        pygame.draw.circle(screen, random.choice([(245,124,35),(181,58,22),(250,190,67)]),(ex,ey),random.choice([1,1,2]))
    # subtle vignette bars
    pygame.draw.rect(screen, (5,7,9), (0,0,WIDTH,HEIGHT), 8)

def draw_soldier_silhouette(center=(590,335), scale=1.0):
    """Stylized armored soldier illustration built from vector shapes."""
    cx,cy=center
    # shoulders and torso
    pygame.draw.polygon(screen,(18,23,24),[(cx-78*scale,cy+8*scale),(cx-48*scale,cy-35*scale),(cx+40*scale,cy-35*scale),(cx+75*scale,cy+10*scale),(cx+58*scale,cy+100*scale),(cx-55*scale,cy+100*scale)])
    pygame.draw.polygon(screen,(47,53,49),[(cx-45*scale,cy-25*scale),(cx+30*scale,cy-25*scale),(cx+45*scale,cy+66*scale),(cx-42*scale,cy+66*scale)])
    # helmet and face shield
    pygame.draw.circle(screen,(15,19,20),(int(cx),int(cy-58*scale)),int(39*scale))
    pygame.draw.arc(screen,(115,113,96),pygame.Rect(cx-40*scale,cy-98*scale,80*scale,65*scale),0,3.14,3)
    pygame.draw.rect(screen,(7,11,13),(cx-29*scale,cy-65*scale,58*scale,25*scale),border_radius=7)
    pygame.draw.line(screen,(92,100,94),(cx-26*scale,cy-55*scale),(cx+26*scale,cy-55*scale),2)
    # straps / armor plates
    pygame.draw.line(screen,(10,13,13),(cx-25*scale,cy-15*scale),(cx+25*scale,cy+52*scale),7)
    pygame.draw.line(screen,(10,13,13),(cx+28*scale,cy-15*scale),(cx-25*scale,cy+52*scale),7)
    for yy in (-5,17,39):
        pygame.draw.rect(screen,(78,78,62),(cx-18*scale,cy+yy*scale,36*scale,12*scale),border_radius=3)
    # rifle held across chest
    pygame.draw.line(screen,(7,9,10),(cx-48*scale,cy+16*scale),(cx+83*scale,cy-8*scale),9)
    pygame.draw.line(screen,(85,85,74),(cx-37*scale,cy+13*scale),(cx+75*scale,cy-8*scale),3)
    pygame.draw.rect(screen,(7,9,10),(cx+56*scale,cy-18*scale,42*scale,8*scale),border_radius=2)

# Android/Pygame can report one physical tap as both FINGERDOWN and
# MOUSEBUTTONDOWN. Ignore the duplicate so START cannot immediately select
# the overlapping Mode 1 button.
_last_menu_tap_ms = -1000
_last_menu_tap_pos = (-10000, -10000)

def accept_menu_tap(pos):
    global _last_menu_tap_ms, _last_menu_tap_pos
    now = pygame.time.get_ticks()
    dx = pos[0] - _last_menu_tap_pos[0]
    dy = pos[1] - _last_menu_tap_pos[1]
    if now - _last_menu_tap_ms < 400 and dx * dx + dy * dy < 70 * 70:
        return False
    _last_menu_tap_ms = now
    _last_menu_tap_pos = pos
    return True

def handle_menu_tap(pos):
    """Handle menu taps in one place so the start tap cannot also select a mode."""
    global menu_page, running, game_mode, selected_map
    if not main_menu:
        return False
    if menu_page == "main":
        if start_btn.collidepoint(pos) or pygame.Rect(25,195,285,49).collidepoint(pos) or pygame.Rect(25,252,285,49).collidepoint(pos):
            menu_page = "modes"
        elif menu_help_btn.collidepoint(pos) or pygame.Rect(25,366,285,49).collidepoint(pos):
            menu_page = "help"
        elif menu_quit_btn.collidepoint(pos) or pygame.Rect(25,423,285,49).collidepoint(pos):
            running = False
        elif pygame.Rect(25,309,285,49).collidepoint(pos):
            menu_page = "modes"
    elif menu_page == "modes":
        if mode1_btn.collidepoint(pos):
            game_mode = 1
            menu_page = "maps"
        elif mode2_btn.collidepoint(pos):
            game_mode = 2
            menu_page = "maps"
        elif mode3_btn.collidepoint(pos):
            game_mode = 3
            menu_page = "maps"
        elif mode_back_btn.collidepoint(pos):
            menu_page = "main"
    elif menu_page == "maps":
        if map_back_btn.collidepoint(pos):
            menu_page = "modes"
        else:
            for i, rect in enumerate(map_cards):
                if rect.collidepoint(pos):
                    selected_map = i
                    reset(game_mode)
                    break
    elif menu_page == "help" and menu_help_btn.collidepoint(pos):
        menu_page = "main"
    return True

def reset(mode=1):
    global player, health, max_health, ammo, max_ammo, score, player_damage, level, enemies, bullets, enemy_bullets, acid_bullets
    global last_spawn, last_shot, game_over, paused, main_menu, game_mode, menu_page, store_open, money, armor_helmet, armor_chest, weapon_level, auto_weapon, shooting_requested, last_reward_score
    global jump_height, jump_velocity, on_ground, zombie_kills, boss_kills
    player = pygame.Rect(110, GROUND_Y - 48, 38, 48)
    health, max_health, ammo, max_ammo, score = 100, 100, 30, 30, 0
    player_damage = 1
    level = 0
    game_mode = mode
    menu_page = "main"
    store_open = False
    money = 0
    armor_helmet = armor_chest = weapon_level = 0
    auto_weapon = False
    shooting_requested = False
    last_reward_score = 0
    zombie_kills = 0
    boss_kills = 0
    enemies, bullets, enemy_bullets, acid_bullets = [], [], [], []
    last_spawn = pygame.time.get_ticks()
    last_shot = 0
    jump_height, jump_velocity, on_ground = 0, 0, True
    game_over = paused = False
    main_menu = False

def soldier(rect, color, facing=1):
    """Draw a more detailed side-view combatant with helmet, vest, limbs and rifle."""
    x, y, w, h = rect.x, rect.y, rect.width, rect.height
    # Legs and tactical boots
    leg_dark = (22, 27, 26)
    pygame.draw.line(screen, leg_dark, (x+w//2-5, y+h-18), (x+w//2-9, y+h-3), 6)
    pygame.draw.line(screen, leg_dark, (x+w//2+5, y+h-18), (x+w//2+10, y+h-3), 6)
    pygame.draw.line(screen, (9, 12, 13), (x+w//2-11, y+h-3), (x+w//2-2, y+h-3), 5)
    pygame.draw.line(screen, (9, 12, 13), (x+w//2+6, y+h-3), (x+w//2+16, y+h-3), 5)
    # Torso and shoulder plates
    torso = pygame.Rect(x+5, y+18, w-10, max(15, h-27))
    pygame.draw.rect(screen, color, torso, border_radius=5)
    pygame.draw.rect(screen, (21, 29, 27), (x+7, y+20, w-14, h-31), 2, border_radius=4)
    pygame.draw.polygon(screen, tuple(min(255,c+22) for c in color),
                        [(x+3,y+22),(x+10,y+17),(x+17,y+23),(x+15,y+33),(x+5,y+32)])
    pygame.draw.polygon(screen, tuple(min(255,c+14) for c in color),
                        [(x+w-17,y+23),(x+w-10,y+17),(x+w-3,y+22),(x+w-5,y+33),(x+w-15,y+33)])
    # Chest rig, pouches and straps
    pygame.draw.line(screen, (17, 21, 20), (x+12,y+22), (x+w-11,y+39), 3)
    pygame.draw.line(screen, (17, 21, 20), (x+w-12,y+22), (x+12,y+39), 3)
    for i in range(2):
        pouch = pygame.Rect(x+9+i*10, y+30, 7, 8)
        pygame.draw.rect(screen, (83, 79, 58), pouch, border_radius=2)
        pygame.draw.rect(screen, (25, 28, 24), pouch, 1, border_radius=2)
    # Neck and head
    pygame.draw.rect(screen, (65, 57, 46), (x+w//2-4,y+12,8,8))
    pygame.draw.ellipse(screen, (150, 117, 86), (x+w//2-8,y+4,16,17))
    # Helmet dome, rim, and dark visor
    pygame.draw.ellipse(screen, (24, 31, 30), (x+w//2-11,y,22,14))
    pygame.draw.arc(screen, (130, 119, 83), pygame.Rect(x+w//2-12,y-1,24,17), 3.14, 6.25, 2)
    visor_x = x+w//2-8 if facing > 0 else x+w//2-9
    pygame.draw.rect(screen, (10, 17, 19), (visor_x,y+7,17,6), border_radius=2)
    pygame.draw.line(screen, (96, 121, 119), (visor_x+2,y+8), (visor_x+12,y+8), 1)
    # Arms angled toward the rifle
    arm_col = tuple(max(0,c-10) for c in color)
    pygame.draw.line(screen, arm_col, (x+8,y+23), (x+w//2+5*facing,y+30), 5)
    pygame.draw.line(screen, arm_col, (x+w-8,y+23), (x+w//2+11*facing,y+26), 5)
    # Rifle with stock, receiver, barrel, magazine and muzzle
    rx = x+w//2 + 2*facing
    ry = y+28
    pygame.draw.line(screen, (8, 10, 11), (rx-10*facing,ry+3), (rx+27*facing,ry-2), 5)
    pygame.draw.line(screen, (94, 96, 84), (rx-5*facing,ry+1), (rx+20*facing,ry-2), 2)
    pygame.draw.line(screen, (7, 9, 10), (rx+18*facing,ry-2), (rx+31*facing,ry-3), 2)
    pygame.draw.line(screen, (15, 17, 16), (rx+3*facing,ry+2), (rx+7*facing,ry+9), 3)
    pygame.draw.circle(screen, (255, 157, 61), (int(rx+32*facing), int(ry-3)), 2)

def background():
    """Draw a playable themed battlefield for the selected map (no external files needed)."""
    themes = [
        ((93, 135, 157), (49, 67, 67), (91, 78, 56)),  # port
        ((214, 171, 105), (151, 111, 64), (183, 133, 66)), # desert
        ((91, 105, 108), (57, 66, 65), (103, 82, 59)), # factory
        ((164, 193, 211), (100, 127, 145), (218, 226, 230)), # snow
        ((93, 106, 116), (49, 56, 60), (111, 76, 55)), # ruined city
        ((89, 128, 89), (40, 75, 52), (102, 91, 57)), # jungle
    ]
    sky, building, ground = themes[selected_map % len(themes)]
    screen.fill(sky)
    # atmospheric clouds / distant haze
    haze = tuple(min(255, c + 22) for c in sky)
    for x, y, r in [(80, 90, 20), (260, 125, 16), (530, 75, 22), (760, 120, 18)]:
        pygame.draw.circle(screen, haze, (x, y), r)
    if selected_map == 0:  # cargo port
        for x in range(10, WIDTH, 125):
            pygame.draw.rect(screen, (122, 65, 39), (x, GROUND_Y-80, 112, 75))
            pygame.draw.rect(screen, (54, 94, 110), (x+5, GROUND_Y-75, 102, 65), 2)
            for xx in range(x+18, x+105, 22): pygame.draw.line(screen, (38,61,70), (xx,GROUND_Y-72),(xx,GROUND_Y-10),2)
        pygame.draw.line(screen, (65, 68, 60), (80,180),(80,GROUND_Y-85),5)
        pygame.draw.line(screen, (65, 68, 60), (80,180),(260,180),4)
    elif selected_map == 1:  # desert village
        for x,w,h in [(0,95,130),(130,105,175),(285,110,145),(450,100,185),(620,120,140),(790,110,165)]:
            pygame.draw.rect(screen, (160,124,77), (x,GROUND_Y-h,w,h))
            pygame.draw.polygon(screen, (111,80,51), [(x-4,GROUND_Y-h),(x+w//2,GROUND_Y-h-17),(x+w+4,GROUND_Y-h)])
            for wx in range(x+16,x+w-8,32): pygame.draw.rect(screen,(55,48,38),(wx,GROUND_Y-h+30,13,19))
    elif selected_map == 2:  # factory
        for x,w,h in [(0,130,180),(160,150,235),(345,135,170),(515,165,220),(715,185,190)]:
            pygame.draw.rect(screen,(54,64,66),(x,GROUND_Y-h,w,h))
            pygame.draw.rect(screen,(94,103,99),(x+8,GROUND_Y-h+12,w-16,12))
            for wx in range(x+18,x+w-10,34): pygame.draw.rect(screen,(27,34,35),(wx,GROUND_Y-h+42,20,28))
    elif selected_map == 3:  # snowy base
        for x,w,h in [(0,100,140),(130,120,200),(290,100,150),(430,130,220),(600,110,165),(760,130,190)]:
            pygame.draw.rect(screen,(111,139,154),(x,GROUND_Y-h,w,h))
            pygame.draw.polygon(screen,(224,234,239),[(x,GROUND_Y-h),(x+w//2,GROUND_Y-h-14),(x+w,GROUND_Y-h)])
        for i in range(65): pygame.draw.circle(screen,(235,244,248),(random.randrange(WIDTH),random.randrange(HEIGHT)),1)
    elif selected_map == 4:  # ruined city
        for x,w,h in [(0,90,145),(105,120,195),(250,95,160),(370,125,220),(525,115,170),(665,105,205),(800,100,150)]:
            pygame.draw.rect(screen,(58,64,67),(x,GROUND_Y-h,w,h))
            pygame.draw.polygon(screen,(35,41,43),[(x,GROUND_Y-h),(x+20,GROUND_Y-h-16),(x+45,GROUND_Y-h+2),(x+w,GROUND_Y-h-8),(x+w,GROUND_Y)])
            for wx in range(x+12,x+w-8,27): pygame.draw.rect(screen,(116,79,48),(wx,GROUND_Y-h+25,9,13))
    else:  # jungle
        for x in range(-10,WIDTH,95):
            pygame.draw.rect(screen,(72,64,43),(x+32,GROUND_Y-125,14,125))
            pygame.draw.circle(screen,(28,78,47),(x+38,GROUND_Y-145),48)
            pygame.draw.circle(screen,(42,99,55),(x+12,GROUND_Y-126),29)
        pygame.draw.rect(screen,(81,91,58),(340,GROUND_Y-92,170,92))
        pygame.draw.rect(screen,(41,61,43),(360,GROUND_Y-72,38,72))
    floor_col = (222,231,235) if selected_map == 3 else ((54,80,51) if selected_map == 5 else ground)
    pygame.draw.rect(screen, floor_col, (0, GROUND_Y, WIDTH, HEIGHT-GROUND_Y))
    pygame.draw.rect(screen, (125, 95, 55) if selected_map not in (3,5) else floor_col, (0, GROUND_Y, WIDTH, 10))
    # foreground crates / cover vary by map
    if selected_map == 0:
        pygame.draw.rect(screen,(117,62,36),(420,GROUND_Y-42,52,42)); pygame.draw.rect(screen,(55,86,95),(425,GROUND_Y-37,42,32),3)
    elif selected_map == 1:
        pygame.draw.rect(screen,(142,105,62),(420,GROUND_Y-42,62,42))
    elif selected_map == 2:
        pygame.draw.rect(screen,(45,51,52),(420,GROUND_Y-52,70,52)); pygame.draw.rect(screen,(126,112,75),(430,GROUND_Y-43,50,3))
    elif selected_map == 3:
        pygame.draw.rect(screen,(193,211,220),(420,GROUND_Y-42,62,42))
    elif selected_map == 4:
        pygame.draw.rect(screen,(66,67,62),(420,GROUND_Y-42,62,42)); pygame.draw.line(screen,(35,38,37),(420,GROUND_Y-42),(482,GROUND_Y),3)
    else:
        pygame.draw.rect(screen,(73,67,42),(420,GROUND_Y-42,62,42)); pygame.draw.circle(screen,(32,78,43),(451,GROUND_Y-56),26)

def draw_hud():
    pygame.draw.rect(screen, DARK, (12, 12, 300, 74), border_radius=10)
    text(f"HP: {health}/{max_health}  LVL: {level if game_mode in (2, 3) else level + 1}", 24, 20)
    pygame.draw.rect(screen, (75, 75, 75), (24, 49, 180, 14), border_radius=5)
    pygame.draw.rect(screen, RED, (24, 49, max(0, 180 * health // max(1, max_health)), 14), border_radius=5)
    text(f"AMMO: {ammo}/{max_ammo}   SCORE: {score}   DMG: {player_damage}", 24, 65)
    map_label = ["PORT", "DESERT", "FACTORY", "SNOW", "RUINS", "JUNGLE"][selected_map % 6]
    text(map_label, WIDTH-130, 20, (255,210,105), FONT)
    if game_mode in (2, 3): text(f"$ {money}  ARMOR H{armor_helmet}/C{armor_chest}", 325, 20, YELLOW)
    if game_mode == 3: text(f"ZOMBIES: {zombie_kills}  GIANTS: {boss_kills}  LEVEL: {level}", 325, 45, (145,220,145), pygame.font.Font(None,22))

def spawn_giant():
    """Spawn the milestone giant; its strength increases every five levels."""
    tier = max(1, level // 5)
    size = min(100, 62 + (tier - 1) * 4)
    hp = 6 + level * 3 + (tier - 1) * 8
    speed = max(2, 2 + level // 2 + (tier - 1))
    rect = pygame.Rect(WIDTH + 5, GROUND_Y - size, size, size)
    enemies.append({"rect": rect, "hp": hp, "max_hp": hp, "speed": speed,
                    "shot": pygame.time.get_ticks(), "zombie": True, "giant": True,
                    "kind": "normal", "jump_phase": 0, "giant_tier": tier})

def spawn_enemy():
    """Spawn zombie types only after their level unlocks; giants are level milestones."""
    if game_mode == 3:
        # New zombie types unlock progressively instead of appearing from the beginning.
        unlocked = ["normal"]
        if level >= 2:
            unlocked.append("acid")
        if level >= 4:
            unlocked.append("leaper")
        kind = random.choice(unlocked)
        size = 40 if kind == "leaper" else 42
        hp = 2 + level
        base_speed = random.randint(2 + level // 2, 3 + level // 2)
        if kind == "leaper": base_speed += 1
        rect = pygame.Rect(WIDTH + 5, GROUND_Y - size, size, size)
        enemies.append({"rect": rect, "hp": hp, "max_hp": hp, "speed": base_speed,
                        "shot": pygame.time.get_ticks(), "zombie": True, "giant": False,
                        "kind": kind, "jump_phase": random.randint(0, 55)})
        return
    if game_mode == 2:
        enemy_hp = 2 + (level // 2)
        speed_bonus = min(3, level // 4)
    else:
        enemy_hp = 2 + level
        speed_bonus = level // 2
    enemies.append({"rect": pygame.Rect(WIDTH + 5, GROUND_Y - 46, 36, 46),
                    "hp": enemy_hp, "max_hp": enemy_hp,
                    "speed": random.randint(2 + speed_bonus, 4 + speed_bonus),
                    "shot": pygame.time.get_ticks(), "zombie": False, "giant": False})

# لا تستدعِ reset هنا؛ لأنها تنقل اللعبة مباشرةً إلى القتال وتخفي القائمة.
last_spawn = pygame.time.get_ticks()
running = True
# ابدأ دائمًا بالقائمة الرئيسية، ولا تدخل القتال إلا بعد اختيار طور صراحةً.
main_menu = True
menu_page = "main"
_startup_frames = 0
while running:
    if _startup_frames < 20:
        hide_android_keyboard()
        _startup_frames += 1
    now = pygame.time.get_ticks()
    # استخرج الأوامر من كل أزرار اللمس المضغوطة في نفس اللحظة.
    move_left = "left" in active_touch_buttons
    move_right = "right" in active_touch_buttons
    shooting = "shoot" in active_touch_buttons
    jump_pressed = "jump" in active_touch_buttons

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if main_menu and menu_page != "main":
                    menu_page = "main"
                elif store_open:
                    store_open = False
                else:
                    running = False
            elif main_menu and menu_page == "help" and event.key == pygame.K_BACKSPACE:
                menu_page = "main"
            elif main_menu and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                menu_page = "modes"
            elif event.key == pygame.K_p:
                paused = not paused
            elif event.key == pygame.K_r:
                ammo = max_ammo
            elif event.key == pygame.K_RETURN and game_over:
                reset(game_mode)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            pos = event_position(event)
            if main_menu:
                if accept_menu_tap(pos):
                    handle_menu_tap(pos)
            elif store_open:
                if store_back_btn.collidepoint(pos): store_open = False
                elif shop_health_btn.collidepoint(pos) and money >= 25:
                    money -= 25; max_health += 25; health = min(max_health, health + 25)
                elif shop_weapon_btn.collidepoint(pos) and money >= 40 and weapon_level < 3:
                    money -= 40; weapon_level += 1; player_damage += 1; max_ammo += 10; ammo = min(max_ammo, ammo + 10)
                elif shop_helmet_btn.collidepoint(pos) and money >= 30 and armor_helmet < 3:
                    money -= 30; armor_helmet += 1
                elif shop_chest_btn.collidepoint(pos) and money >= 40 and armor_chest < 3:
                    money -= 40; armor_chest += 1
                elif shop_special_btn.collidepoint(pos) and money >= 120 and not auto_weapon:
                    money -= 120; auto_weapon = True; ammo = max_ammo
            elif game_over:
                if restart_btn.collidepoint(pos):
                    reset(game_mode)
                elif gameover_home_btn.collidepoint(pos):
                    main_menu = True
                    menu_page = "main"
                    game_over = False
                    paused = False
                    store_open = False
                    active_touch_buttons.clear()
                    # Android may emit FINGERDOWN and MOUSEBUTTONDOWN for one tap.
                    # Prevent the duplicate from activating an overlapping main-menu button.
                    _last_menu_tap_ms = pygame.time.get_ticks()
                    _last_menu_tap_pos = pos
            elif paused and pygame.Rect(310, 275, 280, 45).collidepoint(pos):
                paused = False
            elif paused and pause_home_btn.collidepoint(pos):
                main_menu = True
                menu_page = "main"
                paused = False
                game_over = False
                store_open = False
                active_touch_buttons.clear()
                # Ignore the duplicate mouse event generated by the same Android tap.
                _last_menu_tap_ms = pygame.time.get_ticks()
                _last_menu_tap_pos = pos
            elif pause_btn.collidepoint(pos): paused = not paused
            elif store_btn.collidepoint(pos) and game_mode in (2, 3): store_open = True
            elif not paused:
                # خزّن كل زر مضغوط بدل الاعتماد على زر ماوس واحد.
                if left_btn.collidepoint(pos):
                    active_touch_buttons.add("left")
                if right_btn.collidepoint(pos):
                    active_touch_buttons.add("right")
                if shoot_btn.collidepoint(pos):
                    active_touch_buttons.add("shoot")
                    shooting_requested = True
                if reload_btn.collidepoint(pos):
                    ammo = max_ammo
                if jump_btn.collidepoint(pos):
                    active_touch_buttons.add("jump")
        elif event.type == pygame.MOUSEBUTTONUP:
            # عند رفع الإصبع، حرّر الأزرار الموجودة عند موضعه.
            pos = event_position(event)
            if left_btn.collidepoint(pos):
                active_touch_buttons.discard("left")
            if right_btn.collidepoint(pos):
                active_touch_buttons.discard("right")
            if shoot_btn.collidepoint(pos):
                active_touch_buttons.discard("shoot")
            if jump_btn.collidepoint(pos):
                active_touch_buttons.discard("jump")
        elif event.type == pygame.FINGERDOWN:
            pos = event_position(event)
            if main_menu:
                if accept_menu_tap(pos):
                    handle_menu_tap(pos)
            elif store_open:
                if store_back_btn.collidepoint(pos): store_open = False
                elif shop_health_btn.collidepoint(pos) and money >= 25:
                    money -= 25; max_health += 25; health = min(max_health, health + 25)
                elif shop_weapon_btn.collidepoint(pos) and money >= 40 and weapon_level < 3:
                    money -= 40; weapon_level += 1; player_damage += 1; max_ammo += 10; ammo = min(max_ammo, ammo + 10)
                elif shop_helmet_btn.collidepoint(pos) and money >= 30 and armor_helmet < 3:
                    money -= 30; armor_helmet += 1
                elif shop_chest_btn.collidepoint(pos) and money >= 40 and armor_chest < 3:
                    money -= 40; armor_chest += 1
                elif shop_special_btn.collidepoint(pos) and money >= 120 and not auto_weapon:
                    money -= 120; auto_weapon = True; ammo = max_ammo
            elif game_over:
                if restart_btn.collidepoint(pos):
                    reset(game_mode)
                elif gameover_home_btn.collidepoint(pos):
                    main_menu = True
                    menu_page = "main"
                    game_over = False
                    paused = False
                    store_open = False
                    active_touch_buttons.clear()
                    # Android may emit FINGERDOWN and MOUSEBUTTONDOWN for one tap.
                    # Prevent the duplicate from activating an overlapping main-menu button.
                    _last_menu_tap_ms = pygame.time.get_ticks()
                    _last_menu_tap_pos = pos
            elif paused and pygame.Rect(310, 275, 280, 45).collidepoint(pos):
                paused = False
            elif paused and pause_home_btn.collidepoint(pos):
                main_menu = True
                menu_page = "main"
                paused = False
                game_over = False
                store_open = False
                active_touch_buttons.clear()
                # Ignore the duplicate mouse event generated by the same Android tap.
                _last_menu_tap_ms = pygame.time.get_ticks()
                _last_menu_tap_pos = pos
            elif pause_btn.collidepoint(pos): paused = not paused
            elif store_btn.collidepoint(pos) and game_mode in (2, 3): store_open = True
            elif not paused:
                if left_btn.collidepoint(pos):
                    active_touch_buttons.add("left")
                if right_btn.collidepoint(pos):
                    active_touch_buttons.add("right")
                if shoot_btn.collidepoint(pos):
                    active_touch_buttons.add("shoot")
                    shooting_requested = True
                if reload_btn.collidepoint(pos):
                    ammo = max_ammo
                if jump_btn.collidepoint(pos):
                    active_touch_buttons.add("jump")
        elif event.type == pygame.FINGERUP:
            pos = event_position(event)
            if left_btn.collidepoint(pos):
                active_touch_buttons.discard("left")
            if right_btn.collidepoint(pos):
                active_touch_buttons.discard("right")
            if shoot_btn.collidepoint(pos):
                active_touch_buttons.discard("shoot")
            if jump_btn.collidepoint(pos):
                active_touch_buttons.discard("jump")

    # دعم ضغطات الماوس المستمرة في الأجهزة/الإصدارات التي لا ترسل أحداث اللمس المتعددة.
    # لا نمسح الحالات هنا حتى يظل بالإمكان الجمع بين الحركة والقفز وإطلاق النار.

    keys = pygame.key.get_pressed()
    if keys[pygame.K_UP] or keys[pygame.K_w]:
        jump_pressed = True
    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        move_left = True
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        move_right = True
    if keys[pygame.K_SPACE]:
        shooting = True

    if not game_over and not paused and not main_menu and not store_open:
        previous_player_x = player.x
        if move_left:
            player.x -= 5
        if move_right:
            player.x += 5
        player.x = max(0, min(WIDTH - player.width, player.x))

        # قفزة قصيرة: اضغط زر النط لتفادي الطلقات ثم العودة للأرض.
        if jump_pressed and on_ground:
            jump_velocity = -13
            on_ground = False
        if not on_ground:
            jump_height += jump_velocity
            jump_velocity += 0.7
            if jump_height >= 0:
                jump_height = 0
                jump_velocity = 0
                on_ground = True
        player.y = GROUND_Y - player.height + int(jump_height)

        fire_interval = 95 if auto_weapon else 180
        should_fire = (shooting if auto_weapon else shooting_requested)
        if should_fire and ammo > 0 and now - last_shot >= fire_interval:
            bullets.append(pygame.Rect(player.right, player.y + 22, 16, 5))
            ammo -= 1
            last_shot = now
            if not auto_weapon:
                shooting_requested = False
        if ammo <= 0:
            shooting_requested = False

        if now - last_spawn > max(850, 1900 - score * 2):
            spawn_enemy()
            last_spawn = now

        for b in bullets[:]:
            b.x += 10
            if b.left > WIDTH:
                bullets.remove(b)
                continue
            for e in enemies[:]:
                if b.colliderect(e["rect"]):
                    bullets.remove(b)
                    e["hp"] -= player_damage
                    if e["hp"] <= 0:
                        enemies.remove(e)
                        if game_mode == 3:
                            zombie_kills += 1
                            if e.get("giant", False):
                                # Giants keep the highest reward, regardless of their special type.
                                boss_kills += 1
                                score += 30
                                money += 35
                            elif e.get("kind") == "acid":
                                score += 20
                            elif e.get("kind") == "leaper":
                                score += 15
                            else:
                                score += 10
                            new_level = score // 100
                            if new_level > level:
                                gained_levels = new_level - level
                                level = new_level
                                # Reward money for every new level; progression is unlimited.
                                money += 75 * gained_levels
                                max_health += 10 * gained_levels
                                health = min(max_health, health + 10 * gained_levels)
                                max_ammo += 10 * gained_levels
                                ammo = min(max_ammo, ammo + 10 * gained_levels)
                                # Spawn a giant at each five-level milestone (5, 10, 15...).
                                for milestone in range(level - gained_levels + 1, level + 1):
                                    if milestone > 0 and milestone % 5 == 0:
                                        spawn_giant()
                        else:
                            score += 10
                            if game_mode == 1:
                                new_level = score // 100
                                if new_level > level:
                                    gained_levels = new_level - level
                                    level = new_level
                                    max_health += 20 * gained_levels
                                    health = min(max_health, health + 20 * gained_levels)
                                    max_ammo += 10 * gained_levels
                                    ammo = min(max_ammo, ammo + 10 * gained_levels)
                                    player_damage = 1 + level // 2
                            else:
                                earned_hundreds = score // 100
                                if earned_hundreds > last_reward_score // 100:
                                    money += 60 * (earned_hundreds - last_reward_score // 100)
                                    last_reward_score = earned_hundreds * 100
                                    level = earned_hundreds
                    break

        for e in enemies[:]:
            er = e["rect"]
            if e.get("zombie", False):
                kind = e.get("kind", "normal")
                # Leapers spring toward the player; they keep moving while the player is airborne.
                if kind == "leaper":
                    e["jump_phase"] = (e.get("jump_phase", 0) + 1) % 70
                    if e["jump_phase"] < 24:
                        er.y = GROUND_Y - er.height - int(48 * (1 - abs(e["jump_phase"] - 12) / 12))
                    else:
                        er.y = GROUND_Y - er.height
                er.x -= e["speed"]
                if kind == "acid" and now - e["shot"] > max(900, 2400 - level * 15):
                    acid_bullets.append({"rect": pygame.Rect(er.left, er.y + er.height // 2, 13, 9), "speed": 6 + min(level, 8)})
                    e["shot"] = now
                # A grounded zombie is a physical obstacle: it cannot pass through the soldier.
                # Jumping over it lets it continue forward and leave the screen.
                if on_ground and er.colliderect(player):
                    if previous_player_x + player.width <= er.left + 5 and move_right:
                        player.right = er.left
                    elif previous_player_x >= er.right - 5 and move_left:
                        player.left = er.right
                    elif previous_player_x < er.left:
                        player.right = min(player.right, er.left)
                    else:
                        player.left = max(player.left, er.right)
                    if now - e.get("contact_tick", 0) > 800:
                        health -= max(2, 7 + level * 2 - armor_chest * 2)
                        e["contact_tick"] = now
            else:
                er.x -= e["speed"]
                if now - e["shot"] > 1400:
                    enemy_bullets.append(pygame.Rect(er.left, er.y + 25, 12, 5))
                    e["shot"] = now
            if er.right < 0:
                enemies.remove(e)
                health -= max(1, 8 - armor_helmet - armor_chest * 2)

        for b in enemy_bullets[:]:
            b.x -= 7
            if b.right < 0:
                enemy_bullets.remove(b)
            elif b.colliderect(player):
                enemy_bullets.remove(b)
                if game_mode == 2:
                    damage_taken = 8 + min(4, level // 3)  # الضرر يزيد ببطء وبحد أقصى للزيادة
                else:
                    damage_taken = 10 + level * 2
                damage_taken = max(1, damage_taken - armor_helmet - armor_chest * 2)
                health -= damage_taken

        for acid in acid_bullets[:]:
            acid["rect"].x -= acid["speed"]
            if acid["rect"].right < 0:
                acid_bullets.remove(acid)
            elif acid["rect"].colliderect(player):
                acid_bullets.remove(acid)
                health -= max(4, 9 + level - armor_chest)

        if health <= 0:
            health = 0
            game_over = True

    screen = canvas
    background()
    # Shadow stays on the ground; when the soldier jumps it shrinks and fades.
    shadow_w = max(12, player.width + 12 - int(abs(jump_height) * 0.35))
    shadow_h = max(2, 8 - int(abs(jump_height) * 0.06))
    shadow_alpha = max(35, 115 - int(abs(jump_height) * 1.4))
    shadow_layer = pygame.Surface((shadow_w + 8, shadow_h + 4), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow_layer, (5, 8, 7, shadow_alpha), (4, 2, shadow_w, shadow_h))
    screen.blit(shadow_layer, (player.centerx - shadow_layer.get_width() // 2, GROUND_Y - 5))
    soldier(player, (45, 75, 55), 1)
    for e in enemies:
        if e.get("zombie", False):
            zombie_rect = e["rect"]
            zcol = (82, 132, 70) if not e.get("giant", False) else (112, 88, 63)
            # Zombie shadow stays on the ground even when a leaper is airborne.
            pygame.draw.ellipse(screen, (22, 28, 23), (zombie_rect.centerx-zombie_rect.width//2-4, GROUND_Y-5, zombie_rect.width+8, 7))
            kind = e.get("kind", "normal")
            if kind == "acid": zcol = (94, 133, 57) if not e.get("giant", False) else zcol
            elif kind == "leaper": zcol = (88, 126, 105) if not e.get("giant", False) else zcol
            # Unarmed zombie: hunched body, oversized head, glowing eyes and reaching arms.
            body = pygame.Rect(zombie_rect.x+zombie_rect.width//4, zombie_rect.y+zombie_rect.height//3, zombie_rect.width//2, zombie_rect.height*2//3)
            pygame.draw.rect(screen, zcol, body, border_radius=8)
            pygame.draw.rect(screen, (44, 69, 43), body, 2, border_radius=8)
            head_size = max(15, zombie_rect.width//2)
            head = pygame.Rect(zombie_rect.x+zombie_rect.width//3, zombie_rect.y+2, head_size, head_size)
            pygame.draw.ellipse(screen, (118, 153, 91) if not e.get("giant", False) else (146, 112, 76), head)
            pygame.draw.circle(screen, (224, 55, 42), (head.x+head.width//3, head.y+head.height//2), 2 if not e.get("giant", False) else 4)
            pygame.draw.circle(screen, (224, 55, 42), (head.x+head.width*2//3, head.y+head.height//2), 2 if not e.get("giant", False) else 4)
            arm_y = zombie_rect.y+zombie_rect.height//2
            pygame.draw.line(screen, zcol, (body.left+2, arm_y), (zombie_rect.x-5, arm_y+8), 5 if not e.get("giant", False) else 9)
            pygame.draw.line(screen, zcol, (body.right-2, arm_y), (zombie_rect.right+5, arm_y+3), 5 if not e.get("giant", False) else 9)
            if e.get("kind") == "acid":
                pygame.draw.circle(screen, (110, 255, 65), (head.centerx, head.bottom-2), max(4, head.width//5))
                text("ACID", zombie_rect.centerx, zombie_rect.y-20, (153,255,87), pygame.font.Font(None,18), center=True)
            elif e.get("kind") == "leaper":
                text("LEAPER", zombie_rect.centerx, zombie_rect.y-20, (120,220,195), pygame.font.Font(None,18), center=True)
            if e.get("giant", False):
                text("GIANT", zombie_rect.centerx, zombie_rect.y-36, (255,176,78), pygame.font.Font(None,20), center=True)
        else:
            soldier(e["rect"], (125, 55, 45), -1)
        bar_width_total = e["rect"].width
        pygame.draw.rect(screen, RED, (e["rect"].x, e["rect"].y - 8, bar_width_total, 4))
        bar_width = max(0, bar_width_total * e["hp"] // max(1, e["max_hp"]))
        pygame.draw.rect(screen, GREEN, (e["rect"].x, e["rect"].y - 8, bar_width, 4))
    for b in bullets:
        pygame.draw.rect(screen, YELLOW, b, border_radius=2)
    for b in enemy_bullets:
        pygame.draw.rect(screen, (255, 120, 65), b, border_radius=2)
    for acid in acid_bullets:
        pygame.draw.ellipse(screen, (126, 255, 55), acid["rect"])
        pygame.draw.ellipse(screen, (206, 255, 145), acid["rect"].inflate(-5, -4))

    draw_hud()
    button(left_btn, "◀", (38, 58, 72), BIG)
    button(right_btn, "▶", (38, 58, 72), BIG)
    button(shoot_btn, "FIRE 🔫", (145, 42, 38), FONT)
    button(reload_btn, "RELOAD", (55, 82, 60), FONT)
    button(jump_btn, "JUMP ▲", (45, 85, 145), FONT)
    button(pause_btn, "Ⅱ", (50, 55, 62), BIG)
    if game_mode in (2, 3) and not main_menu:
        button(store_btn, "SHOP $", (125, 85, 25), FONT)
    if store_open and not main_menu:
        draw_panel(pygame.Rect(70, 48, 760, 464), (8, 12, 16), (207, 155, 57), 18, 2)
        text("FIELD ARMORY", WIDTH // 2, 78, (255, 207, 102), BIG, center=True)
        text(f"AVAILABLE CASH  ${money}     •     LEVEL {level}", WIDTH // 2, 116, WHITE, FONT, center=True)
        # Six visual stat/item cards; the four upgrade cards keep their original working hitboxes.
        cards = [(shop_health_btn, "MED KIT", "+25 MAX HP", "$25", (40,95,68)),
                 (shop_weapon_btn, "WEAPON KIT", "+DAMAGE / AMMO", "$40", (43,76,108)),
                 (shop_helmet_btn, "TACTICAL HELMET", f"LEVEL {armor_helmet}/3", "$30", (84,87,78)),
                 (shop_chest_btn, "BODY ARMOR", f"LEVEL {armor_chest}/3", "$40", (103,63,52))]
        for r, title, desc, price, col in cards:
            draw_panel(r, (17,24,28), (191,143,55), 12, 1)
            pygame.draw.circle(screen, col, (r.centerx, r.y+18), 13)
            text(title, r.centerx, r.y+35, (245,205,111), pygame.font.Font(None,23), center=True)
            text(desc, r.centerx, r.y+57, WHITE, pygame.font.Font(None,20), center=True)
            text("BUY  " + price, r.centerx, r.bottom-12, (130,225,144), pygame.font.Font(None,21), center=True)
        draw_panel(shop_special_btn, (25,34,34), (220,166,62), 12, 2)
        special_label = "SPECIAL AUTO GUN  •  OWNED" if auto_weapon else "UNLOCK AUTO GUN  •  $120"
        text("★  SPECIAL WEAPON", shop_special_btn.centerx, shop_special_btn.y+16, (255,206,91), FONT, center=True)
        text(special_label, shop_special_btn.centerx, shop_special_btn.y+40, (134,225,150) if auto_weapon else WHITE, FONT, center=True)
        text("ZOMBIE MODE: +10 points per zombie • Endless levels • Giant bonus", WIDTH // 2, 446, (180,188,183), pygame.font.Font(None,20), center=True)
        button(store_back_btn, "←  RETURN TO BATTLE", (35, 105, 65), FONT)

    if main_menu:
        draw_menu_backdrop()
        if menu_page == "main":
            # Hero composition: soldier on the right, premium menu on the left.
            draw_soldier_silhouette((595, 310), 1.18)
            pygame.draw.rect(screen, (7, 10, 12), (0, 0, 340, HEIGHT))
            pygame.draw.line(screen, (191, 137, 43), (16, 18), (324, 18), 2)
            text("WAR", 30, 38, (230, 230, 219), BIG)
            text("SHOOTER", 30, 88, (237, 174, 47), BIG)
            text("TACTICAL COMBAT", 33, 139, (174, 180, 175), FONT)
            pygame.draw.line(screen, (174, 64, 39), (30, 174), (310, 174), 3)
            menu_items = [(pygame.Rect(25,195,285,49), "◎   PLAY", True),
                          (pygame.Rect(25,252,285,49), "⚔   GAME MODES", False),
                          (pygame.Rect(25,309,285,49), "▣   ARMORY / SHOP", False),
                          (pygame.Rect(25,366,285,49), "⚙   SETTINGS", False),
                          (pygame.Rect(25,423,285,49), "↩   EXIT", False)]
            for r,label,active in menu_items:
                draw_gold_button(r,label,active)
            # Keep existing hitboxes functional and map them to the visual menu.
            draw_panel(pygame.Rect(390, 438, 475, 91), (10,14,16), (94,77,44), 10, 1)
            text("FIELD REPORT", 415, 449, (230,190,102), FONT)
            text("Choose your mission. Survive. Upgrade. Dominate.", 415, 481, WHITE, FONT)
            text("VERSION 1.0  •  MOBILE COMBAT", 415, 507, (150,158,154), pygame.font.Font(None,20))
            # Transparent-compatible invisible hit areas are not drawn over the art.
        elif menu_page == "modes":
            draw_panel(pygame.Rect(22,18,856,524),(9,13,16),(181,132,47),14,2)
            text("SELECT YOUR MISSION", WIDTH//2, 52, (240,194,87), BIG, center=True)
            text("CHOOSE A COMBAT STYLE", WIDTH//2, 87, (170,178,176), FONT, center=True)
            cards = [pygame.Rect(30,125,265,142), pygame.Rect(318,125,265,142), pygame.Rect(606,125,265,142)]
            card_data = [
                ("01  SURVIVAL", "Armed enemies", "Survive the waves", (189,142,58)),
                ("02  LEVELS & SHOP", "Earn cash in battle", "Upgrade your gear", (73,132,165)),
                ("03  ZOMBIE MODE", "Unarmed zombies", "Endless levels • Giants", (80,155,91)),
            ]
            for rect, data in zip(cards, card_data):
                title, line1, line2, accent = data
                draw_panel(rect, (14,22,23), accent, 12, 2)
                text(title, rect.centerx, 153, accent, pygame.font.Font(None,29), center=True)
                text(line1, rect.centerx, 198, WHITE, pygame.font.Font(None,22), center=True)
                text(line2, rect.centerx, 228, (177,186,183), pygame.font.Font(None,20), center=True)
            button(pygame.Rect(35,280,255,48), "▶ PLAY SURVIVAL", (105,72,20), FONT)
            button(pygame.Rect(323,280,255,48), "▶ LEVELS & SHOP", (36,76,102), FONT)
            button(mode3_btn, "▶ ZOMBIE MODE", (38,103,57), FONT)
            button(mode_back_btn, "← BACK", (52,56,57), FONT)
            text("ZOMBIE TRIAL: 3 LEVELS • KILL ZOMBIES • BUY UPGRADES", WIDTH//2, 500, (154,191,154), pygame.font.Font(None,21), center=True)
        elif menu_page == "maps":
            draw_panel(pygame.Rect(18, 16, 864, 528), (8,12,15), (181,132,47), 14, 2)
            text("SELECT BATTLEFIELD", WIDTH//2, 54, (240,194,87), BIG, center=True)
            text("Choose a map for this match", WIDTH//2, 88, (180,187,181), FONT, center=True)
            map_names = ["PORT", "DESERT", "FACTORY", "SNOW BASE", "RUINED CITY", "JUNGLE"]
            map_subs = ["Cargo & cranes", "Sandstone village", "Industrial yard", "Frozen outpost", "Broken streets", "Overgrown ruins"]
            map_colors = [(115,72,44),(149,105,57),(65,80,83),(130,163,184),(73,76,78),(43,94,54)]
            for i, rect in enumerate(map_cards):
                active = selected_map == i
                draw_panel(rect, (15,22,24), (255,194,66) if active else (91,103,101), 10, 2 if active else 1)
                # unique mini-scene thumbnails built with shapes
                pygame.draw.rect(screen, map_colors[i], (rect.x+7, rect.y+8, rect.width-14, 112), border_radius=5)
                for k in range(4):
                    bx = rect.x+10+k*28
                    bh = 28 + ((k*19+i*13)%52)
                    pygame.draw.rect(screen, (35+i*3,43+i*2,43), (bx, rect.y+116-bh, 22, bh))
                    if i == 0:
                        pygame.draw.rect(screen,(133,67,39),(bx,rect.y+80,22,30))
                    elif i == 1:
                        pygame.draw.polygon(screen,(183,139,80),[(bx-2,rect.y+116-bh),(bx+11,rect.y+105-bh),(bx+24,rect.y+116-bh)])
                    elif i == 3:
                        pygame.draw.line(screen,(232,242,246),(bx,rect.y+65),(bx+15,rect.y+83),2)
                    elif i == 5:
                        pygame.draw.circle(screen,(36,107,55),(bx+10,rect.y+58),15)
                text(map_names[i], rect.centerx, rect.y+145, (255,207,102) if active else WHITE, FONT, center=True)
                text(map_subs[i], rect.centerx, rect.y+174, (173,181,178), pygame.font.Font(None,18), center=True)
                draw_gold_button(pygame.Rect(rect.x+8,rect.bottom-39,rect.width-16,29), "SELECTED ✓" if active else "SELECT MAP", active, pygame.font.Font(None,18))
            button(map_back_btn, "← MODES", (52,56,57), FONT)
            text("TAP A MAP CARD TO START", WIDTH//2, 501, (169,177,172), pygame.font.Font(None,20), center=True)
        elif menu_page == "help":
            draw_panel(pygame.Rect(90,70,720,420),(9,13,16),(181,132,47),14,2)
            text("FIELD MANUAL", WIDTH//2, 112, (240,194,87), BIG, center=True)
            text("LEFT / RIGHT  —  MOVE", WIDTH//2, 205, WHITE, FONT, center=True)
            text("FIRE  —  SHOOT ENEMIES", WIDTH//2, 250, WHITE, FONT, center=True)
            text("JUMP  —  AVOID INCOMING FIRE", WIDTH//2, 295, WHITE, FONT, center=True)
            text("RELOAD  —  REFILL AMMO", WIDTH//2, 340, WHITE, FONT, center=True)
            text("Earn money in Levels & Shop mode to upgrade your gear.", WIDTH//2, 390, (183,188,180), FONT, center=True)
            button(menu_help_btn, "←  BACK TO MENU", (87,61,22), FONT)

    if paused and not main_menu:
        # Pause overlay has explicit resume and return-to-main-menu actions.
        draw_panel(pygame.Rect(245, 165, 410, 235), (9, 13, 16), (205, 151, 54), 16, 2)
        text("GAME PAUSED", WIDTH // 2, 210, (240, 194, 87), BIG, center=True)
        text("Choose whether to continue or leave this match", WIDTH // 2, 250, WHITE, FONT, center=True)
        button(pygame.Rect(310, 275, 280, 45), "RESUME GAME  ▶", (45, 91, 61), FONT)
        button(pause_home_btn, "⌂  MAIN MENU", (105, 68, 22), FONT)
    if game_over:
        # Dramatic defeat screen with the requested return-to-main-menu button.
        pygame.draw.rect(screen, (2, 4, 6), (205, 145, 490, 330), border_radius=20)
        pygame.draw.rect(screen, (132, 34, 30), (205, 145, 490, 330), 3, border_radius=20)
        pygame.draw.line(screen, (202, 54, 43), (245, 196), (655, 196), 2)
        text("GAME OVER", WIDTH//2, 224, (238, 62, 51), BIG, center=True)
        text(f"FINAL SCORE: {score}", WIDTH//2, 266, WHITE, FONT, center=True)
        button(restart_btn, "PLAY AGAIN", (45, 110, 55), FONT)
        button(gameover_home_btn, "BACK TO MAIN MENU", (104, 58, 22), FONT)

    scaled_frame = pygame.transform.scale(canvas, (SCREEN_W, SCREEN_H))
    display = pygame.display.get_surface()
    display.blit(scaled_frame, (0, 0))
    pygame.display.flip()
    screen = canvas
    clock.tick(60)

pygame.quit()
sys.exit()
