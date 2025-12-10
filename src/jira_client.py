"""
Модуль для работы с JIRA API.
Загружает задачи из JIRA для анализа.
"""
import os        # Фйловая система
import json      # Сохранение и загрузка данных в формате JSON
import logging   # Ведение логов работы программы
from datetime import datetime, timedelta  # Работа с датами и временем
from typing import List, Dict, Any  # Типизация для лучшей читаемости кода

# Проверяет установку библиотеки jira
try:
    from jira import JIRA                # Основной класс для работы с JIRA API
    from jira.exceptions import JIRAError  # Класс для обработки ошибок JIRA
    JIRA_AVAILABLE = True                # Флаг: библиотека установлена
except ImportError:
    JIRA_AVAILABLE = False               # Флаг: библиотека не установлена
    print("[ВНИМАНИЕ] Установите библиотеку: pip install jira")  


class JiraClient:
    """Клиент для подключения к JIRA и загрузки данных."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Инициализация клиента JIRA.
        
        Args:
            config: Конфигурация из config.py
        """
        self.config = config                          # Сохраняем конфигурацию
        self.logger = logging.getLogger(__name__)     # Логгер 
        
        # Настройки из конфигурации
        jira_config = config.get("jira", {})          # Раздел с настройками JIRA
        self.server = jira_config.get("server", "https://issues.apache.org/jira")  # Адрес сервера
        self.project_key = jira_config.get("project_key", "KAFKA")  # Ключ проекта
        self.max_issues = jira_config.get("max_issues", 1000)  # Максимальное количество задач
        
        # Клиент JIRA (создаётся при первом использовании)
        self._jira = None                              # Инициализирует как None
        
        # Настройки кэширования
        self.cache_dir = "data/cache"                 # Папка для хранения кэшированных данных
        self.cache_duration = timedelta(hours=1)      # Кэш действителен 1 час
        
        # Создаёт папку для кэша если её нет
        if not os.path.exists(self.cache_dir):        # Проверяет существует ли папка
            os.makedirs(self.cache_dir)               # Создаёт папку и все родительские
    
    def get_jira_client(self):
        """Создаёт подключение к JIRA."""
        if self._jira is None:                        # Если клиент ещё не создан
            try:
                # Подключение к JIRA (анонимное для публичных серверов)
                self._jira = JIRA(server={'server': self.server})  # Создаёт объект JIRA
                self.logger.info(f"Подключение к JIRA: {self.server}")  # Логирует подключение
            except Exception as e:
                self.logger.error(f"Ошибка подключения: {e}")  # Логирует ошибку
                raise                                         # Пробрасывает исключение дальше
        return self._jira                                     # Возвращает созданный клиент
    
    def _get_cache_filename(self, cache_key: str) -> str:
        """Генерирует имя файла для кэша."""
        safe_key = cache_key.replace('/', '_').replace(':', '_')  # Заменяет небезопасные символы
        return os.path.join(self.cache_dir, f"{self.project_key}_{safe_key}.json")  # Полный путь
    
    def _is_cache_valid(self, cache_file: str) -> bool:
        """Проверяет актуальность кэша."""
        if not os.path.exists(cache_file):            # Если файл не существует
            return False                              # Кэш невалиден
        
        # Проверяет время последнего изменения файла
        cache_time = datetime.fromtimestamp(os.path.getmtime(cache_file))  # Время изменения файла
        return datetime.now() - cache_time < self.cache_duration  # Сравнивает с текущим временем
    
    def _load_from_cache(self, cache_file: str) -> List[Dict]:
        """Загружает данные из кэша."""
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:  # Открывает файл для чтения
                return json.load(f)                             # Загружает JSON данные
        except (json.JSONDecodeError, FileNotFoundError):       # Если файл повреждён или не найден
            return []                                           # Возвращает пустой список
    
    def _save_to_cache(self, cache_file: str, data: List[Dict]) -> None:
        """Сохраняет данные в кэш."""
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:  # Открывает файл для записи
                json.dump(data, f, ensure_ascii=False, indent=2)  # Сохраняет данные в JSON
        except Exception as e:
            self.logger.error(f"Ошибка сохранения кэша: {e}")   # Логирует ошибку сохранения
    
    def get_closed_issues(self, max_results: int = None) -> List[Dict]:
        """
        Загружает закрытые задачи проекта.
        
        Args:
            max_results: Максимальное количество задач
            
        Returns:
            List[Dict]: Список задач
        """
        if not JIRA_AVAILABLE:                          # Проверяет библиотеку
            self.logger.error("Библиотека jira не установлена")  # Логирует ошибку
            return []                                            # Возвращает пустой список
        
        if max_results is None:                          # Если не указано количество
            max_results = self.max_issues                # Использует значение из конфигурации
        
        cache_key = f"closed_issues_{max_results}"       # Уникальный ключ для кэша
        cache_file = self._get_cache_filename(cache_key)  # Полный путь к файлу кэша
        
        # Загрузка из кэша
        if self._is_cache_valid(cache_file):             # Если кэш актуален
            cached_data = self._load_from_cache(cache_file)  # Загружает данные
            if cached_data:                               # Если данные не пустые
                self.logger.info(f"Данные загружены из кэша: {len(cached_data)} задач")  # Логирует
                return cached_data                        # Возвращает кэшированные данные
        
        # Загружает из JIRA
        self.logger.info(f"Загрузка закрытых задач проекта {self.project_key}...")  # Логируем начало
        
        try:
            jira = self.get_jira_client()                # Получает подключение к JIRA
            
            # JQL запрос для получения закрытых задач
            jql = f'project = {self.project_key} AND status = Closed ORDER BY created DESC'
            
            issues = []                                   # Список для хранения задач
            start_at = 0                                  # Начальная позиция для пагинации
            batch_size = 100                              # Размер пачки за один запрос
            
            while len(issues) < max_results:              # Пока не набрали нужное количество
                batch = jira.search_issues(               # Поиск задач
                    jql,                                  # JQL запрос
                    startAt=start_at,                     # С какой задачи начинать
                    maxResults=min(batch_size, max_results - len(issues)),  # Сколько задач взять
                    fields="*all"                         # Загружает все поля
                )
                
                if not batch:                             # Если нет больше задач
                    break                                 # Прерывает цикл
                
                for issue in batch:                       # Для каждой задачи в пачке
                    issues.append(self._issue_to_dict(issue))  # Преобразует и добавляем в список
                
                start_at += len(batch)                    # Сдвигает позицию для следующей пачки
                self.logger.info(f"Загружено {len(issues)}/{max_results} задач...")  # Прогресс
                
                if len(batch) < batch_size:               # Если получил меньше batch_size
                    break                                 # Значит больше задач нет
            
            self._save_to_cache(cache_file, issues)       # Сохраняет загруженные данные
            
            self.logger.info(f"Загружено {len(issues)} закрытых задач")  # Финальное сообщение
            return issues                                 # Возвращает список задач
            
        except JIRAError as e:                            # Если ошибка JIRA API
            self.logger.error(f"Ошибка JIRA: {e}")        # Логирует ошибку
            return []                                     # Возвращает пустой список
        except Exception as e:                            # Любая другая ошибка
            self.logger.error(f"Ошибка: {e}")             # Логирует ошибку
            return []                                     # Возвращает пустой список
    
    #Загрузка всех задач
    def get_all_issues(self, max_results: int = None) -> List[Dict]:
        """
        Загружает ВСЕ задачи проекта (включая открытые, в работе и закрытые).
        Используется для графиков, где нужны все задачи:
        - Задачи по дням (график 3)
        - Топ пользователей (график 4)  
        - Распределение по приоритетам (график 6)
        
        Args:
            max_results: Максимальное количество задач
            
        Returns:
            List[Dict]: Список задач с различными статусами
        """
        if not JIRA_AVAILABLE:                          # Проверяет библиотеку
            self.logger.error("Библиотека jira не установлена")
            return []
        
        if max_results is None:                          # Если не указано количество
            max_results = self.max_issues                # Использует значение из конфигурации
        
        cache_key = f"all_issues_{max_results}"          # Уникальный ключ для кэша (отличается от закрытых!)
        cache_file = self._get_cache_filename(cache_key)  # Полный путь к файлу кэша
        
        # Загрузка из кэша
        if self._is_cache_valid(cache_file):             # Если кэш актуален
            cached_data = self._load_from_cache(cache_file)  # Загружает данные
            if cached_data:                               # Если данные не пустые
                self.logger.info(f"Данные загружены из кэша: {len(cached_data)} задач")
                return cached_data                        # Возвращает кэшированные данные
        
        # Загружает из JIRA
        self.logger.info(f"Загрузка ВСЕХ задач проекта {self.project_key}...")  # Логирует начало
        
        try:
            jira = self.get_jira_client()                # Получает подключение к JIRA
            
            # JQL запрос для получения ВСЕХ задач
            jql = f'project = {self.project_key} ORDER BY created DESC'
            
            issues = []                                   # Список для хранения задач
            start_at = 0                                  # Начальная позиция для пагинации
            batch_size = 100                              # Размер пачки за один запрос
            
            while len(issues) < max_results:              # Пока не набрали нужное количество
                batch = jira.search_issues(               # Поиск задач
                    jql,                                  # JQL запрос (ВСЕ задачи)
                    startAt=start_at,                     # С какой задачи начинать
                    maxResults=min(batch_size, max_results - len(issues)),  # Сколько задач взять
                    fields="*all"                         # Загружаем все поля
                )
                
                if not batch:                             # Если нет больше задач
                    break                                 # Прерываем цикл
                
                for issue in batch:                       # Для каждой задачи в пачке
                    issues.append(self._issue_to_dict(issue))  # Преобразуем и добавляем в список
                
                start_at += len(batch)                    # Сдвигает позицию для следующей пачки
                self.logger.info(f"Загружено {len(issues)}/{max_results} задач...")  # Прогресс
                
                if len(batch) < batch_size:               # Если получили меньше batch_size
                    break                                 # Значит больше задач нет
            
            self._save_to_cache(cache_file, issues)       # Сохраняет загруженные данные
            
            # Анализирует полученные статусы для отладки
            if issues:
                statuses = set()
                for issue in issues:
                    if 'status' in issue and issue['status']:
                        statuses.add(issue['status'])
                self.logger.info(f"Загружено {len(issues)} задач со статусами: {list(statuses)}")
            else:
                self.logger.warning(f"Не загружено ни одной задачи проекта {self.project_key}")
            
            return issues                                 # Возвращает список задач
            
        except JIRAError as e:                            # Если ошибка JIRA API
            self.logger.error(f"Ошибка JIRA: {e}")
            return []                                     # Возвращает пустой список
        except Exception as e:                            # Любая другая ошибка
            self.logger.error(f"Ошибка: {e}")
            return []                                     # Возвращает пустой список
    
    def _issue_to_dict(self, issue) -> Dict[str, Any]:
        """Преобразует объект задачи JIRA в словарь."""
        fields = issue.fields                             # Получает поля задачи
        
        issue_dict = {                                    # Создаёт словарь с основными полями
            'key': issue.key,                             # Ключ задачи (например "KAFKA-123")
            'summary': fields.summary,                    # Заголовок задачи
            'created': fields.created,                    # Дата создания
            'status': fields.status.name if fields.status else None,  # Статус
            'priority': fields.priority.name if fields.priority else None,  # Приоритет
        }
        
        # Дата закрытия и время выполнения (только для закрытых задач)
        if fields.resolutiondate:                         # Если задача закрыта
            issue_dict['resolved'] = fields.resolutiondate  # Дата закрытия
            try:
                # Преобразует строки в объекты datetime
                created = datetime.fromisoformat(fields.created.replace('Z', '+00:00'))
                resolved = datetime.fromisoformat(fields.resolutiondate.replace('Z', '+00:00'))
                # Вычисляет время выполнения в часах
                issue_dict['open_time_hours'] = (resolved - created).total_seconds() / 3600
            except (ValueError, AttributeError):          # Если не удалось преобразовать
                issue_dict['open_time_hours'] = None      # Устанавливает None
        else:
            # Для незакрытых задач время выполнения не вычисляет
            issue_dict['resolved'] = None
            issue_dict['open_time_hours'] = None
        
        # Автор и исполнитель
        if fields.reporter:                               # Если есть автор
            issue_dict['reporter'] = fields.reporter.displayName  # Имя автора
        if fields.assignee:                               # Если есть исполнитель
            issue_dict['assignee'] = fields.assignee.displayName  # Имя исполнителя
        
        return issue_dict                                 # Возвращает готовый словарь