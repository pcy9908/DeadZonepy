import pygame
import sys
import random
import math
import time
from file_loader import load_images, optimize_images, load_audio
from cutscene import CutsceneManager

# 게임 초기 설정
pygame.init()
# pygame.mixer 초기화
pygame.mixer.init()

# 화면 크기와 기본 설정
WIDTH, HEIGHT = 1600, 900
screen = pygame.display.set_mode((1600, 900))
pygame.display.set_caption("DEAD ZONE")
clock = pygame.time.Clock()

# 리소스 로드
image = load_images()
audio = load_audio()
# 디스플레이 초기화 후 최적화
optimize_images(image)

# 색상 정의
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GRAY = (160, 160, 160)
DARK_GRAY = (96, 96, 96)
LIGHT_RED = (255, 160, 122)
LIGHT_BLUE = (173, 216, 230)
LIGHT_GREEN = (144,238,144)
BLACK = (0, 0, 0)

# 게임 변수 초기화
block_size = 100
grid_rows, grid_cols = HEIGHT // block_size, WIDTH // block_size
current_screen = "start"  # 시작 화면에서 시작
tile_map = [[random.choice(image["tile_image1"]) for _ in range(16)] for _ in range(9)]
e_tile_dict = {1: "e_block1", 11: "e_block2", 21: "e_block3", 31: "e_block4"}
e_tile = e_tile_dict[1]
# 전역 변수 초기화
dragging = False  # 드래그 상태 초기화
selected_tower_image = None  # 선택된 타워 이미지 초기화
selected_tower_ui = None  # 선택된 타워 UI 초기화


# 적 경로 설정 (기본 루트)
path_coords = [
    (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6),
    (2, 6), (3, 6), (4, 6), (5, 6),
    (5, 5), (5, 4), (5, 3), (5, 2), (5, 1),
    (6, 1), (7, 1), (8, 1),
    (8, 2), (8, 3), (8, 4), (8, 5), (8, 6),
    (9, 6), (10, 6), (11, 6), (12, 6),
    (12, 5), (12, 4), (12, 3)
]

# 이벤트 정의
ENEMY_SPAWN_EVENT = pygame.USEREVENT + 1
pygame.time.set_timer(ENEMY_SPAWN_EVENT, 10000)

# BGM 파일 경로

# 글로벌 변수 초기화
enemies = []  # 적 리스트
towers = []  # 타워 리스트
gold = 100  # 초기 자원
life = 10  # 초기 생명
wave = 0  # 초기 웨이브
enemies_spawned = 0  # 현재 웨이브에서 생성된 적 수
max_enemies_per_wave = 20 # 웨이브당 적 최대 수
enemy_spawn_interval = 500  # 적 스폰 간격 (밀리초, 더 빠르게)
last_spawn_time = 0  # 마지막 적 생성 시간
wave_pause = False  # 웨이브 대기 상태
wave_pause_timer = 0  # 웨이브 대기 시간
wave_pause_duration = 1000  # 10초 대기 (밀리초)
current_screen = "start"  # 시작 화면에서 시작

# HUD에 사용될 폰트 설정
Nanum = "fonts/NanumGothicBold.ttf"
font = pygame.font.Font(None, 36)
font12 = pygame.font.Font(Nanum, 12)  # None은 기본 폰트, 36은 폰트 크기
font20 = pygame.font.Font(Nanum, 20)
font20b = pygame.font.Font(Nanum, 20)
font20b.set_bold(True)
font22 = pygame.font.Font(Nanum, 22)
font24 = pygame.font.Font(Nanum, 24)
font36 = pygame.font.Font(Nanum, 36)

# 컷씬 매니저 초기화
cutscene_manager = CutsceneManager(screen, None, WIDTH, HEIGHT)
cutscene_manager.set_font(Nanum, size=36)

# 컷씬 데이터 로드
cutscene_file_path = "cutscene_data.json"
wave_cutscene_waves = [11, 21, 31, 41]
wave_cutscene_active = False  # 컷씬 상태 플래그

# 타워 UI 변수
tower_ui_width = 200  # 타워 UI의 가로 길이
tower_ui_rect = pygame.Rect(1350, 250, tower_ui_width + 80, HEIGHT - 400)  # UI 위치와 크기

TOWER_TYPES = [
    {"name": "Gun Tower", "cost": 50, "color": LIGHT_BLUE, "type": "gun", "image_path": "gun_tower.png"},
    {"name": "Mine Tower", "cost": 50, "color": LIGHT_RED, "type": "mine", "image_path": "mine_tower.png"},
    {"name": "Supply Tower", "cost": 30, "color": LIGHT_GREEN, "type": "supply", "image_path": "supply_tower.png"}
]

selected_tower = None  # 현재 선택된 타워
class Enemy:
    def __init__(self, path_coords, speed=3, health=20, image_path="enemy.png"):
        self.path_coords = path_coords
        self.index = 0
        self.x, self.y = path_coords[self.index]
        self.x *= block_size
        self.y *= block_size
        self.speed = speed
        self.original_speed = speed  # 원래 속도 저장
        self.health = health
        self.max_health = health  # 최대 체력을 별도로 저장
        self.alive = True
        self.slow_duration = 0  # 둔화 지속 시간
        # 적 이미지 로드 및 크기 조정
        self.image = pygame.image.load(image_path)
        self.image = pygame.transform.scale(self.image, (block_size, block_size))  # 블록 크기에 맞게 조정

        # 효과음 로드 및 음량 설정
        self.spawn_sound = audio["spawn"]
        self.spawn_sound.set_volume(0)  # 스폰 소리 음량 조절
        self.death_sound = audio["death"]
        self.death_sound.set_volume(0.2)  # 죽는 소리 음량 조절

        # 적 생성 시 효과음 재생
        self.spawn_sound.play()

    def move(self):
        if self.index < len(self.path_coords) - 1:
            target_x, target_y = self.path_coords[self.index + 1]
            target_x *= block_size
            target_y *= block_size

            dx, dy = target_x - self.x, target_y - self.y
            dist = (dx ** 2 + dy ** 2) ** 0.5

            if dist < self.speed:
                self.x, self.y = target_x, target_y
                self.index += 1
            else:
                self.x += self.speed * dx / dist
                self.y += self.speed * dy / dist
        else:
            self.alive = False
            self.spawn_sound.stop()  # 스폰 소리 중단
            self.death_sound.play()  # 적이 목표에 도달할 때 효과음 재생

    def take_damage(self, damage):
        """적이 피해를 입을 때 처리"""
        self.health -= damage
        if self.health <= 0 and self.alive:
            self.alive = False
            self.spawn_sound.stop()  # 스폰 소리 중단
            self.death_sound.play()  # 적이 죽을 때 효과음 재생

    def draw(self):
        """적의 이미지를 화면에 그리기"""
        screen.blit(self.image, (self.x, self.y))

        # 체력 바 그리기
        health_bar_width = block_size
        health_ratio = self.health / self.max_health  # 최대 체력을 기준으로 비율 계산
        pygame.draw.rect(screen, DARK_GRAY, (self.x, self.y - 10, health_bar_width, 5))  # 배경 바
        pygame.draw.rect(screen, LIGHT_RED, (self.x, self.y - 10, health_bar_width * health_ratio, 5))  # 현재 체력 바
        
    def apply_slow(self, slow_effect, duration=120):
        """둔화 효과 적용"""
        self.speed = self.original_speed * (1 - slow_effect)  # 속도 감소
        self.slow_duration = duration  # 둔화 지속 시간 설정
class BossEnemy(Enemy):
    """보스 좀비 클래스"""
    def __init__(self, path_coords, boss_type, health_increment=0):
        """
        :param path_coords: 적의 경로
        :param boss_type: 보스 타입 (1~4)
        :param health_increment: 웨이브에 따른 체력 증가량
        """
        base_health = [800, 1200, 1600, 2000][boss_type - 1]  # 보스 기본 체력
        health = base_health + health_increment  # 기본 체력 + 추가 체력
        speed = [2.0, 1.8, 1.6, 1.5][boss_type - 1]
        super().__init__(path_coords, speed, health)
        self.type = boss_type
        self.image = image[f"boss{boss_type}"]
        self.image = pygame.transform.scale(self.image, (block_size * 1.5, block_size * 1.5))
        self.cooldowns = {
            "heal_nearby": 0,  # 1단계 능력 쿨타임
            "stun_towers": 0,  # 2단계 능력 쿨타임
            "heal_area": 0     # 3단계 능력 쿨타임
        }

    def update(self, enemies, towers):
        """보스 특수 능력 실행"""
        for key in self.cooldowns:
            if self.cooldowns[key] > 0:
                self.cooldowns[key] -= 1

        if self.type >= 1 and self.cooldowns["heal_nearby"] == 0:
            self._heal_nearby_enemies(enemies, 20)  # 체력 20% 회복
            self.cooldowns["heal_nearby"] = 600  # 10초 쿨타임

        if self.type >= 2 and self.cooldowns["stun_towers"] == 0:
            self._stun_towers(towers, 2, 120)  # 타워 2개를 2초 스턴
            self.cooldowns["stun_towers"] = 720  # 12초 쿨타임

        if self.type >= 3 and self.cooldowns["heal_area"] == 0:
            self._heal_area_enemies(enemies, 30, 2)  # 2칸 범위 내 체력 30% 회복
            self.cooldowns["heal_area"] = 600  # 10초 쿨타임

    def _heal_nearby_enemies(self, enemies, percentage):
        """주변 적 체력 회복"""
        for enemy in enemies:
            dist = math.sqrt((self.x - enemy.x) ** 2 + (self.y - enemy.y) ** 2)
            if dist <= block_size * 3:  # 3칸 내
                heal_amount = enemy.max_health * (percentage / 100)
                enemy.health = min(enemy.max_health, enemy.health + heal_amount)
                print(f"보스({self.type})가 {enemy} 체력을 {heal_amount:.0f} 회복시켰습니다.")

    def _stun_towers(self, towers, count, duration):
        """타워 스턴"""
        for tower in random.sample(towers, min(len(towers), count)):
            tower.cooldown += duration
            print(f"보스({self.type})가 타워 {tower}를 {duration // 60}초간 스턴시켰습니다.")

    def _heal_area_enemies(self, enemies, percentage, range_blocks):
        """범위 내 적 체력 회복"""
        for enemy in enemies:
            dist = math.sqrt((self.x - enemy.x) ** 2 + (self.y - enemy.y) ** 2)
            if dist <= block_size * range_blocks:  # 범위 내
                heal_amount = enemy.max_health * (percentage / 100)
                enemy.health = min(enemy.max_health, enemy.health + heal_amount)
                print(f"보스({self.type})가 범위 내 {enemy} 체력을 {heal_amount:.0f} 회복시켰습니다.")

class SpecialEnemy(Enemy):
    """특수 좀비 클래스"""
    def __init__(self, path_coords, special_type,health_increment=0):
        S_health = [400, 600, 800, 1000][special_type - 1]
        health=S_health+health_increment
        speed = [3.0, 2.8, 2.6, 2.5][special_type - 1]
        super().__init__(path_coords, speed, health)
        self.type = special_type
        self.image = image[f"s_enemy{special_type}"]
        self.image = pygame.transform.scale(self.image, (block_size, block_size))
        self.cooldowns = {
            "boost_speed": 0,  # 1번 능력 쿨타임
            "stun_towers": 0,  # 2번 능력 쿨타임
            "heal_area": 0     # 3번 능력 쿨타임
        }

    def update(self, enemies, towers):
        """특수 좀비 능력 실행"""
        for key in self.cooldowns:
            if self.cooldowns[key] > 0:
                self.cooldowns[key] -= 1

        if self.type >= 1 and self.cooldowns["boost_speed"] == 0:
            self._boost_nearby_speed(enemies, 0.5)  # 이동 속도 30% 증가
            self.cooldowns["boost_speed"] = 300  # 5초 쿨타임

        if self.type >= 2 and self.cooldowns["stun_towers"] == 0:
            self._stun_nearby_towers(towers, 2, 60)  # 타워 2개를 1초 스턴
            self.cooldowns["stun_towers"] = 480  # 8초 쿨타임

        if self.type >= 3 and self.cooldowns["heal_area"] == 0:
            self._heal_area_enemies(enemies, 20, 2)  # 2칸 범위 내 체력 20% 회복
            self.cooldowns["heal_area"] = 420  # 7초 쿨타임

    def _boost_nearby_speed(self, enemies, boost_amount):
        """주변 적 이동 속도 증가"""
        for enemy in enemies:
            dist = math.sqrt((self.x - enemy.x) ** 2 + (self.y - enemy.y) ** 2)
            if dist <= block_size:  # 1칸 내
                enemy.speed += boost_amount
                print(f"특수 좀비({self.type})가 {enemy}의 속도를 {boost_amount * 100:.0f}% 증가시켰습니다.")

    def _stun_nearby_towers(self, towers, count, duration):
        """주변 타워 스턴"""
        for tower in random.sample(towers, min(len(towers), count)):
            tower.cooldown += duration
            print(f"특수 좀비({self.type})가 타워 {tower}를 {duration // 60}초간 스턴시켰습니다.")

    def _heal_area_enemies(self, enemies, percentage, range_blocks):
        """범위 내 적 체력 회복"""
        for enemy in enemies:
            dist = math.sqrt((self.x - enemy.x) ** 2 + (self.y - enemy.y) ** 2)
            if dist <= block_size * range_blocks:
                heal_amount = enemy.max_health * (percentage / 100)
                enemy.health = min(enemy.max_health, enemy.health + heal_amount)
                print(f"특수 좀비({self.type})가 범위 내 {enemy} 체력을 {heal_amount:.0f} 회복시켰습니다.")
 
class Tower:
    def __init__(self, x, y, tower_type):
        if tower_type == "gun":
            self.range = 3 * block_size
            self.damage = 50
            self.reload_time = 40
            self.double_attack = False  # 더블 어택 기본값
            self.image_key = "gun_tower"
            self.shot_sound = audio["gun_sound"]
            self.shot_sound.set_volume(0.02)

        elif tower_type == "mine":
            self.range = 3 * block_size  # 타워 사거리
            self.damage = 70
            self.reload_time = 60  # 공속 조정
            self.explosion_range = block_size  # 폭발 범위 (1블럭)
            self.image_key = "mine_tower"
            self.shot_sound = audio["mine_sound"]
            self.shot_sound.set_volume(0.02)

        elif tower_type == "supply":
            self.range = 2 * block_size
            self.buff_amount = 40
            self.image_key = "supply_tower"
            self.effect_duration = 300  # 버프 지속 시간
            self.reload_time = 0  # 공격하지 않음

        self.x, self.y = x, y
        self.cooldown = 0
        self.level = 1  # 초기 레벨
        self.type = tower_type
        self.angle = 0  # 기본 각도 (아래쪽을 바라봄)

    def draw(self):
        """타워를 화면에 그리기 (회전 포함)"""
        tower_image = image[self.image_key]
        tower_image = pygame.transform.scale(tower_image, (block_size, block_size))
        rotated_image = pygame.transform.rotate(tower_image, self.angle)
        rotated_rect = rotated_image.get_rect(center=(self.x + block_size // 2, self.y + block_size // 2))
        screen.blit(rotated_image, rotated_rect.topleft)

    def attack(self, enemies):
        """타워 공격 로직"""
        if self.cooldown == 0:
            if self.type == "gun":
                target_enemy = max(
                    (enemy for enemy in enemies if self._is_in_range(enemy)),
                    key=lambda e: (e.max_health, e.index),  # 최대 체력 우선, 동일하면 선두 우선
                    default=None
                )
                if target_enemy:
                    # 적과의 각도 계산 및 회전
                    self.angle = self._calculate_angle_to_target(target_enemy)

                    # 첫 번째 공격
                    target_enemy.take_damage(self.damage)
                    self.shot_sound.play()

                    # 더블 어택 로직
                    if self.double_attack:
                        def second_attack():
                            second_target = target_enemy
                            if not second_target.alive:
                                second_target = max(
                                    (enemy for enemy in enemies if self._is_in_range(enemy) and enemy.alive),
                                    key=lambda e: (e.max_health, e.index),
                                    default=None
                                )
                            if second_target:
                                self.angle = self._calculate_angle_to_target(second_target)
                                second_target.take_damage(self.damage)
                                self.shot_sound.play()

                        pygame.time.set_timer(pygame.USEREVENT + 2, 100, True)  # 100ms 딜레이
                        pygame.event.post(pygame.event.Event(pygame.USEREVENT + 2, {"callback": second_attack}))

                    self.cooldown = self.reload_time

            elif self.type == "mine":
                target_enemy = self._get_leading_enemy(enemies)
                if target_enemy:
                    self.angle = self._calculate_angle_to_target(target_enemy)
                    target_enemy.take_damage(self.damage)
                    self.shot_sound.play()

                    # 둔화 효과 적용
                    if hasattr(self, 'slow_effect'):
                        target_enemy.apply_slow(self.slow_effect)

                    # 폭발 범위 내 다른 적에도 피해와 둔화 적용
                    for other_enemy in enemies:
                        if self._is_within_explosion_range(target_enemy, other_enemy):
                            explosion_damage = self.damage // getattr(self, "explosion_damage_reduction", 2)
                            other_enemy.take_damage(explosion_damage)
                            if hasattr(self, 'slow_effect'):
                                other_enemy.apply_slow(self.slow_effect)

                    self.cooldown = self.reload_time
        else:
            self.cooldown -= 1


    def _calculate_angle_to_target(self, enemy):
        """적과의 각도 계산 (기준: 아래쪽이 0도)"""
        dx = enemy.x + block_size // 2 - (self.x + block_size // 2)
        dy = enemy.y + block_size // 2 - (self.y + block_size // 2)
        angle = -math.degrees(math.atan2(dy, dx))  # Pygame의 회전은 반시계 방향
        return angle

    def _is_in_range(self, enemy):
        """적이 타워 사거리 내에 있는지 확인"""
        dist = ((enemy.x - self.x) ** 2 + (enemy.y - self.y) ** 2) ** 0.5
        return dist <= self.range

    def _is_within_explosion_range(self, target_enemy, other_enemy):
        """타겟 적 기준으로 폭발 범위 내에 있는지 확인"""
        dist = ((target_enemy.x - other_enemy.x) ** 2 + (target_enemy.y - other_enemy.y) ** 2) ** 0.5
        return dist <= self.explosion_range

    def _get_leading_enemy(self, enemies):
        """사거리 내에서 가장 앞에 있는 적을 반환"""
        enemies_in_range = [
            enemy for enemy in enemies if self._is_in_range(enemy)
        ]
        if not enemies_in_range:
            return None
        return max(enemies_in_range, key=lambda e: e.index)



# 화면 그리기 함수
def draw_start_screen():
    """시작 화면 그리기"""
    screen.blit(image["start_bg"], (0, 0))
    button_rect = image["start_button"].get_rect(center=(WIDTH // 2+20, HEIGHT // 2 + 300))
    screen.blit(image["start_button"], button_rect.topleft)
    return button_rect

def draw_tiles():
    """화면 타일 그리기"""
    for row in range(9):
        for col in range(16):
            tile_x = col * block_size
            tile_y = row * block_size
            screen.blit(tile_map[row][col], (tile_x, tile_y))

def draw_game_screen():
    """게임 화면 그리기"""
    draw_tiles()
    draw_path()
    screen.blit(image["basecamp"], (1100, 0))
    screen.blit(image["bottom_ui"], (0 ,750))

def draw_path():
    """적 경로 그리기"""
    for col, row in path_coords:
        x1, y1 = col * block_size, row * block_size
        screen.blit(image[e_tile], (x1, y1, block_size, block_size))

def update_tiles(wave):
    global tile_map, e_tile

    if wave == 11:
        tile_map = [[random.choice(image["tile_image2"]) for _ in range(16)] for _ in range(9)]
        e_tile = e_tile_dict[11]
        print("타일이 11로 변경되었습니다.")
    elif wave == 21:
        tile_map = [[random.choice(image["tile_image3"]) for _ in range(16)] for _ in range(9)]
        e_tile = e_tile_dict[21]
        print("타일이 21로 변경되었습니다.")
    elif wave == 31:
        tile_map = [[random.choice(image["tile_image4"]) for _ in range(16)] for _ in range(9)]
        e_tile = e_tile_dict[31]
        print("타일이 31로 변경되었습니다.")

def draw_hud():
    """우상단에 웨이브, 골드, 라이프, 다음 웨이브까지 남은 시간 표시"""
    hud_padding = 30  # 각 텍스트 간 기본 간격
    start_x = 1360
    start_y = 10

    # 배경 이미지 표시
    screen.blit(image["top_ui"], (start_x - 10, start_y - 10))

    # 텍스트 리스트 초기화 (웨이브, 골드, 라이프)
    texts = [
        font24.render(f"Wave: {wave}", True, WHITE),
        font24.render(f"Gold: {gold}", True, WHITE),
        font24.render(f"Life: {life}", True, WHITE),
    ]

    # 다음 웨이브 텍스트 추가
    if wave_pause:
        # 남은 시간 계산
        remaining_time = max(0, wave_pause_duration - (pygame.time.get_ticks() - wave_pause_timer))
        remaining_seconds = remaining_time // 1000  # 초 단위로 변환
        next_wave_text = font24.render(f"Next Wave: {remaining_seconds}s", True, BLACK)
    else:
        next_wave_text = font24.render("Next Wave: --", True, BLACK)
    texts.append(next_wave_text)  # 리스트에 추가

    # 텍스트를 일정 간격으로 배치
    y_offset = 50  # 첫 텍스트의 초기 Y 위치
    for text in texts:
        screen.blit(text, (start_x + 30, start_y + y_offset))
        y_offset += hud_padding  # 다음 텍스트의 위치를 업데이트
        
        
def draw_selected_tower_info(selected_tower):
    """선택된 타워의 정보를 하단 UI에 표시"""
    if selected_tower is None:
        return None

    # UI 위치 및 크기
    info_x, info_y = 400, 780
    image_size = 80

    # 사거리 표시
    draw_tower_range(selected_tower)

    # 타워 이미지 표시
    tower_image = pygame.transform.scale(image[selected_tower.image_key], (image_size, image_size))
    screen.blit(tower_image, (info_x, info_y))

    # 타워 정보 표시
    stats_x = info_x + image_size + 20
    stats_y = info_y
    text_lines = []

    if selected_tower.type == "supply":
        # 지원 타워의 경우
        text_lines.append(f"타워 타입: {selected_tower.type.capitalize()}")
        text_lines.append(f"레벨: {getattr(selected_tower, 'level', 1)}")
        text_lines.append(f"버프량: +{selected_tower.buff_amount} (공격력 증가)")
        text_lines.append(f"사거리: {selected_tower.range // block_size}칸")
    else:
        # 공격 타워의 경우
        buff_damage = sum(
            tower.buff_amount
            for tower in towers
            if tower.type == "supply" and 
            ((tower.x - selected_tower.x) ** 2 + (tower.y - selected_tower.y) ** 2) ** 0.5 <= tower.range
        )
        attack_line = f"공격력: {selected_tower.damage}"
        if buff_damage > 0:
            attack_line += f" (+{buff_damage})"
        text_lines.append(f"타워 타입: {selected_tower.type.capitalize()}")
        text_lines.append(f"레벨: {getattr(selected_tower, 'level', 1)}")
        text_lines.append(attack_line)
        text_lines.append(f"사거리: {selected_tower.range // block_size}칸")
        text_lines.append(f"공속: {selected_tower.reload_time}프레임")

    # 텍스트 렌더링
    for line in text_lines:
        if "(+" in line:  # 추가 공격력 표시 텍스트
            text_surface = font20.render(line, True, LIGHT_GREEN)
        else:
            text_surface = font20.render(line, True, WHITE)
        screen.blit(text_surface, (stats_x, stats_y))
        stats_y += 30

    # 승급 버튼
    button_width, button_height = 140, 50
    upgrade_button_rect = pygame.Rect(stats_x + 200, info_y, button_width, button_height)

    # 버튼 배경 이미지
    button_image = pygame.transform.scale(image["bottom_bg_ui"], (button_width, button_height))

    # 버튼 배경 이미지 그리기
    screen.blit(button_image, upgrade_button_rect.topleft)

    # 버튼 텍스트
    upgrade_text = font24.render("승급", True, RED)
    text_rect = upgrade_text.get_rect(center=upgrade_button_rect.center)

    # 텍스트를 버튼 배경 위에 그리기
    screen.blit(upgrade_text, text_rect)

    # 버튼 사각형 반환
    return upgrade_button_rect
 


def draw_tower_range(selected_tower):
    """선택된 타워의 사거리를 원으로 표시"""
    range_color = LIGHT_BLUE if selected_tower.type == "gun" else LIGHT_RED
    pygame.draw.circle(
        screen,
        range_color,
        (selected_tower.x + block_size // 2, selected_tower.y + block_size // 2),
        selected_tower.range,
        2  # 선의 두께
    )

def handle_upgrade_event(selected_tower, mouse_pos, upgrade_button_rect):
    """승급 이벤트 처리"""
    global gold

    if selected_tower and upgrade_button_rect and upgrade_button_rect.collidepoint(mouse_pos):
        upgrade_cost = 200 + (getattr(selected_tower, 'level', 1) - 1) * 50  # 레벨에 따른 승급 비용 계산
        if gold >= upgrade_cost:  # 골드 충분 여부 확인
            gold -= upgrade_cost  # 골드 차감
            upgrade_tower(selected_tower)  # 선택된 타워 승급
            print(f"승급 완료! 타워 레벨: {getattr(selected_tower, 'level', 1)}")
        else:
            print(f"골드가 부족합니다. 필요 골드: {upgrade_cost}")
                     
def upgrade_tower(tower):
    """타워 승급 로직"""
    global gold

    # 공격 타워
    if tower.type == "gun":
        tower.level += 1
        tower.damage += 50  # 레벨당 공격력 증가
        if tower.level == 2:
            tower.slow_effect = 0.4  # 둔화 효과 증가 (30% 감소)
            tower.image_key = "gun_tower_lv2"
        elif tower.level == 3:
            tower.reload_time = max(10, tower.reload_time - 2)  # 공속 향상
            tower.image_key = "gun_tower_lv3"
        elif tower.level == 4:
            tower.double_attack = True  # 더블 어택 활성화
            tower.image_key = "gun_tower_lv4"
        print(f"총기 타워 승급: 레벨 {tower.level}")

    # 지뢰 타워
    elif tower.type == "mine":
        tower.level += 1
        tower.damage += 30  # 레벨당 공격력 증가
        if tower.level == 2:
            tower.slow_effect = 0.4  # 둔화 효과 증가 (30% 감소)
            tower.image_key = "mine_tower_lv2"
        elif tower.level == 3:
            tower.reload_time = max(10, tower.reload_time - 2)  # 공속 향상
            tower.image_key = "mine_tower_lv3"
        elif tower.level == 4:
            tower.explosion_damage_reduction = 1  # 폭발 피해 감소율 조정 (1.5분의 1 피해)
            tower.image_key = "mine_tower_lv4"
        print(f"지뢰 타워 승급: 레벨 {tower.level}")

    # 보급 타워
    elif tower.type == "supply":
        tower.level += 1
        tower.buff_amount += 20 # 레벨당 버프량 증가
        if tower.level == 2:
            tower.buff_amount += 20  # 버프량 추가 증가
        elif tower.level == 3:
            tower.range += block_size  # 버프 사거리 증가
        elif tower.level == 4:
            tower.buff_amount += 100  # 추가 버프량 증가
        # 지원 타워는 동일 이미지 유지
        print(f"보급 타워 승급: 레벨 {tower.level}")

cutscene_played_waves = []  # 이미 실행된 웨이브를 기록하는 리스트

def handle_wave_logic():
    global wave, wave_pause, wave_pause_timer, wave_cutscene_active, enemies_spawned, last_spawn_time, tile_map, e_tile, wave_pause_duration, gold

    # 컷씬 활성 상태 처리
    if wave_cutscene_active:
        if not cutscene_manager.is_cutscene_active():  # 컷씬 종료 확인
            wave_cutscene_active = False  # 컷씬 종료
            wave_pause = True  # 컷씬 종료 후 대기 상태로 전환
            wave_pause_timer = pygame.time.get_ticks()  # 컷씬 종료 후 타이머 초기화
            wave_pause_duration = 5000  # 5초 대기 시간 설정
            cutscene_manager.cutscenes = []  # 컷씬 데이터를 초기화
            print("컷씬 종료, 게임 화면으로 복귀.")
        else:
            return  # 컷씬이 진행 중이면 다른 로직 실행 안 함

    # 웨이브 대기 상태 처리
    if wave_pause:
        current_time = pygame.time.get_ticks()
        if current_time - wave_pause_timer >= wave_pause_duration:  # 대기 시간이 끝났다면
            wave_pause = False
            wave_pause_timer = 0
            wave += 1
            enemies_spawned = 0
            print(f"Wave {wave} 시작!")

            # 타일 업데이트
            update_tiles(wave)

            # 특정 웨이브에서 컷씬 실행
            if wave in [11, 21, 31, 41] and wave not in cutscene_played_waves:
                cutscene_manager.load_cutscenes_for_wave("cutscene_data.json", wave)
                if cutscene_manager.cutscenes:  # 컷씬이 있는 경우에만 실행
                    wave_cutscene_active = True
                    cutscene_played_waves.append(wave)  # 실행된 웨이브 기록
                    print(f"Wave {wave} 컷씬 실행")
                    return  # 컷씬 실행 중이므로 적 생성 중단

        return  # 대기 상태에서는 적을 생성하지 않음

    # 적 생성 처리 (대기 상태가 아닐 때만)
    if not wave_pause and enemies_spawned < max_enemies_per_wave:
        current_time = pygame.time.get_ticks()
        if current_time - last_spawn_time >= enemy_spawn_interval:
            if wave % 10 == 0 and enemies_spawned == 0:  # 10, 20, 30, 40 등 웨이브 보스 좀비 생성
                boss_type = min(4, wave // 10)  # 보스 좀비 타입 결정 (최대 타입 4)
                enemies.append(BossEnemy(path_coords, boss_type=boss_type, health_increment=100 * wave))
                print(f"보스 좀비 생성! 타입: {boss_type}")

            elif wave % 5 == 0 and wave % 10 != 0 and enemies_spawned == 0:  # 5, 15, 25, 35 등 웨이브 특수 좀비 생성
                special_type = min(4, wave // 5)  # 특수 좀비 타입 결정 (최대 타입 4)
                special_enemy = SpecialEnemy(path_coords, special_type=special_type)  # 객체 생성
                special_enemy.health += 50 * wave  # health_increment 적용
                enemies.append(special_enemy)  # 적 리스트에 추가
                print(f"특수 좀비 생성! 타입: {special_type}")


            else:  # 일반 좀비 생성
                enemies.append(Enemy(path_coords, health=20 + 50 * wave))

            enemies_spawned += 1
            last_spawn_time = current_time
            print(f"적 생성: {enemies_spawned}/{max_enemies_per_wave}")

    # 모든 적이 제거된 경우 웨이브 대기로 전환
    if enemies_spawned == max_enemies_per_wave and all(not enemy.alive for enemy in enemies):
        if not wave_pause:
            if wave in [11, 21, 31, 41] and wave not in cutscene_played_waves:
                cutscene_manager.load_cutscenes_for_wave("cutscene_data.json", wave)
                wave_cutscene_active = True
                cutscene_played_waves.append(wave)  # 실행된 웨이브 기록
                print(f"Wave {wave} 컷씬 실행, 컷씬 이후 대기 시작.")
            else:
                wave_pause = True
                wave_pause_timer = pygame.time.get_ticks()
                gold += 100
                wave_pause_duration = 5000  # 웨이브 종료 후 5초 대기
                print("모든 적 제거됨. 다음 웨이브 대기 5초 시작.")

    # 특수 좀비와 보스 좀비 능력 실행
    for enemy in enemies:
        if isinstance(enemy, SpecialEnemy) or isinstance(enemy, BossEnemy):
            enemy.update(enemies, towers)


def handle_tower_selection(mouse_pos):
    global selected_tower_ui
    for tower in towers:
        # 타워의 위치와 크기 정의
        tower_rect = pygame.Rect(tower.x, tower.y, block_size, block_size)
        if tower_rect.collidepoint(mouse_pos):  # 마우스 클릭이 타워 영역에 있는지 확인
            selected_tower_ui = tower
            print(f"타워 선택됨: {tower.type}, 위치=({tower.x}, {tower.y})")  # 디버깅 메시지
            return
    # 타워 선택 해제
    selected_tower_ui = None
    print("타워 선택 해제")
    
def draw_tower_ui():
    """화면 왼쪽에 타워 선택 UI를 그립니다."""
    # 배경 이미지 그리기
    screen.blit(image["side_ui"], (tower_ui_rect.x, tower_ui_rect.y))

    y_offset = tower_ui_rect.y + 20  # 타워 아이템 시작 위치

    for tower in TOWER_TYPES:
        # 타워 이미지 로드 및 크기 조정
        tower_image = pygame.image.load(tower["image_path"]).convert_alpha()
        tower_image = pygame.transform.scale(tower_image, (100, 100))

        # 타워 이미지 그리기
        screen.blit(tower_image, (tower_ui_rect.x + 90, y_offset))
        screen.blit(image["side_bg_ui"], (tower_ui_rect.x + 30, y_offset + 110))
        # 타워 이름과 비용 텍스트를 이미지 바로 아래에 표시
        tower_text = font20b.render(f"{tower['name']} (${tower['cost']})", True, BLACK)
        text_rect = tower_text.get_rect(center=(tower_ui_rect.x + 145, y_offset + 130))  # 배경 중앙에 텍스트 정렬
        screen.blit(tower_text, text_rect.topleft)

        y_offset += 100 + 50  # 이미지 높이(100) + 텍스트 높이 및 간격(50)

def handle_tower_ui_events(event):
    """타워 UI와 드래그 앤 드롭 이벤트를 처리합니다."""
    global selected_tower, selected_tower_image, dragging, gold

    INSTALLABLE_AREA = pygame.Rect(0, 0, 1300, 700)  # 설치 가능한 영역
    path_blocks = [(x * block_size, y * block_size) for x, y in path_coords]

    # 추가 설치 금지 영역 정의
    RESTRICTED_AREA = pygame.Rect(1100, 0, 200, 300)  # x: 1100~1300, y: 0~200

    if event.type == pygame.MOUSEBUTTONDOWN:
        mouse_x, mouse_y = event.pos
        y_offset = tower_ui_rect.y + 20

        for tower in TOWER_TYPES:
            tower_rect = pygame.Rect(tower_ui_rect.x + 40, y_offset, 200, 100)
            if tower_rect.collidepoint(mouse_x, mouse_y):
                if gold >= tower["cost"]:
                    selected_tower = tower
                    selected_tower_image = pygame.image.load(tower["image_path"]).convert_alpha()
                    selected_tower_image = pygame.transform.scale(selected_tower_image, (block_size, block_size))
                    dragging = True
            y_offset += 100 + 50

    elif event.type == pygame.MOUSEBUTTONUP and dragging:
        mouse_x, mouse_y = event.pos
        grid_x = (mouse_x // block_size) * block_size
        grid_y = (mouse_y // block_size) * block_size

        # 타워 설치 확인
        if (
            INSTALLABLE_AREA.collidepoint(mouse_x, mouse_y) and
            not RESTRICTED_AREA.collidepoint(mouse_x, mouse_y) and  # 추가 설치 금지 영역 체크
            (grid_x, grid_y) not in path_blocks and
            all((tower.x, tower.y) != (grid_x, grid_y) for tower in towers)
        ):
            new_tower = Tower(grid_x, grid_y, selected_tower["type"])
            towers.append(new_tower)
            print(f"타워 설치됨: {new_tower.type}, 위치=({new_tower.x}, {new_tower.y})")
            gold -= selected_tower["cost"]
        else:
            print("설치할 수 없는 위치입니다.")

        # 드래그 상태 초기화
        selected_tower = None
        selected_tower_image = None
        dragging = False


def handle_game_logic():
    """게임 내 주요 로직 처리"""
    global gold, life,wave, current_screen

    # 적 이동 및 상태 확인
    for enemy in enemies[:]:
        enemy.move()
        if not enemy.alive:
            enemies.remove(enemy)
            if enemy.index == len(path_coords) - 1:  # 적이 도달한 경우
                life -= 1
                print(f"적이 도달했습니다! 남은 라이프: {life}")
                if life <= 0:  # 라이프가 0 이하가 되었을 때
                    print("Game Over!")  # 디버그 메시지
                    current_screen = "game_over"  # 게임 오버 화면으로 전환
                    return  # 더 이상 처리하지 않음

    # 타워 공격 처리
    for tower in towers:
        tower.attack(enemies)

# 게임 이벤트 처리 수정
def handle_game_events(retry_rect=None, title_rect=None):
    """게임 이벤트 처리"""
    global current_screen, wave_cutscene_active, wave_pause, wave_pause_timer, enemies_spawned, game_over, selected_tower_ui, gold, mouse_pos

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if current_screen == "start":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = event.pos
                button_rect = draw_start_screen()
                if button_rect.collidepoint(mouse_pos):
                    stop_bgm()
                    wave_pause = True
                    wave_pause_timer = pygame.time.get_ticks()
                    current_screen = "game"

        elif current_screen == "game":
            # 타워 UI 관련 이벤트 처리
            handle_tower_ui_events(event)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()

                # 승급 버튼 클릭 처리 (타워 선택 처리보다 먼저 실행)
                if selected_tower_ui:
                    upgrade_button_rect = draw_selected_tower_info(selected_tower_ui)
                    if upgrade_button_rect and upgrade_button_rect.collidepoint(mouse_pos):
                        handle_upgrade_event(selected_tower_ui, mouse_pos, upgrade_button_rect)
                        return  # 승급 버튼 클릭 처리 후 종료

                # 타워 선택 처리
                handle_tower_selection(mouse_pos)

            if wave_cutscene_active:
                # 컷씬 중 키 입력 처리
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    cutscene_manager.next_cutscene()
                    print("다음 컷씬으로 이동")
                    if not cutscene_manager.is_cutscene_active():
                        wave_cutscene_active = False  # 컷씬 종료
                        print("컷씬 종료, 게임 화면으로 복귀.")
            else:
                # 게임 이벤트 처리
                handle_tower_ui_events(event)

            # 적 생성 이벤트 처리
            if event.type == ENEMY_SPAWN_EVENT and enemies_spawned < max_enemies_per_wave:
                enemies.append(Enemy(path_coords))
                enemies_spawned += 1
                print(f"적 생성: {enemies_spawned}/{max_enemies_per_wave}")

# BGM 재생 함수
def play_start_bgm():
    pygame.mixer.music.load(audio["intro"])
    pygame.mixer.music.set_volume(0.2)
    pygame.mixer.music.play(-1)  # 무한 반복 재생

def stop_bgm():
    pygame.mixer.music.stop()  # BGM 중지        
        
def draw_game_elements():
    """적 및 타워 그리기"""
    for enemy in enemies:
        enemy.draw()
    for tower in towers:
        tower.draw()        

    # 드래그 중인 타워 이미지 그리기
    global dragging, selected_tower_image
    if dragging and selected_tower_image:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        screen.blit(selected_tower_image, (mouse_x - block_size // 2, mouse_y - block_size // 2))   

# 메인 루프 수정
def main():
    global current_screen, wave_cutscene_active, selected_tower_ui

    play_start_bgm()  # 게임 시작 시 BGM 재생

    game_over_timer = None  # 게임 오버 시작 시간을 기록할 변수
    while True:
        screen.fill(WHITE)  # 화면 초기화
        handle_game_events()

        if current_screen == "start":
            draw_start_screen()
        elif current_screen == "game":
            if wave_cutscene_active:
                cutscene_manager.draw_cutscene()  # 컷씬 그리기
            else:
                draw_game_screen()
                handle_wave_logic()  # 웨이브 로직 실행
                handle_game_logic()  # 적 이동 및 타워 공격 실행
                draw_hud()  # HUD 표시
                draw_tower_ui()  # 타워 선택 UI
                draw_game_elements()  # 적 및 타워 그리기

                # 선택된 타워 정보 표시
                if selected_tower_ui is not None:
                    draw_selected_tower_info(selected_tower_ui)

        elif current_screen == "game_over":
            if game_over_timer is None:  # 게임 오버 타이머 초기화
                game_over_timer = pygame.time.get_ticks()  # 현재 시간 기록

            # 게임 오버 화면 그리기
            screen.blit(image["game_over_bg"], (0, 0))
            pygame.display.flip()  # 화면 업데이트

            # 10초가 경과하면 프로그램 종료
            if pygame.time.get_ticks() - game_over_timer >= 10000:
                pygame.quit()
                sys.exit()

        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()
