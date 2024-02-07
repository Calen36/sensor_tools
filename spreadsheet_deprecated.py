""" НА РЕФАКТОРИНГ ИЛИ УДАЛЕНИЕ """
""" В данном файле находится работа с excel таблицами. """

import csv
from datetime import date, datetime, timedelta
from os import path, walk
from statistics import mean
from tkinter import Tk

from openpyxl import Workbook

from graph import create_dual_dataset_point_graph


def get_rows_from_csv(filename: str) -> tuple[str, list]:
    """ Парсим csv файл, возвращаем кортеж с типом сеносра и списком кортежей распознаных строк 
    (sensor_id: int, datetime:datetime, value1: float, value2: float)"""
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
    return row_type, rows
            


def extract_date(filename: str):
    """ Вычленяем дату из имени файла """
    date_str = filename[:10]
    try:
        year, month, day = [int(x) for x in date_str.split('-')]
        return date(year=year, month=month, day=day)
    except:
        return


def get_csv_files(workdir: str, start_date: date, end_date: date) -> list[str]:
    """ Находим файлы, подходящие по дате """
    month_ago = date.today() - timedelta(days=30)
    results = []
    for root, dirs, files in walk(workdir):
        for filename in files:
            if filename.endswith('.csv'):
                file_date = extract_date(filename)
                # отбираем файлы за последний месяц + за заданный период
                if file_date and ((file_date >= start_date and file_date <= end_date) or file_date >= month_ago):
                    file_path = path.join(root, filename)
                    results.append(file_path)
    return results


def get_sensor_data(workdir:str, start_date: date, end_date: date, root_app: Tk) -> tuple[dict[int: tuple[datetime, float, float]], dict[int: tuple[datetime, float, float]]]:
    """ Агрегирует все строки из всех подходящих по дате файлов в два словаря - particle_data и humid_data"""
    
    # находим файлы, подходящие по времени
    files = get_csv_files(workdir, start_date, end_date)
    if not files:
        print('ДЛЯ ЗАДАННЫХ ДАТ ФАЙЛОВ НЕ НАЙДЕНО')
        root_app.update_idletasks()
        return
    print('Сканируется файловый архив...')
    # обновляем gui
    root_app.update_idletasks()
    root_app.update()

    # сюда складываются результаты
    humid_data = {}
    particle_data = {}

    # перебираем файлы, парсим, извлекаем строки и складываем в словари
    for filepath in files:
        root_app.update_idletasks()
        
        sensor_type, rows = get_rows_from_csv(filepath)
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

    return particle_data, humid_data


def create_spreadsheet1(workdir:str, start_date: date, end_date: date, root_app: Tk):
    """ Создаем таблицу excel c усредененными значениями"""
    particle_data, humid_data = get_sensor_data(workdir, start_date, end_date, root_app)
    if not particle_data and not humid_data:
        return
    
    workbook = Workbook()
    humid_sheet = workbook.active
    # ЛИСТ 1 - влажность
    humid_sheet.title = 'Влажность (htu21d)'
    humid_sheet.append(['sensor_id', 'темп. 30дней', 'темп. 7дней', 'темп. 24часа', 
                        'темп. 1час', f'темп. {start_date}—{end_date}', 'влажн. 30дней', 'влажн. 7дней', 
                        'влажн. 24часа', 'влажн. 1час', f'влажн. {start_date}-{end_date}'])
    # ЛИСТ 2 - частицы
    particle_sheet = workbook.create_sheet(title='Частицы (sds011)')
    particle_sheet.append(['sensor_id', 'pm10 30дней', 'pm10 7дней', 'pm10 24часа', 
                           'pm10 1час', f'pm10 {start_date}-{end_date}', 'pm2,5 30дней', 'pm2,5 7дней', 
                           'pm2,5 24часа', 'pm2,5 1час', f'pm2,5 {start_date}—{end_date}'])
    
    now = datetime.now()
    last_month = now - timedelta(days=30)
    last_week = now - timedelta(days=7)
    last_day = now - timedelta(hours=24)
    last_hour = now - timedelta(hours=1)
    span_start = datetime(year=start_date.year,
                          month=start_date.month,
                          day=start_date.day,
                          hour=0,
                          minute=0,
                          second=0)
    span_end = datetime(year=end_date.year,
                        month=end_date.month,
                        day=end_date.day,
                        hour=23,
                        minute=59,
                        second=59)
    
    # ВЫЧИСЛЯЕМ СРЕДНИЕ ЗНАЧЕНИЯ ДЛЯ КАЖДОГО СЕНСОРА И СОЗДАЕМ СТРОКУ В ТАБЛИЦЕ
    """ Оба типа сенсоров ниже можно было бы обработать в одном цикле.
    Два отдельных цикла сделаны специально, чтобы оставить возможность быстрой доработки для
    извлечения большего количества типов данных у разных типов сенсоров."""
    for sensor_id in sorted(particle_data.keys()):
        p1_month = [row[1] for row in particle_data[sensor_id] if row[0] >= last_month]
        p1_month = round(mean(p1_month), 2) if p1_month else None
        p1_week = [row[1] for row in particle_data[sensor_id] if row[0] >= last_week]
        p1_week = round(mean(p1_week), 2) if p1_week else None
        p1_day = [row[1] for row in particle_data[sensor_id] if row[0] >= last_day]
        p1_day = round(mean(p1_day), 2) if p1_day else None
        p1_hour = [row[1] for row in particle_data[sensor_id] if row[0] >= last_hour]
        p1_hour = round(mean(p1_hour), 2) if p1_hour else None
        p1_span = [row[1] for row in particle_data[sensor_id] if span_end >= row[0] >= span_start]
        p1_span = round(mean(p1_span), 2) if p1_span else None
        p2_month = [row[2] for row in particle_data[sensor_id] if row[0] >= last_month]
        p2_month = round(mean(p2_month), 2) if p2_month else None
        p2_week = [row[2] for row in particle_data[sensor_id] if row[0] >= last_week]
        p2_week = round(mean(p2_week), 2) if p2_week else None
        p2_day = [row[2] for row in particle_data[sensor_id] if row[0] >= last_day]
        p2_day = round(mean(p2_day), 2) if p2_day else None
        p2_hour = [row[2] for row in particle_data[sensor_id] if row[0] >= last_hour]
        p2_hour = round(mean(p2_hour), 2) if p2_hour else None
        p2_span = [row[2] for row in particle_data[sensor_id] if span_end >= row[0] >= span_start]
        p2_span = round(mean(p2_span), 2) if p2_span else None
        particle_sheet.append((sensor_id, p1_month, p1_week, p1_day, p1_hour, p1_span, p2_month, p2_week, p2_day, p2_hour, p2_span))
    
    for sensor_id in sorted(humid_data.keys()):
        temp_month = [row[1] for row in humid_data[sensor_id] if row[0] >= last_month]
        temp_month = round(mean(temp_month), 2) if temp_month else None
        temp_week = [row[1] for row in humid_data[sensor_id] if row[0] >= last_week]
        temp_week = round(mean(temp_week), 2) if temp_week else None
        temp_day = [row[1] for row in humid_data[sensor_id] if row[0] >= last_day]
        temp_day = round(mean(temp_day), 2) if temp_day else None
        temp_hour = [row[1] for row in humid_data[sensor_id] if row[0] >= last_hour]
        temp_hour = round(mean(temp_hour), 2) if temp_hour else None
        temp_span = [row[1] for row in humid_data[sensor_id] if span_end >= row[0] >= span_start]
        temp_span = round(mean(temp_span), 2) if temp_span else None
        humid_month = [row[2] for row in humid_data[sensor_id] if row[0] >= last_month]
        humid_month = round(mean(humid_month), 2) if humid_month else None
        humid_week = [row[2] for row in humid_data[sensor_id] if row[0] >= last_week]
        humid_week = round(mean(humid_week), 2) if humid_week else None
        humid_day = [row[2] for row in humid_data[sensor_id] if row[0] >= last_day]
        humid_day = round(mean(humid_day), 2) if humid_day else None
        humid_hour = [row[2] for row in humid_data[sensor_id] if row[0] >= last_hour]
        humid_hour = round(mean(humid_hour), 2) if humid_hour else None
        humid_span = [row[2] for row in humid_data[sensor_id] if span_end >= row[0] >= span_start]
        humid_span = round(mean(humid_span), 2) if humid_span else None
        humid_sheet.append((sensor_id, temp_month, temp_week, temp_day, temp_hour, temp_span, humid_month, humid_week, humid_day, humid_hour, humid_span))
    
    out_base_name = f'MEAN_{date.today()}_{now.hour}-{now.minute}.xlsx'
    out_filename = path.join(workdir, out_base_name)
    workbook.save(out_filename)
    print(f'Сохранен файл {out_filename}')
    return out_filename



def create_spreadsheet(workdir:str, start_date: date, end_date: date, root_app: Tk):
    particle_data, humid_data = get_sensor_data(workdir, start_date, end_date, root_app)
    if not particle_data and not humid_data:
        return
    print(humid_data[list(humid_data.keys())[0]][0])
    create_dual_dataset_point_graph(humid_datasets=humid_data, particle_datasets=particle_data)