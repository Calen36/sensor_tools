import csv
from datetime import date, datetime, timedelta
from os import path, walk
from statistics import mean
from tkinter import Tk


def extract_sensor_data_type(filename: str) -> str:
    """ Определяем тип сенсора по имени файла. Тип dht22 считаем эквивалентным htu21d """
    base_name = path.basename(filename)
    sensor_index = -3 if '_indoors.' not in filename else -4
    return base_name.split('_')[sensor_index].replace('dht22', 'htu21d') 


def get_rows_from_csv(filename: str) -> list[int, datetime, float, float]:
    """ Парсим csv файл"""
    row_type = extract_sensor_data_type(filename)
  
    rows = []
    with open(filename, 'r') as file:
        csv_reader = csv.reader(file, delimiter=';')

        for row in csv_reader:
            try:
                if row_type == 'sds011':
                    rows.append((int(row[0]), datetime.fromisoformat(row[5]), float(row[6]), float(row[9])))
                elif row_type == 'htu21d':
                    rows.append((int(row[0]), datetime.fromisoformat(row[5]), float(row[6]), float(row[7])))
            except:
                pass
    return rows
            

def get_lat_long(workdir:str,
                 sensor_id: int,
                 start_date: date,
                 end_date: date,) -> tuple[float, float]:
    """ Извлекаем широту и долготу сенсора """
    for filename in get_csv_files(workdir, [sensor_id], start_date, end_date):
        with open(filename, 'r') as file:
            n = 0
            for line in file.readlines():
                n += 1
                if n > 1:
                    values = line.split(';')
                    return float(values[3]), float(values[4])
            

def extract_date(filename: str) -> date | None:
    """ Вычленяем дату из имени файла """
    date_str = filename[:10]
    try:
        year, month, day = [int(x) for x in date_str.split('-')]
        return date(year=year, month=month, day=day)
    except:
        return
    

def extract_sensor_id(filename:str) -> date | None:
    """ Вычленяем sensor id из имени файла"""
    name, _ext = path.splitext(filename)
    try:
        if name.endswith('_indoor'):
            return int(name.split('_')[-2])
        return int(name.split('_')[-1])
    except:
        return


def get_csv_files(workdir: str, ids: list[int], start_date: date, end_date: date) -> list[str]:
    """ Находим файлы, подходящие по дате и id """
    results = []
    for root, dirs, files in walk(workdir):
        for filename in files:
            if filename.endswith('.csv'):
                file_date = extract_date(filename)
                file_sensor_id = extract_sensor_id(filename)
                # отбираем файлы c нужными айдишниками за заданный период
                if file_date and file_sensor_id and file_sensor_id in ids and (file_date >= start_date and file_date <= end_date):
                    file_path = path.join(root, filename)
                    results.append(file_path)
    return results


def get_sensor_data(workdir:str,
                    ids: list[int],
                    start_date: date,
                    end_date: date,
                    root_app: Tk
                    ) -> tuple[dict[int: tuple[datetime, float, float]], dict[int: tuple[datetime, float, float]]]:
    """ Агрегирует все строки из всех подходящих по дате файлов в два словаря - particle_data и humid_data"""
    
    # находим файлы, подходящие по времени
    files = get_csv_files(workdir, ids, start_date, end_date)
    if not files:
        return {}, {}
    # обновляем gui
    root_app.update_idletasks()
    root_app.update()

    # сюда складываются результаты
    humid_data = {}
    particle_data = {}

    # перебираем файлы, парсим, извлекаем строки и складываем в словари
    for filepath in files:
        # base_name = path.basename(filepath)
        root_app.update_idletasks()
        
        rows = get_rows_from_csv(filepath)
        sensor_type = extract_sensor_data_type(filepath)
        if sensor_type == 'sds011':
            for row in rows:
                if row[0] in particle_data:
                    particle_data[row[0]].append(row[1:])
                else:
                    particle_data[row[0]] = [row[1:]]
        elif sensor_type == 'htu21d':
            for row in rows:
                if row[0] in humid_data:
                    humid_data[row[0]].append(row[1:])
                else:
                    humid_data[row[0]] = [row[1:]]
    root_app.update_idletasks()

    # сортируем получившиеся датасеты по времени (1му элементу кортежа)
    for sensor_id, dataset in particle_data.items():
        particle_data[sensor_id] = sorted(dataset, key=lambda x: x[0])
    for sensor_id, dataset in humid_data.items():
        humid_data[sensor_id] = sorted(dataset, key=lambda x: x[0])

    return particle_data, humid_data


def round_datetime_down(ts: datetime, round_by: str) -> datetime:
    """ Округляем datetime вниз """
    if round_by == 'year':
        return datetime(year=ts.year, month=1, day=1)
    if round_by == 'month':
        return datetime(year=ts.year, month=ts.month, day=1)
    if round_by == 'day':
        return datetime(year=ts.year, month=ts.month, day=ts.day)
    if round_by == 'hour':
        return datetime(year=ts.year, month=ts.month, day=ts.day, hour=ts.hour)
    if round_by == 'week':
        monday = ts - timedelta(days=ts.weekday() % 7)
        return datetime(year=monday.year, month=monday.month, day=monday.day)
    return ts


def bring_datasets_to_mean_values(datasets: dict[int: list[tuple[datetime, float, float]]],
                                  mean_over: str
                                  ) -> dict[int: list[tuple[datetime, float, float]]]:
    """ Усредняем значения датасетов для временных отрезков с заданным шагом """
    result = {}
    for sensor_id, dataset in datasets.items():
        newdata = {} # промежуточное хранилище
        for dt, value1, value2 in dataset:
            # все времена в выбранном периоде приводим к моменту начала периода
            actual_dt = round_datetime_down(dt, mean_over) 
            if actual_dt in newdata:
                newdata[actual_dt][0].append(value1)
                newdata[actual_dt][1].append(value2)
            else:
                newdata[actual_dt] = ([value1], [value2])    
        # формируем новый датасет, где дата = дата начала периода для каждого периода, а значения = средние значения за период
        newdataset = []
        for dt, values in newdata.items():
            value1 = mean(values[0]) if values[0] else 0
            value2 = mean(values[1]) if values[1] else 0
            newdataset.append((dt, value1, value2))
        result[sensor_id] = newdataset
    return result


def combine_mean_datasets(humid_data: dict[int: list[tuple[datetime, float, float]]],
                          particle_data:  dict[int: list[tuple[datetime, float, float]]],
                          ) -> dict[str: dict[datetime: dict]]:
    """ Формирует данные для печати в отображения """

    if len(humid_data) not in (1, 0) or len(particle_data) not in (1, 0):
        raise ValueError('Максимум 1 датчик каждого типа сенсоров.')
    result = {}

    for period in ('hour', 'day', 'week', 'month', 'year'):
        if humid_data:
            humid_id = list(humid_data.keys())[0]
            combined_data = {ts: {'temp': round(v1, 2), 
                                  'humid': round(v2, 2), 
                                  'p1': None, 
                                  'p2': None, 
                                  'ids': {humid_id},
                                  } for ts, v1, v2 in bring_datasets_to_mean_values(datasets=humid_data, 
                                                                                                mean_over=period)[humid_id]}
        else:
            humid_id, combined_data = None, {}
        if particle_data:
            particle_id = list(particle_data.keys())[0]
            for ts, p1, p2 in bring_datasets_to_mean_values(datasets=particle_data, 
                                                            mean_over=period)[particle_id]:
                if ts in combined_data:
                    combined_data[ts]['p1'] = round(p1, 2)
                    combined_data[ts]['p2'] = round(p2, 2)
                    combined_data[ts]['ids'].add(particle_id)
                else:
                    combined_data[ts] = {'temp': None,
                                         'humid': None,
                                         'p1': round(p1, 2),
                                         'p2': round(p2, 2),
                                         'ids': {particle_id}}
        result[period] = combined_data
    return result



if __name__ == "__main__":
    fn = '/home/durito/Sensor_data/2024/2024-02-01_htu21d_sensor_216.csv'
    with open(fn, 'r') as file:
        reader = csv.reader(file, delimiter='l')
        for i, row in enumerate(reader):
            val = row[3]

            print(val)
            break


if __name__ == "__main__":
    x = extract_sensor_data_type('2024-01-16_sps30_sensor_84439_indoors.csv')
    print(x)