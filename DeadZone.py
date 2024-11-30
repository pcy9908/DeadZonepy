import pygame
import sys
import random

# 게임 초기 설정
pygame.init()
WIDTH, HEIGHT = 1600, 900
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("DEAD ZONE")

# 색상 정의
WHITE = (255, 255, 255)
GRAY = (160, 160, 160)
LIGHT_BLUE = (173, 216, 230)
LIGHT_RED = (255, 160, 122)
DARK_GRAY = (96, 96, 96)

# 이미지 로드 및 크기 조정
start_bg = pygame.image.load("startpage.png")
start_button = pygame.image.load("startButton.png")
start_button = pygame.transform.scale(start_button, (300, 254))

# 타워 관련 이미지
gun_tower = pygame.image.load("gun_tower.png")
mine_tower = pygame.image.load("mine_tower.png")

# 게임 변수
block_size = 50
grid_rows, grid_cols = 18, 32

# 적 경로 설정
path_coords = [
    (6, 1), (7, 1), (8, 1), (9, 1), (10, 1), (11, 1), (12, 1),
    (12, 2), (12, 3), (11, 3), (10, 3), (9, 3), (8, 3), (7, 3), (6, 3),
    (6, 4), (6, 5), (7, 5), (8, 5), (9, 5), (10, 5), (11, 5), (12, 5),
    (12, 6), (12, 7), (11, 7), (10, 7), (9, 7), (8, 7), (7, 7), (6, 7),
    (6, 8), (6, 9), (7, 9), (8, 9), (9, 9), (10, 9), (11, 9), (12, 9),
    (12, 10), (12, 11), (11, 11), (10, 11), (9, 11), (8, 11), (7, 11), (6, 11),
    (6, 12), (6, 13), (7, 13), (8, 13), (9, 13), (10, 13), (11, 13), (12, 13),
    (12, 14), (12, 15), (11, 15), (10, 15), (9, 15), (8, 15), (7, 15), (6, 15)
]
path_coords = [(col + 5, row) for col, row in path_coords]

# 화면 전환 변수
current_screen = "start"

# 적 클래스
class Enemy:
    def __init__(self, path_coords, speed=2):
        self.path_coords = path_coords
        self.index = 0
        self.x, self.y = path_coords[self.index]
        self.x *= block_size
        self.y *= block_size
        self.speed = speed
        self.health = 100
        self.alive = True

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

    def draw(self):
        pygame.draw.circle(screen, LIGHT_RED, (int(self.x + block_size // 2), int(self.y + block_size // 2)), block_size // 3)
        health_bar_width = block_size
        health_ratio = self.health / 100
        pygame.draw.rect(screen, DARK_GRAY, (self.x, self.y - 10, health_bar_width, 5))
        pygame.draw.rect(screen, LIGHT_RED, (self.x, self.y - 10, health_bar_width * health_ratio, 5))

# 타워 클래스
class Tower:
    def __init__(self, x, y, range_=3, damage=20):
        self.x, self.y = x, y
        self.range = range_ * block_size
        self.damage = damage

    def draw(self):
        pygame.draw.rect(screen, LIGHT_BLUE, (self.x, self.y, block_size, block_size))

    def attack(self, enemies):
        for enemy in enemies:
            if enemy.alive:
                dist = ((enemy.x - self.x) ** 2 + (enemy.y - self.y) ** 2) ** 0.5
                if dist <= self.range:
                    enemy.health -= self.damage
                    if enemy.health <= 0:
                        enemy.alive = False

# 적 및 타워 리스트
enemies = []
towers = []

# 적 생성 이벤트
ENEMY_SPAWN_EVENT = pygame.USEREVENT + 1
pygame.time.set_timer(ENEMY_SPAWN_EVENT, 2000)

# 화면 그리기 함수
def draw_start_screen():
    screen.blit(start_bg, (0, 0))
    button_rect = start_button.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 100))
    screen.blit(start_button, button_rect.topleft)
    return button_rect

def draw_game_screen():
    screen.fill(WHITE)
    draw_grid()
    draw_path()

def draw_grid():
    for row in range(grid_rows):
        for col in range(grid_cols):
            x1, y1 = col * block_size, row * block_size
            pygame.draw.rect(screen, GRAY, (x1, y1, block_size, block_size), 1)

def draw_path():
    for col, row in path_coords:
        x1, y1 = col * block_size, row * block_size
        pygame.draw.rect(screen, DARK_GRAY, (x1, y1, block_size, block_size))

def handle_game_logic():
    for enemy in enemies[:]:
        enemy.move()
        if not enemy.alive:
            enemies.remove(enemy)

    for tower in towers:
        tower.attack(enemies)

def draw_game_elements():
    for enemy in enemies:
        enemy.draw()

    for tower in towers:
        tower.draw()

def main():
    global current_screen
    clock = pygame.time.Clock()

    while True:
        screen.fill(WHITE)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if current_screen == "start":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_pos = event.pos
                    button_rect = draw_start_screen()
                    if button_rect.collidepoint(mouse_pos):
                        current_screen = "game"

            elif current_screen == "game":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_x, mouse_y = event.pos
                    grid_x = (mouse_x // block_size) * block_size
                    grid_y = (mouse_y // block_size) * block_size
                    if (grid_x, grid_y) not in [(tower.x, tower.y) for tower in towers]:
                        towers.append(Tower(grid_x, grid_y))

                if event.type == ENEMY_SPAWN_EVENT:
                    enemies.append(Enemy(path_coords))

        if current_screen == "start":
            draw_start_screen()
        elif current_screen == "game":
            draw_game_screen()
            handle_game_logic()
            draw_game_elements()

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()
