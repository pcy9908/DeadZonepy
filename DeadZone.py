import pygame
import sys
import random
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
max_enemies_per_wave = 40  # 웨이브당 적 최대 수
enemy_spawn_interval = 1000  # 적 스폰 간격 (밀리초, 더 빠르게)
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
    {"name": "Mine Tower", "cost": 75, "color": LIGHT_RED, "type": "mine", "image_path": "mine_tower.png"},
    {"name": "Supply Tower", "cost": 20, "color": LIGHT_GREEN, "type": "supply", "image_path": "supply_tower.png"}
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
        self.health = health
        self.max_health = health  # 최대 체력을 별도로 저장
        self.alive = True

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


    @staticmethod
    def handle_wave_upgrades():
        """웨이브가 진행될 때마다 적 체력과 이동 속도 증가"""
        global enemies
        for enemy in enemies:
            enemy.health += 25  # 적 체력 증가
            enemy.speed += 0.2  # 적 이동 속도 약간 증가

class BossEnemy(Enemy):
    """보스 좀비 클래스"""
    def __init__(self, path_coords, speed=2, health=1000):
        super().__init__(path_coords, speed, health, )
        self.image = image["boss1"]
        self.image = pygame.transform.scale(self.image, (block_size * 1.2, block_size * 1.2))  # 보스는 더 큰 크기로 표시

    def take_damage(self, damage):
        """보스는 피해를 입을 때 추가 효과"""
        super().take_damage(damage)
        if not self.alive:
            print("보스 좀비가 사망했습니다!")

class SpecialEnemy(Enemy):
    """특수 좀비 클래스"""
    def __init__(self, path_coords, speed=3, health=200):
        super().__init__(path_coords, speed, health)
        self.image = image["s_enemy"]
        self.image = pygame.transform.scale(self.image, (block_size, block_size))  # 일반 좀비 크기

    def boost_nearby_enemies(self, enemies):
        """특수 능력: 주변 1칸 내의 좀비 속도 증가"""
        for enemy in enemies:
            if enemy is not self:  # 자기 자신은 제외
                dist = ((enemy.x - self.x) ** 2 + (enemy.y - self.y) ** 2) ** 0.5
                if dist <= block_size:  # 1칸 내
                    enemy.speed += 0.5  # 속도 증가
                    print(f"특수 좀비가 {enemy}의 속도를 증가시켰습니다!")        

# Tower 클래스
class Tower:
    def __init__(self, x, y, tower_type):
        # 타워 타입에 따라 속성을 정의
        if tower_type == "gun":
            self.range = 3 * block_size
            self.damage = 20
            self.shot_sound = audio["gun_sound"]
            self.shot_sound.set_volume(0.02)
            self.image_key = "gun_tower"
            
        elif tower_type == "mine":
            self.range = 2 * block_size
            self.damage = 50
            self.shot_sound = audio["mine_sound"]
            self.shot_sound.set_volume(0.02)
            self.image_key = "mine_tower"

        elif tower_type == "supply":
            self.range = 2 * block_size
            self.effect_duration = 300  # 보급 효과 지속 시간 (프레임 단위)
            self.buff_amount = 10  # 버프량
            self.reload_time = 0  # 공격 없음
            self.image_key = "supply_tower"

        self.x, self.y = x, y
        self.reload_time = 30  # 공격 딜레이 (프레임 단위)
        self.cooldown = 0  # 현재 재장전 상태
        self.type = tower_type
  
        
    def draw(self):
        """타워를 화면에 그리기"""
        tower_image = image[self.image_key]
        tower_image = pygame.transform.scale(tower_image, (block_size, block_size))
        screen.blit(tower_image, (self.x, self.y))

    def attack(self, enemies):
        """타워 공격 로직"""
        if self.cooldown == 0:
            if self.type == "gun":
                # 총기 타워: 단일 타겟 공격
                for enemy in enemies:
                    dist = ((enemy.x - self.x) ** 2 + (enemy.y - self.y) ** 2) ** 0.5
                    if dist <= self.range:
                        enemy.take_damage(self.damage)
                        self.shot_sound.play()
                        self.cooldown = self.reload_time
                        break  # 하나의 적만 공격
            elif self.type == "mine":
                # 지뢰 타워: 범위 공격
                for enemy in enemies:
                    dist = ((enemy.x - self.x) ** 2 + (enemy.y - self.y) ** 2) ** 0.5
                    if dist <= self.range:
                        for other_enemy in enemies:
                            dist_to_other = ((other_enemy.x - self.x) ** 2 + (other_enemy.y - self.y) ** 2) ** 0.5
                            if dist_to_other <= self.range:
                                other_enemy.take_damage(self.damage)
                        self.shot_sound.play()
                        self.cooldown = self.reload_time
                        break  # 범위 내 공격 후 종료
        else:
            self.cooldown -= 1

    def provide_support(self):
        """보급 타워의 버프 로직"""
        for tower in towers:
            if tower != self:  # 자신을 제외한 다른 타워
                dist = ((tower.x - self.x) ** 2 + (tower.y - self.y) ** 2) ** 0.5
                if dist <= self.range:
                    if hasattr(tower, "damage"):
                        tower.damage += self.buff_amount  # 공격력 버프량 추가
                    if hasattr(tower, "reload_time"):
                        tower.reload_time = max(10, tower.reload_time - 5)  # 재장전 시간 감소

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
        font24.render(f"Wave: {wave}", True, BLACK),
        font24.render(f"Gold: {gold}", True, BLACK),
        font24.render(f"Life: {life}", True, BLACK),
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
        return  # 선택된 타워가 없으면 아무것도 표시하지 않음

    # UI 위치 및 크기
    info_x, info_y = 400, 780
    image_size = 80

    # 선택된 타워 이미지 표시
    tower_image = pygame.transform.scale(image[selected_tower.image_key], (image_size, image_size))
    screen.blit(tower_image, (info_x, info_y))

    # 타워 정보 텍스트
    stats_x = info_x + image_size + 20  # 텍스트를 오른쪽에 배치
    stats_y = info_y
    text_lines = []

    if selected_tower.type == "supply":
        # 보급 타워의 경우
        text_lines.append(f"타워 타입: {selected_tower.type.capitalize()}")
        text_lines.append(f"레벨: {getattr(selected_tower, 'level', 1)}")  # 레벨 표시
        text_lines.append(f"버프 공격력: +{selected_tower.buff_amount}")
        text_lines.append(f"공속 개선: -5프레임")
    else:
        # 일반 타워의 경우
        text_lines.append(f"타워 타입: {selected_tower.type.capitalize()}")
        text_lines.append(f"레벨: {getattr(selected_tower, 'level', 1)}")  # 레벨 표시
        
        # 기본 공격력과 추가 공격력 표시
        buff_damage = sum(
            tower.buff_amount for tower in towers if tower.type == "supply" and
            ((tower.x - selected_tower.x) ** 2 + (tower.y - selected_tower.y) ** 2) ** 0.5 <= tower.range
        )
        attack_line = f"공격력: {selected_tower.damage}"
        if buff_damage > 0:
            attack_line += f" (+{buff_damage})"  # 추가 공격력은 괄호로 표시
        text_lines.append(attack_line)

        text_lines.append(f"사거리: {selected_tower.range // block_size}칸")
        text_lines.append(f"공속: {selected_tower.reload_time}프레임")

        # 공속 개선 표시
        buff_reload = sum(
            5 for tower in towers if tower.type == "supply" and
            ((tower.x - selected_tower.x) ** 2 + (tower.y - selected_tower.y) ** 2) ** 0.5 <= tower.range
        )
        if buff_reload > 0:
            text_lines.append(f"공속 개선: -{buff_reload}프레임")

    # 텍스트 렌더링
    for line in text_lines:
        text_surface = font20.render(line, True, WHITE)
        screen.blit(text_surface, (stats_x, stats_y))
        stats_y += 30

    # 승급 버튼 추가
    button_width, button_height = 140, 50
    upgrade_button_rect = pygame.Rect(stats_x + 200, info_y, button_width, button_height)  # 텍스트 오른쪽에 위치
    pygame.draw.rect(screen, (255, 69, 0), upgrade_button_rect, border_radius=10)  # 빨간색 버튼
    pygame.draw.rect(screen, (139, 0, 0), upgrade_button_rect, 3, border_radius=10)  # 버튼 테두리

    upgrade_text = font24.render("승급", True, WHITE)
    text_rect = upgrade_text.get_rect(center=upgrade_button_rect.center)
    screen.blit(upgrade_text, text_rect)

    # 승급 비용 표시
    cost_text = font24.render("200 골드", True, WHITE)
    screen.blit(cost_text, (upgrade_button_rect.x, upgrade_button_rect.y + 60))

    return upgrade_button_rect  # 승급 버튼 영역 반환

def handle_upgrade_event(selected_tower, mouse_pos, upgrade_button_rect):
    """승급 이벤트 처리"""
    global gold

    # 클릭한 위치가 승급 버튼 위인지 확인
    if upgrade_button_rect and upgrade_button_rect.collidepoint(mouse_pos):
        if gold >= 200:  # 골드 충분 여부 확인
            gold -= 200  # 골드 차감
            upgrade_tower(selected_tower)  # 선택된 타워 승급
            print(f"승급 완료! 타워 레벨: {selected_tower.level}")
        else:
            print("골드가 부족합니다.")

def handle_wave_logic():
    global wave, wave_pause, wave_pause_timer, wave_cutscene_active, enemies_spawned, last_spawn_time, tile_map, e_tile

    # 컷씬 활성 상태 처리
    if wave_cutscene_active:
        if not cutscene_manager.is_cutscene_active():  # 컷씬 종료 확인
            wave_cutscene_active = False  # 컷씬 종료
            print("컷씬 종료, 웨이브 진행 가능.")
        else:
            return  # 컷씬이 진행 중이면 다른 로직 실행 안 함

    # 웨이브 대기 상태 처리
    if wave_pause:
        current_time = pygame.time.get_ticks()
        remaining_time = (current_time - wave_pause_timer)

        if remaining_time >= wave_pause_duration:  # 대기 시간이 끝났다면
            wave_pause = False
            wave_pause_timer = 0
            wave += 1
            enemies_spawned = 0
            print(f"Wave {wave} 시작!")

            # 타일 업데이트
            update_tiles(wave)

            # 특정 웨이브에서 컷씬 실행
            if wave in [11, 21, 31, 41]:
                cutscene_manager.load_cutscenes_for_wave("cutscene_data.json", wave)
                if cutscene_manager.cutscenes:
                    wave_cutscene_active = True
                    print(f"Wave {wave} 컷씬 실행")
                    return  # 컷씬 실행 중이므로 적 생성 중단

        return  # 대기 상태에서는 적을 생성하지 않음

    # 적 생성 처리 (대기 상태가 아닐 때만)
    if not wave_pause and enemies_spawned < max_enemies_per_wave:
        current_time = pygame.time.get_ticks()
        if current_time - last_spawn_time >= enemy_spawn_interval:
            enemies.append(Enemy(path_coords))  # 적 생성
            enemies_spawned += 1
            last_spawn_time = current_time
            print(f"적 생성: {enemies_spawned}/{max_enemies_per_wave}")

    # 모든 적이 제거된 경우 웨이브 대기로 전환
    if enemies_spawned == max_enemies_per_wave and not enemies:
        if not wave_pause:
            wave_pause = True
            wave_pause_timer = pygame.time.get_ticks()
            print("모든 적 제거됨. 다음 웨이브 대기 시작.")

            # 보스 및 특수 좀비 생성 로직
            if wave % 10 == 0:  # 10, 20, 30 등 웨이브의 마지막 적은 보스 좀비
                boss_enemy = BossEnemy(path_coords)
                enemies.append(boss_enemy)
                print("보스 좀비 생성!")

            elif wave % 5 == 0:  # 5, 15, 25 등 웨이브의 마지막 적은 특수 좀비
                special_enemy = SpecialEnemy(path_coords)
                enemies.append(special_enemy)
                print("특수 좀비 생성!")

            print("웨이브 종료, 다음 웨이브 대기 중...")

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
    
def upgrade_tower(tower):
    """타워 승급 로직"""
    # 타워 레벨 증가
    tower.level = getattr(tower, 'level', 1) + 1  # 레벨이 없으면 1로 시작
    tower.damage += 20  # 공격력 증가
    tower.range += block_size  # 사거리 증가
    tower.reload_time = max(10, tower.reload_time - 5)  # 재장전 시간 감소

    # 보급 타워의 경우 버프 강화
    if tower.type == "supply":
        tower.buff_amount += 5  # 보급 타워 버프 증가

def draw_tower_ui():
    """화면 왼쪽에 타워 선택 UI를 그립니다."""
    # 배경 이미지 그리기
    screen.blit(image["side_ui"], (tower_ui_rect.x, tower_ui_rect.y))

    y_offset = tower_ui_rect.y + 20  # 타워 아이템 시작 위치

    for tower in TOWER_TYPES:
        # 타워 이미지 로드 및 크기 조정
        tower_image = pygame.image.load(tower["image_path"]).convert_alpha()
        tower_image = pygame.transform.scale(tower_image, (200, 100))

        # 타워 이미지 그리기
        screen.blit(tower_image, (tower_ui_rect.x + 40, y_offset))

        # 타워 이름과 비용 텍스트를 이미지 바로 아래에 표시
        tower_text = font12.render(f"{tower['name']} (${tower['cost']})", True, BLACK)
        screen.blit(tower_text, (tower_ui_rect.x + 40, y_offset + 110))  # 이미지 아래 10px 간격

        y_offset += 100 + 50  # 이미지 높이(100) + 텍스트 높이 및 간격(50)

def handle_tower_ui_events(event):
    """타워 UI와 드래그 앤 드롭 이벤트를 처리합니다."""
    global selected_tower, selected_tower_image, dragging, gold

    INSTALLABLE_AREA = pygame.Rect(0, 0, 1300, 700)  # 설치 가능한 영역
    path_blocks = [(x * block_size, y * block_size) for x, y in path_coords]

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
        if INSTALLABLE_AREA.collidepoint(mouse_x, mouse_y) and (grid_x, grid_y) not in path_blocks:
            if all((tower.x, tower.y) != (grid_x, grid_y) for tower in towers):
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

        
def draw_game_over_screen():
    """게임 오버 화면 그리기"""
    # 배경 이미지 표시
    screen.blit(image["game_over_bg"], (0, 0))  # 화면에 배경 이미지 표시

    # 게임 오버 텍스트
    retry_text = font12.render("재도전", True, BLACK)
    title_text = font12.render("타이틀로", True, BLACK)

    # 버튼 위치 설정
    retry_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 - 50, 200, 60)
    title_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 20, 200, 60)

    # 버튼 그리기
    pygame.draw.rect(screen, LIGHT_RED, retry_rect)
    pygame.draw.rect(screen, LIGHT_BLUE, title_rect)

    # 텍스트 버튼에 렌더링 (버튼 중심에 위치)
    retry_text_rect = retry_text.get_rect(center=retry_rect.center)
    title_text_rect = title_text.get_rect(center=title_rect.center)
    screen.blit(retry_text, retry_text_rect)  # 텍스트를 버튼 중심에 맞게 배치
    screen.blit(title_text, title_text_rect)

    return retry_rect, title_rect

def reset_game():
    """게임 상태 초기화"""
    global life, gold, wave, enemies, towers, game_over, current_screen

    life = 10
    gold = 100
    wave = 0
    enemies = []
    towers = []
    game_over = False
    current_screen = "game"
    
def handle_game_over_events(retry_rect, title_rect):
    """게임 오버 화면에서 이벤트 처리"""
    global current_screen, life, game_over

    for event in pygame.event.get():
        if event.type == pygame.QUIT:  # 게임 종료
            pygame.quit()
            sys.exit()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # 마우스 왼쪽 클릭
            mouse_pos = pygame.mouse.get_pos()
            if retry_rect.collidepoint(mouse_pos):  # 재도전 버튼 클릭
                reset_game()
            elif title_rect.collidepoint(mouse_pos):  # 타이틀로 버튼 클릭
                current_screen = "start"

def handle_game_logic():
    """게임 내 주요 로직 처리"""
    global gold, life,wave

    # 적 이동 및 상태 확인
    for enemy in enemies[:]:
        enemy.move()
        if not enemy.alive:
            enemies.remove(enemy)
            if enemy.index == len(path_coords) - 1:  # 적이 도달한 경우
                life -= 1
                if life <= 0:
                    print("Game Over!")  # 디버그용 (추후 종료 처리 추가 가능)

    # 타워 공격 처리
    for tower in towers:
        tower.attack(enemies)        

# 게임 이벤트 처리 수정
def handle_game_events():
    global current_screen, wave_cutscene_active, wave_pause, wave_pause_timer, enemies_spawned, game_over, gold  # 글로벌 변수 선언

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
            # 게임 이벤트 처리
            handle_tower_ui_events(event)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                handle_tower_selection(mouse_pos)
                    
                # 선택된 타워 승급 버튼 클릭 처리
                if selected_tower_ui:
                    upgrade_button_rect = draw_selected_tower_info(selected_tower_ui)
                    if upgrade_button_rect and upgrade_button_rect.collidepoint(mouse_pos):
                        # 골드 확인 및 승급 처리
                        if gold >= 200:
                            print("승급하시겠습니까? [확인 버튼을 추가하거나 팝업 처리]")
                            confirmed = input("승급하시겠습니까? (y/n): ").strip().lower()
                            if confirmed == 'y':
                                gold -= 200
                                upgrade_tower(selected_tower_ui)
                                print("승급 완료!")
                            else:
                                print("승급 취소.")
                        else:
                            print("골드가 부족합니다.") 
            if wave_cutscene_active:                   
                # 컷씬 중 키 입력 처리
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    cutscene_manager.next_cutscene()
                    print("다음 컷씬으로 이동")
                    if not cutscene_manager.is_cutscene_active():
                        wave_cutscene_active = False  # 컷씬 종료
                        print("컷씬 종료, 게임 화면으로 복귀.")

                # 적 생성 이벤트 처리
                if event.type == ENEMY_SPAWN_EVENT and enemies_spawned < max_enemies_per_wave:
                    enemies.append(Enemy(path_coords))
                    enemies_spawned += 1
                    print(f"적 생성: {enemies_spawned}/{max_enemies_per_wave}")
    
            if event.type == ENEMY_SPAWN_EVENT and enemies_spawned < max_enemies_per_wave:
                enemies.append(Enemy(path_coords))
                enemies_spawned += 1

        elif current_screen == "game_over":
            retry_rect, title_rect = draw_game_over_screen()
            handle_game_over_events(retry_rect, title_rect)                            


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
    while True:
        screen.fill(WHITE)   # 화면 초기화
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
            draw_game_over_screen()

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()
