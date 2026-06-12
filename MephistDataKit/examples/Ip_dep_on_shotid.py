import numpy as np
import matplotlib.pyplot as plt
import mephistdatakit as mdk

CONST_SHOTS_TO_PROCESS = 10 #число импульсов, которые будут обработаны, начиная с последних

def safe_interp(new_time, old_time, data, default=0.0):
    """
    Безопасная интерполяция данных на новую временную сетку
    """
    if data is None or len(data) == 0:
        return np.full_like(new_time, default)
    
    # Убираем дубликаты времени
    unique_indices = np.unique(old_time, return_index=True)[1]
    old_time_unique = old_time[unique_indices]
    data_unique = data[unique_indices]
    
    # Интерполяция
    return np.interp(new_time, old_time_unique, data_unique, left=default, right=default)

# Создаем клиента
client = mdk.Client()

# Получаем список импульсов
shots_list = client.get_shots_list()

# Списки для хранения данных
h2_shots = {'ids': [], 'max_currents': []}
he_shots = {'ids': [], 'max_currents': []}

# Обрабатываем каждый импульс
for shot_id in shots_list[-CONST_SHOTS_TO_PROCESS:]:
    try:
        shot = mdk.Shot(client.get_shot(shot_id))
        
        gas_type = shot.get_gas()
        Time = np.linspace(0, 21, 1000)
        
        try:
            time_ip, Ip = shot.get_plasma_current()
            
            if Ip is not None and len(Ip) > 0:
                Ip_interp = safe_interp(Time, time_ip, Ip, 0.0)
                
                # Находим максимум тока в интервале 5-12 мс
                idx_start = int(5/21 * 1000)
                idx_end = int(12/21 * 1000)
                
                if idx_end > len(Ip_interp):
                    idx_end = len(Ip_interp)
                
                max_Ip = np.max(Ip_interp[idx_start:idx_end])
                
                # Фильтруем некорректные значения 
                # значения больше 30 - некорректное вычитания синтетического сигнала
                # значение меньше 500 А - шум.
                if max_Ip < 0 or max_Ip > 30 or max_Ip<0.5:
                    max_Ip = 0
            else:
                max_Ip = 0.0
                
        except Exception as e:
            max_Ip = 0.0
        
        # Сохраняем данные в соответствующий список
        if max_Ip > 0:  # Игнорируем нулевые значения
            if gas_type == 'H2':
                h2_shots['ids'].append(shot_id)
                h2_shots['max_currents'].append(max_Ip)
            elif gas_type == 'He':
                he_shots['ids'].append(shot_id)
                he_shots['max_currents'].append(max_Ip)
                
    except Exception as e:
        print(f"Ошибка при обработке импульса {shot_id}: {e}")
        continue

plt.figure(figsize=(12, 8))

if len(h2_shots['ids']) > 0:
    plt.scatter(h2_shots['ids'], h2_shots['max_currents'], 
                color='blue', marker='o', s=50, alpha=0.7, label='H₂')

if len(he_shots['ids']) > 0:
    plt.scatter(he_shots['ids'], he_shots['max_currents'], 
                color='red', marker='s', s=50, alpha=0.7, label='He')

plt.xlabel('Номер импульса', fontsize=12)
plt.ylabel('Максимальный ток плазмы (kA)', fontsize=12)
plt.title('Максимальный ток плазмы в зависимости от номера импульса на токамаке МИФИСТ-0', fontsize=14)
plt.grid(True, alpha=0.3)
plt.legend(fontsize=12)
plt.tight_layout()

print(f"\nСтатистика обработки:")
print(f"Всего импульсов обработано: {len(shots_list)}")
print(f"Импульсов с H₂: {len(h2_shots['ids'])}")
print(f"Импульсов с He: {len(he_shots['ids'])}")

plt.show()
