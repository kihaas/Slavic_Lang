import subprocess
import tempfile
import os
import time
import uuid
import shutil
import threading


class DockerExecutor:
    def __init__(self, timeout=30):  # Увеличил таймаут
        self.timeout = timeout
        self.process = None

        # Проверяем Docker
        try:
            result = subprocess.run(
                ["docker", "ps"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print("✅ Docker работает")
            else:
                raise Exception("Docker не отвечает")
        except Exception as e:
            raise Exception(f"Docker не запущен! Ошибка: {e}")

    def run(self, code, input_data=None):
        """
        Запускает код в Docker
        input_data - строка, которая будет передана в stdin (для input())
        """
        result = {"stdout": "", "stderr": "", "error": None}

        # Создаем временную папку
        temp_dir = os.path.join(tempfile.gettempdir(), f"tsar_{uuid.uuid4().hex}")
        os.makedirs(temp_dir, exist_ok=True)
        script_path = os.path.join(temp_dir, "script.py")

        try:
            # Записываем код
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(code)

            print(f"📝 Временный файл: {script_path}")

            # Формируем команду Docker
            docker_cmd = [
                "docker", "run",
                "--rm",
                "--memory", "128m",
                "--cpus", "0.5",
                "--network", "none",
                "--read-only",
                "-v", f"{temp_dir}:/app:ro",
                "-w", "/app",
                "python:3.12-slim",
                "python", "-u", "script.py"  # -u для unbuffered output
            ]

            print(f"🐳 Запуск контейнера...")

            # Запускаем процесс
            self.process = subprocess.Popen(
                docker_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                bufsize=1  # Строчный буфер
            )

            # Если есть данные для ввода, отправляем их
            stdout_data = []
            stderr_data = []

            def read_output():
                for line in self.process.stdout:
                    stdout_data.append(line)
                    print(f"📤 {line}", end='')  # Для отладки

            def read_error():
                for line in self.process.stderr:
                    stderr_data.append(line)
                    print(f"⚠️ {line}", end='')  # Для отладки

            # Запускаем потоки для чтения вывода
            stdout_thread = threading.Thread(target=read_output)
            stderr_thread = threading.Thread(target=read_error)
            stdout_thread.daemon = True
            stderr_thread.daemon = True
            stdout_thread.start()
            stderr_thread.start()

            # Ждем завершения с таймаутом
            try:
                self.process.wait(timeout=self.timeout)
            except subprocess.TimeoutExpired:
                self.process.kill()
                result["error"] = f"⏱ Превышено время выполнения ({self.timeout} сек)"

            # Собираем результаты
            result["stdout"] = ''.join(stdout_data)
            result["stderr"] = ''.join(stderr_data)

        except Exception as e:
            result["error"] = f"❌ Ошибка: {str(e)}"
        finally:
            # Удаляем временную папку
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except:
                pass
            self.process = None

        return result

    def stop(self):
        """Остановка выполнения"""
        if self.process:
            try:
                self.process.kill()
                print("⏹ Процесс остановлен")
            except:
                pass


# Тест
if __name__ == "__main__":
    print("🐳 ТЕСТ DOCKER")
    print("=" * 50)

    executor = DockerExecutor(timeout=10)

    # Тест 1: Простой вывод
    test1 = """
print("✅ Тест 1: Простой вывод")
print("Привет из контейнера!")
"""
    print("\n📝 Тест 1:")
    result = executor.run(test1)
    print("📤 Результат:", result["stdout"])

    # Тест 2: С input (пока не поддерживается, но покажем ошибку)
    test2 = """
print("✅ Тест 2: С input")
name = input("Как тебя зовут? ")
print(f"Привет, {name}!")
"""
    print("\n📝 Тест 2:")
    result = executor.run(test2)
    print("📤 Результат:", result["stdout"])
    if result["stderr"]:
        print("⚠️ Ошибка (нормально для теста):", result["stderr"])