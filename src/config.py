import os  # Файловая система и проверка существования файлов
import yaml  # YAML файлы (формат конфигурации)


def load_config(config_path="configs/settings.yaml"):
    """
    Загрузка конфигурации из YAML файла.
    
    Args:
        config_path: Путь к файлу конфигурации
        
    Returns:
        dict: Конфигурация в виде словаря
    """
    if not os.path.exists(config_path):
        # Возвращаем конфигурацию по умолчанию, если файл не найден
        return {
            "jira": {  # Раздел настроек JIRA
                "server": "https://issues.apache.org/jira",  # Адрес сервера JIRA
                "project_key": "KAFKA",  # Ключ проекта JIRA
                "max_issues": 1000,  # Максимальное количество задач для загрузки
                "use_cache": True  # Кеширование
            },
            "visualization": {  # Раздел настроек визуализации
                "output_dir": "reports"  # Папка для сохранения отчётов и графиков
            }
        }
    
    # Если файл существует, открываем его для чтения
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)  # Безопасная загрузка YAML (без исполнения кода)


def get_config():
    """
    Получение конфигурации приложения.
    
    Returns:
        dict: Конфигурация
    """
    config = load_config()  # Конфигурация из файла
    
    # Форматирование JQL фильтров
    if "jql_filters" in config.get("jira", {}):
        project_key = config["jira"]["project_key"]  # Ключ проекта
        jql_filters = config["jira"]["jql_filters"]  # Фильтры JQL
        for key, value in jql_filters.items():
            # Подставляем project_key в JQL запросы
            jql_filters[key] = value.format(project_key=project_key)
    
    return config  # Готовая конфигурацию


# Тестирование
if __name__ == "__main__":
    # Этот код выполняется только при прямом запуске файла
    config = get_config()  # Получаем конфигурацию
    print("Конфигурация загружена успешно:")
    print(f"  Сервер: {config['jira']['server']}")  # Выводим адрес сервера
    print(f"  Проект: {config['jira']['project_key']}")  # Выводим ключ проекта