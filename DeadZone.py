import tkinter as tk
import time
import threading
from tkinter import messagebox

class TowerDefenseGame:
    def __init__(self, root):
        self.root = root
        self.root.title("DEAD ZONE")
        self.root.geometry("1600x900")

        # 이미지 로드
        self.start_page_bg = tk.PhotoImage(file="startpage.png")
        self.game_over_page_bg = tk.PhotoImage(file="gameoverpage.png")

        # 메인 화면
        self.main_frame = tk.Frame(self.root, width=1600, height=900, bg="white")
        self.main_frame.pack()
        self.create_main_screen()

        # 게임 화면 변수
        self.canvas = None
        self.block_size = 50
        self.grid_rows = 18
        self.grid_cols = 32
        self.towers = []
        self.enemies = []
        self.wave_number = 0
        self.gold = 100
        self.life = 10
        self.path_coords = self.generate_path()
        self.game_over_flag = False
        
    def create_main_screen(self):
        """시작 화면 생성"""
        self.main_canvas = tk.Canvas(self.main_frame, width=1600, height=900)
        self.main_canvas.pack()
        self.main_canvas.create_image(0, 0, anchor="nw", image=self.start_page_bg)

        title = tk.Label(self.main_canvas, text="DEAD ZONE", font=("Arial", 50), bg="#000000", fg="white")
        title.place(x=600, y=200)

        start_button = tk.Button(self.main_canvas, text="게임 시작", font=("Arial", 20),
                                 command=self.start_game_screen, width=15, height=2, bg="#87ceeb")
        start_button.place(x=700, y=600)
    def start_game_screen(self):
        """게임 화면으로 전환"""
        self.main_frame.destroy()
        self.canvas = tk.Canvas(self.root, width=1600, height=900, bg="white")
        self.canvas.pack()

        self.create_grid()
        self.create_path()

        self.wave_label = tk.Label(self.root, text=f"Wave: {self.wave_number}", font=("Arial", 20))
        self.wave_label.place(x=10, y=10)

        self.gold_label = tk.Label(self.root, text=f"Gold: {self.gold}", font=("Arial", 20))
        self.gold_label.place(x=750, y=10)

        self.life_label = tk.Label(self.root, text=f"Life: {self.life}", font=("Arial", 20))
        self.life_label.place(x=1450, y=10)

        self.enemy_health_label = tk.Label(self.root, text="Max Enemy HP: 0", font=("Arial", 20))
        self.enemy_health_label.place(x=1300, y=50)

        self.create_tower_buttons()
        self.canvas.bind("<Button-1>", self.place_tower)

        threading.Thread(target=self.initial_wait, daemon=True).start()
        self.start_attack_loop()  # 공격 루프 시작

    def initial_wait(self):
        """게임 시작 전 대기 시간 제공"""
        for i in range(4, 0, -1):
            self.wave_label.config(text=f"Wave starts in: {i} seconds")
            time.sleep(1)
        self.start_waves()

    def create_grid(self):
        """게임 그리드 생성"""
        for row in range(self.grid_rows):
            for col in range(self.grid_cols):
                x1 = col * self.block_size
                y1 = row * self.block_size
                x2 = x1 + self.block_size
                y2 = y1 + self.block_size
                self.canvas.create_rectangle(x1, y1, x2, y2, fill="#f0f0f0", outline="#d0d0d0")

    def generate_path(self):
        """Z 모양 경로 생성 (커브 8개, 경로를 우측으로 이동)"""
        base_path = [
            (5, 1), (6, 1), (7, 1), (8, 1), (9, 1), (10, 1), (11, 1), (12, 1),
            (12, 2), (12, 3), (11, 3), (10, 3), (9, 3), (8, 3), (7, 3), (6, 3),
            (6, 4), (6, 5), (7, 5), (8, 5), (9, 5), (10, 5), (11, 5), (12, 5),
            (12, 6), (12, 7), (11, 7), (10, 7), (9, 7), (8, 7), (7, 7), (6, 7),
            (6, 8), (6, 9), (7, 9), (8, 9), (9, 9), (10, 9), (11, 9), (12, 9),
            (12, 10), (12, 11), (11, 11), (10, 11), (9, 11), (8, 11), (7, 11), (6, 11),
            (6, 12), (6, 13), (7, 13), (8, 13), (9, 13), (10, 13), (11, 13), (12, 13),
            (12, 14), (12, 15), (11, 15), (10, 15), (9, 15), (8, 15), (7, 15), (6, 15)
        ]
        # 모든 열 값을 5씩 증가
        adjusted_path = [(col + 5, row) for col, row in base_path]
        return adjusted_path




    def create_path(self):
        """경로 표시"""
        for col, row in self.path_coords:
            x1 = col * self.block_size
            y1 = row * self.block_size
            x2 = x1 + self.block_size
            y2 = y1 + self.block_size
            self.canvas.create_rectangle(x1, y1, x2, y2, fill="#a0a0a0", outline="")

        # 시작점과 끝점 표시
        start_col, start_row = self.path_coords[0]
        end_col, end_row = self.path_coords[-1]
        self.canvas.create_text(start_col * self.block_size + 25, start_row * self.block_size + 25,
                                text="START", fill="green", font=("Arial", 12))
        self.canvas.create_text(end_col * self.block_size + 25, end_row * self.block_size + 25,
                                text="END", fill="red", font=("Arial", 12))


    def create_tower_buttons(self):
        """타워 선택 버튼 생성"""
        button_frame = tk.Frame(self.root)
        button_frame.place(x=1200, y=800)

        gun_button = tk.Button(button_frame, text="총기 타워", font=("Arial", 15), command=lambda: self.select_tower("gun"), width=10, bg="#add8e6")
        gun_button.grid(row=0, column=0, padx=10)

        mine_button = tk.Button(button_frame, text="지뢰 타워", font=("Arial", 15), command=lambda: self.select_tower("mine"), width=10, bg="#ffa07a")
        mine_button.grid(row=0, column=1, padx=10)

    def select_tower(self, tower_type):
        """타워 타입 선택"""
        self.selected_tower_type = tower_type
        if tower_type == "gun":
            messagebox.showinfo("Tower Selected", "총기 타워가 선택되었습니다.")
        elif tower_type == "mine":
            messagebox.showinfo("Tower Selected", "지뢰 타워가 선택되었습니다.")

    def place_tower(self, event):
        """타워 배치"""
        if self.selected_tower_type is None:
            messagebox.showwarning("No Tower Selected", "먼저 타워를 선택하세요!")
            return

        col = event.x // self.block_size
        row = event.y // self.block_size
        x1 = col * self.block_size
        y1 = row * self.block_size
        x2 = x1 + self.block_size
        y2 = y1 + self.block_size

        if (col, row) in self.path_coords:
            return

        for tower in self.towers:
            if tower["col"] == col and tower["row"] == row:
                self.upgrade_tower(tower)
                return

        if self.gold >= 50:
            if messagebox.askyesno("Tower Placement", "타워를 설치하시겠습니까?"):
                if self.selected_tower_type == "gun":
                    tower_id = self.canvas.create_rectangle(x1, y1, x2, y2, fill="#5f9ea0", outline="black")
                    self.towers.append({
                        "col": col,
                        "row": row,
                        "id": tower_id,
                        "type": "gun",
                        "damage": 20,
                        "attack_speed": 0.2,
                        "range": 2,
                        "last_attack_time": 0
                    })
                elif self.selected_tower_type == "mine":
                    tower_id = self.canvas.create_rectangle(x1, y1, x2, y2, fill="#ffa500", outline="black")
                    self.towers.append({
                        "col": col,
                        "row": row,
                        "id": tower_id,
                        "type": "mine",
                        "damage": 7,
                        "attack_speed": 0.5,
                        "range": 1,
                        "last_attack_time": 0
                    })

                self.gold -= 50
                self.gold_label.config(text=f"Gold: {self.gold}")

                threading.Thread(target=self.attack_enemies, args=(self.towers[-1],), daemon=True).start()
        else:
            messagebox.showerror("Error", "골드가 부족합니다!")


    def upgrade_tower(self, tower):
        """타워 승급"""
        cost = 200 * (2 ** (tower.get("upgrade_level", 0)))
        if self.gold >= cost:
            if messagebox.askyesno("Upgrade Tower", f"타워를 승급하시겠습니까? {cost} 골드 필요합니다."):
                tower["damage"] +=10
                tower["attack_speed"] /= 1.2
                self.gold -= cost
                self.gold_label.config(text=f"Gold: {self.gold}")
                tower["upgrade_level"] = tower.get("upgrade_level", 0) + 1
                color = "#4b0082" if tower["type"] == "gun" else "#8b0000"
                self.canvas.itemconfig(tower["id"], fill=color)
        else:
            messagebox.showerror("Error", "골드가 부족합니다!")


    def start_attack_loop(self):
        """타워의 공격 루프를 실행"""
        for tower in self.towers:
            self.attack_enemies(tower)
        self.root.after(100, self.start_attack_loop)  # 100ms 후 반복 실행

    def attack_enemies(self, tower):
        """타워가 적을 공격"""
        current_time = time.time()  # 현재 시간 (초 단위)
    
        # 마지막 공격 시간과 공격 속도를 기반으로 공격 여부 결정
        if current_time - tower.get("last_attack_time", 0) < tower["attack_speed"]:
            return  # 공격할 시간이 되지 않았으면 종료

        for enemy in self.enemies[:]:
            if enemy["health"] > 0:
                e_col, e_row = self.path_coords[enemy["path_index"]] if enemy["path_index"] < len(self.path_coords) else (-1, -1)
                if abs(e_col - tower["col"]) <= tower["range"] and abs(e_row - tower["row"]) <= tower["range"]:
                    enemy["health"] -= tower["damage"]
                    self.update_health_bar(enemy)
                    if enemy["health"] <= 0:
                        self.canvas.delete(enemy["id"])
                        self.canvas.delete(enemy["health_bar"])
                        self.enemies.remove(enemy)
                        self.gold += 2
                        self.gold_label.config(text=f"Gold: {self.gold}")
                    tower["last_attack_time"] = current_time  # 공격 시간을 업데이트
                    break  # 한 번에 한 적만 공격


    def update_health_bar(self, enemy):
        """체력바 업데이트"""
        col, row = self.path_coords[enemy["path_index"]]
        x1 = col * self.block_size + 10
        y1 = row * self.block_size - 5
        x2 = x1 + 30 * (enemy["health"] / enemy["max_health"])
        self.canvas.coords(enemy["health_bar"], x1, y1, x2, y1 + 3)

    def start_waves(self):
        """웨이브 시작"""
        while True:
            self.wave_number += 1
            self.wave_label.config(text=f"Wave: {self.wave_number}")
            self.spawn_wave()
            time.sleep(15)  # 다음 웨이브 대기

    def spawn_wave(self):
        """적 웨이브 생성"""
        base_health = 40
        enemy_health = base_health * (1.1 ** (self.wave_number - 1))  # 일반 적 체력
        self.current_wave_max_health = enemy_health # 최대 체력값 출력용
        new_wave_enemies = []  # 새 웨이브 적들을 임시로 저장

        for i in range(40):  # 각 웨이브에 40마리 적 생성
            enemy = {
                "id": self.canvas.create_oval(
                    self.path_coords[0][0] * self.block_size + 10,
                    self.path_coords[0][1] * self.block_size + 10,
                    self.path_coords[0][0] * self.block_size + 40,
                    self.path_coords[0][1] * self.block_size + 40,
                    fill="#ff4500", outline="black"
                ),
                "health": enemy_health,
                "max_health": enemy_health,
                "path_index": 0,
                "health_bar": self.canvas.create_rectangle(0, 0, 0, 0, fill="green", outline="black")
            }
            new_wave_enemies.append(enemy)  # 새 웨이브에 추가
            self.enemies.append(enemy)      # 전체 적 리스트에 추가
            threading.Thread(target=self.move_enemy, args=(enemy, 0.03), daemon=True).start()  # 적 이동
            time.sleep(0.3)  # 적 생성 간격
        
        self.update_max_health_label()

    # 최대 체력값 출력용
    def update_max_health_label(self):
        """현재 웨이브 적 최대 체력을 업데이트하여 라벨에 표시"""
        if hasattr(self, 'current_wave_max_health'):
            self.enemy_health_label.config(
                text=f"Max Enemy HP: {self.current_wave_max_health}"
            )

    def move_enemy(self, enemy, speed):
        """적 이동 (부드럽게)"""
        while enemy in self.enemies:
            if enemy["path_index"] < len(self.path_coords) - 1:
                # 시작 위치와 목표 위치 계산
                start_col, start_row = self.path_coords[enemy["path_index"]]
                end_col, end_row = self.path_coords[enemy["path_index"] + 1]

                start_x = start_col * self.block_size + 10
                start_y = start_row * self.block_size + 10
                end_x = end_col * self.block_size + 10
                end_y = end_row * self.block_size + 10

                # 부드러운 이동 (10단계)
                for step in range(10):
                    dx = (end_x - start_x) / 10
                    dy = (end_y - start_y) / 10
                    self.canvas.move(enemy["id"], dx, dy)
                    self.canvas.move(enemy["health_bar"], dx, dy)
                    time.sleep(speed)

                enemy["path_index"] += 1
            else:
                # 적이 경로를 완주한 경우
                if enemy in self.enemies:
                    self.enemies.remove(enemy)  # 리스트에서 적 제거
                    self.canvas.delete(enemy["id"])
                    self.canvas.delete(enemy["health_bar"])  # 체력바 삭제
                    self.life -= 1  # 라이프 감소
                    self.life_label.config(text=f"Life: {self.life}")

                # 게임 오버 체크
                if self.life <= 0:
                    self.game_over()
                break
    def game_over(self):
        """게임 종료 처리: 게임 오버 화면으로 전환"""
        if self.game_over_flag:
            return

        self.game_over_flag = True
        self.enemies = []
        self.towers = []

        self.canvas.destroy()  # 게임 캔버스 제거
        self.create_game_over_screen()

    def create_game_over_screen(self):
        """게임 오버 화면 생성"""
        self.game_over_canvas = tk.Canvas(self.root, width=1600, height=900)
        self.game_over_canvas.pack()
        self.game_over_canvas.create_image(0, 0, anchor="nw", image=self.game_over_page_bg)

        retry_button = tk.Button(self.game_over_canvas, text="재도전", font=("Arial", 20), command=self.reset_game, bg="#87ceeb", width=15, height=2)
        retry_button.place(x=600, y=600)

        home_button = tk.Button(self.game_over_canvas, text="홈으로", font=("Arial", 20), command=self.go_to_home, bg="#ffa07a", width=15, height=2)
        home_button.place(x=900, y=600)

    def reset_game(self):
        """게임을 리셋하고 처음부터 시작"""
        self.game_over_canvas.destroy()
        self.wave_number = 0
        self.gold = 100
        self.life = 10
        self.towers = []
        self.enemies = []
        self.game_over_flag = False
        self.start_game_screen()

    def go_to_home(self):
        """홈 화면으로 이동"""
        self.game_over_canvas.destroy()
        self.main_frame = tk.Frame(self.root, width=1600, height=900, bg="white")
        self.main_frame.pack()
        self.create_main_screen()


if __name__ == "__main__":
    root = tk.Tk()
    game = TowerDefenseGame(root)
    root.mainloop()