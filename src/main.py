import sys    # Для работы с системными параметрами и завершения программы
import os     # Для работы с файловой системой и путями
import logging   # Для ведения логов (записей о работе программы)

# Путь к корневой папке проекта в путь поиска модулей
# Чтобы Python мог находить наши модули в папке src/
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Импортирование наших собственных модулей
try:
    from src.config import get_config      # Функция для загрузки конфигурации
    from src.jira_client import JiraClient  # Класс для работы с JIRA API
    from src.data_processor import DataProcessor  # Класс для обработки данных
    from src.plot_builder import PlotBuilder  # Класс для построения графиков - ДОБАВЛЕН!
    IMPORT_SUCCESS = True  # Флаг: все модули успешно импортированы
except ImportError as e:
    # Если какой-то модуль не найден (ещё не реализован)
    IMPORT_SUCCESS = False  # Флаг: импорт не удался
    print(f"Ошибка: {e}")  # Ошибка


def setup_logging(config):
    """Настройка логирования."""
    # Настройка системы логирования
    logging.basicConfig(
        # Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        # Берёт из конфигурации или использует INFO по умолчанию
        level=getattr(logging, config.get("logging", {}).get("level", "INFO")),
        # Формат вывода логов
        # Берёт из конфигурации или использует простой формат
        format=config.get("logging", {}).get("format", "%(message)s"),
    )


def print_banner():
    """Вывод заголовка программы при запуске."""
    print("\n" + "="*50)  # Верхняя разделительная линия
    print("JIRA ANALYTICS TOOL")  # Название программы
    print("="*50 + "\n")  # Нижняя разделительная линия


def main():
    """Главная функция программы - точка входа."""
    print_banner()  # Выводим красивый заголовок
    
    try:
        # 1. Загрузка конфигурации
        print("[1/8] Загрузка конфигурации...")  # Шаг 1 из 8 
        config = get_config()  # Получает настройки из config.py
        jira_config = config.get("jira", {})  # Извлекаем настройки JIRA
        # Выводит информацию о проекте и сервере
        print(f"Проект: {jira_config.get('project_key', 'KAFKA')}")
        print(f"Сервер: {jira_config.get('server', 'https://issues.apache.org/jira')}")
        print(f"Максимум задач: {jira_config.get('max_issues', 1000)}")
        
        setup_logging(config)  # Настраивает систему логирования
        
        # Проверяет, все ли модули импортировались
        if not IMPORT_SUCCESS:
            print("\n[ВНИМАНИЕ] Не все модули доступны.")
            print("Это демонстрационная версия программы.")
            return 0  # Завершает программу успешно (демо-версия)
        
        # 2. Подключение к JIRA
        print("\n[2/8] Подключение к JIRA...")
        jira_client = JiraClient(config)  # Создает клиент для работы с JIRA
        
         # 3. Загрузка задач (для демонстрации загружает разумное количество)
        print("   Загрузка задач...")
        
        # Загружаем два набора данных
        # 3.1 Для графиков 1, 2, 5 -  закрытые задачи
        print("   a) Загрузка закрытых задач...")
        max_closed = min(jira_config.get('max_issues', 1000), 500)  # Не более 500 для скорости
        closed_issues = jira_client.get_closed_issues(max_results=max_closed)
        
        # Проверка, удалось ли загрузить закрытые задачи
        if not closed_issues:
            print("   Не удалось загрузить закрытые задачи. Возможные причины:")
            print("   • Нет подключения к интернету")
            print("   • Публичный JIRA сервер недоступен")
            print("   • В проекте нет закрытых задач")
            print("\n   Программа завершена, так как нет данных для анализа.")
            return 1  # Завершаем с ошибкой
        
        # 3b. Для графиков 3, 4, 6 - ВСЕ задачи (открытые, в работе и закрытые)
        print("   b) Загрузка всех задач...")
        max_all = min(jira_config.get('max_issues', 1000), 500)  
        
        all_issues = jira_client.get_all_issues(max_results=max_all)
        
        # Проверка, удалось ли загрузить все задачи
        if not all_issues:
            print("   ВНИМАНИЕ: Не удалось загрузить все задачи.")
            print("   Использую закрытые задачи для всех графиков как fallback.")
            all_issues = closed_issues  # Fallback на закрытые задачи
            print("   Рекомендуется проверить подключение к JIRA API.")
        else:
            # Анализируем состав задач для информативности
            closed_count = sum(1 for issue in all_issues if issue.get('status') == 'Closed')
            other_count = len(all_issues) - closed_count
            print(f"   Загружено {len(all_issues)} задач: {closed_count} закрытых, {other_count} с другими статусами")
            
            # Собираем уникальные статусы для отображения
            unique_statuses = set()
            for issue in all_issues:
                if issue.get('status'):
                    unique_statuses.add(issue['status'])
            if unique_statuses:
                print(f"   Найдены статусы: {', '.join(sorted(unique_statuses))}")
        
        print(f"   Загружено {len(closed_issues)} закрытых задач")
        if all_issues != closed_issues:
            print(f"   Загружено {len(all_issues)} всех задач (включая разные статусы)")
        
        # 4. Обработка данных
        print("\n[3/8] Обработка данных...")
        data_processor = DataProcessor(config)  # Создает обработчик данных
        
        # Создаем два DataFrame
        # 4.1 DataFrame для закрытых задач (графики 1, 2, 5)
        df_closed = data_processor.create_dataframe(closed_issues)
        
        # 4.2 DataFrame для всех задач (графики 3, 4, 6)
        df_all = data_processor.create_dataframe(all_issues)
        
        # Проверяет, есть ли данные для обработки
        if df_closed.empty:
            print("   Нет данных для обработки (закрытые задачи)")
            return 1  # Возвращает код ошибки
        
        print(f"   Обработано {len(df_closed)} закрытых задач")
        print(f"   Обработано {len(df_all)} всех задач")
        
        # 5. Статистика
        print("\n[4/8] Анализ статистики...")
        #Статистику считаем только по закрытым задачам (по заданию)
        stats = data_processor.get_statistics(df_closed)
        
        # Выводит основную статистику
        print(f"   Всего задач (закрытых): {stats.get('total_tasks', 0)}")
        if 'time_stats' in stats:
            time_stats = stats['time_stats']
            print(f"   Среднее время выполнения: {time_stats.get('mean', 0):.1f} часов")
            print(f"   Медиана: {time_stats.get('median', 0):.1f} часов")
            print(f"   Минимальное время: {time_stats.get('min', 0):.1f} часов")
            print(f"   Максимальное время: {time_stats.get('max', 0):.1f} часов")
        
        # 6. Подготовка данных для графиков
        print("\n[5/8] Подготовка данных для графиков...")
        # Подготавливаем данные отдельно для разных наборов
        
        # Для графиков 1, 2, 5 (закрытые задачи)
        plot_data_closed = data_processor.prepare_for_plotting(df_closed)
        
        # Для графиков 3, 4, 6 (все задачи)
        plot_data_all = data_processor.prepare_for_plotting(df_all)
        
        # Объединяет данные для передачи в PlotBuilder
        plot_data = {**plot_data_closed, **plot_data_all}
        
        print(f"   Подготовлено {len(plot_data)} наборов данных для графиков")
        
        # 7. Создание объекта для построения графиков
        print("\n[6/8] Инициализация построителя графиков...")
        plot_builder = PlotBuilder(config)  # Создает объект для построения графиков
        
        # 8. Построение всех 6 графиков согласно заданию
        print("\n[7/8] Построение 6 графиков аналитики...")
        # Передает оба DataFrame в PlotBuilder
        # df_all - для графиков 3, 4, 6
        # df_closed - для графиков 1, 2, 5 (PlotBuilder должен использовать его внутри методов)
        plot_paths = plot_builder.create_all_plots(plot_data, df_all, df_closed)
        
        # Выводит информацию о созданных графиках
        print(f"   Создано {len(plot_paths)} графиков:")
        for plot_name, plot_path in plot_paths.items():
            # Извлекает только имя файла из полного пути
            filename = os.path.basename(plot_path)
            print(f"   • {filename}")
        
        # 9. Завершение работы
        print("\n[8/8] Программа успешно завершена!")
        
        # Выводит итоговое сообщение со списком всех графиков
        print("\n" + "="*60)
        print("ВСЕ 6 ГРАФИКОВ УСПЕШНО ПОСТРОЕНЫ")
        print("="*60)
        print("\nСозданные графики (соответствие заданию):")
        print("1. open_time_histogram.png     - Время в открытом состоянии (закрытые задачи)")
        print("2. status_times.png            - Распределение по состояниям (закрытые задачи)")
        print("3. daily_tasks.png             - Задачи по дням с накопительным итогом (все задачи)")
        print("4. top_users.png               - Топ-30 пользователей (все задачи)")
        print("5. logged_time_histogram.png   - Залогированное время (закрытые задачи)")
        print("6. priority_distribution.png   - Распределение по приоритетам (все задачи)")
        
        print("\n" + "="*60)
        print("Графики сохранены в папке 'reports/'")
        print("="*60)
        
        print("\nПримечания:")
        print("• Графики 1, 2, 5 строятся на закрытых задачах (требование задания)")
        print("• Графики 3, 4, 6 строятся на всех задачах")
        print("• Графики 5 и 6 являются упрощёнными версиями")
        print("• Для полной реализации требуется доступ к worklog и changelog JIRA")
        print("• Для просмотра графиков откройте файлы в папке 'reports/'")
        
        return 0  # Успешное завершение программы
        
    except KeyboardInterrupt:
        # Обработка прерывания пользователем (Ctrl+C)
        print("\n\n[ИНФО] Работа прервана пользователем")
        return 130  # Стандартный код завершения для Ctrl+C
        
    except Exception as e:
        # Обработка любых других ошибок
        print(f"\n[ОШИБКА] {e}")
        import traceback  # Для детальной информации об ошибке
        traceback.print_exc()  # Выводит полный стек вызовов
        return 1  # Код ошибки
     

if __name__ == "__main__":
    # Точка входа в программу
    # Выполняется только если файл запущен напрямую (python src/main.py)
    sys.exit(main())  # Запускает главную функцию и передает её код возврата в систему