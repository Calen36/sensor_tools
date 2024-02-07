import matplotlib.pyplot as plt
from matplotlib import font_manager
from typing import Dict, Tuple
from datetime import datetime


def bluish_colors_generator():
    """ Выдает цвета в синей гамме """
    for name in ['blue', 'Turquoise', 'CadetBlue', 'MidnightBlue', 'Indigo']:
        yield name
    while True:
        yield 'blue'

def reddish_colors_generator():
    """ Выдает цвета в красно-оранжевой гамме """
    for name in ['red', 'Coral', 'DarkOrange', 'DeepPink', 'DarkRed']:
        yield name
    while True:
        yield 'red'

def marker_generator():
    """ Выдает символы маркеров """
    for marker in 'ovhDX*s+^<>12348':
        yield marker
    while True:
        yield '.'


def create_dual_dataset_point_graph(humid_datasets: dict[str, tuple[datetime, float]], 
                                    particle_datasets: dict[str, tuple[datetime, float]],
                                    sensor_names: dict[int:str] = {},
                                    title: str = '',
                                    graph_style: str = ''):
    """ Рисуем графики на основе переданных датасетов. У каждого (из 2х) типа датасетов - своя ось ординат.
    """

    fig, ax1 = plt.subplots()
    if title:
        title_font = font_manager.FontProperties(weight='bold', size=14)
        ax1.set_title(title, fontproperties=title_font)
        fig.canvas.manager.set_window_title(title)

    bluish_color = bluish_colors_generator()
    reddish_color = reddish_colors_generator()
    marker = marker_generator()
    
    # ГРАФИКИ ВЛАЖНОСТИ
    for sensor_id, dataset in humid_datasets.items():
        sensor_name = sensor_names.get(sensor_id, 'None')
        x_values = [data[0] for data in dataset]
        y_values = [data[2] for data in dataset]
        
        # различные стили
        if graph_style == 'point':
            ax1.scatter(x_values, y_values, label=sensor_name, color=next(bluish_color), s=5)
        elif graph_style == 'line':
            ax1.plot(x_values, y_values, label=sensor_name, color=next(bluish_color), linewidth=1)
        else:
            ax1.plot(x_values, y_values, label=sensor_name, color=next(bluish_color), linewidth=1, marker=next(marker))
    
    # Втарая ось ординат для частиц
    ax2 = ax1.twinx()

    # ГРАФИКИ ЧАСТИЦ
    for sensor_id, dataset in particle_datasets.items():
        sensor_name = sensor_names.get(sensor_id, 'None')
        x_values = [data[0] for data in dataset]
        y_values_p1 = [data[1] for data in dataset]
        y_values_p2 = [data[2] for data in dataset]
        
        # различные стили
        if graph_style == 'point':
            ax2.scatter(x_values, y_values_p1, label=f'{sensor_name} pm10', color=next(reddish_color), s=5)
            ax2.scatter(x_values, y_values_p2, label=f'{sensor_name} pm2.5', color=next(reddish_color), s=5)
        elif graph_style == 'line':
            ax2.plot(x_values, y_values_p1, label=f'{sensor_name} pm10', color=next(reddish_color), linewidth=1)
            ax2.plot(x_values, y_values_p2, label=f'{sensor_name} pm2.5', color=next(reddish_color), linewidth=1)
        else:
            ax2.plot(x_values, y_values_p1, label=f'{sensor_name} pm10', color=next(reddish_color), linewidth=1, marker=next(marker))
            ax2.plot(x_values, y_values_p2, label=f'{sensor_name} pm2.5', color=next(reddish_color), linewidth=1, marker=next(marker))

    # Отображаем легенду    
    ax1.legend(loc='upper left')
    ax2.legend(loc='upper right')

    # Подписи осей
    ax1.set_xlabel('Время')
    ax1.set_ylabel('Влажность, %')
    ax2.set_ylabel('Частицы, ppm')
    
    # Выдаем окно графика
    plt.show()


if __name__ == "__main__":
    def test():
        dataset1 = [(datetime(2022, 1, 1), 10, 11), (datetime(2022, 1, 2), 15, 17), (datetime(2022, 1, 3), 12, 15)]
        dataset2 = [(datetime(2022, 1, 1), 8, 7), (datetime(2022, 1, 2), 11, 9), (datetime(2022, 1, 3), 9, 6)]
        sensor_ids = {123: 'aбра_123', 234: "кадабра_234", 567: "Foo_567", 789: 'AHA789'}
        create_dual_dataset_point_graph(humid_datasets={123: dataset1, 234: dataset2}, 
                                        particle_datasets={789: dataset2}, 
                                        sensor_names=sensor_ids, 
                                        title='ABRACADABra',
                                        graph_style='curve')
    test()
