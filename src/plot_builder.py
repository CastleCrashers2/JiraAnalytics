"""
Модуль для построения графиков на основе данных из JIRA.
Создает 6 графиков согласно заданию лабораторной работы.
"""
import os
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
import logging


class PlotBuilder:
    """Класс для создания 6 графиков согласно заданию."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Инициализация построителя графиков.
        
        Args:
            config: Конфигурация приложения
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Настройки визуализации
        viz_config = config.get("visualization", {})
        self.output_dir = viz_config.get("output_dir", "reports")
        self.figure_size = viz_config.get("figure_size", {"width": 12, "height": 8})
        self.dpi = viz_config.get("dpi", 150)
        self.save_format = viz_config.get("save_format", "png")
        
        # Создаёт папку для отчётов
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        # Настройка стиля графиков
        plt.style.use('seaborn-v0_8-darkgrid')
        sns.set_palette("husl")
        plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
        plt.rcParams['axes.unicode_minus'] = False
    
    # ========== ОСНОВНОЙ МЕТОД: СОЗДАНИЕ ВСЕХ 6 ГРАФИКОВ ==========
    
    def create_all_plots(self, plot_data: Dict[str, Any], df_all: pd.DataFrame, df_closed: pd.DataFrame) -> Dict[str, str]:
        """
        Создаёт все 6 графиков согласно заданию.
        
        Args:
            plot_data: Данные для построения графиков (из DataProcessor)
            df_all: DataFrame с ВСЕМИ задачами (для графиков 3, 4, 6)
            df_closed: DataFrame только с ЗАКРЫТЫМИ задачами (для графиков 1, 2, 5)
            
        Returns:
            Dict: Словарь с путями к сохранённым графикам в правильной последовательности
        """
        self.logger.info("Создание 6 графиков аналитики...")
        plot_paths = {}
        
        # ГРАФИК 1: Гистограмма времени в открытом состоянии (закрытые задачи)
        if 'open_time_data' in plot_data and not df_closed.empty:
            path = self.plot_open_time_histogram(plot_data['open_time_data'])
            plot_paths['1_open_time_histogram'] = path
        
        # ГРАФИК 2: Распределение времени по состояниям (закрытые задачи)
        if not df_closed.empty:
            path = self.plot_status_times(df_closed)
            plot_paths['2_status_times'] = path
        
        # ГРАФИК 3: Количество задач по дням с накопительным итогом (все задачи)
        if 'daily_tasks_data' in plot_data and not df_all.empty:
            path = self.plot_daily_tasks(plot_data['daily_tasks_data'])
            plot_paths['3_daily_tasks'] = path
        
        # ГРАФИК 4: Топ-30 пользователей (все задачи)
        if not df_all.empty:
            path = self.plot_top_users(df_all)
            plot_paths['4_top_users'] = path
        
        # ГРАФИК 5: Гистограмма залогированного времени (закрытые задачи)
        if not df_closed.empty:
            path = self.plot_logged_time_histogram(df_closed)
            plot_paths['5_logged_time_histogram'] = path
        
        # ГРАФИК 6: Распределение по приоритетам (все задачи)
        if not df_all.empty:
            path = self.plot_priority_distribution(df_all)
            plot_paths['6_priority_distribution'] = path
        
        self.logger.info(f"Создано {len(plot_paths)} графиков из 6 требуемых")
        return plot_paths
    
    # ========== ГРАФИК 1: Время в открытом состоянии ==========
    
    def plot_open_time_histogram(self, open_time_data: pd.Series) -> str:
        """
        ГРАФИК 1: Гистограмма времени, которое задача провела в открытом состоянии.
        Задание: "от момента создания до момента закрытия", "только закрытые задачи"
        
        Args:
            open_time_data: Время выполнения в часах
            
        Returns:
            str: Путь к сохранённому файлу
        """
        fig, ax = plt.subplots(figsize=(self.figure_size['width'], self.figure_size['height']))
        
        # Фильтруем данные (исключаем выбросы)
        data = open_time_data.dropna()
        if len(data) > 0:
            q95 = data.quantile(0.95)
            data_filtered = data[data <= q95]
            
            # Если после фильтрации данных мало, используем все
            if len(data_filtered) < 10:
                data_filtered = data
            
            # Строим гистограмму
            n_bins = min(30, len(data_filtered))
            counts, bins, patches = ax.hist(
                data_filtered, 
                bins=n_bins,
                edgecolor='black',
                alpha=0.7,
                color='skyblue',
                label=f'Задачи (всего: {len(open_time_data)})'
            )
        
        # Настройки осей
        ax.set_xlabel('Время в открытом состоянии (часы)', fontsize=12)
        ax.set_ylabel('Количество задач', fontsize=12)
        ax.set_title('ГРАФИК 1: Время в открытом состоянии (закрытые задачи)', 
                    fontsize=14, fontweight='bold')
        
        # Статистика
        if len(open_time_data) > 0:
            stats_text = (
                f'Всего задач: {len(open_time_data)}\n'
                f'Среднее: {open_time_data.mean():.1f} ч\n'
                f'Медиана: {open_time_data.median():.1f} ч\n'
                f'Станд. отклонение: {open_time_data.std():.1f} ч'
            )
            ax.text(
                0.80, 0.75, stats_text,
                transform=ax.transAxes,
                fontsize=10,
                verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8)
            )
        
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        filename = f"1_open_time_histogram.{self.save_format}"
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=self.dpi, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"График 1 создан: {filepath}")
        return filepath
    
    # ========== ГРАФИК 2: Распределение времени по состояниям ==========
    
    def plot_status_times(self, df_closed: pd.DataFrame) -> str:
        """
        ГРАФИК 2: Диаграммы распределения времени по состояниям задачи.
        Задание: "Для каждого состояния своя диаграмма", "только закрытые задачи"
        
        Внимание: Так как у нас нет данных о времени в каждом состоянии,
        используем упрощённый вариант - распределение задач по статусам.
        
        Args:
            df_closed: DataFrame с закрытыми задачами
            
        Returns:
            str: Путь к сохранённому файлу
        """
        # Создаём подграфики
        n_statuses = 1  # По умолчанию 1 статус
        
        if 'status' in df_closed.columns and len(df_closed) > 0:
            unique_statuses = df_closed['status'].unique()
            n_statuses = len(unique_statuses)
        
        # Ограничиваем количество подграфиков для читаемости
        n_cols = min(3, n_statuses)
        n_rows = (n_statuses + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, 
                                figsize=(self.figure_size['width'], 
                                        self.figure_size['height'] * max(1, n_rows * 0.8)))
        
        # Если только один график
        if n_statuses == 1:
            axes = np.array([axes])
        
        axes = axes.flatten()
        
        if 'status' in df_closed.columns and len(df_closed) > 0:
            for idx, status in enumerate(unique_statuses):
                if idx < len(axes):
                    # Фильтруем задачи по статусу
                    status_df = df_closed[df_closed['status'] == status]
                    
                    if len(status_df) > 0 and 'open_time_hours' in status_df.columns:
                        time_data = status_df['open_time_hours'].dropna()
                        
                        if len(time_data) > 0:
                            # Гистограмма времени для этого статуса
                            axes[idx].hist(
                                time_data,
                                bins=min(20, len(time_data)),
                                edgecolor='black',
                                alpha=0.7,
                                color=plt.cm.tab20(idx / max(1, n_statuses-1))
                            )
                            
                            axes[idx].set_xlabel('Время (часы)')
                            axes[idx].set_ylabel('Количество задач')
                            axes[idx].set_title(f'Статус: {status}\n({len(time_data)} задач)')
                            axes[idx].grid(True, alpha=0.3)
                            
                            # Статистика
                            stats_text = (
                                f'Среднее: {time_data.mean():.1f} ч\n'
                                f'Медиана: {time_data.median():.1f} ч'
                            )
                            axes[idx].text(
                                0.85, 0.95, stats_text,
                                transform=axes[idx].transAxes,
                                fontsize=9,
                                verticalalignment='top',
                                bbox=dict(boxstyle='round', facecolor='white', alpha=0.7)
                            )
                        else:
                            axes[idx].text(0.5, 0.5, f'Нет данных о времени\nдля статуса: {status}',
                                         ha='center', va='center')
                            axes[idx].set_title(f'Статус: {status}')
                    else:
                        axes[idx].text(0.5, 0.5, f'Задач: {len(status_df)}\nНет данных о времени',
                                     ha='center', va='center')
                        axes[idx].set_title(f'Статус: {status}')
            
            # Скрываем лишние оси
            for idx in range(len(unique_statuses), len(axes)):
                axes[idx].set_visible(False)
        else:
            # Если нет данных о статусах
            axes[0].text(0.5, 0.5, 'Нет данных о статусах задач', ha='center', va='center')
            axes[0].set_title('Нет данных')
            
            for idx in range(1, len(axes)):
                axes[idx].set_visible(False)
        
        fig.suptitle('ГРАФИК 2: Распределение времени по состояниям задачи\n(закрытые задачи)', 
                    fontsize=16, fontweight='bold', y=1.02)
        
        plt.tight_layout()
        filename = f"2_status_times.{self.save_format}"
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=self.dpi, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"График 2 создан: {filepath}")
        return filepath
    
    # ========== ГРАФИК 3: Количество задач по дням ==========

    def plot_daily_tasks(self, daily_data: Dict) -> str:
        """
     ГРАФИК 3: Количество заведенных и закрытых задач в день с накопительным итогом.
      """
        fig, axes = plt.subplots(2, 1, figsize=(self.figure_size['width'], self.figure_size['height'] * 1.5))
    
        dates = daily_data.get('dates', [])
        created = daily_data.get('created', [])
        resolved = daily_data.get('resolved', [])
    
        #Проверяет, что resolved не пустой и его длина совпадает с dates
        if len(dates) == 0:
         axes[0].text(0.5, 0.5, 'Нет данных по дням', ha='center', va='center')
         axes[1].text(0.5, 0.5, 'Нет данных по дням', ha='center', va='center')
        else:
        # График 3a: Ежедневное количество задач
         x = np.arange(len(dates))
        width = 0.35
        
        # Всегда строим график созданных задач
        axes[0].bar(x - width/2, created, width, label='Создано', color='lightblue', alpha=0.8)
        
        # Строим график закрытых задач, только если данные есть и длина совпадает
        if len(resolved) > 0 and len(resolved) == len(dates):
            axes[0].bar(x + width/2, resolved, width, label='Закрыто', color='lightcoral', alpha=0.8)
        else:
            # Если нет данных о закрытых, просто показываем информацию
            self.logger.warning(f"Нет данных о закрытых задачах для графика 3. "
                              f"Dates: {len(dates)}, Created: {len(created)}, Resolved: {len(resolved)}")
            # Можно добавить текст или просто оставить только created
        
        axes[0].set_xlabel('Календарные дни', fontsize=12)
        axes[0].set_ylabel('Количество задач в день', fontsize=12)
        axes[0].set_title('График 3a: Созданные и закрытые задачи по дням (все задачи)', 
                         fontsize=14, fontweight='bold')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        
        # Упрощаем подписи дат
        if len(dates) > 10:
            step = max(1, len(dates) // 10)
            axes[0].set_xticks(x[::step])
            date_labels = [str(d).split()[0] for d in dates]
            axes[0].set_xticklabels(date_labels[::step], rotation=45, ha='right')
        
        # График 3b: Накопительный итог
        created_cum = daily_data.get('created_cumulative', np.cumsum(created))
        
        # Для resolved_cumulative проверяем наличие данных
        if 'resolved_cumulative' in daily_data:
            resolved_cum = daily_data['resolved_cumulative']
            if len(resolved_cum) == len(dates):
                axes[1].plot(dates, resolved_cum, 'r-', linewidth=2, label='Закрыто (накоп.)', 
                           marker='s', markersize=4)
            else:
                # Если длины не совпадают, вычисляем кумулятивную сумму из resolved
                if len(resolved) == len(dates):
                    resolved_cum = np.cumsum(resolved)
                    axes[1].plot(dates, resolved_cum, 'r-', linewidth=2, label='Закрыто (накоп.)', 
                               marker='s', markersize=4)
        else:
            # Если ключа нет, пытаемся вычислить из resolved
            if len(resolved) == len(dates):
                resolved_cum = np.cumsum(resolved)
                axes[1].plot(dates, resolved_cum, 'r-', linewidth=2, label='Закрыто (накоп.)', 
                           marker='s', markersize=4)
        
        # Всегда строим график созданных задач (накопительный)
        axes[1].plot(dates, created_cum, 'b-', linewidth=2, label='Создано (накоп.)', 
                    marker='o', markersize=4)
        
        axes[1].set_xlabel('Календарные дни', fontsize=12)
        axes[1].set_ylabel('Накопительное количество задач', fontsize=12)
        axes[1].set_title('График 3b: Накопительный итог по задачам', fontsize=14, fontweight='bold')
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)
        
        # Добавляем заполнение между кривыми, если есть обе
        if 'resolved_cum' in locals() and len(created_cum) == len(resolved_cum):
            axes[1].fill_between(dates, created_cum, resolved_cum, 
                                where=created_cum >= resolved_cum, 
                                alpha=0.2, color='blue', label='Нерешенные')
    
        fig.suptitle('ГРАФИК 3: Динамика задач по дням', fontsize=16, fontweight='bold', y=1.02)
        plt.tight_layout()
    
        filename = f"3_daily_tasks.{self.save_format}"
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=self.dpi, bbox_inches='tight')
        plt.close()
    
        self.logger.info(f"График 3 создан: {filepath}")
        return filepath
    
    # ========== ГРАФИК 4: Топ-30 пользователей ==========
    
    def plot_top_users(self, df_all: pd.DataFrame) -> str:
        """
        ГРАФИК 4: Топ-30 пользователей по общему количеству задач.
        Задание: "общее количество задач, где пользователь указан как исполнитель и репортер"
        
        Args:
            df_all: DataFrame со всеми задачами
            
        Returns:
            str: Путь к сохранённому файлу
        """
        fig, ax = plt.subplots(figsize=(self.figure_size['width'], self.figure_size['height']))
        
        # Собираем данные обо всех пользователях
        user_tasks = {}
        
        # Обрабатываем репортеров
        if 'reporter' in df_all.columns:
            reporter_data = df_all['reporter'].dropna()
            for reporter in reporter_data:
                if reporter in user_tasks:
                    user_tasks[reporter]['reporter'] += 1
                else:
                    user_tasks[reporter] = {'reporter': 1, 'assignee': 0}
        
        # Обрабатываем исполнителей
        if 'assignee' in df_all.columns:
            assignee_data = df_all['assignee'].dropna()
            for assignee in assignee_data:
                if assignee in user_tasks:
                    user_tasks[assignee]['assignee'] += 1
                else:
                    user_tasks[assignee] = {'reporter': 0, 'assignee': 1}
        
        if user_tasks:
            # Рассчитываем общее количество задач для каждого пользователя
            user_totals = {}
            for user, counts in user_tasks.items():
                total = counts['reporter'] + counts['assignee']
                user_totals[user] = total
            
            # Сортируем по убыванию и берем топ-30
            sorted_users = sorted(user_totals.items(), key=lambda x: x[1], reverse=True)
            top_users = sorted_users[:30]
            
            if top_users:
                users = [user for user, _ in top_users]
                totals = [total for _, total in top_users]
                
                # Разделяем на репортерские и исполнительские задачи
                reporter_counts = [user_tasks[user]['reporter'] for user in users]
                assignee_counts = [user_tasks[user]['assignee'] for user in users]
                
                y_pos = np.arange(len(users))
                bar_height = 0.35
                
                # Создаем stacked bar chart (столбцы с накоплением)
                bars_reporter = ax.barh(y_pos, reporter_counts, bar_height,
                                       color='skyblue', label='Репортер', edgecolor='black')
                bars_assignee = ax.barh(y_pos, assignee_counts, bar_height,
                                       left=reporter_counts,
                                       color='lightcoral', label='Исполнитель', edgecolor='black')
                
                ax.set_yticks(y_pos)
                ax.set_yticklabels(users, fontsize=9)
                ax.set_xlabel('Общее количество задач', fontsize=12)
                ax.set_title(f'ГРАФИК 4: Топ-30 пользователей по задачам\n'
                           f'(всего пользователей: {len(user_tasks)})', 
                           fontsize=14, fontweight='bold')
                ax.grid(True, alpha=0.3, axis='x')
                
                # Добавляем легенду
                ax.legend(loc='center right')
                
                # Добавляем общее количество задач на каждый столбец
                for i, (total, reporter, assignee) in enumerate(zip(totals, reporter_counts, assignee_counts)):
                    # Общее количество справа
                    ax.text(total + max(totals)*0.01, i, f'всего: {total}', 
                           va='center', fontsize=8, fontweight='bold')
                    
                    # Детализация внутри столбца (если есть место)
                    if reporter > 0:
                        ax.text(reporter/2, i, f'реп: {reporter}', 
                               va='center', ha='center', fontsize=7, color='black')
                    if assignee > 0:
                        ax.text(reporter + assignee/2, i, f'исп: {assignee}', 
                               va='center', ha='center', fontsize=7, color='black')
                
                # Статистика в углу
                stats_text = (
                    f'Всего задач: {sum(totals)}\n'
                    f'Среднее на пользователя: {np.mean(totals):.1f}\n'
                    f'Максимум: {max(totals)}\n'
                    f'Минимум в топе: {min(totals)}'
                )
                ax.text(0.75, 0.98, stats_text,
                       transform=ax.transAxes,
                       fontsize=10,
                       verticalalignment='top',
                       bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
            else:
                ax.text(0.5, 0.5, 'Нет данных о пользователях', 
                       ha='center', va='center')
                ax.set_title('Топ пользователей по задачам', fontsize=14)
        else:
            ax.text(0.5, 0.5, 'Нет данных о пользователях', 
                   ha='center', va='center')
            ax.set_title('Топ пользователей по задачам', fontsize=14)
        
        plt.tight_layout()
        filename = f"4_top_users.{self.save_format}"
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=self.dpi, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"График 4 создан: {filepath}")
        return filepath
    
    # ========== ГРАФИК 5: Залогированное время ==========
    
    def plot_logged_time_histogram(self, df_closed: pd.DataFrame) -> str:
        """
        ГРАФИК 5: Гистограмма залогированного времени.
        Задание: "время, которое затратил пользователь на выполнение", "только закрытые задачи"
        
        Внимание: Так как у нас нет реальных данных worklog,
        используем время в открытом состоянии как приближение.
        
        Args:
            df_closed: DataFrame с закрытыми задачами
            
        Returns:
            str: Путь к сохранённому файлу
        """
        fig, ax = plt.subplots(figsize=(self.figure_size['width'], self.figure_size['height']))
        
        if 'open_time_hours' in df_closed.columns:
            data = df_closed['open_time_hours'].dropna()
            
            if len(data) > 0:
                # Фильтруем выбросы
                q95 = data.quantile(0.95)
                data_filtered = data[data <= q95]
                
                if len(data_filtered) < 10:
                    data_filtered = data
                
                # Строим гистограмму
                n_bins = min(25, len(data_filtered))
                ax.hist(
                    data_filtered,
                    bins=n_bins,
                    edgecolor='black',
                    alpha=0.7,
                    color='orange',
                    label=f'Приближённое время\n(всего: {len(data)} задач)'
                )
                
                ax.set_xlabel('Приближённое залогированное время (часы)', fontsize=12)
                ax.set_ylabel('Количество задач', fontsize=12)
                
                # Статистика
                stats_text = (
                    f'Всего задач: {len(data)}\n'
                    f'Среднее: {data.mean():.1f} ч\n'
                    f'Медиана: {data.median():.1f} ч\n'
                    f'Максимум: {data.max():.1f} ч'
                )
                ax.text(
                    0.85, 0.75, stats_text,
                    transform=ax.transAxes,
                    fontsize=10,
                    verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8)
                )
                
                ax.legend(loc='upper right')
                ax.grid(True, alpha=0.3)
            else:
                ax.text(0.5, 0.5, 'Нет данных о времени выполнения', 
                       ha='center', va='center', fontsize=12)
        else:
            ax.text(0.5, 0.5, 'Нет данных о времени выполнения', 
                   ha='center', va='center', fontsize=12)
        
        ax.set_title('ГРАФИК 5: Распределение времени выполнения\n(закрытые задачи, приближённые данные)', 
                    fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        filename = f"5_logged_time_histogram.{self.save_format}"
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=self.dpi, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"График 5 создан: {filepath}")
        return filepath
    
    # ========== ГРАФИК 6: Распределение по приоритетам ==========
    
    def plot_priority_distribution(self, df_all: pd.DataFrame) -> str:
        """
        ГРАФИК 6: Количество задач по степени серьезности (приоритетам).
        Задание: "количество задач по степени серьезности"
        
        Args:
            df_all: DataFrame со всеми задачами
            
        Returns:
            str: Путь к сохранённому файлу
        """
        fig, ax = plt.subplots(figsize=(self.figure_size['width'], self.figure_size['height']))
        
        if 'priority' in df_all.columns:
            priority_data = df_all['priority'].dropna()
            
            if len(priority_data) > 0:
                priority_counts = priority_data.value_counts()
                
                # Сортируем по убыванию
                priority_counts = priority_counts.sort_values(ascending=False)
                
                # Создаём столбчатую диаграмму
                bars = ax.bar(
                    range(len(priority_counts)),
                    priority_counts.values,
                    color=plt.cm.Set2(np.linspace(0, 1, len(priority_counts))),
                    edgecolor='black',
                    alpha=0.8
                )
                
                # Настройка осей
                ax.set_xlabel('Степень серьезности (приоритет)', fontsize=12)
                ax.set_ylabel('Количество задач', fontsize=12)
                ax.set_xticks(range(len(priority_counts)))
                ax.set_xticklabels(priority_counts.index, rotation=45, ha='right')
                
                # Добавляем значения на столбцы
                for bar, value in zip(bars, priority_counts.values):
                    height = bar.get_height()
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        height + 0.5,
                        str(value),
                        ha='center',
                        va='bottom',
                        fontsize=10,
                        fontweight='bold'
                    )
                
                # Статистика
                total_tasks = len(df_all)
                priority_tasks = len(priority_data)
                if total_tasks > 0:
                    percentage = (priority_tasks / total_tasks) * 100
                    stats_text = f'Задач с приоритетом: {priority_tasks}/{total_tasks} ({percentage:.1f}%)'
                    ax.text(
                        0.71, 0.98, stats_text,
                        transform=ax.transAxes,
                        fontsize=10,
                        verticalalignment='top',
                        bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8)
                    )
                
                ax.grid(True, alpha=0.3, axis='y')
            else:
                ax.text(0.5, 0.5, 'Нет данных о приоритетах', 
                       ha='center', va='center', fontsize=12)
        else:
            ax.text(0.5, 0.5, 'Нет данных о приоритетах', 
                   ha='center', va='center', fontsize=12)
        
        ax.set_title('ГРАФИК 6: Распределение задач по степени серьезности (все задачи)', 
                    fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        filename = f"6_priority_distribution.{self.save_format}"
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=self.dpi, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"График 6 создан: {filepath}")
        return filepath


# ========== ФУНКЦИЯ ДЛЯ ТЕСТИРОВАНИЯ ==========

def test_plot_builder():
    """Тестирование модуля построения графиков."""
    print("Тестирование PlotBuilder...")
    
    import datetime
    
    # Тестовые данные
    test_plot_data = {
        'open_time_data': pd.Series([24, 48, 72, 96, 120, 144, 168, 192, 216, 240]),
        'daily_tasks_data': {
            'dates': pd.date_range('2024-01-01', periods=10),
            'created': [3, 5, 2, 4, 6, 3, 5, 2, 4, 3],
            'resolved': [2, 3, 4, 2, 5, 3, 4, 2, 3, 2],
            'created_cumulative': [3, 8, 10, 14, 20, 23, 28, 30, 34, 37],
            'resolved_cumulative': [2, 5, 9, 11, 16, 19, 23, 25, 28, 30]
        }
    }
    
    # Тестовый DataFrame для всех задач
    test_df_all = pd.DataFrame({
        'reporter': ['User A', 'User B', 'User A', 'User C', 'User B'] * 4,
        'assignee': ['Dev A', 'Dev B', 'Dev A', 'Dev C', 'Dev B'] * 4,
        'priority': ['Critical', 'Major', 'Minor', 'Trivial', 'Major'] * 4,
        'status': ['Closed', 'Open', 'In Progress', 'Resolved', 'Closed'] * 4,
        'open_time_hours': [24, 48, 72, 96, 120] * 4
    })
    
    # Тестовый DataFrame для закрытых задач
    test_df_closed = pd.DataFrame({
        'status': ['Closed', 'Closed', 'Closed', 'Closed', 'Closed'] * 4,
        'open_time_hours': [24, 48, 72, 96, 120] * 4
    })
    
    # Тестовая конфигурация
    test_config = {
        "visualization": {
            "output_dir": "test_reports",
            "figure_size": {"width": 10, "height": 6},
            "dpi": 100,
            "save_format": "png"
        }
    }
    
    # Создаём строитель графиков
    builder = PlotBuilder(test_config)
    
    print("\n1. Создание всех 6 графиков:")
    plot_paths = builder.create_all_plots(test_plot_data, test_df_all, test_df_closed)
    
    print(f"\n2. Создано {len(plot_paths)} графиков:")
    for plot_name, path in plot_paths.items():
        print(f"   • {plot_name}: {path}")
    
    print("\nТестирование завершено!")
    print("Проверьте папку 'test_reports' для просмотра графиков.")
    
    return builder


if __name__ == "__main__":
    # При прямом запуске тестирует модуль
    test_plot_builder()