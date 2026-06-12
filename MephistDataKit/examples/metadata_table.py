"""
Tokamak MEPHI API Client
========================
Пример работы с клиентом доступа к данным импульсов токамака МИФИСТ через сеть Интернет.
"""

import matplotlib.pyplot as plt
import mephistdatakit as mdk
import numpy as np
import csv

CONST_SHOTS_TO_PROCESS = 10 #число импульсов, которые будут обработаны, начиная с последних


def safe_interp(new_time, old_time, data, default=0.0):
    """
    Безопасная интерполяция данных на новую временную сетку
    """
    if data is None or len(data) == 0:
        return np.full_like(new_time, default)
    
    unique_indices = np.unique(old_time, return_index=True)[1]
    old_time_unique = old_time[unique_indices]
    data_unique = data[unique_indices]
    
    return np.interp(new_time, old_time_unique, data_unique, left=default, right=default)

def process_shot(shot):
    try:
        shot_time = shot.get_shot_time()
        Time = np.linspace(0, 21, 1000)
        
        # Получаем плотность 
        try:
            time_ne, ne = shot.get_plasma_density()
            if ne is not None and len(ne) > 0:
                ne = safe_interp(Time, time_ne, ne, 0.0)
                max_ne = max(ne[int(5/21*1000):int(12/21*1000)]) if len(ne) > 0 else 0.0
                if max_ne < 0:
                    max_ne = 0
            else:
                ne = np.zeros(len(Time))
                max_ne = 0.0
        except Exception as e:
            max_ne = 0.0
        
        # Получаем ток плазмы 
        try:
            time_ip, Ip = shot.get_plasma_current()
            if Ip is not None and len(Ip) > 0:
                Ip = safe_interp(Time, time_ip, Ip, 0.0)
                max_Ip = max(Ip[int(5/21*1000):int(12/21*1000)]) if len(Ip) > 0 else 0.0
                if max_Ip < 0 or max_Ip > 30:
                    max_Ip = 0
            else:
                Ip = np.zeros(len(Time))
                max_Ip = 0.0
        except Exception as e:
            Ip = np.zeros(len(Time))
            max_Ip = 0.0
        
        # Получаем тороидальное поле
        try:
            time_bphi, B_phi = shot.get_torfield()
            B_phi = safe_interp(Time, time_bphi, B_phi, 0.0)
            max_Bphi = max(B_phi[int(5/21*1000):int(12/21*1000)]) if len(B_phi) > 0 else 0.0
        except Exception as e:
            B_phi = np.zeros(len(Time))
            max_Bphi = 0.0
        
        # Получаем метаданные
        shot_id = shot.get_shot_id()
        timestamp = shot.get_shot_time()
        gas = shot.get_gas()
        pressure = shot.get_pressure()
        comment = shot.get_comment()
        
        # Преобразуем numpy типы в стандартные Python типы
        pressure_val = float(pressure) if hasattr(pressure, '__float__') else pressure
        ip_max_val = float(max_Ip) if hasattr(max_Ip, '__float__') else max_Ip
        bphi_max_val = float(max_Bphi) if hasattr(max_Bphi, '__float__') else max_Bphi
        ne_max_val = float(max_ne) if hasattr(max_ne, '__float__') else max_ne
        
        plot_data = {
            "shot_time": str(shot_time),
            "shot_id": int(shot_id),
            "timestamp": str(timestamp),
            "gas": str(gas),
            "pressure": pressure_val,
            "comment": str(comment),
            "ip_max": ip_max_val,
            "bphi_max": bphi_max_val,
            "ne_max": ne_max_val,
            "plasma": bool(max_Ip > 0.7 and 'VAC' not in str(gas)),
        }
        
        return plot_data
        
    except Exception as e:
        # Возвращаем минимальные данные даже при критической ошибке
        plot_data = {
            "shot_time": "",
            "shot_id": 0,
            "timestamp": "",
            "gas": "",
            "pressure": 0.0,
            "comment": "",
            "ip_max": 0.0,
            "bphi_max": 0.0,
            "ne_max": 0.0,
            "plasma": False,
        }
        return plot_data

def format_value(value, fmt=None):
    """Форматирование значения для отображения в таблице"""
    if fmt == 'e' and isinstance(value, (int, float)):
        return f"{value:.2e}"
    elif fmt == 'f' and isinstance(value, (int, float)):
        return f"{value:.2f}"
    elif isinstance(value, float):
        return f"{value:.2e}"
    elif isinstance(value, bool):
        return "✓" if value else "✗"
    else:
        return str(value)

def print_table(data_list):
    """Печать красиво отформатированной таблицы"""
    if not data_list:
        print("Нет данных для отображения")
        return
    
    # Определяем ширину колонок
    headers = ["ID", "Время", "Газ", "Давление", "B_phi", "I_p", "n_e", "Плазма", "Комментарий"]
    col_names = ["shot_id", "shot_time", "gas", "pressure", "bphi_max", "ip_max", "ne_max", "plasma", "comment"]
    
    # Вычисляем максимальные ширины
    col_widths = [len(h) for h in headers]
    
    for data in data_list:
        for i, col in enumerate(col_names):
            if col == "pressure" or col == "ne_max":
                value = format_value(data[col], 'e')
            elif col == "bphi_max" or col == "ip_max":
                value = format_value(data[col], 'f')
            elif col == "plasma":
                value = "✓" if data[col] else "✗"
            else:
                value = str(data[col])[:50]  # Ограничиваем длину комментария
                value = value.replace('\n', ' ') # убираем переносы
                
            col_widths[i] = max(col_widths[i], len(str(value)))
    
    # Печатаем заголовок
    header_line = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    separator = "-+-".join("-" * col_widths[i] for i in range(len(headers)))
    
    print(header_line)
    print(separator)
    
    # Печатаем данные
    for data in data_list:
        row = []
        for i, col in enumerate(col_names):
            if col == "pressure" or col == "ne_max":
                value = format_value(data[col], 'e')
            elif col == "bphi_max" or col == "ip_max":
                value = format_value(data[col], 'f')
            elif col == "plasma":
                value = "✓" if data[col] else "✗"
            else:
                value = str(data[col])[:50]
                value = value.replace('\n', ' ') # убираем переносы
            row.append(value.ljust(col_widths[i]))
        print(" | ".join(row))

def save_to_csv(data_list, filename="metadata.csv"):
    """Сохранение данных в CSV файл"""
    if not data_list:
        print("Нет данных для сохранения")
        return
    
    # Определяем заголовки
    fieldnames = ["shot_id", "shot_time", "gas", "pressure", "bphi_max", "ip_max", "ne_max", "plasma", "comment"]
    
    # Преобразуем данные для CSV (убираем форматирование)
    csv_data = []
    for data in data_list:
        csv_row = {}
        for key in fieldnames:
            if key == "plasma":
                csv_row[key] = "TRUE" if data[key] else "FALSE"
            else:
                csv_row[key] = data[key]
        csv_data.append(csv_row)
    
    # Сохраняем в файл
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_data)
    
    print(f"\nДанные сохранены в файл: {filename}")

if __name__ == "__main__":
    NUMBER_OF_SHOTS = CONST_SHOTS_TO_PROCESS
    
    # Создаем клиента
    client = mdk.Client()
    
    # Проверяем соединение (Необязательно)
    client.test_connection()
    # Проверяем аутентификацию (Необязательно, она повторяется при каждом запросе файла)
    client.authenticate()
    # Получаем list с списком импульсов в int листе
    shots_list = client.get_shots_list()
    
    all_data = []
    
    for shot_id in shots_list[-NUMBER_OF_SHOTS:]:
        try:
            shot = mdk.Shot(client.get_shot(shot_id))
            data = process_shot(shot)
            if data['shot_time'] == "":
                continue
            all_data.append(data)
        except Exception as e:
            print(f"Ошибка обработки выстрела {shot_id}: {e}")
    
    # Печатаем таблицу
    print_table(all_data)
    
    # Сохраняем в CSV
    # save_to_csv(all_data)
    
    cache_info = client.cache_info()
    print(f"\nФайлов в кэше: {cache_info['files_count']}")
    print(f"Размер кэша: {cache_info['total_size_mb']:.2f} MB")