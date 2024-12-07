import pygame
import sys
import random

# 게임 초기 설정
pygame.init()
# pygame.mixer 초기화
pygame.mixer.init()
# 화면 크기와 기본 설정
WIDTH, HEIGHT = 1600, 900
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("DEAD ZONE")
clock = pygame.time.Clock()

# 색상 정의
WHITE = (255, 255, 255)
GRAY = (160, 160, 160)
DARK_GRAY = (96, 96, 96)
LIGHT_RED = (255, 160, 122)
LIGHT_BLUE = (173, 216, 230)
BLACK = (0, 0, 0)

# 게임 변수 초기화
block_size = 100
grid_rows, grid_cols = HEIGHT // block_size, WIDTH // block_size
current_screen = "start"  # 시작 화면에서 시작

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

# 이미지 로드 및 크기 조정
start_bg = pygame.image.load("startpage.png")
start_button = pygame.image.load("startButton.png")
start_button = pygame.transform.scale(start_button, (300, 254))
top_ui = pygame.image.load('ui4.png')
side_ui = pygame.image.load("ui5.png")
bottom_ui = pygame.image.load("ui3.png")
# 타워 관련 이미지
gun_tower = pygame.image.load("gun_tower.png")
mine_tower = pygame.image.load("mine_tower.png")
m_bg_s1 = pygame.image.load("block1.png")
m_bg_s2 = pygame.image.load("block2.png")
m_bg_s3 = pygame.image.load("block3.png")
m_bg_s4 = pygame.image.load("block4.png")
e_block = pygame.image.load("e_block.png")
tile_image = [m_bg_s1, m_bg_s2, m_bg_s3, m_bg_s4]

tile_map = [[random.choice(tile_image) for _ in range(16)] for _ in range(9)]
# 이벤트 정의
ENEMY_SPAWN_EVENT = pygame.USEREVENT + 1
pygame.time.set_timer(ENEMY_SPAWN_EVENT, 10000)
# BGM 파일 경로
start_bgm_path = "인트로.mp3"
spawn_sound_path="좀비1.mp3"
death_sound_path = "좀비사망.mp3"
gun_sound_path = "총3.mp3"
mine_sound_path = "지뢰폭발1.mp3"
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
wave_pause_duration = 10000  # 10초 대기 (밀리초)
current_screen = "start"  # 시작 화면에서 시작
# HUD에 사용될 폰트 설정
font = pygame.font.Font(None, 36)  # None은 기본 폰트, 36은 폰트 크기

# 타워 UI 변수
tower_ui_width = 200  # 타워 UI의 가로 길이
tower_ui_rect = pygame.Rect(1350, 250, tower_ui_width + 80, HEIGHT - 400)  # UI 위치와 크기

TOWER_TYPES = [
    {"name": "Gun Tower", "cost": 50, "color": LIGHT_BLUE, "type": "gun", "image_path": "gun_tower.png"},
    {"name": "Mine Tower", "cost": 75, "color": LIGHT_RED, "type": "mine", "image_path": "mine_tower.png"},
]

selected_tower = None  # 현재 선택된 타워
class Enemy:
    def __init__(self, path_coords, speed=3, health=20, image_path="enemy.png", spawn_sound_path=spawn_sound_path, death_sound_path=death_sound_path):
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
        self.spawn_sound = pygame.mixer.Sound(spawn_sound_path)
        self.spawn_sound.set_volume(0)  # 스폰 소리 음량 조절
        self.death_sound = pygame.mixer.Sound(death_sound_path)
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
# Tower 클래스
class Tower:
    def __init__(self, x, y, tower_type,gun_sound_path = gun_sound_path,mine_sound_path=mine_sound_path):
        # 타워 타입에 따라 속성을 정의
        if tower_type == "gun":
            self.range = 3 * block_size
            self.damage = 20
            self.shot_sound = pygame.mixer.Sound(gun_sound_path)
            self.shot_sound.set_volume(0.02)  
            
        elif tower_type == "mine":
            self.range = 2 * block_size
            self.damage = 50
            self.shot_sound = pygame.mixer.Sound(mine_sound_path)
            self.shot_sound.set_volume(0.02)  
        else:
            raise ValueError("Invalid tower type")

        self.x, self.y = x, y
        self.reload_time = 30  # 공격 딜레이 (프레임 단위)
        self.cooldown = 0  # 현재 재장전 상태
        self.type = tower_type
  
        
    def draw(self):
        """타워를 화면에 그리기"""
        pygame.draw.rect(screen, TOWER_TYPES[0 if self.type == "gun" else 1]["color"], (self.x, self.y, block_size, block_size))

    def attack(self, enemies):
        """타워의 공격 로직"""
        if self.cooldown == 0:  # 공격 가능 상태
            for enemy in enemies:
                if enemy.alive:
                    # 타겟까지의 거리 계산
                    dist = ((enemy.x - self.x)**2 + (enemy.y - self.y)**2)**0.5
                    if dist <= self.range:
                        enemy.take_damage(self.damage)  # 적 체력 감소
                        self.shot_sound.play()
                        self.cooldown = self.reload_time  # 쿨다운 초기화
                        break  # 한 번에 하나의 적만 공격
        else:
            self.cooldown -= 1  # 쿨다운 감소
# 화면 그리기 함수
def draw_start_screen():
    """시작 화면 그리기"""
    screen.blit(start_bg, (0, 0))
    button_rect = start_button.get_rect(center=(WIDTH // 2+20, HEIGHT // 2 + 300))
    screen.blit(start_button, button_rect.topleft)
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
    screen.blit(bottom_ui, (0 ,750))


def draw_grid():
    """그리드 그리기"""
    for row in range(grid_rows):
        for col in range(grid_cols):
            x1, y1 = col * block_size, row * block_size
            pygame.draw.rect(screen, GRAY, (x1, y1, block_size, block_size), 1)


def draw_path():
    """적 경로 그리기"""
    for col, row in path_coords:
        x1, y1 = col * block_size, row * block_size
        screen.blit(e_block, (x1, y1, block_size, block_size))

def draw_hud():
    """우상단에 웨이브, 골드, 라이프, 다음 웨이브까지 남은 시간 표시"""
    hud_padding = 30  # 각 텍스트 간 기본 간격
    start_x = 1360
    start_y = 10

    # 배경 이미지 표시
    screen.blit(top_ui, (start_x - 10, start_y - 10))

    # 텍스트 리스트 초기화 (웨이브, 골드, 라이프)
    texts = [
        font.render(f"Wave: {wave}", True, BLACK),
        font.render(f"Gold: {gold}", True, BLACK),
        font.render(f"Life: {life}", True, BLACK),
    ]

    # 다음 웨이브 텍스트 추가
    if wave_pause:
        # 남은 시간 계산
        remaining_time = max(0, wave_pause_duration - (pygame.time.get_ticks() - wave_pause_timer))
        remaining_seconds = remaining_time // 1000  # 초 단위로 변환
        next_wave_text = font.render(f"Next Wave: {remaining_seconds}s", True, BLACK)
    else:
        next_wave_text = font.render("Next Wave: --", True, BLACK)
    texts.append(next_wave_text)  # 리스트에 추가

    # 텍스트를 일정 간격으로 배치
    y_offset = 50  # 첫 텍스트의 초기 Y 위치
    for text in texts:
        screen.blit(text, (start_x + 30, start_y + y_offset))
        y_offset += hud_padding  # 다음 텍스트의 위치를 업데이트


def handle_wave_logic():
    """웨이브 관리 로직"""
    global wave, enemies_spawned, wave_pause, wave_pause_timer, last_spawn_time, enemy_spawn_interval

    # 웨이브 대기 상태 처리
    if wave_pause:
        remaining_time = pygame.time.get_ticks() - wave_pause_timer
        if remaining_time >= wave_pause_duration:  # 대기 시간이 끝난 경우
            wave_pause = False  # 대기 상태 종료
            wave_pause_timer = 0  # 대기 타이머 초기화
            wave += 1  # 다음 웨이브로 진행
            enemies_spawned = 0  # 생성된 적 수 초기화
            last_spawn_time = pygame.time.get_ticks()  # 적 생성 시작 시간 초기화
            print(f"Wave {wave} 시작!")  # 디버깅 메시지
        return  # 대기 중에는 더 이상 진행하지 않음

    # 적 생성 처리 (한 번에 여러 마리씩 생성)
    if enemies_spawned < max_enemies_per_wave:
        current_time = pygame.time.get_ticks()
        if current_time - last_spawn_time >= enemy_spawn_interval:  # 생성 간격 확인
            zombies_per_batch = 2  # 한 번에 생성할 좀비 수
            for _ in range(zombies_per_batch):
                if enemies_spawned < max_enemies_per_wave:  # 총 좀비 수 체크
                    enemies.append(Enemy(path_coords))  # 적 생성
                    enemies_spawned += 1
                    print(f"적 생성: {enemies_spawned}/{max_enemies_per_wave}")  # 디버깅 메시지
            last_spawn_time = current_time  # 마지막 생성 시간 갱신
            print(f"last_spawn_time 갱신: {last_spawn_time}")  # 디버깅 메시지

    # 좀비 모두 제거 후 대기 상태로 전환
    if enemies_spawned == max_enemies_per_wave:
        if not enemies:  # 적 리스트가 비어 있으면 (모든 적이 제거됨)
            if wave_pause_timer == 0:  # 대기 타이머가 설정되지 않은 경우
                wave_pause_timer = pygame.time.get_ticks()  # 대기 타이머 시작
                wave_pause = True
                print("모든 좀비 제거됨. 대기 상태 진입.")  # 디버깅 메시지

def draw_tower_ui():
    """화면 왼쪽에 타워 선택 UI를 그립니다."""
    # 배경 이미지 그리기
    screen.blit(side_ui, (tower_ui_rect.x, tower_ui_rect.y))

    y_offset = tower_ui_rect.y + 20  # 타워 아이템 시작 위치

    for tower in TOWER_TYPES:
        # 타워 이미지 로드 및 크기 조정
        tower_image = pygame.image.load(tower["image_path"]).convert_alpha()
        tower_image = pygame.transform.scale(tower_image, (200, 100))

        # 타워 이미지 그리기
        screen.blit(tower_image, (tower_ui_rect.x + 40, y_offset))

        # 타워 이름과 비용 텍스트를 이미지 바로 아래에 표시
        tower_text = font.render(f"{tower['name']} (${tower['cost']})", True, BLACK)
        screen.blit(tower_text, (tower_ui_rect.x + 40, y_offset + 110))  # 이미지 아래 10px 간격

        y_offset += 100 + 50  # 이미지 높이(100) + 텍스트 높이 및 간격(50)


def handle_tower_ui_events(event):
    """타워 UI와 드래그 앤 드롭 이벤트를 처리합니다."""
    global selected_tower, gold

    # 화면 크기와 설치 가능 영역 정의
    INSTALLABLE_AREA = pygame.Rect(0, 0, 1300, 700)  # 설치 가능한 영역 (1300x700)

    # 경로 영역 정의
    path_blocks = [(x * block_size, y * block_size) for x, y in path_coords]  # 경로를 픽셀 좌표로 변환

    if event.type == pygame.MOUSEBUTTONDOWN:
        mouse_x, mouse_y = event.pos
        y_offset = tower_ui_rect.y + 20

        for tower in TOWER_TYPES:
            # 타워 이미지의 클릭 영역 정의
            tower_rect = pygame.Rect(tower_ui_rect.x + 40, y_offset, 200, 100)  # 이미지 크기에 맞게 조정
            if tower_rect.collidepoint(mouse_x, mouse_y):  # 클릭된 경우
                if gold >= tower["cost"]:  # 골드가 충분한지 확인
                    selected_tower = tower
            y_offset += 100 + 50  # 이미지와 텍스트 높이 + 간격

    elif event.type == pygame.MOUSEBUTTONUP and selected_tower:
        mouse_x, mouse_y = event.pos
        grid_x = (mouse_x // block_size) * block_size
        grid_y = (mouse_y // block_size) * block_size

        # 설치 가능한 영역과 경로 체크
        if INSTALLABLE_AREA.collidepoint(mouse_x, mouse_y):  # 드롭 위치가 설치 가능 영역인지 확인
            if (grid_x, grid_y) not in path_blocks:  # 경로 위에 설치되지 않도록 확인
                if (grid_x, grid_y) not in [(tower.x, tower.y) for tower in towers]:  # 타워 중복 설치 방지
                    towers.append(Tower(grid_x, grid_y, selected_tower["type"]))  # 타워 설치
                    gold -= selected_tower["cost"]  # 비용 차감
                else:
                    print("중복 설치 불가")
            else:
                print("경로 위에는 설치할 수 없습니다.")  # 디버깅 메시지
        else:
            print("설치 불가능한 영역입니다.")  # 디버깅 메시지

        selected_tower = None  # 선택된 타워 초기화


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
        
        
def handle_game_events():
    global current_screen, wave_pause, wave_pause_timer, enemies_spawned  # 전역 변수 선언

    for event in pygame.event.get():
        if event.type == pygame.QUIT:  # 게임 종료
            pygame.quit()
            sys.exit()

        if current_screen == "start":  # 시작 화면 처리
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = event.pos
                button_rect = draw_start_screen()
                if button_rect.collidepoint(mouse_pos):
                    stop_bgm()
                    wave_pause = True  # 대기 상태로 전환
                    wave_pause_timer = pygame.time.get_ticks()  # 대기 타이머 시작
                    current_screen = "game"
                    
        elif current_screen == "game":  # 게임 화면 처리
            handle_tower_ui_events(event)  # 타워 UI 관련 이벤트 처리

            if event.type == ENEMY_SPAWN_EVENT and enemies_spawned < max_enemies_per_wave:
                enemies.append(Enemy(path_coords))  # 새로운 적 생성
                enemies_spawned += 1
# BGM 재생 함수
def play_start_bgm():
    pygame.mixer.music.load(start_bgm_path)  # 배경 음악 로드
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
def main():
    global current_screen, gold
    # 게임 메인 루프
    play_start_bgm()  # 게임 시작 시 BGM 재생
    # 게임 메인 루프
    while True:
        screen.fill(WHITE)  # 화면 초기화
        handle_game_events()


        # 화면 전환
        if current_screen == "start":
            draw_start_screen()
        elif current_screen == "game":
            draw_game_screen()
            draw_hud()  # HUD 표시
            draw_tower_ui()  # 타워 선택 UI 그리기
            handle_game_logic()  # 게임 로직 처리
            handle_wave_logic() # 웨이브 로직 처리
            draw_game_elements()  # 적 및 타워 그리기

        pygame.display.flip()  # 화면 업데이트
        clock.tick(60)  # FPS 설정
if __name__ == "__main__":
    main() 
