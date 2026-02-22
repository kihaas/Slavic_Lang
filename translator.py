import re


class TsarTranslator:
    """Заменяет царские слова на Python"""

    def __init__(self, mapping):
        self.mapping = mapping
        # Сортируем по длине (самые длинные слова сначала)
        self.words = sorted(mapping.keys(), key=len, reverse=True)

    def translate(self, code):
        """Простая замена слов с защитой от замен внутри строк"""
        lines = code.split('\n')
        result = []

        for line in lines:
            # Обрабатываем каждую строку отдельно
            new_line = self.translate_line(line)
            result.append(new_line)

        return '\n'.join(result)

    def translate_line(self, line):
        """Переводит одну строку, игнорируя строки в кавычках"""
        result = ""
        i = 0
        in_string = False
        string_char = None

        while i < len(line):
            char = line[i]

            # Проверяем начало/конец строки
            if char in '"\'' and (i == 0 or line[i - 1] != '\\'):
                if not in_string:
                    in_string = True
                    string_char = char
                elif string_char == char:
                    in_string = False
                    string_char = None
                result += char
                i += 1
                continue

            # Если не в строке - заменяем слова
            if not in_string:
                matched = False
                for word in self.words:
                    # Проверяем, что слово начинается с текущей позиции
                    if line[i:i + len(word)] == word:
                        # Проверяем границы слова
                        before = i == 0 or not line[i - 1].isalpha()
                        after = i + len(word) >= len(line) or not line[i + len(word)].isalpha()

                        if before and after:
                            result += self.mapping[word]
                            i += len(word)
                            matched = True
                            break

                if not matched:
                    result += char
                    i += 1
            else:
                result += char
                i += 1

        return result


# Тест
if __name__ == "__main__":
    mapping = {
        "короче": "#",
        "выведи": "print",
        "спроси": "input",
        "ежели": "if",
        "пока": "while",
        "истина": "True",
        "ложь": "False"
    }

    t = TsarTranslator(mapping)
    code = """
короче Это комментарий
имя = спроси("Как тебя зовут?")
ежели имя == "Петр":
    выведи("Здравствуй, царь!")
"""
    print(t.translate(code))