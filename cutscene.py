import pygame
import json

class CutsceneManager:
    def __init__(self, screen, font, width, height):
        self.screen = screen
        self.font = font
        self.width = width
        self.height = height
        self.cutscenes = []  # 현재 웨이브의 컷씬 데이터를 저장
        self.current_cutscene_index = 0

    def set_font(self, font_path, size):
        """폰트를 설정하는 메서드"""
        self.font = pygame.font.Font(font_path, size)

    def load_cutscenes_for_wave(self, file_path, wave):
        """
        통합 JSON 파일에서 특정 웨이브의 컷씬 데이터를 로드
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                all_cutscenes = json.load(f)

            wave_key = f"{wave}"  # 웨이브 키 (예: "11", "21")
            if wave_key in all_cutscenes:
                self.cutscenes = all_cutscenes[wave_key]  # 해당 웨이브의 컷씬 데이터 저장
                self.current_cutscene_index = 0  # 컷씬 인덱스 초기화
                print(f"Wave {wave} 컷씬 로드 완료.")
            else:
                self.cutscenes = []  # 해당 웨이브에 컷씬 데이터가 없을 경우 초기화
                print(f"Wave {wave} 컷씬 데이터가 없습니다.")
        except FileNotFoundError:
            print(f"컷씬 파일 {file_path}을 찾을 수 없습니다.")
            self.cutscenes = []
        except json.JSONDecodeError:
            print(f"컷씬 파일 {file_path}의 JSON 구문 오류.")
            self.cutscenes = []

    def has_cutscene_for_wave(self, wave):
        """
        특정 웨이브에 대해 컷씬 데이터가 존재하는지 확인
        """
        try:
            with open("cutscene_data.json", "r", encoding="utf-8") as f:
                all_cutscenes = json.load(f)
            return str(wave) in all_cutscenes  # 해당 웨이브가 컷씬 데이터에 있는지 확인
        except FileNotFoundError:
            print("컷씬 데이터 파일을 찾을 수 없습니다.")
            return False
        except json.JSONDecodeError:
            print("컷씬 데이터 파일의 JSON 구문 오류.")
            return False

    def draw_cutscene(self):
        """
        현재 컷씬을 화면에 그리는 메서드
        """
        if self.current_cutscene_index >= len(self.cutscenes):
            return  # 모든 컷씬이 끝난 경우

        # 현재 컷씬 데이터
        cutscene = self.cutscenes[self.current_cutscene_index]

        # 이미지 로드 및 크기 조정
        if "image" in cutscene:
            try:
                image_path = cutscene["image"]
                image = pygame.image.load(image_path)
                scaled_image = pygame.transform.scale(image, (self.width, self.height))
                self.screen.blit(scaled_image, (0, 0))
            except pygame.error:
                print(f"이미지 {image_path} 로드 오류.")

        # 텍스트 출력
        if "text" in cutscene:
            text = cutscene["text"]
            text_surface = self.font.render(text, True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=(self.width // 2, self.height - 50))
            self.screen.blit(text_surface, text_rect)

    def next_cutscene(self):
        """
        다음 컷씬으로 이동
        """
        if self.current_cutscene_index < len(self.cutscenes) - 1:
            self.current_cutscene_index += 1
            print(f"컷씬 {self.current_cutscene_index + 1}로 이동.")
        else:
            print("더 이상 컷씬이 없습니다.")
            self.cutscenes = []  # 컷씬 데이터를 초기화하여 종료 상태 설정

    def is_cutscene_active(self):
        """
        컷씬이 아직 활성 상태인지 확인
        """
        return self.current_cutscene_index < len(self.cutscenes)
