import csv
from datetime import date, datetime, timedelta
from os import path, walk
from statistics import mean
from tkinter import Tk


def get_rows_from_csv(filename: str) -> list[int, datetime, float, float]:
    """ Парсим csv файл"""
    base_name = path.basename(filename)
    # определяем тип сенсора по имени файла
    for row_type in ('sds011', 'htu21d'):
        if row_type in base_name:
            break 
  
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
            


def extract_date(filename: str):
    """ Вычленяем дату из имени файла """
    date_str = filename[:10]
    try:
        year, month, day = [int(x) for x in date_str.split('-')]
        return date(year=year, month=month, day=day)
    except:
        return

def extract_sensor_id(filename:str):
    """ Вычленяем sensor id из имени файла"""
    name, _ext = path.splitext(filename)
    try:
        return int(name.split('_')[-1])
    except:
        return

def get_csv_files(workdir: str, ids: list[int], start_date: date, end_date: date) -> list[str]:
    """ Находим файлы, подходящие по дате """
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


def get_sensor_data(workdir:str, ids: list[int], start_date: date, end_date: date, root_app: Tk) -> tuple[dict[int: tuple[datetime, float, float]], dict[int: tuple[datetime, float, float]]]:
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
        base_name = path.basename(filepath)
        root_app.update_idletasks()
        
        rows = get_rows_from_csv(filepath)
        if '_sds011_' in base_name:
            for row in rows:
                if row[0] in particle_data:
                    particle_data[row[0]].append(row[1:])
                else:
                    particle_data[row[0]] = [row[1:]]
        elif '_htu21d_' in base_name:
            for row in rows:
                if row[0] in humid_data:
                    humid_data[row[0]].append(row[1:])
                else:
                    humid_data[row[0]] = [row[1:]]
    root_app.update_idletasks()

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
    return ts



def bring_datasets_to_mean_values(datasets: dict[int: list[tuple[datetime, float, float]]],
                                  mean_over: str
                                  ) -> dict[int: list[tuple[datetime, float, float]]]:
    for sensor_id, dataset in datasets.items():
        newdata = {}
        for dt, value1, value2 in dataset:
            actual_dt = round_datetime_down(dt, mean_over)
            if actual_dt in newdata:
                newdata[actual_dt][0].append(value1)
                newdata[actual_dt][1].append(value2)
            else:
                newdata[actual_dt] = ([value1], [value2])
        newdataset = []
        for dt, values in newdata.items():
            value1 = mean(values[0]) if values[0] else 0
            value2 = mean(values[1]) if values[1] else 0
            newdataset.append((dt, value1, value2))
        datasets[sensor_id] = newdataset
    return datasets