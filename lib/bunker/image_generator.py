from typing import List, Tuple
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os

from lib.bunker.player import Player

class ImageGenerator:
    """Класс для генерации изображений статуса игры"""
    
    @staticmethod
    def wrap_text(text: str, max_width: int, font) -> Tuple[List[str], int]:
        """
        Переносит текст по строкам, чтобы он вписывался в заданную ширину
        
        Args:
            text: Текст для переноса
            max_width: Максимальная ширина строки
            font: Шрифт для расчета ширины
            
        Returns:
            Tuple[List[str], int]: Список строк и высота текста
        """
        lines = []
        words = str(text).split()
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            # Используем getbbox вместо getlength для лучшей совместимости
            width = font.getbbox(test_line)[2] if hasattr(font, 'getbbox') else font.getsize(test_line)[0]
            
            if width <= max_width:
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Используем getbbox или getsize в зависимости от доступности метода
        line_height = (font.getbbox('A')[3] if hasattr(font, 'getbbox') else font.getsize('A')[1]) + 4
        total_height = len(lines) * line_height
        return lines, total_height
    
    @staticmethod
    def generate_status_image(players: List[Player]) -> BytesIO:
        """
        Генерация изображения с таблицей статусов игроков
        
        Args:
            players: Список игроков
            
        Returns:
            BytesIO: Файл с изображением таблицы статусов
        """
        try:
            # Используем всех игроков вместо только активных
            all_players = players
            
            # Определяем шрифты и цвета в стиле Material Design
            font_path = os.path.join(os.path.dirname(__file__), 'fonts/arial.ttf')
            if not os.path.exists(font_path):
                possible_paths = [
                    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
                    "/usr/share/fonts/TTF/Arial.ttf",
                    "C:/Windows/Fonts/arial.ttf",
                    "/System/Library/Fonts/Arial.ttf"
                ]
                
                for path in possible_paths:
                    if os.path.exists(path):
                        font_path = path
                        break
                else:
                    header_font = ImageFont.load_default()
                    cell_font = ImageFont.load_default()
                    font_path = "default"
            
            if font_path != "default":
                try:
                    header_font = ImageFont.truetype(font_path, 18)  # Увеличили размер шрифта заголовка
                    cell_font = ImageFont.truetype(font_path, 14)   # Увеличили размер шрифта ячеек
                except:
                    header_font = ImageFont.load_default()
                    cell_font = ImageFont.load_default()
            
            # Material Design цвета
            colors = {
                'background': (250, 250, 250),      # Светло-серый фон
                'header_bg': (33, 150, 243),        # Material Blue
                'header_text': (255, 255, 255),     # Белый текст заголовка
                'row_even': (255, 255, 255),        # Белый для четных строк
                'row_odd': (245, 245, 245),         # Светло-серый для нечетных строк
                'text': (33, 33, 33),               # Темно-серый текст
                'inactive_text': (158, 158, 158),   # Серый для неактивных игроков
                'border': (224, 224, 224),          # Светло-серая граница
                'shadow': (0, 0, 0, 30)             # Тень для заголовка
            }
            
            # Определяем колонки
            columns = ["Игрок", "Пол", "Тело", "Черта", "Проф.", "Здоровье", "Хобби", "Фобия", "Инв.", "Рюкзак", "Доп."]
            
            # Определяем максимальные ширины для каждой колонки
            max_column_widths = [200, 150, 150, 150, 150, 150, 150, 150, 150, 200, 200]
            
            # Рассчитываем минимальные ширины колонок на основе заголовков
            min_column_widths = []
            for column in columns:
                if hasattr(header_font, 'getbbox'):
                    width = header_font.getbbox(column)[2]
                else:
                    width = header_font.getsize(column)[0]
                min_column_widths.append(width + 30)  # Увеличили отступ
            
            # Подготавливаем данные игроков и рассчитываем необходимую ширину для каждой колонки
            player_data_rows = []
            column_widths = min_column_widths.copy()
            
            for i, player in enumerate(all_players):
                player_data = [
                    f"[{i+1}] {player.name}",
                    player.get_revealed_attribute("gender") or "?",
                    player.get_revealed_attribute("body") or "?",
                    player.get_revealed_attribute("trait") or "?",
                    player.get_revealed_attribute("profession") or "?",
                    player.get_revealed_attribute("health") or "?",
                    player.get_revealed_attribute("hobby") or "?",
                    player.get_revealed_attribute("phobia") or "?",
                    player.get_revealed_attribute("inventory") or "?",
                    player.get_revealed_attribute("backpack") or "?",
                    player.get_revealed_attribute("additional") or "?"
                ]
                player_data_rows.append((player_data, player.is_active))
                
                for i, data in enumerate(player_data):
                    if hasattr(cell_font, 'getbbox'):
                        width = cell_font.getbbox(data)[2]
                    else:
                        width = cell_font.getsize(data)[0]
                    column_widths[i] = min(max(column_widths[i], width + 30), max_column_widths[i])
            
            # Рассчитываем размеры изображения
            padding = 20  # Увеличили отступы
            header_height = 50  # Увеличили высоту заголовка
            min_cell_height = 40  # Увеличили минимальную высоту ячейки
            
            # Рассчитываем высоту для каждого ряда
            row_heights = []
            
            for player_data, is_active in player_data_rows:
                max_height = min_cell_height
                for i, data in enumerate(player_data):
                    lines, height = ImageGenerator.wrap_text(data, column_widths[i] - 20, cell_font)
                    max_height = max(max_height, height + 15)  # Увеличили отступ
                row_heights.append(max_height)
            
            # Общая ширина и высота изображения
            width = sum(column_widths) + padding * 2
            height = header_height + sum(row_heights) + padding * 2
            
            # Создаем изображение
            image = Image.new('RGB', (width, height), color=colors['background'])
            draw = ImageDraw.Draw(image)
            
            # Рисуем заголовок с тенью
            x = padding
            y = padding
            
            # Рисуем тень заголовка
            shadow_rect = (x, y + 2, x + sum(column_widths), y + header_height + 2)
            draw.rectangle(shadow_rect, fill=colors['shadow'])
            
            # Рисуем сам заголовок
            header_rect = (x, y, x + sum(column_widths), y + header_height)
            draw.rectangle(header_rect, fill=colors['header_bg'])
            
            # Рисуем текст заголовка
            x = padding
            for i, column in enumerate(columns):
                if hasattr(header_font, 'getbbox'):
                    text_width = header_font.getbbox(column)[2]
                    text_height = header_font.getbbox(column)[3]
                else:
                    text_width, text_height = header_font.getsize(column)
                
                text_x = x + (column_widths[i] - text_width) / 2
                text_y = y + (header_height - text_height) / 2
                
                draw.text((text_x, text_y), column, font=header_font, fill=colors['header_text'])
                x += column_widths[i]
            
            # Рисуем данные игроков
            current_y = padding + header_height
            
            for row, ((player_data, is_active), row_height) in enumerate(zip(player_data_rows, row_heights)):
                x = padding
                
                for i, data in enumerate(player_data):
                    # Выбираем цвет фона в зависимости от четности строки
                    cell_color = colors['row_even'] if row % 2 == 0 else colors['row_odd']
                    
                    # Рисуем ячейку с закругленными углами
                    cell_rect = (x, current_y, x + column_widths[i], current_y + row_height)
                    draw.rectangle(cell_rect, fill=cell_color, outline=colors['border'])
                    
                    # Делаем перенос текста и отрисовываем его
                    lines, _ = ImageGenerator.wrap_text(data, column_widths[i] - 20, cell_font)
                    line_height = (cell_font.getbbox('A')[3] if hasattr(cell_font, 'getbbox') else cell_font.getsize('A')[1]) + 4
                    
                    # Рассчитываем вертикальный отступ
                    total_text_height = len(lines) * line_height
                    y_offset = (row_height - total_text_height) / 2
                    
                    # Выбираем цвет текста в зависимости от активности игрока
                    text_color = colors['inactive_text'] if not is_active else colors['text']
                    
                    for j, line in enumerate(lines):
                        line_y = current_y + y_offset + j * line_height
                        draw.text((x + 10, line_y), line, font=cell_font, fill=text_color)
                    
                    x += column_widths[i]
                
                current_y += row_height
            
            # Сохраняем изображение в байты
            image_bytes = BytesIO()
            image.save(image_bytes, format='PNG')
            image_bytes.seek(0)

            return image_bytes
        
        except Exception as e:
            print(f"Ошибка при создании изображения: {e}")
            # Создаем простое изображение с сообщением об ошибке
            error_image = Image.new('RGB', (400, 100), color=colors['background'])
            draw = ImageDraw.Draw(error_image)
            
            try:
                font = ImageFont.load_default()
                draw.text((10, 10), f"Ошибка создания изображения: {str(e)[:50]}", font=font, fill=(255, 0, 0))
            except:
                draw.text((10, 10), "Ошибка создания изображения", fill=(255, 0, 0))
            
            error_bytes = BytesIO()
            error_image.save(error_bytes, format='PNG')
            error_bytes.seek(0)
            
            return error_bytes