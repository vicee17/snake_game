import sys
import random
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel,
    QMessageBox, QDialog, QPushButton, QComboBox, QHBoxLayout
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import (
    QPainter, QColor, QFont, QAction, QPainterPath, QPen
)

CELL_SIZE = 20
GAME_SPEED_MS = 150

class SettingsDialog(QDialog):
    def __init__(self, current_width: int, current_height: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки")
        self.setModal(True)

        self.combo = QComboBox()
        self.combo.addItems(["600 x 400", "800 x 600", "1024 x 768"])

        current_text = f"{current_width} x {current_height}"
        idx = self.combo.findText(current_text)
        if idx != -1:
            self.combo.setCurrentIndex(idx)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Выберите размер окна:"))
        layout.addWidget(self.combo)

        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Отмена")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def get_size(self):
        text = self.combo.currentText()
        w, h = map(int, text.split(" x "))
        return w, h

class SnakeGameWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.snake = []
        self.food = (0, 0)
        self.direction = (CELL_SIZE, 0)
        self.game_over = False
        self.score = 0
        self.timer = None
        self.countdown = 0
        self.countdown_timer = None

    def reset_game(self):
        if self.timer:
            self.timer.stop()
        if self.countdown_timer:
            self.countdown_timer.stop()

        self.snake = [(100, 100), (80, 100), (60, 100)]
        self.food = self._spawn_food()
        self.direction = (CELL_SIZE, 0)
        self.game_over = False
        self.score = 0
        self.countdown = 3

        self.update()

        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self._tick_countdown)
        self.countdown_timer.start(1000)

    def _tick_countdown(self):
        self.countdown -= 1
        self.update()
        if self.countdown <= 0:
            self.countdown_timer.stop()
            self.countdown = 0
            self.timer = QTimer()
            self.timer.timeout.connect(self._update_game)
            self.timer.start(GAME_SPEED_MS)

    def _spawn_food(self):
        cols = self.width() // CELL_SIZE
        rows = self.height() // CELL_SIZE
        if cols <= 0 or rows <= 0:
            return (0, 0)
        for _ in range(100):
            x = random.randint(0, cols - 1) * CELL_SIZE
            y = random.randint(0, rows - 1) * CELL_SIZE
            pos = (x, y)
            if pos not in self.snake:
                return pos
        return (0, 0)

    def _update_game(self):
        if self.game_over or not self.snake:
            return

        head_x, head_y = self.snake[0]
        dx, dy = self.direction
        new_head = (head_x + dx, head_y + dy)

        if (new_head[0] < 0 or new_head[0] >= self.width() or
            new_head[1] < 0 or new_head[1] >= self.height()):
            self.game_over = True
            self.timer.stop()
            self.update()
            return

        if new_head in self.snake:
            self.game_over = True
            self.timer.stop()
            self.update()
            return

        self.snake.insert(0, new_head)

        if new_head == self.food:
            self.food = self._spawn_food()
            self.score += 1
        else:
            self.snake.pop()

        self.update()

    def keyPressEvent(self, event):
        if self.game_over:
            if event.key() in (Qt.Key.Key_Space, Qt.Key.Key_Return):
                self.reset_game()
            elif event.key() == Qt.Key.Key_Escape:
                self.parent().back_to_main_menu()
            return

        key = event.key()
        if key == Qt.Key.Key_Left and self.direction != (CELL_SIZE, 0):
            self.direction = (-CELL_SIZE, 0)
        elif key == Qt.Key.Key_Right and self.direction != (-CELL_SIZE, 0):
            self.direction = (CELL_SIZE, 0)
        elif key == Qt.Key.Key_Up and self.direction != (0, CELL_SIZE):
            self.direction = (0, -CELL_SIZE)
        elif key == Qt.Key.Key_Down and self.direction != (0, -CELL_SIZE):
            self.direction = (0, CELL_SIZE)

    def _draw_snake_and_food(self, painter):
        if self.snake:
            radius = CELL_SIZE // 2
            path = QPainterPath()
            points = [(x + radius, y + radius) for x, y in self.snake]
            path.moveTo(points[0][0], points[0][1])
            for px, py in points[1:]:
                path.lineTo(px, py)

            snake_width = radius * 1.6
            pen = QPen(QColor(0, 255, 0), snake_width,
                       cap=Qt.PenCapStyle.RoundCap,
                       join=Qt.PenJoinStyle.RoundJoin)
            painter.strokePath(path, pen)

            head_x, head_y = self.snake[0]
            cx, cy = head_x + radius, head_y + radius
            head_radius = radius * 1.1
            painter.setBrush(QColor(0, 200, 0))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(cx - head_radius, cy - head_radius, head_radius * 2, head_radius * 2)

            eye_size = max(2, int(radius // 3))
            dx, dy = self.direction
            painter.setBrush(QColor(255, 255, 255))
            if dx == CELL_SIZE:
                painter.drawEllipse(cx + head_radius//2, cy - head_radius//3, eye_size, eye_size)
                painter.drawEllipse(cx + head_radius//2, cy + head_radius//3 - eye_size, eye_size, eye_size)
            elif dx == -CELL_SIZE:
                painter.drawEllipse(cx - head_radius//2 - eye_size, cy - head_radius//3, eye_size, eye_size)
                painter.drawEllipse(cx - head_radius//2 - eye_size, cy + head_radius//3 - eye_size, eye_size, eye_size)
            elif dy == -CELL_SIZE:
                painter.drawEllipse(cx - head_radius//3, cy - head_radius//2 - eye_size, eye_size, eye_size)
                painter.drawEllipse(cx + head_radius//3 - eye_size, cy - head_radius//2 - eye_size, eye_size, eye_size)
            elif dy == CELL_SIZE:
                painter.drawEllipse(cx - head_radius//3, cy + head_radius//2, eye_size, eye_size)
                painter.drawEllipse(cx + head_radius//3 - eye_size, cy + head_radius//2, eye_size, eye_size)

            painter.setPen(QColor(255, 0, 0))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            tongue_len = 4
            if dx == CELL_SIZE:
                painter.drawLine(cx + head_radius, cy, cx + head_radius + tongue_len, cy)
            elif dx == -CELL_SIZE:
                painter.drawLine(cx - head_radius, cy, cx - head_radius - tongue_len, cy)
            elif dy == -CELL_SIZE:
                painter.drawLine(cx, cy - head_radius, cx, cy - head_radius - tongue_len)
            elif dy == CELL_SIZE:
                painter.drawLine(cx, cy + head_radius, cx, cy + head_radius + tongue_len)

        fx, fy = self.food
        painter.setBrush(QColor(255, 0, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(fx, fy, CELL_SIZE, CELL_SIZE)

        if CELL_SIZE >= 16:
            stem_x = fx + CELL_SIZE // 2
            stem_y = fy + CELL_SIZE // 4
            painter.setPen(QColor(50, 180, 50))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawLine(stem_x, stem_y, stem_x, stem_y - 4)
            painter.setBrush(QColor(50, 200, 50))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(stem_x + 2, stem_y - 6, 4, 3)

    def _draw_score(self, painter):
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Arial", 12))
        painter.drawText(10, 20, f"Счёт: {self.score}")

    def paintEvent(self, event):
          painter = QPainter(self)
          painter.setRenderHint(QPainter.RenderHint.Antialiasing)

          painter.fillRect(self.rect(), QColor(0, 0, 0))

          grid_color = QColor(50, 50, 50)
          painter.setPen(grid_color)
          for x in range(0, self.width(), CELL_SIZE):
              painter.drawLine(x, 0, x, self.height())
          for y in range(0, self.height(), CELL_SIZE):
              painter.drawLine(0, y, self.width(), y)

          if self.game_over and self.countdown == 0:
              painter.setPen(QColor(255, 50, 50))
              painter.setFont(QFont("Arial", 20))
              text = f"Игра окончена!\nСчёт: {self.score}\nНажмите ПРОБЕЛ"
              painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, text)
              return

          if self.countdown > 0:
              painter.setPen(QColor(255, 255, 0))
              painter.setFont(QFont("Arial", 48, QFont.Weight.Bold))
              if self.countdown == 3:
                  text = "Приготовиться!"
              elif self.countdown == 2:
                  text = "2"
              elif self.countdown == 1:
                  text = "1"
              else:
                  text = "Старт!"
              painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, text)

              self._draw_snake_and_food(painter)
              self._draw_score(painter)
              return

          self._draw_snake_and_food(painter)
          self._draw_score(painter)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Змейка")
        self.resize(600, 400)

        self.stack = QWidget()
        self.setCentralWidget(self.stack)
        self.setup_menu()
        self.game_widget = None
        self.menu_bar = self.menuBar()
        self.menu_bar.setVisible(False)

    def setup_menu(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("ЗМЕЙКА")
        title.setFont(QFont("Arial", 32, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: white;")

        btn_start = QPushButton("Новая игра")
        btn_settings = QPushButton("Настройки")
        btn_exit = QPushButton("Выход")

        for btn in (btn_start, btn_settings, btn_exit):
            btn.setFixedWidth(200)
            btn.setFixedHeight(40)

        btn_start.clicked.connect(self.start_game)
        btn_settings.clicked.connect(self.open_settings)
        btn_exit.clicked.connect(self.close)

        layout.addWidget(title)
        layout.addSpacing(40)
        layout.addWidget(btn_start, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(btn_settings, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(btn_exit, alignment=Qt.AlignmentFlag.AlignCenter)

        self.stack.setLayout(layout)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape and self.game_widget:
            self.back_to_main_menu()

    def start_game(self):
        self.game_widget = SnakeGameWidget()
        self.game_widget.reset_game()  
        self.setCentralWidget(self.game_widget)
        self.menu_bar.setVisible(True)
        self.setup_game_menu()

    def setup_game_menu(self):
        self.menu_bar.clear()
        game_menu = self.menu_bar.addMenu("Игра")

        restart_action = QAction("Новая игра", self)
        restart_action.triggered.connect(self.restart_game)
        game_menu.addAction(restart_action)

        settings_action = QAction("Настройки", self)
        settings_action.triggered.connect(self.open_settings_from_game)
        game_menu.addAction(settings_action)

        main_menu_action = QAction("В главное меню", self)
        main_menu_action.triggered.connect(self.back_to_main_menu)
        game_menu.addAction(main_menu_action)

    def restart_game(self):
        if self.game_widget:
            self.game_widget.reset_game()

    def open_settings_from_game(self):
        self.open_settings(in_game=True)

    def open_settings(self, in_game=False):
        try:
            if in_game:
                w, h = self.width(), self.height()
            else:
                w, h = 600, 400
            dialog = SettingsDialog(w, h, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                new_w, new_h = dialog.get_size()
                new_w = (new_w // CELL_SIZE) * CELL_SIZE
                new_h = (new_h // CELL_SIZE) * CELL_SIZE
                self.resize(new_w, new_h)
                if in_game and self.game_widget:
                    self.game_widget.reset_game()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось применить настройки:\n{e}")

    def back_to_main_menu(self):
        if self.game_widget:
            if self.game_widget.timer:
                self.game_widget.timer.stop()
            if self.game_widget.countdown_timer:
                self.game_widget.countdown_timer.stop()

        self.menu_bar.setVisible(False)
        self.setCentralWidget(None)
        self.stack = QWidget()
        self.setCentralWidget(self.stack)
        self.setup_menu()

def main():
    try:
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        QMessageBox.critical(None, "Критическая ошибка", f"Программа завершена с ошибкой:\n{e}")
        sys.exit(1)

if __name__ == "__main__":
    main()