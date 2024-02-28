from math import ceil
from typing import Dict, Tuple
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
from matplotlib import font_manager, dates

from data import get_ds_time_span


def bluish_colors_generator():
    """ Выдает цвета в синей гамме """
    for name in ['blue', 'Turquoise', 'CadetBlue', 'MidnightBlue', 'Indigo', 'Teal', 'Steelblue', 'aquamarine', 'cyan', 'slateblue']:
        yield name
    while True:
        yield 'blue'


def reddish_colors_generator():
    """ Выдает цвета в красно-оранжевой гамме """
    for name in ['red', 'maroon', 'magenta', 'purple', 'orange', 'chocolate', 'pink', 'hotpink', 'plum', 'mediumorchid', 'lightsalmon', 'sienna', 'goldenrod', 'darkgoldenrod', 'peru', 'saddlebrouwn']:
        yield name
    while True:
        yield 'crimson'


def marker_generator():
    """ Выдает символы маркеров """
    for marker in 'ovhDX*s+^<>12348':
        yield marker
    while True:
        yield '.'


def render_graph(humid_datasets: dict[str, tuple[datetime, float]], 
                 particle_datasets: dict[str, tuple[datetime, float]],
                 sensor_names: dict[int:str] = {},
                 title: str = '',
                 graph_style: str = ''):
    """ Рисуем графики на основе переданных датасетов. У каждого (из 2х) типа датасетов - своя ось ординат."""

    fig, ax1 = plt.subplots()
    if title:
        title = title.replace('\\n', '\n')
        title_font = font_manager.FontProperties(weight='bold', size=14)
        ax1.set_title(title, fontproperties=title_font)
        fig.canvas.manager.set_window_title(title)

    bluish_color = bluish_colors_generator()
    reddish_color = reddish_colors_generator()
    marker = marker_generator()

    ax1.grid(True, axis='both', color='lightgrey')

    y_max = 0

    # humid_ax.grid(True, axis='y', zorder=0, color=humid_grid_color)

    # ГРАФИКИ ВЛАЖНОСТИ
    if humid_datasets:

        for sensor_id, dataset in humid_datasets.items():
            sensor_name = sensor_names.get(sensor_id, sensor_id)
            x_values = [data[0] for data in dataset]
            y_values = [data[2] for data in dataset]
            y_max_humid = max(y_values)
            y_max = y_max if y_max > y_max_humid else y_max_humid

            # различные стили
            if graph_style == 'point':
                ax1.scatter(x_values, y_values, label=f'Влажность {sensor_name}', color=next(bluish_color), s=5)
            elif graph_style == 'line':
                ax1.plot(x_values, y_values, label=f'Влажность {sensor_name}', color=next(bluish_color), linewidth=1)
            else:
                ax1.plot(x_values, y_values, label=f'Влажность {sensor_name}', zorder=2, color=next(bluish_color), linewidth=1, marker=next(marker))


    # ГРАФИКИ ЧАСТИЦ
    if particle_datasets:
        for sensor_id, dataset in particle_datasets.items():
            sensor_name = sensor_names.get(sensor_id, sensor_id)
            x_values = [data[0] for data in dataset]
            y_values_p1 = [data[1] for data in dataset]
            y_values_p2 = [data[2] for data in dataset]
            y_max_particle = max(y_values_p1+y_values_p2)
            y_max = y_max if y_max > y_max_particle else y_max_particle

            # различные стили
            if graph_style == 'point':
                ax1.scatter(x_values, y_values_p1, label=f'{sensor_name} pm10', color=next(reddish_color), s=5)
                ax1.scatter(x_values, y_values_p2, label=f'{sensor_name} pm2.5', color=next(reddish_color), s=5)
            elif graph_style == 'line':
                ax1.plot(x_values, y_values_p1, label=f'{sensor_name} pm10', color=next(reddish_color), linewidth=1)
                ax1.plot(x_values, y_values_p2, label=f'{sensor_name} pm2.5', color=next(reddish_color), linewidth=1)
            else:
                ax1.plot(x_values, y_values_p1, label=f'{sensor_name} pm10', color=next(reddish_color), linewidth=1, marker=next(marker))
                ax1.plot(x_values, y_values_p2, label=f'{sensor_name} pm2.5', color=next(reddish_color), linewidth=1, marker=next(marker))
        

    time_span = get_ds_time_span(humid_datasets, particle_datasets) # разница по времени между первой и последнеей точкой

    if time_span < timedelta(days=3):
        plt.gca().xaxis.set_major_formatter(dates.DateFormatter('%d.%m %H:%M'))
        ax1.set_xlabel('Время')
    else:
        plt.gca().xaxis.set_major_formatter(dates.DateFormatter('%d.%m.%Y'))
        ax1.set_xlabel('Дата')


    plt.ylim(0, y_max * 1.1)
        
    plt.legend(loc='upper right')
    plt.legend(bbox_to_anchor=(0.5, -0.1), loc='upper center', ncol=2)

    total = len(particle_datasets) * 2 + len(humid_datasets)
    bottom_margin = ceil(total / 2) * 0.035 + 0.1
    print('TOTAL', total, bottom_margin )
    plt.subplots_adjust(bottom=bottom_margin, top=0.9, left=0.05, right=0.98)

    # Выдаем окно графика
    plt.show()


if __name__ == "__main__":
    def test():
        dataset1 = [(datetime(2022, 1, 1), 10, 11), (datetime(2022, 1, 2), 15, 17), (datetime(2022, 1, 3), 12, 15)]
        dataset2 = [(datetime(2022, 1, 1), 8, 7), (datetime(2022, 1, 2), 11, 9), (datetime(2022, 1, 3), 9, 6)]
        sensor_ids = {123: 'aбра_123', 234: "кадабра_234", 567: "Foo_567", 789: 'AHAp'}
        hd ={123: dataset1, 234: dataset2, 2: dataset1, 3: dataset1, 4: dataset1, 5: dataset1, 6: dataset1}
        render_graph(humid_datasets=hd, 
                                        particle_datasets={789: dataset2, 444: dataset1}, 
                                        sensor_names=sensor_ids, 
                                        title='ABRACADABra\n@1afsd',
                                        graph_style='curve')
    test()
