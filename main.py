import sys
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QTextEdit, QSplitter,
                             QMessageBox, QFileDialog, QStatusBar)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

from translator import TsarTranslator
from docker_executor import DockerExecutor  # используем новую версию


class ExecutionThread(QThread):
    output = pyqtSignal(str)
    error = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, translator, executor, code):
        super().__init__()
        self.translator = translator
        self.executor = executor
        self.code = code

    def run(self):
        try:
            self.output.emit("🔧 Трансляция...")
            python_code = self.translator.translate(self.code)

            # Показываем результат трансляции (для отладки)
            self.output.emit("✅ Трансляция успешна")
            self.output.emit("\n📄 Python код:\n" + python_code)
            self.output.emit("\n🐳 Запуск в Docker...")

            result = self.executor.run(python_code)

            if result["stdout"]:
                self.output.emit("\n📤 Результат:\n" + result["stdout"])
            if result["stderr"]:
                self.error.emit("\n⚠️ Ошибки:\n" + result["stderr"])
            if result["error"]:
                self.error.emit("\n❌ " + result["error"])

        except Exception as e:
            self.error.emit(f"\n❌ Ошибка: {str(e)}")
        finally:
            self.finished.emit()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Царский питон")
        self.setGeometry(200, 200, 1000, 700)

        # Загружаем словарь
        try:
            with open("dictionary.json", "r", encoding="utf-8") as f:
                self.mapping = json.load(f)
        except FileNotFoundError:
            self.mapping = {
                "короче": "#", "выведи": "print", "спроси": "input",
                "ежели": "if", "илиежели": "elif", "иначе": "else",
                "пока": "while", "для": "for", "в": "in",
                "диапазон": "range", "истина": "True", "ложь": "False"
            }

        self.translator = TsarTranslator(self.mapping)

        # Проверяем Docker
        self.docker_ok = False
        try:
            self.executor = DockerExecutor(timeout=10)
            self.docker_ok = True
        except Exception as e:
            print(f"❌ Docker не доступен: {e}")

        self.current_file = None
        self.init_ui()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout()
        central.setLayout(layout)

        # Панель инструментов
        toolbar = QHBoxLayout()

        self.new_btn = QPushButton("📄 Новый")
        self.open_btn = QPushButton("📂 Открыть")
        self.save_btn = QPushButton("💾 Сохранить")
        self.run_btn = QPushButton("▶ Запустить")
        self.stop_btn = QPushButton("⏹ Стоп")

        self.new_btn.clicked.connect(self.new_file)
        self.open_btn.clicked.connect(self.open_file)
        self.save_btn.clicked.connect(self.save_file)
        self.run_btn.clicked.connect(self.run_code)
        self.stop_btn.clicked.connect(self.stop_code)

        for btn in [self.new_btn, self.open_btn, self.save_btn, self.run_btn, self.stop_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    font-size: 14px;
                    padding: 5px 15px;
                    background-color: #f0f0f0;
                    border: 1px solid #ccc;
                    border-radius: 3px;
                }
                QPushButton:hover { background-color: #e0e0e0; }
                QPushButton:disabled { background-color: #f8f8f8; color: #999; }
            """)

        toolbar.addWidget(self.new_btn)
        toolbar.addWidget(self.open_btn)
        toolbar.addWidget(self.save_btn)
        toolbar.addWidget(self.run_btn)
        toolbar.addWidget(self.stop_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Редактор и вывод
        splitter = QSplitter(Qt.Vertical)

        self.editor = QTextEdit()
        self.editor.setFont(QFont("Consolas", 12))
        self.editor.setPlaceholderText("Пишите код на Царском питоне...")
        splitter.addWidget(self.editor)

        self.output = QTextEdit()
        self.output.setFont(QFont("Consolas", 11))
        self.output.setReadOnly(True)
        self.output.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #333;
                font-family: Consolas;
            }
        """)
        splitter.addWidget(self.output)

        splitter.setSizes([500, 200])
        layout.addWidget(splitter)

        # Статус бар
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.update_status()

        if not self.docker_ok:
            self.run_btn.setEnabled(False)
            self.output.append("❌ Docker не запущен!")
            self.output.append("\n💡 Решение:")
            self.output.append("1. Запустите Docker Desktop")
            self.output.append("2. Подождите 1 минуту")
            self.output.append("3. Перезапустите программу")

    def update_status(self):
        status = "Готов"
        if self.current_file:
            status += f" | Файл: {self.current_file}"
        if not self.docker_ok:
            status += " | ⚠️ Docker не доступен"
        self.status_bar.showMessage(status)

    def new_file(self):
        self.editor.clear()
        self.current_file = None
        self.update_status()

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Открыть файл", "", "Царский питон (*.tsar);;Все файлы (*)"
        )
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    self.editor.setText(f.read())
                self.current_file = file_path
                self.update_status()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось открыть файл: {e}")

    def save_file(self):
        if self.current_file:
            file_path = self.current_file
        else:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Сохранить файл", "", "Царский питон (*.tsar)"
            )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(self.editor.toPlainText())
                self.current_file = file_path
                self.update_status()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл: {e}")

    def run_code(self):
        if not self.editor.toPlainText().strip():
            QMessageBox.warning(self, "Предупреждение", "Код пустой!")
            return

        if not self.docker_ok:
            QMessageBox.critical(self, "Ошибка", "Docker не доступен!")
            return

        self.output.clear()
        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

        self.thread = ExecutionThread(
            self.translator, self.executor, self.editor.toPlainText()
        )
        self.thread.output.connect(self.output.append)
        self.thread.error.connect(self.output.append)
        self.thread.finished.connect(self.on_execution_finished)
        self.thread.start()

    def stop_code(self):
        if hasattr(self, 'thread') and self.thread.isRunning():
            self.executor.stop()
            self.thread.terminate()
            self.output.append("\n⏹ Выполнение остановлено")
            self.on_execution_finished()

    def on_execution_finished(self):
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.update_status()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())