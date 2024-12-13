import pygame

pygame.init()

def load_images():
    """이미지 로드 및 초기화"""
    return {
        "start_bg": pygame.image.load("startpage.png"),
        "start_button": pygame.transform.scale(pygame.image.load("startButton.png"), (300, 254)),
        "game_over_bg" : pygame.transform.scale(pygame.image.load("game_over.png"), (1600, 900)),
        "zombie": pygame.image.load("enemy.png"),
        "boss1": pygame.image.load("boss1.png"),
        "boss2": pygame.image.load("boss2.png"),
        "boss3": pygame.image.load("boss3.png"),
        "boss4": pygame.image.load("boss4.png"),
        "top_ui": pygame.image.load("ui4.png"),
        "side_ui": pygame.image.load("ui5.png"),
        "bottom_ui": pygame.image.load("ui3.png"),
        "basecamp":  pygame.transform.scale(pygame.image.load("basecamp.png"), (250, 300)),       
        #gun
        "gun_tower": pygame.image.load("gun_tower.png"),
        "gun_tower_lv2": pygame.image.load("gun_tower_lv2.png"),
        "gun_tower_lv3": pygame.image.load("gun_tower_lv3.png"),
        "gun_tower_lv4": pygame.image.load("gun_tower_lv4.png"),
        #mine
        "mine_tower": pygame.image.load("mine_tower.png"),
        "mine_tower_lv2": pygame.image.load("mine_tower_lv2.png"),
        "mine_tower_lv3": pygame.image.load("mine_tower_lv3.png"),
        "mine_tower_lv4": pygame.image.load("mine_tower_lv4.png"),
        #supply
        "supply_tower": pygame.image.load("supply_tower.png"),
        "s_enemy1": pygame.image.load("s_enemy1.png"),
        "s_enemy2": pygame.image.load("s_enemy2.png"),
        "s_enemy3": pygame.image.load("s_enemy3.png"),
        "s_enemy4": pygame.image.load("s_enemy4.png"),
        "tile_image1": [
            pygame.image.load("block1.png"),
            pygame.image.load("block2.png"),
            pygame.image.load("block3.png"),
            pygame.image.load("block4.png"),
        ],
        "tile_image2": [
            pygame.image.load("block5.png"),
            pygame.image.load("block6.png"),
            pygame.image.load("block7.png"),
            pygame.image.load("block8.png"),
        ],
        "tile_image3": [
            pygame.image.load("block9.png"),
            pygame.image.load("block10.png"),
            pygame.image.load("block11.png"),
            pygame.image.load("block12.png"),
        ],
        "tile_image4": [
            pygame.image.load("block13.png"),
            pygame.image.load("block14.png"),
            pygame.image.load("block15.png"),
            pygame.image.load("block16.png"),
        ],
        "e_block1": pygame.image.load("e_block1.png"),
        "e_block2": pygame.image.load("e_block2.png"),
        "e_block3": pygame.image.load("e_block3.png"),
        "e_block4": pygame.image.load("e_block4.png"),
    }

def optimize_images(images):
    """이미지 최적화 (convert_alpha 호출)"""
    for key, value in images.items():
        if isinstance(value, list):
            images[key] = [img.convert_alpha() for img in value]
        else:
            images[key] = value.convert_alpha()

def load_audio():
    """오디오 로드"""
    return {
        "intro": "인트로.mp3",
        "spawn": pygame.mixer.Sound("좀비1.mp3"),
        "death": pygame.mixer.Sound("좀비사망.mp3"),
        "gun_sound": pygame.mixer.Sound("총3.mp3"),
        "mine_sound": pygame.mixer.Sound("지뢰폭발1.mp3"),
        "boss": "보스.mp3",

    }
