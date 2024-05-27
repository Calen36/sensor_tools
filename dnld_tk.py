from dataclasses import dataclass
from datetime import date, timedelta
import gzip
from os import path, makedirs, remove
import re
import shutil
from tkinter import Tk
from typing import Any

import requests

from data import extract_sensor_id


@dataclass
class Result:
    """ Уиверсальный датакласс для возвращениия результатов операции"""
    success: bool  # успешно ли все прошло
    value: Any  # резлутьтат, если все успешно, в противном случае - описание проблемы


def download_arhcive(target_dir: str, sensor_type: str, sensor_id: str, date: date) -> Result:
    """ Скачиваем файл архива """
    try:
        date_repr = f'{date.year}-{str(date.month).zfill(2)}-{str(date.day).zfill(2)}'
        filename = f'{date_repr}_{sensor_type}_sensor_{sensor_id}.csv.gz'
        url = f'https://archive.sensor.community/{date.year}/{date_repr}/{filename}'
        if not path.exists(target_dir):
            makedirs(target_dir)
        target_file_path = path.join(target_dir, filename)
        print(f'{url}', end = '')

        response = requests.get(url)  # делаем запрос
        if response.status_code == 200:
            with open(target_file_path, "wb") as file:  # Пишем в файл
                for chunk in response.iter_content(chunk_size=4096):
                    file.write(chunk)
            print(' \t... СКАЧАН')
            return Result(True, target_file_path)  # успех
        if response.status_code == 404:
            print(f' \t... Не найден')
        else:
            print(f' \t... Ошибка, статус {response.status_code}')
        return Result(False, response.status_code)
    except Exception as ex:
        print(f' \t... Ошибка, {type(ex)}')
        return Result(False, ex)
    

def download_csv(target_dir: str, sensor_type: str, sensor_id: str, date: date) -> Result:
    """ Скачиваем неархивированный файл csv"""
    try:
        date_repr = f'{date.year}-{str(date.month).zfill(2)}-{str(date.day).zfill(2)}'
        filename = f'{date_repr}_{sensor_type}_sensor_{sensor_id}.csv'
        if date.year >= 2023:
            url = f'https://archive.sensor.community/{date_repr}/{filename}'
        else:
            url = f'https://archive.sensor.community/{date.year}/{date_repr}/{filename}'
            
        if not path.exists(target_dir):
            makedirs(target_dir)
        target_file_path = path.join(target_dir, filename)
        print(f'{url}', end = '')

        response = requests.get(url)  # делаем запрос
        if response.status_code == 200:
            with open(target_file_path, "wb") as file:  # Пишем в файл
                for chunk in response.iter_content(chunk_size=4096):
                    file.write(chunk)
            print(' \t... СКАЧАН')
            return Result(True, target_file_path)  # успех
        if response.status_code == 404:
            print(f' \t... Не найден')
        else:
            print(f' \t... Ошибка, статус {response.status_code}')
        return Result(False, response.status_code)
    except Exception as ex:
        print(f' \t... Ошибка, {type(ex)}')
        return Result(False, ex)
    

def unpack_gz(archive_file: str) -> Result:
    """ Распаковываем архив .gz в ту же папку, где он находится. """
    try:
        base_name = path.basename(path.splitext(archive_file)[0])
        target_file_path = path.join(path.dirname(archive_file), base_name)
        with gzip.open(archive_file, 'rb') as f_in:
            with open(target_file_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        print(f'\tСохранен файл {target_file_path}')
        return Result(True, target_file_path)
    except Exception as ex:
        print(f'\tОшибка при распаковке: {str(ex)[:100]}')
        return Result(False, ex)


def get_year_dir(workdir:str, day: date) -> str:
    """ Находим или создаем каталог года в рабочем каталоге"""
    year_dir = path.normpath(path.join(workdir, str(day.year)))
    if not path.exists(year_dir):
        makedirs(year_dir)
    return year_dir


def batch_download(particle_ids: list,
                   humid_ids: list,
                   workdir: str,
                   start_date: date, 
                   end_date: date, 
                   root_app: Tk) -> None:
    """ Последовательная закачка и распаковка файлов """
    delta = end_date - start_date
    # создаем date объект для каждого дня в диапазоне от start_date до end_date
    dates = [start_date+timedelta(days=n) for n in range(delta.days + 1)]

    tasks = [(s_id, 'sds011') for s_id in particle_ids] + [(s_id, 'htu21d') for s_id in humid_ids]
    for day in dates:
        year_dir = get_year_dir(workdir, day)
        for sensor_id, sensor_type in tasks:
            if not root_app.allow_download:
                print('Закачка прервана')
                return
            # пытаемся скачать архив
            if day < date(year=2022, month=7, day=1):
                dnld_result = download_arhcive(target_dir=year_dir,
                                               sensor_id=sensor_id,
                                               sensor_type=sensor_type,
                                               date=day)
                # Если не скачано - пробуем альтернативное наименование сенсора
                if sensor_type == 'htu21d' and not dnld_result.success:
                    dnld_result = download_arhcive(target_dir=year_dir,
                                                   sensor_id=sensor_id,
                                                   sensor_type='dht22',
                                                   date=day)
                # если архив скачался - распаковываем его, а затем удаляем
                if dnld_result.success:
                    unpack_result = unpack_gz(dnld_result.value)
                    if unpack_result.success:
                        remove(dnld_result.value)

            else:
                dnld_result = download_csv(target_dir=year_dir,
                                           sensor_id=sensor_id,
                                           sensor_type=sensor_type,
                                           date=day)
                if sensor_type == 'htu21d' and not dnld_result.success:
                    dnld_result = download_csv(target_dir=year_dir,
                                               sensor_id=sensor_id,
                                               sensor_type='dht22',
                                               date=day)

            # обновляем окно приложения
            root_app.update_idletasks()
            root_app.update()


def get_remote_filenames(day: date) -> list[str]:
    """ Возвращает список существующих url файлов за заданную дату. """
    retries_left = 3
    results = []
    date_repr = f'{day.year}-{str(day.month).zfill(2)}-{str(day.day).zfill(2)}'
    if day.year < 2023:
        url = f'https://archive.sensor.community/{day.year}/{date_repr}/'
    else:
        url = f'https://archive.sensor.community/{date_repr}/'
        
    while retries_left:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                html = response.content.decode(encoding='utf8')
                main_pattern = r'\d{4}\-\d{2}\-\d{2}_\S{3,7}_sensor_\d{1,10}.'
                csv_files = re.findall(main_pattern + r'csv', html)
                gz_files = re.findall(main_pattern + r'gz', html)
                results += [url + fn for fn in csv_files]
                results += [url + fn for fn in gz_files]
            return results
        except:
            retries_left -= 1
    print('Список файлов не получен!')
    return results


def aggregate_remote_filenames(sensor_ids: list[int], start_date: date, end_date: date, may_go_flag: bool) -> dict:
    results = {sid: [] for sid in sensor_ids}
    current_day = start_date
    while current_day <= end_date:
        current_day += timedelta(days=1)
        if may_go_flag:
            print(f'Запрашиваю список всех файлов за {current_day}... ', end='')
            files = get_remote_filenames(current_day)
            if files:
                print(f'ok ({len(files)})')
            else:
                print('файлов не найдено')
            for filename in files:
                sensor_id = extract_sensor_id(filename)
                if sensor_id in results:
                    results[sensor_id].append(filename)
    return results


if __name__ == "__main__":
    print('-'*80)
    date1 = date(year=2022, month=9, day=1)
    date2 = date(year=2022, month=11, day=20)
    files = aggregate_remote_filenames(sensor_ids=[82268, 84439], start_date=date1, end_date=date2, may_go_flag=True)    
    print(files)
    # print(today)
    # fns = get_remote_filenames(date(year=2022, month=9, day=1))
    # print(fns)

