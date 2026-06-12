"""
Tokamak MEPHI API Client
========================

Клиент для доступа к файловому хранилищу с данными импульсов плазмы токамака МИФИСТ через сеть Интернет.
Поддерживает авторизацию через токены, обработку сообщений сервера, кэширование файлов и очищение кэша. 
"""
import io, sys, os, requests, h5py, re, time, json
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from tqdm import tqdm
from .config import Config, SERVER_MESSAGE
from mephistdatakit import __version__

class Client:
    """
    Клиент для взаимодействия с shots-api сервером токамака МИФИСТ.
    
    Этот класс предоставляет методы для аутентификации, получения списка импульсов,
    скачивания файлов, их кэширования и управления кэшем.
    
    """
    
    def __init__(self, config_filename: str = "config.yaml"):

        """
        Инициализация клиента.
         Args:
            config_filename (str): название конфигурационного файла. 
            Может быть как названием файла, так и полным путём. По умолчанию config.yaml.
            Желательно, чтобы запуск программы с вызовом объекта Client() производился в корневой директории проекта
        """
        
        config = Config(config_filename)
        
        # Получаем логгер для этого модуля из объекта - синглтона
        self.logger = config.get_logger('api')
        
        self.base_url = config.base_url
        self.base_path = config.base_path
        self.api_token = config.api_token
        self.cache_enabled = config.cache_enabled
        self.cache_dir = config.cache_dir
        self.timeout = config.timeout
        self.chunk_size = config.chunk_size
        self.show_progress = config.show_progress
        self.cache_max_bytes = config.cache_max_bytes
        self.show_server_messages = config.show_server_messages
        self.last_message = ""
        self.client_version = __version__
        self.verbose_stats =config.verbose_stats
        
        # Создаем сессию
        self.session = requests.Session()
        self.session.verify = config.verify_ssl
        self.session.timeout = self.timeout

        if self.api_token:
            self.session.headers.update({
                "Authorization": f"Bearer {self.api_token}",
                "client-version": __version__,
                "client-cache-size": f"{self.cache_info().get('total_size_mb'):.2f}",       
            })
        
        if self.cache_enabled:
            os.makedirs(self.cache_dir, exist_ok=True)
    
    def _log_server_message(self, message: str) -> None:
        """
        Надстройка над logging. Логирует сообщения от сервера с эмодзи 💬.
        
        Args:
            message (str): Сообщение от сервера
        """
        if self.show_server_messages and message:
            self.logger.log(SERVER_MESSAGE, f"Сообщение сервера: {message}")
    
    def _format_speed(self, bytes_per_second: float) -> str:
        """
        Форматирует скорость в человеко-читаемый вид.
        
        Args:
            bytes_per_second (float): Скорость в байтах в секунду
            
        Returns:
            str: Отформатированная строка скорости
        """
        if bytes_per_second >= 1024 ** 3:  # GB/s
            return f"{bytes_per_second / (1024 ** 3):.2f} GB/s"
        elif bytes_per_second >= 1024 ** 2:  # MB/s
            return f"{bytes_per_second / (1024 ** 2):.2f} MB/s"
        elif bytes_per_second >= 1024:  # KB/s
            return f"{bytes_per_second / 1024:.2f} KB/s"
        else:  # B/s
            return f"{bytes_per_second:.0f} B/s"
    
    def _format_time(self, seconds: float) -> str:
        """
        Форматирует время в человеко-читаемый вид.
        
        Args:
            seconds (float): Время в секундах
            
        Returns:
            str: Отформатированная строка времени
        """
        if seconds < 1:
            return f"{seconds * 1000:.0f} мс"
        elif seconds < 60:
            return f"{seconds:.1f} с"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = seconds % 60
            return f"{minutes} мин {secs:.0f} с"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = seconds % 60
            return f"{hours} ч {minutes} мин {secs:.0f} с"
    
    def _download_shot_from_server(self, url: str, shot_id: int) -> Tuple[bytes, Dict[str, Any]]:
        """
        Скачивает файл  с сервера 
        
        Args:
            url (str): URL для скачивания
            shot_id (int): Идентификатор импульса
            
        Returns:
            Tuple[bytes, Dict[str, Any]]: (содержимое файла, статистика скачивания). 
            Статистика временно отключена, переменная Dict пустая
        """
        start_time = time.time()
        response = self.session.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        
        # Статистика.  Пока выключил её by NEEfimov
        stats = {
            'total_size': total_size,
            'start_time': start_time,
            'chunks': []
        }
        
        content = bytearray()
        
        try:
            if self.show_progress:
                
                self.logger.info(f"Скачивание импульса {shot_id}...")
                
                with tqdm(total=total_size, unit='B', unit_scale=True, 
                         unit_divisor=1024, desc=f"Импульс {shot_id}", 
                         bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} {rate_fmt}{postfix}]') as pbar: #[{elapsed}<{remaining},
                    
                    chunk_start_time = time.time()
                    for chunk in response.iter_content(chunk_size=self.chunk_size):
                        if chunk:
                            content.extend(chunk)
                            downloaded += len(chunk)
                            
                            pbar.update(len(chunk))
                            
                            # Записываем статистику по чанку
                            """
                            chunk_time = time.time() - chunk_start_time
                            if chunk_time > 0:
                                chunk_speed = len(chunk) / chunk_time
                                stats['chunks'].append({
                                    'size': len(chunk),
                                    'time': chunk_time,
                                    'speed': chunk_speed
                                })
                            chunk_start_time = time.time()
                            """
            else:
                # Без прогресс-бара
                self.logger.info(f"Скачивание импульса {shot_id}...")
                last_update_time = time.time()
                last_update_downloaded = 0
                
                for chunk in response.iter_content(chunk_size=self.chunk_size):
                    if chunk:
                        content.extend(chunk)
                        downloaded += len(chunk)
                        
                        # Обновляем статистику каждые 0.5 секунды
                        current_time = time.time()
                        if current_time - last_update_time >= 0.5:
                            chunk_size = downloaded - last_update_downloaded
                            chunk_time = current_time - last_update_time
                            """
                            if chunk_time > 0:
                                chunk_speed = chunk_size / chunk_time
                                stats['chunks'].append({
                                    'size': chunk_size,
                                    'time': chunk_time,
                                    'speed': chunk_speed
                                })
                            """
                            last_update_time = current_time
                            last_update_downloaded = downloaded
                
                """
                # Добавляем последний чанк
                if downloaded > last_update_downloaded:
                    chunk_size = downloaded - last_update_downloaded
                    chunk_time = time.time() - last_update_time
                    if chunk_time > 0:
                        chunk_speed = chunk_size / chunk_time
                        stats['chunks'].append({
                            'size': chunk_size,
                            'time': chunk_time,
                            'speed': chunk_speed
                        })
                """       
        except Exception as e:
            self.logger.error(f"Скачивание импульса {shot_id} не удалось. Причина: {str(e)}")
           
        total_time = time.time() - start_time
        
        # Рассчитываем среднюю скорость
        if total_time > 0:
            avg_speed = downloaded / total_time
        else:
            avg_speed = 0
        
        """
        stats.update({
            'downloaded': downloaded,
            'total_time': total_time,
            'avg_speed': avg_speed,
            'end_time': time.time()
        })
        """
        return bytes(content), stats
    
    def _print_download_stats(self, stats: Dict[str, Any], shot_id: int) -> None:
        """
        Выводит статистику скачивания.
        
        Args:
            stats (Dict[str, Any]): Статистика скачивания
            shot_id (int): Идентификатор импульса
        """
        total_size = stats['total_size']
        total_time = stats['total_time']
        avg_speed = stats['avg_speed']
        
        if total_time > 0:
            size_str = self._bytes_to_human(total_size)
            time_str = self._format_time(total_time)
            speed_str = self._format_speed(avg_speed)
            
            #self.logger.info(f"Импульс {shot_id} скачан: {size_str} за {time_str} ({speed_str})")
    
    def _parse_cache_size(self, size_str: str) -> int:
        """
        Парсит строку с размером кэша (например, "500 MB", "1GB", "100KB").
        
        Args:
            size_str (str): Строка с размером
            
        Returns:
            int: Размер в байтах
        """
        if not size_str or size_str == "0":
            return 0
        
        size_str = size_str.lower().replace(" ", "")
        
        # Регулярное выражение для поиска числа и единицы измерения
        pattern = r'^(\d+(?:\.\d+)?)([kmgt]?b)$'
        match = re.match(pattern, size_str)
        
        if not match:
            error_message = f"Неверный формат размера кэша в config.yaml: {size_str}. Используйте формат типа '500MB', '1GB', '100KB'"
            self.logger.error(error_message)
            sys.exit(1)  
        
        size_value = float(match.group(1))
        unit = match.group(2)
        
        units = {
            'b': 1,
            'kb': 1024,
            'mb': 1024 ** 2,
            'gb': 1024 ** 3,
            'tb': 1024 ** 4
        }
        
        if unit not in units:
            error_message = f"Неизвестная единица измерения в config.yaml: {unit}. Используйте B, KB, MB, GB, TB"
            self.logger.error(error_message)
            sys.exit(1)       
        
        return int(size_value * units[unit])
    
    def _get_cached_files_info(self) -> List[Tuple[Path, int, float]]:
        """
        Получает информацию о файлах в кэше.
        
        Returns:
            List[Tuple[Path, int, float]]: Список кортежей (путь, размер, время модификации)
        """
        cache_path = Path(self.cache_dir)
        if not cache_path.exists():
            return []
        
        files_info = []
        for cache_file in cache_path.glob("*.nxs"):
            if cache_file.exists():
                stat = cache_file.stat()
                files_info.append((cache_file, stat.st_size, stat.st_mtime))
        
        # Сортируем по времени модификации (старые файлы первыми)
        files_info.sort(key=lambda x: x[2])
        return files_info
    
    def _cleanup_cache_if_needed(self, new_file_size: int = 0) -> None:
        """
        Проверяет размер кэша и удаляет старые файлы при превышении лимита.
        
        Args:
            new_file_size (int): Размер нового файла, который будет добавлен и который нельзя удалять
        Returns:
            None
        """
        if not self.cache_enabled or self.cache_max_bytes <= 0:
            return
        
        files_info = self._get_cached_files_info()
        if not files_info:
            return
        
        current_size = sum(size for _, size, _ in files_info)
        total_size_with_new = current_size + new_file_size

        if total_size_with_new > self.cache_max_bytes:
            self.logger.warning(f"Размер кэша ({current_size / (1024**2):.2f} MB) превышает лимит "
                               f"({self.cache_max_bytes / (1024**2):.2f} MB). Удаляем старые файлы...")
            
            deleted_count = 0
            deleted_size = 0
            
            for file_path, file_size, mtime in files_info:
                if total_size_with_new <= self.cache_max_bytes:
                    break
                
                try:
                    file_path.unlink()
                    deleted_count += 1
                    deleted_size += file_size
                    total_size_with_new -= file_size
                except Exception as e:
                    self.logger.error(f"Ошибка при удалении {file_path.name}: {e}")
            
            if deleted_count > 0:
                self.logger.info(f"Удалено файлов: {deleted_count}, освобождено: {deleted_size / (1024**2):.2f} MB")
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Обрабатывает ответ сервера, извлекая сообщения и проверяя ошибки.
        
        Args:
            response (requests.Response): Ответ от сервера
            
        Returns:
            Dict[str, Any]: Данные ответа
            
        Raises:
            requests.exceptions.HTTPError: Если произошла ошибка HTTP
        """
        try:
            data = response.json()
            self.last_message = data.get("message", "")   
            return data
        except ValueError:
            # Если ответ не JSON (например, файл)
            self.last_message = response.headers.get("X-Message", "")
            return {"raw_response": response}
    
    def _get_cached_file(self, shot_id: int) -> Optional[h5py.File]:
        """
        Возвращает файл из кэша. Если не обнаруживает - возвращает None
        
        Args:
            shot_id (int): Идентификатор импульса
            
        Returns:
           h5py.File: HDF5 файл в кэше или None если файл не найден
        """
        
        try:
            if not self.cache_enabled:
                return None
            
            # Ищем файл в кэше
            cache_file = self.cache_dir + os.sep + f"{shot_id}MD.nxs"
            if os.path.exists(cache_file):
                # Обновляем время последнего доступа (через touch)
                Path(cache_file).touch()
                return h5py.File(cache_file, 'r') 
            
            return None
        except FileNotFoundError as e:
            self.logger.warning(f"Файл {shot_id}MD.nxs не найден: {e}")
            return None
        except Exception as e:
            self.logger.warning(f"Ошибка при доступе к кэшированному файлу {shot_id}MD.nxs: {e}")
            return None

    def _save_to_cache(self, shot_id: str, content: bytes) -> Optional[Path]:
        """
        Сохраняет файл в кэш с проверкой лимита размера.
        
        Args:
            shot_id (str): Идентификатор импульса
            content (bytes): Содержимое файла
            
        Returns:
            Path: Путь к сохраненному файлу или None в случае ошибки
        """
        if not self.cache_enabled:
            self.logger.warning("Кэширование запрещено настройками")
            return None
        
        # Проверяем и очищаем кэш перед сохранением
        self._cleanup_cache_if_needed(len(content))
        
        cache_file = Path(self.cache_dir + os.sep + f"{shot_id}MD.nxs")
        
        try:
            cache_file.write_bytes(content)
            self.logger.info(f"Файл сохранен в кэш: {cache_file.name} ({len(content) / (1024*1024):.1f} MB)")
            
            # После сохранения проверяем, что не превысили лимит
            self._cleanup_cache_if_needed(0)
            
            return cache_file
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении в кэш: {e}")
            return None
    
    def test_connection(self) -> bool:
        """
        Проверяет соединение с shots-api сервером.
        
        Returns:
            bool: True если соединение успешно, False в противном случае
        """
        try:
            response = self.session.get(f"{self.base_url}/{self.base_path}/health")
            response.raise_for_status()
            health_status = self._handle_response(response)
            self.logger.info("Сервер доступен и отвечает")
            return True
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Не удалось подключиться к серверу.\n  Проверьте наличие доступа в сеть\n  Проверьте корректность адреса {self.base_url}\n  Обратитесь к администратору tokamak@mephi.ru")
            sys.exit(1)
            return False
        
    def authenticate(self) -> Dict[str, Any]:
        """
        Проверяет аутентификацию и получает информацию о пользователе.
        Проверяет актуальность версии клиентского приложения
        Необязательно к вызову для скачивания файлов, так как 
        при каждом скачивании токен передаётся независимо
        
        Returns:
            Dict[str, Any]: Информация о пользователе и статус аутентификации
            
        Raises:
            requests.exceptions.HTTPError: Если произошла ошибка аутентификации
        """
        try:
            response = self.session.get(f"{self.base_url}/{self.base_path}/auth/test")
            response.raise_for_status()
            auth_info = self._handle_response(response)
            self.logger.info("Аутентификация успешна")
            
            server_message = auth_info.get('message')
            if server_message:
                self._log_server_message(server_message)
            
            # проверка актуальности версии клиента
            last_client_version = auth_info.get('user', {}).get('version')
            if last_client_version and self.client_version:
                try:
                    current_version_num = int(self.client_version.replace(".", ""))
                    last_version_num = int(last_client_version.replace(".", ""))
                    if current_version_num < last_version_num:
                        self.logger.warning(f"Версия вашего приложения устарела! Актуальная версия: {last_client_version}. Ваша версия: {self.client_version}")
                        self.logger.warning("Выполните команду git pull, находясь в локальной сети лаборатории, для обновления")
                except (ValueError, AttributeError):
                    pass
            
            return auth_info
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"Ошибка аутентификации: {e}")
            if e.response.status_code == 401:
                try:
                    error_data = e.response.json()
                    server_message = error_data.get('message')
                    if server_message:
                        self._log_server_message(server_message)
                except:
                    pass
            sys.exit(1)
    
    def get_shots_list(self) -> list[int]:
        """
        Получает список доступных на сервере импульсов.
        Попытка скачивания импульса не из этого списка приведёт к ошибке скачивания
        Returns:
            list[int]
        Raises:
            requests.exceptions.HTTPError: Если произошла ошибка HTTP
        """
        try:
            response = self.session.get(f"{self.base_url}/{self.base_path}/shots-list")
            response.raise_for_status()
            shots_data = self._handle_response(response)
            self.logger.info("Получен список импульсов")
            
            server_message = shots_data.get('message')
            if server_message:
                self._log_server_message(server_message)
            
            return shots_data.get('shots', [])
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"Ошибка при получении списка импульсов: {e}")
            return []
    
    def get_shot(self, shot_id: int, force_download: bool = False) -> Optional[h5py.File]:
        """
        Скачивает HDF5 файл импульса с сервера или возвращает из кэша.
        При наличии файлов в кэше вообще не обращается к серверу, так что
        работа может вестись офлайн.
        
        Args:
            shot_id (int): Идентификатор импульса
            force_download (bool): Принудительно скачать с сервера, игнорируя кэш
            
        Returns:
            h5py.File: hdf5 файл или None в случае ошибки
            
        Raises:
            requests.exceptions.HTTPError: Если произошла ошибка HTTP
            FileNotFoundError: Если импульс не найден
        """
        
        try:
            # Проверяем кэш если включено и не принудительная загрузка
            if self.cache_enabled and not force_download:
                cached_file = self._get_cached_file(shot_id)
                if cached_file:
                    self.logger.info(f"Импульс {shot_id} загружен из кэша")
                    return cached_file
            
            # Формируем URL для скачивания
            download_url = f"{self.base_url}/{self.base_path}/shots/{shot_id}/download"
            
            # Скачиваем с сервера с прогресс-баром
            content, download_stats = self._download_shot_from_server(download_url, shot_id)
            
            # Получаем сообщение из заголовков
            response = self.session.get(download_url, stream=True)
            response.raise_for_status()
            server_message = str(response.headers.get('x-message', ''))
            if server_message:
                self._log_server_message(server_message)
            
            # Выводим статистику скачивания
            #self._print_download_stats(download_stats, shot_id)
            
            # Сохраняем в кэш если включено
            if self.cache_enabled:
                self._save_to_cache(str(shot_id), content)
               
            file_bytes = io.BytesIO(content)
            return h5py.File(file_bytes, 'r')
        
        except FileNotFoundError as e:
            self.logger.warning(f"Импульс {shot_id} не найден")
            return None
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"Ошибка при скачивании. Импульс {shot_id} не найден")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    server_message = error_data.get('message', '')
                    if server_message:
                        self._log_server_message(server_message)
                except:
                    pass
            return None
        except Exception as e:
            self.logger.error(f"Неизвестная ошибка при скачивании: {e}")
            return None
        

    def update_repo(self) -> int:
        """
        Скачивает с сервера последнюю версию репозитория
        TODO
        """
        pass 


    def clear_cache(self) -> int:
        """
        Полностью очищает кэш файлов.
        
        Returns:
            int: Количество удаленных файлов
        """
        if not Path(self.cache_dir).exists():
            return 0
        
        deleted_count = 0
        for cache_file in Path(self.cache_dir).glob("*.nxs"):
            try:
                cache_file.unlink()
                deleted_count += 1
            except Exception as e:
                self.logger.error(f"Ошибка при удалении файла {cache_file.name}: {e}")
        
        if deleted_count > 0:
            self.logger.info(f"Кэш очищен. Удалено файлов: {deleted_count}")
        
        return deleted_count
    
    def cache_info(self) -> Dict[str, Any]:
        """
        Получает информацию о кэше.
        
        Returns:
            Dict[str, Any]: Информация о кэше
        """
        if not Path(self.cache_dir).exists():
            return {
                "enabled": self.cache_enabled,
                "files_count": 0,
                "total_size": 0,
                "total_size_mb": 0,
                "cache_max_bytes": self.cache_max_bytes,
                "cache_max_human": self._bytes_to_human(self.cache_max_bytes) if self.cache_max_bytes > 0 else "не ограничен"
            }
        
        files_info = self._get_cached_files_info()
        total_size = sum(size for _, size, _ in files_info)
        
        cache_info_dict = {
            "enabled": self.cache_enabled,
            "cache_dir": str(self.cache_dir),
            "files_count": len(files_info),
            "total_size": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "cache_max_bytes": self.cache_max_bytes,
            "cache_max_human": self._bytes_to_human(self.cache_max_bytes) if self.cache_max_bytes > 0 else "не ограничен"
        }
        
        # Добавляем детальную информацию о файлах только если уровень логирования logging.INFO (20) или ниже
        if self.logger.isEnabledFor(20):
            cache_info_dict["files"] = [
                {
                    "name": file_path.name,
                    "size": size,
                    "size_human": self._bytes_to_human(size),
                    "modified": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mtime)),
                    "modified_timestamp": mtime
                }
                for file_path, size, mtime in files_info
            ]
        
        return cache_info_dict
    
    def cache_management(self, action: str = "info", **kwargs) -> Dict[str, Any]:
        """
        Управление кэшем через единый интерфейс.
        
        Args:
            action: Действие ('info', 'clear', 'cleanup', 'list')
            **kwargs: Параметры для действия
            
        Returns:
            Dict[str, Any]: Результат выполнения
        """
        actions = {
            'info': self.cache_info,
            'clear': self.clear_cache,
            'cleanup': lambda: self._cleanup_cache_if_needed(),
            'list': lambda: {"files": self._get_cached_files_info()}
        }
        
        if action not in actions:
            self.logger.error(f"Неизвестное действие: {action}. Доступные: {list(actions.keys())}")
            return {"error": f"Неизвестное действие: {action}"}
        
        result = actions[action]()
        if action == 'cleanup':
            self.logger.info("Проверка и очистка кэша выполнена")
        
        return result
    
    def _bytes_to_human(self, bytes_count: int) -> str:
        """
        Преобразует байты в человеко-читаемый формат.
        
        Args:
            bytes_count (int): Количество байтов
            
        Returns:
            str: Строка в формате "XX.XX MB/GB/KB"
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_count < 1024.0:
                return f"{bytes_count:.2f} {unit}"
            bytes_count /= 1024.0
        return f"{bytes_count:.2f} TB"
    
    def get_last_message(self) -> str:
        """
        Возвращает последнее сообщение от сервера.
        
        Returns:
            str: Последнее сообщение
        """
        return self.last_message


    def get_server_stats(self) -> Optional[Dict[str, Any]]:
        """
        Получает общую статистику сервера в "понятном" формате
        Пока что сырая фича.
        
        Returns:
            Dict: JSON статистики сервера
        """
        try:
            response = self.session.get(f"{self.base_url}/{self.base_path}/stats")
            response.raise_for_status()
            stats_data = self._handle_response(response)
            
            server_message = stats_data.get("message", "")
            
            if server_message:
                self._log_server_message(server_message)
            
            if self.verbose_stats:
                self._print_formatted_stats(stats_data)
            
            return stats_data
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Статистика не доступна: {e}")
            return None
    
    def get_user_stats(self) -> Optional[Dict[str, Any]]:
        """
        Получает персональную статистику пользователя
        
        Returns:
            Dict: JSON с персональной статистикой
        """
        try:
            response = self.session.get(f"{self.base_url}/{self.base_path}/user-stats")
            response.raise_for_status()
            user_stats = self._handle_response(response)
            
            # Логируем сообщение от сервера
            server_message = user_stats.get("message", "")
            if server_message:
                self._log_server_message(server_message)
            
            if self.verbose_stats:
                self._print_formatted_user_stats(user_stats)
            
            return user_stats
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Персональная статистика не доступна: {e}")
            return None
    
    def get_user_info(self) -> Optional[Dict[str, Any]]:
        """
        Получает детальную информацию о пользователе
        
        Returns:
            Dict: JSON с информацией о клиенте
        """
        try:
            response = self.session.get(f"{self.base_url}/{self.base_path}/client-info")
            response.raise_for_status()
            client_info = self._handle_response(response)
            
            # Логируем сообщение от сервера
            server_message = client_info.get("message", "")
            if server_message:
                self._log_server_message(server_message)
            
            if self.verbose_stats:
                self._print_formatted_user_info(client_info)
            
            return client_info
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Информация о клиенте не доступна: {e}")
            return None
    
    def save_server_stats(self, filename: str = "server_stats.json") -> bool:
        """
        Сохраняет статистику в JSON файл
        
        Args:
            filename: Имя файла для сохранения
            
        Returns:
            bool: True если успешно, False если ошибка
        """
        try:
            stats = self.get_server_stats()
            if stats:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(stats, f, indent=2, ensure_ascii=False)
                self.logger.info(f"Статистика сохранена в файл: {filename}")
                return True
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении статистики: {e}")
        return False
    
    def save_user_stats(self, filename: str = "user_stats.json") -> bool:
        """
        Сохраняет персональную статистику в JSON файл
        
        Args:
            filename: Имя файла для сохранения
            
        Returns:
            bool: True если успешно, False если ошибка
        """
        try:
            user_stats = self.get_user_stats()
            if user_stats:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(user_stats, f, indent=2, ensure_ascii=False)
                self.logger.info(f"Персональная статистика сохранена в файл: {filename}")
                return True
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении персональной статистики: {e}")
        return False
    
    def save_user_info_to_file(self, filename: str = "user_info.json") -> bool:
        """
        Сохраняет информацию о клиенте в JSON файл
        
        Args:
            filename: Имя файла для сохранения
            
        Returns:
            bool: True если успешно, False если ошибка
        """
        try:
            client_info = self.get_user_info()
            if client_info:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(client_info, f, indent=2, ensure_ascii=False)
                self.logger.info(f"Информация о клиенте сохранена в файл: {filename}")
                return True
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении информации о клиенте: {e}")
        return False
    
    def _print_formatted_stats(self, stats_data: Dict[str, Any]) -> None:
        """Выводит форматированную статистику сервера"""
        print("\n" + "="*50)
        print("СТАТИСТИКА СЕРВЕРА")
        print("="*50)
        
        server_info = stats_data.get("server_info", {})
        print(f"\nОбщая статистика:")
        print(f"  Всего запросов: {server_info.get('total_requests', 0):,}")
        print(f"  Уникальных пользователей: {server_info.get('unique_users', 0)}")
        print(f"  Уникальных импульсов: {server_info.get('unique_shots', 0)}")
        print(f"  Запросов сегодня: {server_info.get('requests_today', 0)}")
        
        your_stats = stats_data.get("your_stats", {})
        print(f"\nВаша статистика:")
        print(f"  Пользователь: {your_stats.get('username', 'N/A')}")
        print(f"  Ваших запросов: {your_stats.get('your_requests', 0)}")
        
        # Топ пользователей
        top_users = stats_data.get("top_users", [])
        if top_users:
            print(f"\nТоп-10 пользователей:")
            for i, (user, count) in enumerate(top_users[:10], 1):
                print(f"  {i:2}. {user}: {count} запросов")
        
        # Топ импульсов
        top_shots = stats_data.get("top_shots", [])
        if top_shots:
            print(f"\nТоп-10 импульсов:")
            for i, (shot_id, count) in enumerate(top_shots[:10], 1):
                print(f"  {i:2}. Импульс {shot_id}: {count} загрузок")
        
        print("="*50 + "\n")
    
    def _print_formatted_user_stats(self, user_stats: Dict[str, Any]) -> None:
        """Выводит форматированную персональную статистику"""
        print("\n" + "="*50)
        print("ВАША СТАТИСТИКА")
        print("="*50)
        
        summary = user_stats.get("summary", {})
        print(f"\nОбщая информация:")
        print(f"  Пользователь: {summary.get('username', 'N/A')}")
        print(f"  Всего скачано: {summary.get('total_downloaded', '0 GB')}")
        print(f"  Скачано файлов: {summary.get('total_files', 0)}")
        print(f"  Средний размер файла: {summary.get('average_file_size', '0 MB')}")
        print(f"  Последняя активность: {summary.get('last_activity', 'Never')}")
        
        cache_info = user_stats.get("cache_info")
        if cache_info:
            print(f"\nИнформация о кэше:")
            print(f"  Размер кэша: {cache_info.get('value', 'N/A')}")
            print(f"  Обновлено: {cache_info.get('last_updated', 'N/A')}")
        
        network_info = user_stats.get("network_info", {})
        print(f"\nСетевая информация:")
        print(f"  Использовано уникальных IP: {network_info.get('unique_ips_used', 0)}")
        print(f"  Текущий IP: {network_info.get('current_ip', 'N/A')}")
        
        last_download = user_stats.get("last_download")
        if last_download:
            print(f"\nПоследняя загрузка:")
            print(f"  Импульс: {last_download.get('shot_id', 'N/A')}")
            size_mb = last_download.get('file_size', 0) / (1024 * 1024)
            print(f"  Размер: {size_mb:.2f} MB")
            print(f"  Время: {last_download.get('timestamp', 'N/A')}")
        
        daily_stats = user_stats.get("daily_statistics", {})
        if daily_stats:
            print(f"\nСтатистика по дням (последние 7 дней):")
            sorted_days = sorted(daily_stats.keys(), reverse=True)[:7]
            for day in sorted_days:
                data = daily_stats[day]
                print(f"  {day}: {data.get('files', 0)} файлов, {data.get('mb', 0):.1f} MB")
        
        print("="*50 + "\n")
    
    def _print_formatted_user_info(self, client_info: Dict[str, Any]) -> None:
        """Выводит форматированную информацию о клиенте"""
        print("\n" + "="*50)
        print("ПОЛНАЯ ИНФОРМАЦИЯ О КЛИЕНТЕ")
        print("="*50)
        
        user_info = client_info.get("user_info", {})
        print(f"\nОсновная информация:")
        print(f"  Пользователь: {user_info.get('username', 'N/A')}")
        print(f"  Последняя активность: {user_info.get('last_activity', 'Never')}")
        print(f"  Размер кэша: {user_info.get('cache_size', 'N/A')}")
        print(f"  Кэш обновлён: {user_info.get('cache_last_updated', 'N/A')}")
        
        stats = client_info.get("statistics", {})
        if stats:
            print(f"\nСтатистика скачиваний:")
            total_gb = stats.get('total_downloaded_bytes', 0) / (1024 * 1024 * 1024)
            print(f"  Всего скачано: {total_gb:.2f} GB")
            print(f"  Файлов скачано: {stats.get('total_files_downloaded', 0)}")
            
            last_dl = stats.get('last_download')
            if last_dl:
                size_mb = last_dl.get('file_size', 0) / (1024 * 1024)
                print(f"  Последняя загрузка:")
                print(f"    Импульс: {last_dl.get('shot_id', 'N/A')}")
                print(f"    Размер: {size_mb:.2f} MB")
                print(f"    Время: {last_dl.get('timestamp', 'N/A')}")
        
        connection_history = client_info.get("connection_history", [])
        if connection_history:
            print(f"\nИстория подключений ({len(connection_history)} записей):")
            for i, conn in enumerate(connection_history[-5:], 1):  # Последние 5
                print(f"  {i}. IP: {conn.get('ip', 'N/A')}")
                print(f"     Первое подключение: {conn.get('first_seen', 'N/A')}")
                print(f"     Последнее подключение: {conn.get('last_seen', 'N/A')}")
        
        print("="*50 + "\n")
    
