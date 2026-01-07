import asyncio
import pygame
import random
import math
import sys
import os

# --- 全局配置 ---
WIDTH, HEIGHT = 1280, 720
FPS = 60

# 颜色常量
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (200, 50, 50)
GREEN = (50, 200, 50)
BLUE = (50, 150, 255)
YELLOW = (255, 200, 0)
CYAN = (0, 255, 255)
DARK_BG = (20, 20, 30)

pygame.init()
pygame.mixer.init()

# 设置应用图标
def set_game_icon():
    icon = pygame.Surface((32, 32), pygame.SRCALPHA)
    pygame.draw.circle(icon, (0, 100, 200), (16, 16), 16)
    pygame.draw.polygon(icon, WHITE, [(16, 6), (26, 26), (6, 26)])
    pygame.display.set_icon(icon)

set_game_icon()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("求生之路")
clock = pygame.time.Clock()

# 字体初始化
try:
    font_ui = pygame.font.SysFont(['simhei', 'microsoftyahei'], 20, bold=True)
    font_btn = pygame.font.SysFont(['simhei', 'microsoftyahei'], 28, bold=True)
    font_big = pygame.font.SysFont(['simhei', 'microsoftyahei'], 60, bold=True)
    font_card = pygame.font.SysFont(['simhei', 'microsoftyahei'], 26, bold=True)
    font_dmg = pygame.font.SysFont(['arial', 'simhei'], 24, bold=True)
except:
    font_ui = pygame.font.Font(None, 24)
    font_btn = pygame.font.Font(None, 32)
    font_big = pygame.font.Font(None, 60)
    font_card = pygame.font.Font(None, 28)
    font_dmg = pygame.font.Font(None, 24)

# --- UI组件 ---
class Button:
    def __init__(self, x, y, w, h, text, callback, color=(60, 60, 80)):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.callback = callback
        self.base_color = color
        self.hover_color = (min(color[0]+40,255), min(color[1]+40,255), min(color[2]+40,255))
        
    def draw(self, surf):
        mx, my = pygame.mouse.get_pos()
        color = self.hover_color if self.rect.collidepoint(mx, my) else self.base_color
        pygame.draw.rect(surf, color, self.rect, border_radius=8)
        pygame.draw.rect(surf, WHITE, self.rect, 2, border_radius=8)
        txt_surf = font_btn.render(self.text, True, WHITE)
        txt_rect = txt_surf.get_rect(center=self.rect.center)
        surf.blit(txt_surf, txt_rect)

    def check_click(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.callback()
                return True
        return False

class Slider:
    def __init__(self, x, y, w, h, initial_val, callback):
        self.rect = pygame.Rect(x, y, w, h)
        self.val = initial_val 
        self.callback = callback
        self.dragging = False
        
    def draw(self, surf):
        pygame.draw.rect(surf, (80, 80, 80), self.rect, border_radius=5)
        fill_rect = pygame.Rect(self.rect.x, self.rect.y, self.rect.width * self.val, self.rect.height)
        pygame.draw.rect(surf, CYAN, fill_rect, border_radius=5)
        handle_x = self.rect.x + self.rect.width * self.val
        handle_y = self.rect.centery
        pygame.draw.circle(surf, WHITE, (int(handle_x), int(handle_y)), self.rect.height + 2)
        txt = font_ui.render(f"{int(self.val * 100)}%", True, WHITE)
        surf.blit(txt, (self.rect.right + 15, self.rect.y - 5))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
                self.update_val(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                self.update_val(event.pos[0])

    def update_val(self, mouse_x):
        relative_x = mouse_x - self.rect.x
        self.val = max(0.0, min(1.0, relative_x / self.rect.width))
        self.callback(self.val)

class VirtualJoystick:
    def __init__(self, x, y, radius):
        self.center = pygame.math.Vector2(x, y)
        self.radius = radius
        self.knob_pos = pygame.math.Vector2(x, y)
        self.knob_radius = radius // 2.5
        self.dragged = False
        self.output = pygame.math.Vector2(0, 0)

    def update(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if (pygame.math.Vector2(event.pos) - self.center).length() <= self.radius * 1.5:
                self.dragged = True
                self.update_knob(event.pos)
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragged = False
            self.knob_pos = pygame.math.Vector2(self.center)
            self.output = pygame.math.Vector2(0, 0)
        elif event.type == pygame.MOUSEMOTION:
            if self.dragged:
                self.update_knob(event.pos)

    def update_knob(self, pos):
        vec = pygame.math.Vector2(pos) - self.center
        if vec.length() > self.radius:
            vec = vec.normalize() * self.radius
        self.knob_pos = self.center + vec
        self.output = vec / self.radius

    def draw(self, surf):
        s = pygame.Surface((self.radius*2, self.radius*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 255, 255, 50), (self.radius, self.radius), self.radius)
        pygame.draw.circle(s, (255, 255, 255, 100), (self.radius, self.radius), self.radius, 2)
        surf.blit(s, (self.center.x - self.radius, self.center.y - self.radius))
        pygame.draw.circle(surf, (0, 255, 255, 150), (int(self.knob_pos.x), int(self.knob_pos.y)), int(self.knob_radius))

# --- 资源管理 ---
class AssetManager:
    def __init__(self):
        self.images = {}
        self.sounds = {}
        self.music_vol = 0.5
        self.sfx_vol = 0.5
        self.MAX_VOL = 0.3 
        self.generate_defaults()

    def generate_defaults(self):
        bg = pygame.Surface((512, 512))
        bg.fill((25, 25, 35))
        for _ in range(80):
            pygame.draw.circle(bg, (40, 40, 50), (random.randint(0,512), random.randint(0,512)), 2)
        self.images['bg'] = bg

        enemy = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.circle(enemy, (200, 50, 50), (20, 20), 18)
        pygame.draw.polygon(enemy, BLACK, [(10, 15), (20, 20), (10, 25)]) 
        pygame.draw.polygon(enemy, BLACK, [(30, 15), (20, 20), (30, 25)])
        self.images['enemy'] = enemy

        gem = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.rect(gem, (0, 255, 255), (5, 5, 10, 10))
        pygame.draw.rect(gem, WHITE, (5, 5, 10, 10), 1)
        self.images['gem'] = gem

    def load(self):
        if os.path.exists("bg.png"): self.images['bg'] = pygame.image.load("bg.png").convert()
        
        if os.path.exists("bgm.mp3"):
            try:
                pygame.mixer.music.load("bgm.mp3")
                self.set_music_vol(self.music_vol)
                pygame.mixer.music.play(-1)
            except: pass
        
        try:
            if os.path.exists("shoot.wav"): self.sounds['shoot'] = pygame.mixer.Sound("shoot.wav")
            if os.path.exists("kill.wav"): self.sounds['kill'] = pygame.mixer.Sound("kill.wav")
            if os.path.exists("levelup.wav"): self.sounds['levelup'] = pygame.mixer.Sound("levelup.wav")
            self.set_sfx_vol(self.sfx_vol)
        except: pass

    def set_music_vol(self, val):
        self.music_vol = val
        real_vol = (val * val) * self.MAX_VOL 
        pygame.mixer.music.set_volume(real_vol)

    def set_sfx_vol(self, val):
        self.sfx_vol = val
        real_vol = (val * val) * self.MAX_VOL
        for s in self.sounds.values():
            s.set_volume(real_vol)

assets = AssetManager()
assets.load()

# --- 游戏实体 ---
class Camera:
    def __init__(self):
        self.offset = pygame.math.Vector2(0, 0)
    def center_target(self, target):
        tx = target.rect.centerx - WIDTH // 2
        ty = target.rect.centery - HEIGHT // 2
        self.offset.x += (tx - self.offset.x) * 0.1
        self.offset.y += (ty - self.offset.y) * 0.1

camera = Camera()

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.pos = pygame.math.Vector2(0, 0) 
        self.radius = 20 
        self.hp = 100
        self.max_hp = 100
        self.xp = 0
        self.level = 1
        self.next_level_xp = 50 
        self.speed = 3.5
        self.weapon_speed = 20 
        self.damage = 30
        self.bullet_count = 1 
        self.penetrate = 0    
        self.weapon_cd = 0
        self.redraw_body()

    def redraw_body(self):
        size = int(self.radius * 2)
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (0, 200, 255), (self.radius, self.radius), self.radius)
        pygame.draw.circle(self.image, WHITE, (self.radius, self.radius), self.radius * 0.6)
        self.rect = self.image.get_rect(center=self.pos)

    def grow(self):
        self.radius += 2
        self.max_hp += 20
        self.hp = self.max_hp
        self.redraw_body()

    def update(self, joy_vec):
        move = pygame.math.Vector2(0, 0)
        # 键盘输入
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w] or keys[pygame.K_UP]: move.y = -1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: move.y = 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: move.x = -1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: move.x = 1
        
        # 摇杆输入覆盖
        if joy_vec.length() > 0: move = joy_vec

        if move.length() > 0:
            if move.length() > 1: move = move.normalize()
            self.pos += move * self.speed
            self.rect.center = self.pos
        self.weapon_cd -= 1

    def check_levelup(self):
        if self.xp >= self.next_level_xp:
            self.xp -= self.next_level_xp
            self.level += 1
            self.next_level_xp = int(self.next_level_xp * 1.3)
            self.grow()
            return True
        return False

class Enemy(pygame.sprite.Sprite):
    def __init__(self, player, diff_mult):
        super().__init__()
        self.image = assets.images['enemy']
        angle = random.uniform(0, 6.28)
        dist = random.uniform(800, 1200)
        self.pos = pygame.math.Vector2(player.pos.x + math.cos(angle)*dist, player.pos.y + math.sin(angle)*dist)
        self.rect = self.image.get_rect(center=self.pos)
        self.player = player
        self.speed = random.uniform(1.5, 2.2) * diff_mult['speed']
        base_hp = 30 + player.level * 5
        self.hp = base_hp * diff_mult['hp']

    def update(self):
        direction = self.player.pos - self.pos
        if direction.length() > 0: direction = direction.normalize()
        self.pos += direction * self.speed
        self.rect.center = self.pos

class Bullet(pygame.sprite.Sprite):
    def __init__(self, start, target, dmg, pene):
        super().__init__()
        self.pos = pygame.math.Vector2(start)
        direction = target - start
        if direction.length() > 0: self.vel = direction.normalize() * 18
        else: self.vel = pygame.math.Vector2(1, 0)
        self.damage = dmg
        self.penetrate = pene
        self.image = pygame.Surface((12, 12), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255, 255, 100), (6, 6), 6)
        self.rect = self.image.get_rect(center=self.pos)
        self.life = 80
    def update(self):
        self.pos += self.vel
        self.rect.center = self.pos
        self.life -= 1
        if self.life <= 0: self.kill()

class Item(pygame.sprite.Sprite):
    def __init__(self, pos, amount):
        super().__init__()
        self.image = assets.images['gem']
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.math.Vector2(pos)
        self.amount = amount
        self.float_y = 0
        self.float_dir = 1
    def update(self):
        self.float_y += 0.2 * self.float_dir
        if abs(self.float_y) > 3: self.float_dir *= -1
        self.rect.centery = self.pos.y + self.float_y
        self.rect.centerx = self.pos.x

class DamageText(pygame.sprite.Sprite):
    def __init__(self, pos, value):
        super().__init__()
        self.image = font_dmg.render(str(int(value)), True, YELLOW)
        self.rect = self.image.get_rect(center=pos)
        self.timer = 30
        self.vel_y = -1
    def update(self):
        self.rect.y += self.vel_y
        self.timer -= 1
        if self.timer <= 0: self.kill()

# --- 游戏控制器 ---
class Game:
    def __init__(self):
        self.state = "MENU"
        self.prev_state = "MENU"
        self.difficulty = "NORMAL"
        self.diff_mult = {'hp': 1.0, 'speed': 1.0, 'spawn': 1.0}
        
        cx = WIDTH // 2
        # 菜单按钮
        self.menu_btns = [
            Button(cx-100, 300, 200, 50, "简单模式", lambda: self.start_game("EASY"), (50, 150, 50)),
            Button(cx-100, 370, 200, 50, "普通模式", lambda: self.start_game("NORMAL"), (50, 50, 150)),
            Button(cx-100, 440, 200, 50, "困难模式", lambda: self.start_game("HARD"), (150, 50, 50)),
            Button(cx-100, 510, 200, 50, "系统设置", self.goto_settings, (80, 80, 80)),
            Button(cx-100, 580, 200, 50, "退出游戏", sys.exit, (50, 50, 50))
        ]
        
        # 暂停按钮
        self.pause_btns = [
            Button(cx-100, 280, 200, 50, "继续游戏", self.resume_game, (50, 150, 50)),
            Button(cx-100, 350, 200, 50, "系统设置", self.goto_settings, (80, 80, 80)),
            Button(cx-100, 420, 200, 50, "返回主菜单", self.back_to_menu, (150, 50, 50))
        ]
        
        # 设置组件
        self.settings_slider_music = Slider(cx-150, 280, 300, 20, assets.music_vol, assets.set_music_vol)
        self.settings_slider_sfx = Slider(cx-150, 380, 300, 20, assets.sfx_vol, assets.set_sfx_vol)
        self.settings_back_btn = Button(cx-100, 520, 200, 50, "保存并返回", self.exit_settings, (50, 150, 50))

        # 移动端控件
        self.joystick = VirtualJoystick(120, HEIGHT-120, 80)
        self.pause_icon_btn = Button(WIDTH-60, 20, 40, 40, "||", self.pause_game, (100,100,100))
        self.return_btn = Button(cx-100, HEIGHT//2 + 80, 200, 50, "返回主菜单", self.back_to_menu, (100,100,100))

    def start_game(self, diff):
        if diff == "EASY": self.diff_mult = {'hp': 0.7, 'speed': 0.8, 'spawn': 1.2}
        elif diff == "NORMAL": self.diff_mult = {'hp': 1.0, 'speed': 1.0, 'spawn': 1.0}
        elif diff == "HARD": self.diff_mult = {'hp': 1.5, 'speed': 1.2, 'spawn': 0.7}

        self.player = Player()
        self.all_sprites = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.items = pygame.sprite.Group()
        self.texts = pygame.sprite.Group()
        self.all_sprites.add(self.player)
        self.enemy_timer = 0
        self.spawn_rate = 60 * self.diff_mult['spawn']
        self.state = "RUNNING"
        pygame.mouse.set_visible(False)

    def goto_settings(self):
        self.prev_state = self.state 
        self.state = "SETTINGS"
        pygame.mouse.set_visible(True)

    def exit_settings(self):
        if self.prev_state == "MENU": self.state = "MENU"
        else: self.state = "PAUSE"

    def pause_game(self):
        self.state = "PAUSE"
        pygame.mouse.set_visible(True)

    def resume_game(self):
        self.state = "RUNNING"
        pygame.mouse.set_visible(False)

    def back_to_menu(self):
        self.state = "MENU"
        pygame.mouse.set_visible(True)

    def handle_shooting(self):
        mouse = pygame.mouse.get_pressed()
        mx, my = pygame.mouse.get_pos()
        is_firing = mouse[0]
        
        # 触屏防误触：点击摇杆区域不射击
        if math.hypot(mx - self.joystick.center.x, my - self.joystick.center.y) < self.joystick.radius + 50:
            is_firing = False

        if is_firing and self.player.weapon_cd <= 0:
            target = pygame.math.Vector2(mx + camera.offset.x, my + camera.offset.y)
            if 'shoot' in assets.sounds: assets.sounds['shoot'].play()
            
            for i in range(self.player.bullet_count):
                spread = pygame.math.Vector2(random.randint(-10,10), random.randint(-10,10))
                b = Bullet(self.player.pos, target + spread, self.player.damage, self.player.penetrate)
                self.bullets.add(b)
                self.all_sprites.add(b)
            self.player.weapon_cd = self.player.weapon_speed

    def apply_upgrade(self, opt):
        if 'levelup' in assets.sounds: assets.sounds['levelup'].play()
        if opt["type"] == "count": self.player.bullet_count += 1
        elif opt["type"] == "speed": self.player.weapon_speed = max(5, int(self.player.weapon_speed * 0.8))
        elif opt["type"] == "dmg": self.player.damage += 20
        elif opt["type"] == "pene": self.player.penetrate += 1
        elif opt["type"] == "heal": self.player.hp = min(self.player.max_hp, self.player.hp + self.player.max_hp*0.5)

    def draw_game_ui(self):
        sx = self.player.rect.centerx - camera.offset.x
        sy = self.player.rect.top - camera.offset.y - 30
        lvl_surf = font_ui.render(f"Lv.{self.player.level}", True, YELLOW)
        screen.blit(lvl_surf, lvl_surf.get_rect(center=(sx, sy)))

        bar_w, bar_h = 800, 12
        bar_x = (WIDTH - bar_w) // 2
        bar_y = HEIGHT - 30
        
        s = pygame.Surface((bar_w, bar_h))
        s.set_alpha(100)
        s.fill(BLACK)
        screen.blit(s, (bar_x, bar_y))
        
        exp_pct = min(1, self.player.xp / self.player.next_level_xp)
        if exp_pct > 0:
            pygame.draw.rect(screen, CYAN, (bar_x, bar_y, bar_w*exp_pct, bar_h), border_radius=6)
        pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bar_w, bar_h), 1, border_radius=6)
        
        exp_txt = font_ui.render(f"经验值 {self.player.xp}/{self.player.next_level_xp}", True, WHITE)
        screen.blit(exp_txt, (bar_x + 10, bar_y - 25))

        pygame.draw.rect(screen, (50,0,0), (20, 20, 250, 25), border_radius=5)
        hp_pct = max(0, self.player.hp / self.player.max_hp)
        pygame.draw.rect(screen, RED, (20, 20, 250 * hp_pct, 25), border_radius=5)
        pygame.draw.rect(screen, WHITE, (20, 20, 250, 25), 2, border_radius=5)
        hp_txt = font_ui.render(f"生命值: {int(self.player.hp)} / {int(self.player.max_hp)}", True, WHITE)
        screen.blit(hp_txt, (100, 22))

    def show_levelup_menu(self):
        pygame.mouse.set_visible(True)
        options = [
            {"name": "双发连射", "desc": "子弹数量 +1", "type": "count"},
            {"name": "超频冷却", "desc": "射速 +20%", "type": "speed"},
            {"name": "贫铀弹头", "desc": "伤害 +20", "type": "dmg"},
            {"name": "钨芯穿甲", "desc": "穿透 +1", "type": "pene"},
            {"name": "纳米修复", "desc": "回复 50% HP", "type": "heal"}
        ]
        choices = random.sample(options, 3)
        input_active = False 
        
        waiting = True
        while waiting:
            # 兼容异步循环的非阻塞等待（仅针对网页版生效，本地版无影响）
            # 注意：此处为同步阻塞循环，在网页端会在此处暂停渲染直到选择
            # 为了更好的体验，建议网页版避免这种 while 循环，但为了代码通用性保持现状
            
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(200)
            overlay.fill(DARK_BG)
            screen.blit(overlay, (0,0))

            title = font_big.render(">>> 基因进化 <<<", True, CYAN)
            screen.blit(title, (WIDTH//2 - title.get_width()//2, 80))
            
            mx, my = pygame.mouse.get_pos()
            rects = []
            
            for i, opt in enumerate(choices):
                x = WIDTH//2 - 250
                y = 180 + i * 140
                rect = pygame.Rect(x, y, 500, 120)
                rects.append(rect)
                
                is_hover = rect.collidepoint(mx, my)
                bg_color = (60, 60, 90) if is_hover else (40, 40, 60)
                border_color = CYAN if is_hover else (100, 100, 100)
                
                pygame.draw.rect(screen, bg_color, rect, border_radius=15)
                pygame.draw.rect(screen, border_color, rect, 3, border_radius=15)
                
                name_color = YELLOW if is_hover else (200, 200, 200)
                t1 = font_card.render(f"{i+1}. {opt['name']}", True, name_color)
                t2 = font_ui.render(opt["desc"], True, WHITE)
                screen.blit(t1, (x+30, y+25))
                screen.blit(t2, (x+30, y+70))

            if not input_active:
                hint = font_ui.render("请松开鼠标/手指...", True, RED)
            else:
                hint = font_ui.render("点击卡片 或 按 1/2/3 选择", True, GREEN)
            screen.blit(hint, (WIDTH//2 - hint.get_width()//2, HEIGHT - 100))

            pygame.display.flip()

            if not pygame.mouse.get_pressed()[0]: input_active = True

            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()
                if input_active:
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        for i, rect in enumerate(rects):
                            if rect.collidepoint(event.pos):
                                self.apply_upgrade(choices[i])
                                waiting = False
                                self.state = "RUNNING"
                                pygame.mouse.set_visible(False)
                    if event.type == pygame.KEYDOWN:
                        idx = -1
                        if event.key == pygame.K_1: idx = 0
                        elif event.key == pygame.K_2: idx = 1
                        elif event.key == pygame.K_3: idx = 2
                        if idx != -1:
                            self.apply_upgrade(choices[idx])
                            waiting = False
                            self.state = "RUNNING"
                            pygame.mouse.set_visible(False)

    # 异步主循环入口
    async def run(self):
        while True:
            # 1. 菜单
            if self.state == "MENU":
                screen.fill(DARK_BG)
                t = pygame.time.get_ticks() / 1000
                for i in range(10):
                    x = int(WIDTH/2 + math.sin(t + i)*400)
                    y = int(HEIGHT/2 + math.cos(t*0.5 + i)*200)
                    pygame.draw.circle(screen, (30, 30, 50), (x,y), 50)
                title = font_big.render("求生之路", True, CYAN)
                screen.blit(title, (WIDTH//2 - title.get_width()//2, 100))
                for btn in self.menu_btns: btn.draw(screen)
                mx, my = pygame.mouse.get_pos()
                pygame.draw.circle(screen, GREEN, (mx, my), 5)
                
                pygame.display.flip()
                for event in pygame.event.get():
                    if event.type == pygame.QUIT: sys.exit()
                    for btn in self.menu_btns: btn.check_click(event)

            # 2. 设置
            elif self.state == "SETTINGS":
                screen.fill(DARK_BG)
                t = font_big.render("系统设置", True, WHITE)
                screen.blit(t, (WIDTH//2 - t.get_width()//2, 100))
                
                vol_txt = font_btn.render("背景音乐", True, YELLOW)
                screen.blit(vol_txt, (WIDTH//2 - 250, 230))
                self.settings_slider_music.draw(screen)
                
                sfx_txt = font_btn.render("音效大小", True, YELLOW)
                screen.blit(sfx_txt, (WIDTH//2 - 250, 330))
                self.settings_slider_sfx.draw(screen)
                
                self.settings_back_btn.draw(screen)
                mx, my = pygame.mouse.get_pos()
                pygame.draw.circle(screen, GREEN, (mx, my), 5)
                
                pygame.display.flip()
                for event in pygame.event.get():
                    if event.type == pygame.QUIT: sys.exit()
                    self.settings_slider_music.handle_event(event)
                    self.settings_slider_sfx.handle_event(event)
                    self.settings_back_btn.check_click(event)

            # 3. 游戏运行
            elif self.state == "RUNNING":
                self.enemy_timer += 1
                if self.enemy_timer >= self.spawn_rate:
                    self.enemy_timer = 0
                    self.enemies.add(Enemy(self.player, self.diff_mult))
                    self.all_sprites.add(self.enemies.sprites()[-1])
                
                # 事件处理
                events = pygame.event.get()
                for e in events:
                    if e.type == pygame.QUIT: sys.exit()
                    if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE: self.state = "PAUSE"
                    
                    # 虚拟控件
                    self.joystick.update(e)
                    self.pause_icon_btn.check_click(e)

                self.player.update(self.joystick.output)
                self.enemies.update()
                self.bullets.update()
                self.items.update()
                self.texts.update()
                camera.center_target(self.player)
                self.handle_shooting()

                hits = pygame.sprite.groupcollide(self.enemies, self.bullets, False, False)
                for enemy, bullets in hits.items():
                    for bullet in bullets:
                        enemy.hp -= bullet.damage
                        self.texts.add(DamageText(enemy.rect.center, bullet.damage))
                        if bullet.penetrate <= 0: bullet.kill()
                        else: bullet.penetrate -= 1
                        if enemy.hp <= 0:
                            if 'kill' in assets.sounds: assets.sounds['kill'].play()
                            gem = Item(enemy.pos, 10)
                            self.items.add(gem)
                            self.all_sprites.add(gem)
                            enemy.kill()
                            break
                hits = pygame.sprite.spritecollide(self.player, self.enemies, False, pygame.sprite.collide_circle)
                if hits:
                    self.player.hp -= 0.8
                    if self.player.hp <= 0: self.state = "GAME_OVER"
                hits = pygame.sprite.spritecollide(self.player, self.items, True, pygame.sprite.collide_rect)
                for gem in hits:
                    self.player.xp += gem.amount
                    if self.player.check_levelup(): self.state = "LEVEL_UP"

                # 绘图
                bg_img = assets.images['bg']
                bg_w, bg_h = bg_img.get_size()
                start_x = int(camera.offset.x % bg_w)
                start_y = int(camera.offset.y % bg_h)
                cols = (WIDTH // bg_w) + 2
                rows = (HEIGHT // bg_h) + 2
                for r in range(-1, rows):
                    for c in range(-1, cols):
                        screen.blit(bg_img, (c*bg_w - start_x, r*bg_h - start_y))

                for s in self.all_sprites: screen.blit(s.image, s.rect.topleft - camera.offset)
                for b in self.bullets: screen.blit(b.image, b.rect.topleft - camera.offset)
                for t in self.texts: screen.blit(t.image, t.rect.topleft - camera.offset)
                
                # UI绘制
                mx, my = pygame.mouse.get_pos()
                pygame.draw.circle(screen, GREEN, (mx, my), 5, 1)
                pygame.draw.line(screen, GREEN, (mx-10, my), (mx+10, my))
                pygame.draw.line(screen, GREEN, (mx, my-10), (mx, my+10))
                
                self.joystick.draw(screen) # 摇杆
                self.pause_icon_btn.draw(screen) # 暂停钮
                self.draw_game_ui()
                
                pygame.display.flip()
                clock.tick(FPS)

            # 4. 暂停
            elif self.state == "PAUSE":
                s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                s.fill((0, 0, 0, 150))
                screen.blit(s, (0,0))
                t = font_big.render("已暂停", True, WHITE)
                screen.blit(t, (WIDTH//2 - t.get_width()//2, 100))
                for btn in self.pause_btns: btn.draw(screen)
                mx, my = pygame.mouse.get_pos()
                pygame.draw.circle(screen, GREEN, (mx, my), 5)
                pygame.display.flip()
                for event in pygame.event.get():
                    if event.type == pygame.QUIT: sys.exit()
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: self.resume_game()
                    for btn in self.pause_btns: btn.check_click(event)

            # 5. 升级
            elif self.state == "LEVEL_UP":
                self.show_levelup_menu()
                clock.tick() 

            # 6. 结束
            elif self.state == "GAME_OVER":
                pygame.mouse.set_visible(True)
                screen.fill(BLACK)
                t1 = font_big.render("游戏结束", True, RED)
                t2 = font_ui.render(f"最终等级: {self.player.level}", True, WHITE)
                
                self.return_btn.draw(screen)
                
                screen.blit(t1, (WIDTH//2 - t1.get_width()//2, HEIGHT//2 - 60))
                screen.blit(t2, (WIDTH//2 - t2.get_width()//2, HEIGHT//2 + 20))
                
                pygame.display.flip()
                for event in pygame.event.get():
                    if event.type == pygame.QUIT: sys.exit()
                    self.return_btn.check_click(event)

            # 关键：出让控制权给浏览器
            await asyncio.sleep(0)

if __name__ == "__main__":
    game = Game()
    asyncio.run(game.run())