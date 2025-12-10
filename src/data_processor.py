"""
Модуль для обработки данных из JIRA.
Преобразует сырые данные в формат, удобный для построения графиков.
"""
import pandas as pd           # Библиотека для работы с табличными данными
import numpy as np           # Для математических операций (нужна для статистики)
import logging               # Для записи логов работы программы
from datetime import datetime, timedelta  # Для работы с датами
from typing import Dict, List, Any  # Аннотации типов для документации


class DataProcessor:
    """Класс для обработки данных из JIRA."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Создание объекта обработчика данных.
        
        Args:
            config: Настройки из конфигурационного файла
        """
        self.config = config  # Сохранение настроек
        self.logger = logging.getLogger(__name__)  # Логгер 
        
        # Параметры обработки данных
        data_config = config.get("data_processing", {})
        # Количество интервалов для гистограммы
        self.histogram_bins = data_config.get("histogram_bins", 50)
        # Порог для долгих задач (7 дней в часах)
        self.long_task_threshold = data_config.get("long_task_threshold_hours", 168)
    
    def create_dataframe(self, issues: List[Dict]) -> pd.DataFrame:
        """
        Преобразует список задач в DataFrame Pandas.
        
        Args:
            issues: Список задач из JIRA
            
        Returns:
            pd.DataFrame: Таблица с обработанными данными
        """
        if not issues:  # Проверка, есть ли данные
            self.logger.warning("Нет данных для обработки")
            return pd.DataFrame()  # Возврат пустой таблицы
        self.logger.info(f"Обработка {len(issues)} задач")
        
        # Создание DataFrame из списка словарей
        df = pd.DataFrame(issues)
        
        # Преобразование строки с датами в объекты datetime
        df = self._convert_dates(df)
        
        # Добавление вычисляемых колонок
        df = self._add_calculated_fields(df)
        
        # Очищита данных от ошибок
        df = self._clean_data(df)
        
        return df  # Возврат готовой таблицы
    
    def _convert_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Преобразует текстовые даты в формат datetime."""
        # Колонки, которые содержат даты
        date_columns = ['created', 'resolved', 'updated']
        
        for col in date_columns:  # Для каждой колонки с датой
            if col in df.columns:  # Если колонка существует в таблице
                try:
                    # Преобразование строки в datetime (с обработкой ошибок)
                    df[col] = pd.to_datetime(df[col], errors='coerce', utc=True)
                except Exception:
                    pass  # Если ошибка - оставляет как есть
        
        return df
    
    def _add_calculated_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """Добавляет новые вычисляемые колонки."""
        # Если есть дата создания, добавляет производные
        if 'created' in df.columns:
            df['created_date'] = df['created'].dt.date  # Только дата (без времени)
            df['created_year'] = df['created'].dt.year  # Год создания
            df['created_month'] = df['created'].dt.month  # Месяц создания
        
        # Если есть дата закрытия
        if 'resolved' in df.columns:
            df['resolved_date'] = df['resolved'].dt.date
        
        # Если есть время выполнения в часах, вычисляет дни
        if 'open_time_hours' in df.columns:
            df['open_time_days'] = df['open_time_hours'] / 24  # Переводит часы в дни
        
        return df
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Удаляет некорректные данные."""
        original_count = len(df)  # Запоминает исходное количество строк
        
        # Удаляет задачи без даты создания
        if 'created' in df.columns:
            df = df.dropna(subset=['created'])
        
        # Удаляет задачи с отрицательным временем выполнения
        if 'open_time_hours' in df.columns:
            df = df[df['open_time_hours'] >= 0]
        
        # Логируем количество удалённых строк
        cleaned_count = len(df)
        if cleaned_count < original_count:
            self.logger.info(f"Удалено {original_count - cleaned_count} некорректных записей")
        
        return df
    
    def prepare_for_plotting(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Готовит данные для построения графиков.
        
        Args:
            df: DataFrame с данными
            
        Returns:
            Dict: Данные для каждого типа графика
        """
        if df.empty:  # Если таблица пустая
            return {}  # Возвращает пустой словарь
        
        plotting_data = {}  # Словарь для хранения данных графиков
        
        # 1. Данные для гистограммы времени выполнения
        if 'open_time_hours' in df.columns:
            plotting_data['open_time_data'] = df['open_time_hours'].dropna()
        
        # 2. Данные для графика приоритетов
        if 'priority' in df.columns:
            # Сколько задач каждого приоритета
            priority_counts = df['priority'].value_counts()
            plotting_data['priority_data'] = {
                'labels': priority_counts.index.tolist(),  # Названия приоритетов
                'values': priority_counts.values.tolist()  # Количество задач
            }
        
        # 3. Данные для графика по дням
        if 'created_date' in df.columns:
            # Сколько задач создано в каждый день
            created_by_day = df['created_date'].value_counts().sort_index()
            plotting_data['daily_tasks_data'] = {
                'dates': created_by_day.index.tolist(),    # Даты
                'created': created_by_day.values.tolist()  # Количество
            }
        
        return plotting_data
    
    def get_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Вычисляет статистику по данным.
        
        Args:
            df: DataFrame с данными
            
        Returns:
            Dict: Статистические показатели
        """
        if df.empty:
            return {}
        
        stats = {
            'total_tasks': len(df),  # Общее количество задач
        }
        
        # Статистика по времени выполнения
        if 'open_time_hours' in df.columns:
            time_data = df['open_time_hours'].dropna()  # Убирает пустые значения
            if len(time_data) > 0:  # Если есть данные
                stats['time_stats'] = {
                    'mean': time_data.mean(),    # Среднее значение
                    'median': time_data.median(),  # Медиана
                    'min': time_data.min(),      # Минимальное значение
                    'max': time_data.max()       # Максимальное значение
                }
        
        return stats