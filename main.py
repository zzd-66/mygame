
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
DARK_BG = (15, 15, 30)

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

# --- 字体初始化 ---
try:
    if os.path.exists("font.ttf"):
        font_path = "font.ttf"
        font_ui = pygame.font.Font(font_path, 20)
        font_btn = pygame.font.Font(font_path, 28)
        font_big = pygame.font.Font(font_path, 60)
        font_card = pygame.font.Font(font_path, 26)
        font_dmg = pygame.font.Font(font_path, 24)
    else:
        font_ui = pygame.font.SysFont(['simhei', 'microsoftyahei'], 20, bold=True)
        font_btn = pygame.font.SysFont(['simhei', 'microsoftyahei'], 28, bold=True)
        font_big = pygame.font.SysFont(['simhei', 'microsoftyahei'], 60, bold=True)
        font_card = pygame.font.SysFont(['simhei', 'microsoftyahei'], 26, bold=True)
        font_dmg = pygame.font.SysFont(['arial', 'simhei'], 24, bold=True)
except:
    font_ui = pygame.font.Font(None, 24); font_btn = pygame.font.Font(None, 32)
    font_big = pygame.font.Font(None, 60); font_card = pygame.font.Font(None, 28); font_dmg = pygame.font.Font(None, 24)

# --- UI组件 ---
class Button:
    def __init__(self, x, y, w, h, text, callback, color=(60, 60, 80)):
        self.rect = pygame.Rect(x, y, w, h); self.text = text; self.callback = callback
        self.base_color = color; self.hover_color = (min(color[0]+40,255), min(color[1]+40,255), min(color[2]+40,255))
    def draw(self, surf):
        mx, my = pygame.mouse.get_pos()
        color = self.hover_color if self.rect.collidepoint(mx, my) else self.base_color
        pygame.draw.rect(surf, color, self.rect, border_radius=8)
        pygame.draw.rect(surf, WHITE, self.rect, 2, border_radius=8)
        txt_surf = font_btn.render(self.text, True, WHITE)
        txt_rect = txt_surf.get_rect(center=self.rect.center); surf.blit(txt_surf, txt_rect)
    def check_click(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos): self.callback(); return True
        return False

class Slider:
    def __init__(self, x, y, w, h, initial_val, callback):
        self.rect = pygame.Rect(x, y, w, h); self.val = initial_val; self.callback = callback; self.dragging = False
    def draw(self, surf):
        pygame.draw.rect(surf, (80, 80, 80), self.rect, border_radius=5)
        fill_rect = pygame.Rect(self.rect.x, self.rect.y, self.rect.width * self.val, self.rect.height)
        pygame.draw.rect(surf, CYAN, fill_rect, border_radius=5)
        pygame.draw.circle(surf, WHITE, (int(self.rect.x + self.rect.width * self.val), self.rect.centery), self.rect.height + 2)
        txt = font_ui.render(f"{int(self.val * 100)}%", True, WHITE); surf.blit(txt, (self.rect.right + 15, self.rect.y - 5))
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos): self.dragging = True; self.update_val(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP: self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging: self.update_val(event.pos[0])
    def update_val(self, mouse_x):
        self.val = max(0.0, min(1.0, (mouse_x - self.rect.x) / self.rect.width)); self.callback(self.val)

class VirtualJoystick:
    def __init__(self, x, y, radius):
        self.center = pygame.math.Vector2(x, y); self.radius = radius
        self.knob_pos = pygame.math.Vector2(x, y); self.knob_radius = radius // 2.5
        self.dragged = False; self.output = pygame.math.Vector2(0, 0)
    def update_knob(self, pos):
        vec = pygame.math.Vector2(pos) - self.center
        if vec.length() > self.radius: vec = vec.normalize() * self.radius
        self.knob_pos = self.center + vec; self.output = vec / self.radius
    def reset(self):
        self.knob_pos = pygame.math.Vector2(self.center); self.output = pygame.math.Vector2(0, 0)
    def draw(self, surf):
        s = pygame.Surface((self.radius*2, self.radius*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 255, 255, 50), (self.radius, self.radius), self.radius)
        pygame.draw.circle(s, (255, 255, 255, 100), (self.radius, self.radius), self.radius, 2)
        surf.blit(s, (self.center.x - self.radius, self.center.y - self.radius))
        pygame.draw.circle(surf, (0, 255, 255, 150), (int(self.knob_pos.x), int(self.knob_pos.y)), int(self.knob_radius))

# --- 资源管理 ---
class AssetManager:
    def __init__(self):
        self.images = {}; self.sounds = {}; self.music_vol = 0.5; self.sfx_vol = 0.5; self.MAX_VOL = 0.3; self.generate_defaults()
    def generate_defaults(self):
        bg = pygame.Surface((512, 512)); bg.fill((10, 10, 35))
        for _ in range(150): 
            x, y = random.randint(0, 511), random.randint(0, 511)
            size = random.randint(1, 2); alpha = random.randint(100, 255)
            s = pygame.Surface((size, size)); s.fill((220, 230, 255)); s.set_alpha(alpha); bg.blit(s, (x, y))
        self.images['bg'] = bg
        enemy = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.circle(enemy, (200, 50, 50), (20, 20), 18)
        pygame.draw.polygon(enemy, BLACK, [(10, 15), (20, 20), (10, 25)]) 
        pygame.draw.polygon(enemy, BLACK, [(30, 15), (20, 20), (30, 25)]); self.images['enemy'] = enemy
        gem = pygame.Surface((20, 20), pygame.SRCALPHA); pygame.draw.rect(gem, (0, 255, 255), (5, 5, 10, 10))
        pygame.draw.rect(gem, WHITE, (5, 5, 10, 10), 1); self.images['gem'] = gem
    def load(self):
        if os.path.exists("bg.png"): self.images['bg'] = pygame.image.load("bg.png").convert()
        if os.path.exists("bgm.mp3"):
            try: pygame.mixer.music.load("bgm.mp3"); self.set_music_vol(self.music_vol); pygame.mixer.music.play(-1)
            except: pass
        try:
            for n in ['shoot', 'kill', 'levelup']:
                p = f"{n}.wav"
                if os.path.exists(p): self.sounds[n] = pygame.mixer.Sound(p)
            self.set_sfx_vol(self.sfx_vol)
        except: pass
    def set_music_vol(self, val): self.music_vol = val; pygame.mixer.music.set_volume(val * self.MAX_VOL)
    def set_sfx_vol(self, val):
        self.sfx_vol = val
        for s in self.sounds.values(): s.set_volume(val * self.MAX_VOL)

assets = AssetManager(); assets.load()

# --- 游戏实体 ---
class Camera:
    def __init__(self): self.offset = pygame.math.Vector2(0, 0)
    def center_target(self, target):
        tx, ty = target.rect.centerx - WIDTH // 2, target.rect.centery - HEIGHT // 2
        self.offset.x += (tx - self.offset.x) * 0.1; self.offset.y += (ty - self.offset.y) * 0.1

camera = Camera()

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__(); self.pos = pygame.math.Vector2(0, 0); self.radius = 20 
        self.hp, self.max_hp = 100, 100; self.xp, self.level, self.next_level_xp = 0, 1, 50 
        self.speed = 3.5; self.weapon_speed, self.damage = 20, 30; self.bullet_count, self.penetrate = 1, 0; self.weapon_cd = 0; self.redraw_body()
    def redraw_body(self):
        size = int(self.radius * 2); self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (0, 200, 255), (self.radius, self.radius), self.radius)
        pygame.draw.circle(self.image, WHITE, (self.radius, self.radius), self.radius * 0.6)
        self.rect = self.image.get_rect(center=self.pos)
    def grow(self): self.radius += 2; self.max_hp += 20; self.hp = self.max_hp; self.redraw_body()
    def update(self, joy_vec):
        move = pygame.math.Vector2(0, 0); keys = pygame.key.get_pressed()
        if keys[pygame.K_w]: move.y = -1
        if keys[pygame.K_s]: move.y = 1
        if keys[pygame.K_a]: move.x = -1
        if keys[pygame.K_d]: move.x = 1
        if joy_vec.length() > 0: move = joy_vec
        if move.length() > 0:
            if move.length() > 1: move = move.normalize()
            self.pos += move * self.speed; self.rect.center = self.pos
        self.weapon_cd -= 1
    def check_levelup(self):
        if self.xp >= self.next_level_xp:
            self.xp -= self.next_level_xp; self.level += 1; self.next_level_xp = int(self.next_level_xp * 1.3)
            self.grow(); return True
        return False

class Enemy(pygame.sprite.Sprite):
    def __init__(self, player, diff_mult):
        super().__init__(); self.image = assets.images['enemy']; angle = random.uniform(0, 6.28)
        dist = random.uniform(800, 1200)
        self.pos = player.pos + pygame.math.Vector2(math.cos(angle)*dist, math.sin(angle)*dist)
        self.rect = self.image.get_rect(center=self.pos); self.player = player
        self.speed = random.uniform(1.5, 2.2) * diff_mult['speed']; self.hp = (30 + player.level * 5) * diff_mult['hp']
    def update(self):
        dir = (self.player.pos - self.pos).normalize() if (self.player.pos - self.pos).length() > 0 else pygame.math.Vector2(0,0)
        self.pos += dir * self.speed; self.rect.center = self.pos

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
      
        if self.life <= 0:
            self.kill()

class Item(pygame.sprite.Sprite):
    def __init__(self, pos, amount):
        super().__init__(); self.image = assets.images['gem']; self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.math.Vector2(pos); self.amount = amount; self.float_y, self.float_dir = 0, 1
    def update(self):
        self.float_y += 0.2 * self.float_dir; 
        if abs(self.float_y) > 3: self.float_dir *= -1
        self.rect.centery = self.pos.y + self.float_y; self.rect.centerx = self.pos.x

class DamageText(pygame.sprite.Sprite):
    def __init__(self, pos, value):
        super().__init__()
        self.image = font_dmg.render(str(int(value)), True, YELLOW)
        self.rect = self.image.get_rect(center=pos)
        self.timer, self.vel_y = 30, -1

    
    def update(self):
        self.rect.y += self.vel_y
        self.timer -= 1
       
        if self.timer <= 0:
            self.kill()

# --- 游戏控制器 ---
class Game:
    def __init__(self):
        self.state = "PLATFORM_SELECT" 
        self.control_mode = "PC"
        self.prev_state = "MENU"; self.difficulty = "NORMAL"; self.diff_mult = {'hp': 1.0, 'speed': 1.0, 'spawn': 1.0}
        self.levelup_choices = []; self.levelup_input_active = False
        self.last_aim_pos = pygame.math.Vector2(WIDTH - 100, HEIGHT // 2)
        self.joy_finger_id = None; self.aim_finger_id = None

        cx = WIDTH // 2
        self.platform_btns = [
            Button(cx-220, 350, 200, 60, "电脑模式", lambda: self.set_mode("PC"), (100, 100, 150)),
            Button(cx+20, 350, 200, 60, "手机模式", lambda: self.set_mode("MOBILE"), (100, 150, 100))
        ]
        self.menu_btns = [
            Button(cx-100, 300, 200, 50, "简单模式", lambda: self.start_game("EASY"), (50, 150, 50)),
            Button(cx-100, 370, 200, 50, "普通模式", lambda: self.start_game("NORMAL"), (50, 50, 150)),
            Button(cx-100, 440, 200, 50, "困难模式", lambda: self.start_game("HARD"), (150, 50, 50)),
            Button(cx-100, 510, 200, 50, "系统设置", self.goto_settings, (80, 80, 80)),
            Button(cx-100, 580, 200, 50, "退出游戏", sys.exit, (50, 50, 50))
        ]
        self.pause_btns = [
            Button(cx-100, 280, 200, 50, "继续游戏", self.resume_game, (50, 150, 50)),
            Button(cx-100, 350, 200, 50, "系统设置", self.goto_settings, (80, 80, 80)),
            Button(cx-100, 420, 200, 50, "返回主菜单", self.back_to_menu, (150, 50, 50))
        ]
        self.settings_slider_music = Slider(cx-150, 280, 300, 20, assets.music_vol, assets.set_music_vol)
        self.settings_slider_sfx = Slider(cx-150, 380, 300, 20, assets.sfx_vol, assets.set_sfx_vol)
        self.settings_back_btn = Button(cx-100, 520, 200, 50, "保存并返回", self.exit_settings, (50, 150, 50))
        self.joystick = VirtualJoystick(120, HEIGHT-120, 80)
        self.pause_icon_btn = Button(WIDTH-60, 20, 40, 40, "||", self.pause_game, (100,100,100))
        self.return_btn = Button(cx-100, HEIGHT//2 + 80, 200, 50, "返回主菜单", self.back_to_menu, (100,100,100))

    def set_mode(self, m): self.control_mode = m; self.state = "MENU"
    def start_game(self, diff):
        if diff == "EASY": self.diff_mult = {'hp': 0.7, 'speed': 0.8, 'spawn': 1.2}
        elif diff == "NORMAL": self.diff_mult = {'hp': 1.0, 'speed': 1.0, 'spawn': 1.0}
        else: self.diff_mult = {'hp': 1.5, 'speed': 1.2, 'spawn': 0.7}
        self.player = Player(); self.all_sprites = pygame.sprite.Group(self.player)
        self.enemies, self.bullets, self.items, self.texts = pygame.sprite.Group(), pygame.sprite.Group(), pygame.sprite.Group(), pygame.sprite.Group()
        self.spawn_rate = 60 * self.diff_mult['spawn']; self.state = "RUNNING"; pygame.mouse.set_visible(False)
    
    def goto_settings(self): self.prev_state = self.state; self.state = "SETTINGS"; pygame.mouse.set_visible(True)
    def exit_settings(self): self.state = self.prev_state if self.prev_state == "MENU" else "PAUSE"
    def pause_game(self): self.state = "PAUSE"; pygame.mouse.set_visible(True)
    def resume_game(self): self.state = "RUNNING"; pygame.mouse.set_visible(False)
    def back_to_menu(self): self.state = "MENU"; pygame.mouse.set_visible(True)

    def apply_upgrade(self, opt):
        if 'levelup' in assets.sounds: assets.sounds['levelup'].play()
        if opt["type"] == "count": self.player.bullet_count += 1
        elif opt["type"] == "speed": self.player.weapon_speed = max(5, int(self.player.weapon_speed * 0.8))
        elif opt["type"] == "dmg": self.player.damage += 20
        elif opt["type"] == "pene": self.player.penetrate += 1
        elif opt["type"] == "heal": self.player.hp = min(self.player.max_hp, self.player.hp + self.player.max_hp*0.5)

    def handle_shooting(self):
        if self.control_mode == "PC": self.last_aim_pos = pygame.math.Vector2(pygame.mouse.get_pos())
        is_firing = (self.control_mode == "MOBILE" and self.aim_finger_id is not None) or (self.control_mode == "PC" and pygame.mouse.get_pressed()[0])
        if is_firing and self.player.weapon_cd <= 0:
            target = self.last_aim_pos + camera.offset
            if 'shoot' in assets.sounds: assets.sounds['shoot'].play()
            for _ in range(self.player.bullet_count):
                off = pygame.math.Vector2(random.randint(-10,10), random.randint(-10,10))
                b = Bullet(self.player.pos, target + off, self.player.damage, self.player.penetrate)
                self.bullets.add(b); self.all_sprites.add(b)
            self.player.weapon_cd = self.player.weapon_speed

    def draw_game_ui(self):
        # 计算玩家在屏幕上的绝对坐标
        sx = self.player.rect.centerx - camera.offset.x
        sy = self.player.rect.top - camera.offset.y - 30 # 在头顶上方30像素
        # 渲染文字
        lvl_surf = font_ui.render(f"Lv.{self.player.level}", True, YELLOW)
        lvl_rect = lvl_surf.get_rect(center=(sx, sy))
        screen.blit(lvl_surf, lvl_rect)
        # 补全血条文字
        pygame.draw.rect(screen, (50,0,0), (20, 20, 250, 25), border_radius=5)
        pygame.draw.rect(screen, RED, (20, 20, 250 * (self.player.hp/self.player.max_hp), 25), border_radius=5)
        pygame.draw.rect(screen, WHITE, (20, 20, 250, 25), 2, border_radius=5)
        hp_txt = font_ui.render(f"生命值: {int(self.player.hp)} / {int(self.player.max_hp)}", True, WHITE)
        screen.blit(hp_txt, (35, 23))
        # 补全经验条文字 + 方框
        bar_x, bar_y, bar_w, bar_h = (WIDTH-800)//2, HEIGHT-30, 800, 12
        pygame.draw.rect(screen, (0,0,0,100), (bar_x, bar_y, bar_w, bar_h), border_radius=6)
        pygame.draw.rect(screen, CYAN, (bar_x, bar_y, bar_w*(self.player.xp/self.player.next_level_xp), bar_h), border_radius=6)
        pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bar_w, bar_h), 1, border_radius=6)
        xp_txt = font_ui.render(f"经验值 {self.player.xp} / {self.player.next_level_xp}", True, WHITE)
        screen.blit(xp_txt, (bar_x, bar_y - 25))

    def init_levelup(self):
        pygame.mouse.set_visible(True); self.levelup_input_active = False 
        options = [{"name": "双发连射", "desc": "数量+1", "type": "count"},{"name": "超频冷却", "desc": "射速+20%", "type": "speed"},{"name": "贫铀弹头", "desc": "伤害+20", "type": "dmg"},{"name": "钨芯穿甲", "desc": "穿透+1", "type": "pene"},{"name": "纳米修复", "desc": "回复50% HP", "type": "heal"}]
        self.levelup_choices = random.sample(options, 3)

    async def run(self):
        while True:
            if self.state == "PLATFORM_SELECT":
                screen.fill(DARK_BG); title = font_big.render("请选择操作平台", True, CYAN)
                screen.blit(title, (WIDTH//2 - title.get_width()//2, 150))
                for b in self.platform_btns: b.draw(screen)
                pygame.display.flip()
                for e in pygame.event.get():
                    if e.type == pygame.QUIT: sys.exit()
                    for b in self.platform_btns: b.check_click(e)

            elif self.state == "MENU":
                screen.fill(DARK_BG); t = pygame.time.get_ticks() / 1000
                for i in range(10):
                    x, y = int(WIDTH/2 + math.sin(t+i)*400), int(HEIGHT/2 + math.cos(t*0.5+i)*200)
                    pygame.draw.circle(screen, (30, 30, 50), (x,y), 50)
                title = font_big.render("求生之路", True, CYAN); screen.blit(title, (WIDTH//2 - title.get_width()//2, 100))
                for btn in self.menu_btns: btn.draw(screen)
                pygame.display.flip()
                for e in pygame.event.get(): 
                    if e.type == pygame.QUIT: sys.exit()
                    for btn in self.menu_btns: btn.check_click(e)

            elif self.state == "SETTINGS":
                screen.fill(DARK_BG); t = font_big.render("系统设置", True, WHITE); screen.blit(t, (WIDTH//2 - t.get_width()//2, 100))
                screen.blit(font_btn.render("背景音乐", True, YELLOW), (WIDTH//2-250, 230)); self.settings_slider_music.draw(screen)
                screen.blit(font_btn.render("音效大小", True, YELLOW), (WIDTH//2-250, 330)); self.settings_slider_sfx.draw(screen); self.settings_back_btn.draw(screen)
                pygame.display.flip()
                for e in pygame.event.get():
                    if e.type == pygame.QUIT: sys.exit()
                    self.settings_slider_music.handle_event(e); self.settings_slider_sfx.handle_event(e); self.settings_back_btn.check_click(e)

            elif self.state == "RUNNING":
                events = pygame.event.get()
                for e in events:
                    if e.type == pygame.QUIT: sys.exit()
                    if self.control_mode == "MOBILE":
                        if e.type == pygame.FINGERDOWN:
                            fx, fy = e.x * WIDTH, e.y * HEIGHT
                            if fx < WIDTH // 3: self.joy_finger_id = e.finger_id; self.joystick.update_knob((fx, fy))
                            else: self.aim_finger_id = e.finger_id; self.last_aim_pos = pygame.math.Vector2(fx, fy)
                        elif e.type == pygame.FINGERMOTION:
                            fx, fy = e.x * WIDTH, e.y * HEIGHT
                            if e.finger_id == self.joy_finger_id: self.joystick.update_knob((fx, fy))
                            elif e.finger_id == self.aim_finger_id: self.last_aim_pos = pygame.math.Vector2(fx, fy)
                        elif e.type == pygame.FINGERUP:
                            if e.finger_id == self.joy_finger_id: self.joy_finger_id = None; self.joystick.reset()
                            if e.finger_id == self.aim_finger_id: self.aim_finger_id = None
                    if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE: self.state = "PAUSE"
                    self.pause_icon_btn.check_click(e)

                # 逻辑与渲染
                if pygame.time.get_ticks() % 100 == 0: 
                    e = Enemy(self.player, self.diff_mult); self.enemies.add(e); self.all_sprites.add(e)
                self.player.update(self.joystick.output); self.enemies.update(); self.bullets.update(); self.items.update(); self.texts.update()
                camera.center_target(self.player); self.handle_shooting()
                hits = pygame.sprite.groupcollide(self.enemies, self.bullets, False, False)
                for en, bulls in hits.items():
                    for bu in bulls:
                        en.hp -= bu.damage; self.texts.add(DamageText(en.rect.center, bu.damage))
                        if bu.penetrate <= 0: bu.kill()
                        else: bu.penetrate -= 1
                        if en.hp <= 0:
                            if 'kill' in assets.sounds: assets.sounds['kill'].play()
                            it = Item(en.pos, 10); self.items.add(it); self.all_sprites.add(it); en.kill(); break
                if pygame.sprite.spritecollide(self.player, self.enemies, False, pygame.sprite.collide_circle):
                    self.player.hp -= 0.8
                    if self.player.hp <= 0: self.state = "GAME_OVER"
                for gem in pygame.sprite.spritecollide(self.player, self.items, True):
                    self.player.xp += gem.amount
                    if self.player.check_levelup(): self.init_levelup(); self.state = "LEVEL_UP"

                screen.fill(DARK_BG); bg = assets.images['bg']; tw, th = bg.get_size()
                start_x, start_y = int(camera.offset.x % tw), int(camera.offset.y % th)
                for r in range(-1, (HEIGHT // th) + 2):
                    for c in range(-1, (WIDTH // tw) + 2): screen.blit(bg, (c*tw - start_x, r*th - start_y))
                for s in self.all_sprites: screen.blit(s.image, s.rect.topleft - camera.offset)
                for b in self.bullets: screen.blit(b.image, b.rect.topleft - camera.offset)
                for t in self.texts: screen.blit(t.image, t.rect.topleft - camera.offset)
                # 准星
                pygame.draw.circle(screen, GREEN, (int(self.last_aim_pos.x), int(self.last_aim_pos.y)), 6, 1)
                pygame.draw.line(screen, GREEN, (self.last_aim_pos.x-10, self.last_aim_pos.y), (self.last_aim_pos.x+10, self.last_aim_pos.y))
                pygame.draw.line(screen, GREEN, (self.last_aim_pos.x, self.last_aim_pos.y-10), (self.last_aim_pos.x, self.last_aim_pos.y+10))
                if self.control_mode == "MOBILE": self.joystick.draw(screen)
                self.pause_icon_btn.draw(screen); self.draw_game_ui()
                pygame.display.flip(); clock.tick(FPS)

            elif self.state == "LEVEL_UP":
                overlay = pygame.Surface((WIDTH, HEIGHT))
                overlay.set_alpha(200)
                overlay.fill(DARK_BG)
                screen.blit(overlay, (0,0))
                title = font_big.render(">>> 基因进化 <<<", True, CYAN)
                screen.blit(title, (WIDTH//2 - title.get_width()//2, 80))
                
              
                mx, my = pygame.mouse.get_pos()
                rects = []
                for i, opt in enumerate(self.levelup_choices):
                    x, y = WIDTH//2 - 250, 180 + i * 140
                    rect = pygame.Rect(x, y, 500, 120)
                    rects.append(rect)
                    
                    # 判断鼠标是否悬停
                    is_hover = rect.collidepoint(mx, my)
                    # 根据是否悬停选择颜色（高光效果）
                    card_bg = (60, 60, 90) if is_hover else (40, 40, 60)
                    border_col = CYAN if is_hover else WHITE
                    name_col = YELLOW if is_hover else (200, 200, 200)
                    
                    # 绘制卡片背景和边框
                    pygame.draw.rect(screen, card_bg, rect, border_radius=15)
                    pygame.draw.rect(screen, border_col, rect, 2, border_radius=15)
                    
                    # 绘制文字
                    t1 = font_card.render(f"{i+1}. {opt['name']}", True, name_col)
                    t2 = font_ui.render(opt["desc"], True, WHITE)
                    screen.blit(t1, (x+30, y+25))
                    screen.blit(t2, (x+30, y+70))

                if not self.levelup_input_active:
                    hint = font_ui.render("请松开鼠标/手指...", True, RED)
                    if not pygame.mouse.get_pressed()[0]: 
                        self.levelup_input_active = True
                else:
                    hint = font_ui.render("点击卡片 或 按 1/2/3 选择", True, GREEN)
                screen.blit(hint, (WIDTH//2 - hint.get_width()//2, HEIGHT - 100))
                
                pygame.display.flip()

                for event in pygame.event.get():
                    if event.type == pygame.QUIT: sys.exit()
                    if self.levelup_input_active:
                        idx = -1
                        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                            for i, rect in enumerate(rects):
                                if rect.collidepoint(event.pos):
                                    idx = i
                        elif event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_1: idx = 0
                            elif event.key == pygame.K_2: idx = 1
                            elif event.key == pygame.K_3: idx = 2
                        
                        if idx != -1:
                            self.apply_upgrade(self.levelup_choices[idx])
                            self.state = "RUNNING"
                            pygame.mouse.set_visible(False)

            elif self.state == "PAUSE":
                # 隔离绘制，防止设置菜单重叠
                s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA); s.fill((0, 0, 0, 150)); screen.blit(s, (0,0))
                t = font_big.render("已暂停", True, WHITE); screen.blit(t, (WIDTH//2 - t.get_width()//2, 100))
                for btn in self.pause_btns: btn.draw(screen)
                pygame.display.flip()
                for e in pygame.event.get():
                    if e.type == pygame.QUIT: sys.exit()
                    for btn in self.pause_btns: btn.check_click(e)

            elif self.state == "GAME_OVER":
                pygame.mouse.set_visible(True); screen.fill(BLACK)
                t1 = font_big.render("游戏结束", True, RED); t2 = font_ui.render(f"最终等级: {self.player.level}", True, WHITE)
                screen.blit(t1, (WIDTH//2 - 100, HEIGHT//2 - 60)); screen.blit(t2, (WIDTH//2 - 100, HEIGHT//2 + 20))
                self.return_btn.draw(screen); pygame.display.flip()
                for event in pygame.event.get():
                    if event.type == pygame.QUIT: sys.exit()
                    self.return_btn.check_click(event)

            await asyncio.sleep(0)

if __name__ == "__main__":
    game = Game()
    asyncio.run(game.run())