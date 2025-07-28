#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import requests
import re
from typing import List, Set
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QGridLayout, QLabel, QLineEdit, 
                             QPushButton, QTextEdit, QCheckBox, QSpinBox,
                             QGroupBox, QScrollArea, QFrame, QMessageBox,
                             QFileDialog, QProgressBar, QTabWidget)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon

class WordGeneratorThread(QThread):
    """Поток для генерации слов, чтобы не блокировать интерфейс"""
    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(dict)
    
    def __init__(self, conditions):
        super().__init__()
        self.conditions = conditions
    
    def run(self):
        try:
            self.progress_signal.emit("Загружаем словарь...")
            dictionary_words = self.get_russian_words()
            
            self.progress_signal.emit("Фильтруем слова по условиям...")
            filtered_words = self.filter_words_by_conditions(dictionary_words, self.conditions)
            
            self.progress_signal.emit("Генерируем комбинации...")
            possible_combinations = self.generate_possible_words(self.conditions)
            
            self.progress_signal.emit("Проверяем реальные существительные...")
            real_nouns = [word for word in possible_combinations 
                         if word in dictionary_words and self.is_noun(word)]
            
            results = {
                'dictionary_words': len(dictionary_words),
                'filtered_words': filtered_words,
                'possible_combinations': possible_combinations,
                'real_nouns': real_nouns
            }
            
            self.finished_signal.emit(results)
            
        except Exception as e:
            self.progress_signal.emit(f"Ошибка: {str(e)}")
    
    def get_russian_words(self) -> Set[str]:
        """Загружает список русских слов из интернета"""
        try:
            url = "https://raw.githubusercontent.com/danakt/russian-words/master/russian.txt"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                words = set()
                for line in response.text.split('\n'):
                    word = line.strip().lower()
                    if len(word) == 5 and re.match(r'^[а-яё]+$', word):
                        words.add(word)
                return words
        except:
            pass
        
        # Базовый список слов
        return {
            'метла', 'булка', 'книга', 'лапша', 'мама', 'ночь', 'окно', 
            'печь', 'рука', 'стол', 'тень', 'ухо', 'флаг', 'хлеб', 'царь', 
            'чай', 'шар', 'щетка', 'эхо', 'юла', 'яма', 'парта', 'театр',
            'дом', 'звук', 'игра', 'снег', 'дождь', 'ветер', 'солнце', 'луна', 
            'звезда', 'вода', 'огонь', 'земля', 'небо', 'море', 'лес', 'поле', 
            'гора', 'река', 'город', 'село', 'сад', 'путь', 'день', 'год', 
            'час', 'минута', 'секунда', 'утро', 'вечер', 'неделя', 'месяц'
        }
    
    def is_noun(self, word: str) -> bool:
        """Проверяет, является ли слово существительным"""
        known_nouns = {
            'метла', 'булка', 'книга', 'лапша', 'мама', 'ночь', 'окно', 
            'печь', 'рука', 'стол', 'тень', 'ухо', 'флаг', 'хлеб', 'царь', 
            'чай', 'шар', 'щетка', 'эхо', 'юла', 'яма', 'парта', 'театр',
            'дом', 'звук', 'игра', 'снег', 'дождь', 'ветер', 'солнце', 'луна', 
            'звезда', 'вода', 'огонь', 'земля', 'небо', 'море', 'лес', 'поле', 
            'гора', 'река', 'город', 'село', 'сад', 'путь', 'день', 'год', 
            'час', 'минута', 'секунда'
        }
        
        if word in known_nouns:
            return True
        
        # Исключаем прилагательные
        if word.endswith(('ый', 'ой', 'ий', 'ая', 'яя', 'ое', 'ее')):
            return False
        
        # Исключаем глаголы
        if word.endswith(('ть', 'ти', 'чь', 'л', 'ла', 'ло', 'ли')):
            return False
        
        # Исключаем глаголы в повелительном наклонении
        if word.endswith(('и', 'й')) and len(word) >= 3:
            return False
        
        # Исключаем глаголы с приставками
        if word.startswith(('по', 'за', 'под', 'над', 'от', 'до', 'про', 'пере')):
            return False
        
        # Исключаем наречия
        if word.endswith(('о', 'е')) and len(word) >= 4:
            if len(word) <= 3:
                return True
        
        # Исключаем множественное число
        if word.endswith(('ы', 'и')) and len(word) >= 4:
            return False
        
        # Дополнительные проверки для 5-буквенных слов
        if len(word) == 5:
            if word.endswith(('а', 'я', 'ь')):
                return True
            if word[-1] in 'бвгджзйклмнпрстфхцчшщ':
                return True
        
        return False
    
    def filter_words_by_conditions(self, words: Set[str], conditions: dict) -> List[str]:
        """Фильтрует слова по заданным условиям"""
        forbidden_letters = set(conditions['forbidden_letters'])
        required_letters = set(conditions['required_letters'])
        word_length = conditions['word_length']
        positional_constraints = conditions['positional_constraints']
        only_nouns = conditions['only_nouns']
        exclude_verbs = conditions['exclude_verbs']
        
        # Доступные буквы
        all_russian_letters = set('абвгдеёжзийклмнопрстуфхцчшщъыьэюя')
        available_letters = all_russian_letters - forbidden_letters
        
        filtered_words = []
        
        for word in words:
            if len(word) != word_length:
                continue
                
            # Проверяем доступные буквы
            if not all(letter in available_letters for letter in word):
                continue
            
            # Проверяем обязательные буквы
            if required_letters and not all(letter in word for letter in required_letters):
                continue
            
            # Проверяем позиционные ограничения
            skip_word = False
            for letter, positions in positional_constraints.items():
                if letter in word:
                    for pos in positions:
                        if pos < len(word) and word[pos] == letter:
                            skip_word = True
                            break
                    if skip_word:
                        break
            if skip_word:
                continue
            
            # Проверяем существительные
            if only_nouns and not self.is_noun(word):
                continue
            
            # Проверяем исключение глаголов
            if exclude_verbs and self.is_verb(word):
                continue
            
            filtered_words.append(word)
        
        return sorted(filtered_words)
    
    def is_verb(self, word: str) -> bool:
        """Проверяет, является ли слово глаголом"""
        verb_endings = {
            'ть', 'ти', 'чь', 'л', 'ла', 'ло', 'ли',
            'ю', 'ешь', 'ет', 'ем', 'ете', 'ют', 'и', 'й'
        }
        
        known_verbs = {
            'бежать', 'ходить', 'петь', 'читать', 'писать', 'говорить',
            'думать', 'работать', 'играть', 'смотреть', 'слушать',
            'кушать', 'пить', 'спать', 'жить', 'учить', 'знать'
        }
        
        if word in known_verbs:
            return True
        
        for ending in verb_endings:
            if word.endswith(ending):
                return True
        
        if any(suffix in word for suffix in ['ова', 'ева', 'ива', 'ыва']):
            return True
        
        verb_prefixes = ['по', 'за', 'под', 'над', 'от', 'до', 'про', 'пере', 'вы', 'в', 'с']
        for prefix in verb_prefixes:
            if word.startswith(prefix) and len(word) > len(prefix) + 2:
                return True
        
        return False
    
    def generate_possible_words(self, conditions: dict) -> List[str]:
        """Генерирует возможные слова по условиям"""
        forbidden_letters = set(conditions['forbidden_letters'])
        required_letters = set(conditions['required_letters'])
        word_length = conditions['word_length']
        positional_constraints = conditions['positional_constraints']
        
        all_russian_letters = set('абвгдеёжзийклмнопрстуфхцчшщъыьэюя')
        available_letters = all_russian_letters - forbidden_letters
        
        possible_words = []
        
        # Генерируем комбинации
        def generate_combinations(current_word, position):
            if position == word_length:
                # Проверяем условия
                if required_letters and not all(letter in current_word for letter in required_letters):
                    return
                
                skip_word = False
                for letter, positions in positional_constraints.items():
                    if letter in current_word:
                        for pos in positions:
                            if pos < len(current_word) and current_word[pos] == letter:
                                skip_word = True
                                break
                        if skip_word:
                            break
                if skip_word:
                    return
                
                possible_words.append(current_word)
                return
            
            for letter in available_letters:
                generate_combinations(current_word + letter, position + 1)
        
        generate_combinations("", 0)
        return sorted(list(set(possible_words)))


class WordGeneratorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("🎯 Генератор слов по условиям")
        self.setGeometry(100, 100, 1200, 800)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной layout
        main_layout = QHBoxLayout(central_widget)
        
        # Левая панель с настройками
        left_panel = self.create_settings_panel()
        main_layout.addWidget(left_panel, 1)
        
        # Правая панель с результатами
        right_panel = self.create_results_panel()
        main_layout.addWidget(right_panel, 2)
        
        # Инициализация условий
        self.conditions = {
            'word_length': 5,
            'forbidden_letters': set(),
            'required_letters': set(),
            'positional_constraints': {},
            'only_nouns': True,
            'exclude_verbs': True
        }
        
        # Поток для генерации
        self.generator_thread = None
        
    def create_settings_panel(self):
        """Создает панель с настройками"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Заголовок
        title = QLabel("⚙️ Настройки условий")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)
        
        # Длина слова
        length_group = QGroupBox("Длина слова")
        length_layout = QHBoxLayout(length_group)
        self.length_spinbox = QSpinBox()
        self.length_spinbox.setRange(3, 10)
        self.length_spinbox.setValue(5)
        self.length_spinbox.valueChanged.connect(self.update_conditions)
        length_layout.addWidget(QLabel("Количество букв:"))
        length_layout.addWidget(self.length_spinbox)
        layout.addWidget(length_group)
        
        # Запрещенные буквы
        forbidden_group = QGroupBox("Запрещенные буквы")
        forbidden_layout = QVBoxLayout(forbidden_group)
        
        self.forbidden_input = QLineEdit()
        self.forbidden_input.setPlaceholderText("Введите буквы через запятую (например: с,л,о)")
        self.forbidden_input.textChanged.connect(self.update_forbidden_letters)
        forbidden_layout.addWidget(self.forbidden_input)
        
        # Кнопки для быстрого добавления
        forbidden_buttons_layout = QGridLayout()
        russian_letters = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'
        for i, letter in enumerate(russian_letters):
            btn = QPushButton(letter.upper())
            btn.setMaximumWidth(30)
            btn.clicked.connect(lambda checked, l=letter: self.toggle_forbidden_letter(l))
            forbidden_buttons_layout.addWidget(btn, i // 7, i % 7)
        forbidden_layout.addLayout(forbidden_buttons_layout)
        layout.addWidget(forbidden_group)
        
        # Обязательные буквы
        required_group = QGroupBox("Обязательные буквы")
        required_layout = QVBoxLayout(required_group)
        
        self.required_input = QLineEdit()
        self.required_input.setPlaceholderText("Введите буквы через запятую (например: в,р)")
        self.required_input.textChanged.connect(self.update_required_letters)
        required_layout.addWidget(self.required_input)
        
        # Кнопки для быстрого добавления
        required_buttons_layout = QGridLayout()
        for i, letter in enumerate(russian_letters):
            btn = QPushButton(letter.upper())
            btn.setMaximumWidth(30)
            btn.clicked.connect(lambda checked, l=letter: self.toggle_required_letter(l))
            required_buttons_layout.addWidget(btn, i // 7, i % 7)
        required_layout.addLayout(required_buttons_layout)
        layout.addWidget(required_group)
        
        # Позиционные ограничения
        positional_group = QGroupBox("Позиционные ограничения")
        positional_layout = QVBoxLayout(positional_group)
        
        self.positional_input = QLineEdit()
        self.positional_input.setPlaceholderText("Формат: буква:позиция,позиция (например: в:3,4 или р:1)")
        self.positional_input.textChanged.connect(self.update_positional_constraints)
        positional_layout.addWidget(self.positional_input)
        layout.addWidget(positional_group)
        
        # Дополнительные фильтры
        filters_group = QGroupBox("Дополнительные фильтры")
        filters_layout = QVBoxLayout(filters_group)
        
        self.only_nouns_checkbox = QCheckBox("Только существительные")
        self.only_nouns_checkbox.setChecked(True)
        self.only_nouns_checkbox.stateChanged.connect(self.update_conditions)
        filters_layout.addWidget(self.only_nouns_checkbox)
        
        self.exclude_verbs_checkbox = QCheckBox("Исключить глаголы")
        self.exclude_verbs_checkbox.setChecked(True)
        self.exclude_verbs_checkbox.stateChanged.connect(self.update_conditions)
        filters_layout.addWidget(self.exclude_verbs_checkbox)
        layout.addWidget(filters_group)
        
        # Кнопки управления
        buttons_layout = QHBoxLayout()
        
        self.generate_btn = QPushButton("🎲 Генерировать")
        self.generate_btn.clicked.connect(self.generate_words)
        self.generate_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 10px; font-weight: bold; }")
        buttons_layout.addWidget(self.generate_btn)
        
        self.save_btn = QPushButton("💾 Сохранить")
        self.save_btn.clicked.connect(self.save_results)
        self.save_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; padding: 10px; }")
        buttons_layout.addWidget(self.save_btn)
        
        layout.addLayout(buttons_layout)
        
        # Прогресс бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        layout.addStretch()
        return panel
    
    def create_results_panel(self):
        """Создает панель с результатами"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Заголовок
        title = QLabel("📊 Результаты")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)
        
        # Табы для разных результатов
        self.tabs = QTabWidget()
        
        # Таб со словами из словаря
        self.dictionary_tab = QWidget()
        dictionary_layout = QVBoxLayout(self.dictionary_tab)
        self.dictionary_text = QTextEdit()
        self.dictionary_text.setReadOnly(True)
        dictionary_layout.addWidget(QLabel("Слова из словаря:"))
        dictionary_layout.addWidget(self.dictionary_text)
        self.tabs.addTab(self.dictionary_tab, "📚 Словарь")
        
        # Таб с комбинациями
        self.combinations_tab = QWidget()
        combinations_layout = QVBoxLayout(self.combinations_tab)
        self.combinations_text = QTextEdit()
        self.combinations_text.setReadOnly(True)
        combinations_layout.addWidget(QLabel("Все комбинации:"))
        combinations_layout.addWidget(self.combinations_text)
        self.tabs.addTab(self.combinations_tab, "🎲 Комбинации")
        
        # Таб с существительными
        self.nouns_tab = QWidget()
        nouns_layout = QVBoxLayout(self.nouns_tab)
        self.nouns_text = QTextEdit()
        self.nouns_text.setReadOnly(True)
        nouns_layout.addWidget(QLabel("Реальные существительные:"))
        nouns_layout.addWidget(self.nouns_text)
        self.tabs.addTab(self.nouns_tab, "📖 Существительные")
        
        layout.addWidget(self.tabs)
        
        # Статистика
        self.stats_label = QLabel("Статистика появится после генерации")
        self.stats_label.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 10px; border-radius: 5px; }")
        layout.addWidget(self.stats_label)
        
        return panel
    
    def update_conditions(self):
        """Обновляет условия"""
        self.conditions['word_length'] = self.length_spinbox.value()
        self.conditions['only_nouns'] = self.only_nouns_checkbox.isChecked()
        self.conditions['exclude_verbs'] = self.exclude_verbs_checkbox.isChecked()
    
    def update_forbidden_letters(self):
        """Обновляет запрещенные буквы"""
        text = self.forbidden_input.text().lower()
        letters = {letter.strip() for letter in text.split(',') if letter.strip()}
        self.conditions['forbidden_letters'] = letters
    
    def update_required_letters(self):
        """Обновляет обязательные буквы"""
        text = self.required_input.text().lower()
        letters = {letter.strip() for letter in text.split(',') if letter.strip()}
        self.conditions['required_letters'] = letters
    
    def update_positional_constraints(self):
        """Обновляет позиционные ограничения"""
        text = self.positional_input.text().lower()
        constraints = {}
        
        for part in text.split(','):
            part = part.strip()
            if ':' in part:
                letter, positions = part.split(':', 1)
                letter = letter.strip()
                try:
                    pos_list = [int(p.strip()) - 1 for p in positions.split(',')]  # -1 для индексации с 0
                    constraints[letter] = pos_list
                except ValueError:
                    continue
        
        self.conditions['positional_constraints'] = constraints
    
    def toggle_forbidden_letter(self, letter):
        """Переключает букву в запрещенных"""
        current = set(self.forbidden_input.text().lower().split(','))
        current.discard('')
        
        if letter in current:
            current.discard(letter)
        else:
            current.add(letter)
        
        self.forbidden_input.setText(','.join(sorted(current)))
    
    def toggle_required_letter(self, letter):
        """Переключает букву в обязательных"""
        current = set(self.required_input.text().lower().split(','))
        current.discard('')
        
        if letter in current:
            current.discard(letter)
        else:
            current.add(letter)
        
        self.required_input.setText(','.join(sorted(current)))
    
    def generate_words(self):
        """Запускает генерацию слов"""
        self.generate_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Бесконечный прогресс
        
        # Обновляем условия
        self.update_conditions()
        self.update_forbidden_letters()
        self.update_required_letters()
        self.update_positional_constraints()
        
        # Запускаем поток
        self.generator_thread = WordGeneratorThread(self.conditions)
        self.generator_thread.progress_signal.connect(self.update_progress)
        self.generator_thread.finished_signal.connect(self.show_results)
        self.generator_thread.start()
    
    def update_progress(self, message):
        """Обновляет прогресс"""
        self.progress_bar.setFormat(message)
    
    def show_results(self, results):
        """Показывает результаты"""
        self.generate_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        # Обновляем тексты
        filtered_words = results['filtered_words']
        possible_combinations = results['possible_combinations']
        real_nouns = results['real_nouns']
        
        self.dictionary_text.setText('\n'.join(f"{i+1:4d}. {word}" for i, word in enumerate(filtered_words)))
        self.combinations_text.setText('\n'.join(f"{i+1:4d}. {word}" for i, word in enumerate(possible_combinations)))
        self.nouns_text.setText('\n'.join(f"{i+1:4d}. {word}" for i, word in enumerate(real_nouns)))
        
        # Обновляем статистику
        stats = f"""
📊 Статистика:
• Слов в словаре: {results['dictionary_words']}
• Слов из словаря: {len(filtered_words)}
• Всех комбинаций: {len(possible_combinations)}
• Реальных существительных: {len(real_nouns)}
        """
        self.stats_label.setText(stats)
        
        # Сохраняем результаты для сохранения в файл
        self.current_results = results
    
    def save_results(self):
        """Сохраняет результаты в файл"""
        if not hasattr(self, 'current_results'):
            QMessageBox.warning(self, "Предупреждение", "Сначала сгенерируйте слова!")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Сохранить результаты", "", "Текстовые файлы (*.txt)"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("🎯 Результаты генератора слов\n")
                    f.write("=" * 50 + "\n\n")
                    
                    f.write("Условия:\n")
                    f.write(f"• Длина слова: {self.conditions['word_length']}\n")
                    f.write(f"• Запрещенные буквы: {', '.join(sorted(self.conditions['forbidden_letters']))}\n")
                    f.write(f"• Обязательные буквы: {', '.join(sorted(self.conditions['required_letters']))}\n")
                    f.write(f"• Позиционные ограничения: {self.conditions['positional_constraints']}\n")
                    f.write(f"• Только существительные: {self.conditions['only_nouns']}\n")
                    f.write(f"• Исключить глаголы: {self.conditions['exclude_verbs']}\n\n")
                    
                    f.write("Статистика:\n")
                    f.write(f"• Слов в словаре: {self.current_results['dictionary_words']}\n")
                    f.write(f"• Слов из словаря: {len(self.current_results['filtered_words'])}\n")
                    f.write(f"• Всех комбинаций: {len(self.current_results['possible_combinations'])}\n")
                    f.write(f"• Реальных существительных: {len(self.current_results['real_nouns'])}\n\n")
                    
                    f.write("Слова из словаря:\n")
                    f.write("-" * 30 + "\n")
                    for i, word in enumerate(self.current_results['filtered_words'], 1):
                        f.write(f"{i:4d}. {word}\n")
                    
                    f.write("\nВсе комбинации:\n")
                    f.write("-" * 30 + "\n")
                    for i, word in enumerate(self.current_results['possible_combinations'], 1):
                        f.write(f"{i:4d}. {word}\n")
                    
                    f.write("\nРеальные существительные:\n")
                    f.write("-" * 30 + "\n")
                    for i, word in enumerate(self.current_results['real_nouns'], 1):
                        f.write(f"{i:4d}. {word}\n")
                
                QMessageBox.information(self, "Успех", f"Результаты сохранены в файл:\n{filename}")
                
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл:\n{str(e)}")


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Современный стиль
    
    window = WordGeneratorGUI()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main() 