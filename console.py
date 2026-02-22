#!/usr/bin/env python
"""
Консольная версия Царского питона с отладкой
"""

import sys
import json
import os
from translator import TsarTranslator
from docker_executor import DockerExecutor


def print_color(text, color):
    """Цветной вывод в консоль"""
    colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'cyan': '\033[96m',
        'reset': '\033[0m'
    }
    print(f"{colors.get(color, '')}{text}{colors['reset']}")


def main():
    print_color("=" * 50, 'cyan')
    print_color("ЦАРСКИЙ ПИТОН - Консольная версия", 'cyan')
    print_color("=" * 50, 'cyan')

    # Загружаем словарь
    try:
        with open("dictionary.json", "r", encoding="utf-8") as f:
            mapping = json.load(f)
        print_color(f"✅ Словарь загружен: {len(mapping)} слов", 'green')
    except FileNotFoundError:
        print_color("⚠️ Файл словаря не найден, использую базовый", 'yellow')
        mapping = {
            "короче": "#", "выведи": "print", "спроси": "input",
            "ежели": "if", "иначе": "else", "пока": "while",
            "для": "for", "в": "in", "диапазон": "range",
            "истина": "True", "ложь": "False"
        }

    translator = TsarTranslator(mapping)

    # Получаем код
    if len(sys.argv) < 2:
        print_color("\nИспользование:", 'yellow')
        print("  python console.py файл.tsar")
        print("  python console.py run 'код напрямую'")
        print("\nПримеры:")
        print('  python console.py run "выведи(\'Привет\')"')
        print("  python console.py examples/hello.tsar")
        sys.exit(1)

    if sys.argv[1] == "run" and len(sys.argv) > 2:
        # Код из командной строки
        code = sys.argv[2]
        print_color(f"\n📝 Исходный код (прямой ввод):", 'blue')
        print(code)
    else:
        # Код из файла
        try:
            with open(sys.argv[1], "r", encoding="utf-8") as f:
                code = f.read()
            print_color(f"\n📂 Файл: {sys.argv[1]}", 'blue')
            print_color("📝 Исходный код:", 'blue')
            print(code)
        except Exception as e:
            print_color(f"❌ Ошибка чтения файла: {e}", 'red')
            sys.exit(1)

    print_color("\n" + "-" * 50, 'cyan')
    print_color("🔧 Трансляция...", 'blue')
    python_code = translator.translate(code)

    print_color("\n📄 Результат трансляции (Python):", 'yellow')
    print(python_code)
    print_color("-" * 50, 'cyan')

    # Проверяем Docker
    try:
        print_color("\n🐳 Проверка Docker...", 'blue')
        executor = DockerExecutor(timeout=10)
        print_color("✅ Docker готов", 'green')
    except Exception as e:
        print_color(f"❌ Docker не доступен: {e}", 'red')
        print("\n💡 Решение:")
        print("  1. Установите Docker Desktop с https://www.docker.com/")
        print("  2. Запустите Docker Desktop")
        print("  3. Дождитесь появления иконки в трее")
        print("  4. Попробуйте снова")
        sys.exit(1)

    # Запускаем
    print_color("\n🚀 Запуск в изолированном контейнере...", 'blue')
    result = executor.run(python_code)

    print_color("\n" + "=" * 50, 'cyan')
    print_color("РЕЗУЛЬТАТ ВЫПОЛНЕНИЯ", 'cyan')
    print_color("=" * 50, 'cyan')

    if result["stdout"]:
        print_color("\n📤 STDOUT (вывод программы):", 'green')
        print(result["stdout"])

    if result["stderr"]:
        print_color("\n⚠️ STDERR (ошибки):", 'red')
        print(result["stderr"])

    if result["error"]:
        print_color(f"\n❌ ОШИБКА: {result['error']}", 'red')

    if not any([result["stdout"], result["stderr"], result["error"]]):
        print_color("\n🤔 Программа ничего не вывела", 'yellow')

    print_color("\n" + "=" * 50, 'cyan')


if __name__ == "__main__":
    main()