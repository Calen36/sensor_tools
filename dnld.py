from dataclasses import dataclass
from datetime import date, timedelta
import gzip
from os import path, makedirs, remove
import shutil
from tkinter import Tk
from typing import Any

import requests


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
        url = f'https://archive.sensor.community/{date_repr}/{filename}'
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
            # пытаемся скачать архив
            if day.year < 2023:
                dnld_result = download_arhcive(target_dir=year_dir,
                                            sensor_id=sensor_id,
                                            sensor_type=sensor_type,
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
            # обновляем окно приложения
            root_app.update_idletasks()
            root_app.update()
