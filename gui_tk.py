from datetime import timedelta, date
from os import path
import sys
from tkinter import Tk, Button, Frame, Label, LEFT, RIGHT, TOP, Entry, TclError, Radiobutton, StringVar, ttk, NW, W, SE
from tkinter.filedialog import askdirectory
from tkinter.constants import END
from tkinter.scrolledtext import ScrolledText

from tkcalendar import Calendar

from dnld_tk import batch_download
from data import get_sensor_data, bring_datasets_to_mean_values, get_lat_long
from graph import render_graph
from logger import PrintLogger
from spreadsheet import create_spreadsheet
from storage import get_workdir, ensure_dir_exists

# ОТКРЫТИЕ ФАЙЛА ВО ВНЕШНЕМ ПРИЛОЖЕНИИ
if sys.platform == 'win32':
    from os import startfile  # под linux данная функция отсутствует.
else:
    import subprocess
    def startfile(filename: str):
        subprocess.run(["xdg-open", filename])


class MainGUI(Tk):
    def __init__(self):
        Tk.__init__(self)
        self.title('Sensor tools')
        self.geometry("800x850")
        self.workdir = get_workdir()
        self.root = Frame(self)
        self.root.pack(expand=True, fill='both')
        self.main_frame = Frame(self.root)
        self.main_frame.pack(expand=True, fill='both')
        self.spreadsheet_path = None  # тут будет находиться путь к созданной таблице
        # Применяем стиль
        self.tk.call("source", "azure.tcl")
        self.tk.call("set_theme", "light")
        self.allow_download = True

    # КАЛЕНДАРИ
        self.cal_label = Label(self.main_frame, text='Начальная и конечная даты периода: ')
        self.cal_label.pack()
        self.cal_frame = Frame(self.main_frame)
        self.cal1 = Calendar(self.cal_frame, selectmode='day', date_pattern='yyyy-mm-dd', locale='ru_RU')
        self.cal1.pack(side=LEFT, padx=10)
        self.cal2 = Calendar(self.cal_frame, selectmode='day', date_pattern='yyyy-mm-dd', locale='ru_RU')
        self.cal2.pack(side=LEFT, padx=10)
        self.cal_frame.pack(pady=10)

    # ВКЛАДКИ
        self.tab_control = ttk.Notebook(self.main_frame)
        self.tab1_frame = Frame(self.tab_control)
        self.tab_control.add(self.tab1_frame, text="  Выкачка файлов  ")

        self.tab2_frame = Frame(self.tab_control)
        self.tab_control.add(self.tab2_frame, text=" Создание таблиц  ")

        self.tab3_frame = Frame(self.tab_control)
        self.tab_control.add(self.tab3_frame, text=" Создание графиков  ")
        self.tab_control.pack(expand=True, fill="both")
        self.tab_control.select(self.tab2_frame)


    # ВКЛАДКА 1
        # self.create_calendars(frame=self.tab1_frame, name1='dnld1', name2='dnld2')

        self.humid_id_entry_frame = Frame(self.tab1_frame, pady=10)
        self.humid_id_label = Label(self.humid_id_entry_frame, text='ID сенсора htu21d (dht22): ')
        self.humid_id_label.pack(side=LEFT)
        self.humid_id_entry = Entry(self.humid_id_entry_frame, width=40)
        self.humid_id_entry.pack(side=LEFT)
        # self.humid_id_entry.bind('<Control-с>', self.copy_text)
        # self.humid_id_entry.bind('<Control-С>', self.copy_text)
        # self.humid_id_entry.bind('<Control-М>', self.paste_text)
        # self.humid_id_entry.bind('<Control-м>', self.paste_text)

        self.humid_id_entry_frame.pack()

        self.particle_id_entry_frame = Frame(self.tab1_frame)
        self.particle_id_label = Label(self.particle_id_entry_frame, text='ID сенсора sds011: ')
        self.particle_id_label.pack(side=LEFT)
        self.particle_id_entry = Entry(self.particle_id_entry_frame, width=40)
        self.particle_id_entry.pack(side=LEFT)
        self.particle_id_entry.bind('<Control-c>', self.copy_text)
        self.particle_id_entry.bind('<Control-v>', self.paste_text)
        self.particle_id_entry_frame.pack()

        self.download_button = Button(self.tab1_frame, text="  Начать скачивание  ", command=self.download)
        self.download_button.pack(pady=10)
        self.download_stop_button = Button(self.tab1_frame, text="Прервать скачивание", command=self.stop_download)
        self.download_stop_button.pack(pady=10)
        self.download_stop_button.config(state='disabled')  # выключаем кнопку закачки на время работы



    # ВКЛАДКА 2
        # Ввод id сенсоров
        self.table_id_entry_frame = Frame(self.tab2_frame)
        self.table_id_label = Label(self.table_id_entry_frame, text='ID сенсоров: ')
        self.table_id_label.pack(side=LEFT)
        self.table_id_entry = Entry(self.table_id_entry_frame, width=51)
        self.table_id_entry.pack(side=LEFT)
        self.table_id_entry_frame.pack()
        self.create_ss_button = Button(self.tab2_frame, text="Создать таблицу", command=self.create_spreadsheet)
        self.create_ss_button.pack(pady=10)
        self.open_spreadsheet_button = Button(self.tab2_frame, text="Открыть таблицу", command=self.open_spreadsheet)
        self.open_spreadsheet_button.pack(pady=30)
        self.open_spreadsheet_button.config(state='disabled')


    # ВКЛАДКА 3
        # Ввод id сенсоров
        self.graph_id_entry_frame = Frame(self.tab3_frame)
        self.graph_id_label = Label(self.graph_id_entry_frame, text='ID сенсоров: ')
        self.graph_id_label.pack(side=LEFT)
        self.graph_id_entry = Entry(self.graph_id_entry_frame, width=51)
        self.graph_id_entry.pack(side=LEFT)
        self.graph_id_entry_frame.pack()

        self.graph_title_entry_frame = Frame(self.tab3_frame)
        self.graph_title_label = Label(self.graph_title_entry_frame, text='Заголовок графика: ')
        self.graph_title_label.pack(side=LEFT, pady=5)
        self.graph_title_entry = Entry(self.graph_title_entry_frame, width=44)
        self.graph_title_entry.pack(side=RIGHT)
        self.graph_title_entry_frame.pack()

        # Блок радио-переключателей
        self.radio_input_frame = Frame(self.tab3_frame)
        self.radio_input_frame.pack(anchor=W, padx=40, expand=True, fill='x')
        # ВЫБОР ПЕРИОДА
        self.mean_period_frame = Frame(self.radio_input_frame)
        self.mean_period_frame.pack(side=LEFT, anchor=NW)    
        self.mean_period_var = StringVar()
        self.mean_period_var.set("none")
        self.mean_period_label = Label(self.mean_period_frame, text='Период усреднения: ')
        self.mean_period_label.pack(anchor=W)
        self.raio_mean_without = Radiobutton(self.mean_period_frame, text="Без усреднения", variable=self.mean_period_var, value="none")
        self.raio_mean_without.pack(anchor=W)
        self.raio_mean_hour = Radiobutton(self.mean_period_frame, text="Час", variable=self.mean_period_var, value="hour")
        self.raio_mean_hour.pack(anchor=W)
        self.raio_mean_day = Radiobutton(self.mean_period_frame, text="Сутки", variable=self.mean_period_var, value="day")
        self.raio_mean_day.pack(anchor=W)
        self.raio_mean_week = Radiobutton(self.mean_period_frame, text="Неделя", variable=self.mean_period_var, value="week")
        self.raio_mean_week.pack(anchor=W)
        self.raio_mean_month = Radiobutton(self.mean_period_frame, text="Месяц", variable=self.mean_period_var, value="month")
        self.raio_mean_month.pack(anchor=W)
        self.raio_mean_year = Radiobutton(self.mean_period_frame, text="Год", variable=self.mean_period_var, value="year")
        self.raio_mean_year.pack(anchor=W)
        # ВЫБОР СИТЛЯ ГРАФИКА
        self.graph_style_frame = Frame(self.radio_input_frame)
        self.graph_style_frame.pack(side=LEFT, anchor=NW, padx=40)    
        self.graph_style_var = StringVar()
        self.graph_style_var.set("line")
        self.graph_style_label = Label(self.graph_style_frame, text='Стиль графика: ')
        self.graph_style_label.pack(anchor=W)
        self.raio_line_type = Radiobutton(self.graph_style_frame, text="Линии", variable=self.graph_style_var, value="line")
        self.raio_line_type.pack(anchor=W)
        self.raio_point_type = Radiobutton(self.graph_style_frame, text="Точки", variable=self.graph_style_var, value="point")
        self.raio_point_type.pack(anchor=W)
        self.raio_line_type = Radiobutton(self.graph_style_frame, text="Линии и маркеры", variable=self.graph_style_var, value="default")
        self.raio_line_type.pack(anchor=W)
        # Кнопка создания
        self.create_graph_btn = Button(self.radio_input_frame, padx=20, pady=20, text="Создать график", command=self.create_graph)
        self.create_graph_btn.pack(side=RIGHT)
    # РАБОЧИЙ КАТАЛОГ
        self.workdir_frame = Frame(self.root, padx=20, pady=20)
        self.workdir_frame.pack(expand=True, fill="both")
        self.workdir_label = Label(self.workdir_frame, text=f'Рабочий каталог: {self.workdir}')
        self.workdir_label.pack(side=LEFT)
        self.change_workdir_button = Button(self.workdir_frame, 
                                        text="Сменить", 
                                        command=self.select_workdir)
        self.change_workdir_button.pack(side=RIGHT)
    # ЛОГ
        self.log_widget = ScrolledText(self.root, font=("consolas", "8", "normal"))
        self.log_widget.pack(expand=True, fill='both')
        self.redirect_logging()  # перенаправляем stdout в текстовый виджет

    def select_workdir(self):
        """ Смена рабочего каталога """
        new_dir = askdirectory(initialdir=self.workdir)
        if new_dir:
            self.workdir = new_dir
            self.workdir_label.config(text=f'Рабочий каталог: {self.workdir}')
    
    def get_dates(self) -> tuple[date, date]:
        """ Читаем введенные даты """
        date1 = self.cal1.selection_get()
        date2 = self.cal2.selection_get()
        if date1 > date2:
            date1, date2 = date2, date1
        return date1, date2

    def copy_text(self, event):
        widget = event.widget
        selected_text = widget.selection_get()
        if selected_text:
            self.clipboard_clear()
            self.clipboard_append(selected_text)

    def paste_text(self, event):
        widget = event.widget
        text = self.clipboard_get()
        print(text)
        # widget.insert('insert', text)

    def create_graph(self):
        """ Отрисовка графиков """
        if not path.exists(self.workdir):
            print(f'Не найден каталог {self.workdir}')
            return
        issues = []
        # Получаем и валидируем введенные данные.
        date1, date2 = self.get_dates()
        selected_graph_style = self.graph_style_var.get()
        selected_mean_period = self.mean_period_var.get()
        inputed_ids_raw = self.graph_id_entry.get()
        inputed_title = rf'{self.graph_title_entry.get()}'
        try:
            if not inputed_ids_raw:
                raise ValueError
            sensor_ids = {int(y[0]): y[1] for y in [x.strip().split()+[x.strip().split()[0]] for x in inputed_ids_raw.split(',') if x.strip()]}
        except:
            issues.append("ВВЕДИТЕ КОРРЕКТНЫЕ ID СЕНСОРОВ")
        
        self.logger.flush()
        # Если нашлись проблемы - сообщаем о них
        for issue in issues:
            print(issue)

        if not issues:
            print('Сканируется файловый архив...')
            self.update_idletasks()
            # Собираем данные из csv-файлов
            particle_data, humid_data = get_sensor_data(workdir=self.workdir,
                                                        ids=sorted(sensor_ids.keys()),
                                                        start_date=date1,
                                                        end_date=date2,
                                                        root_app=self)
            if not particle_data and not humid_data:
                print('Данных по введенным ID за заданный период не найдено.')
                return
            print('Сканирование завершено.')
            # УСРЕДНЯЕМ ДАННЫЕ ПО ПЕРИОДАМ, ЕСЛИ НЕОБХОДИМО
            if selected_mean_period != 'none':
                humid_data = bring_datasets_to_mean_values(humid_data, mean_over=selected_mean_period)
                particle_data = bring_datasets_to_mean_values(particle_data, mean_over=selected_mean_period)
            # ОТРИСОВЫВАЕМ ГРАФИК
            render_graph(humid_datasets=humid_data,
                         particle_datasets=particle_data, 
                         sensor_names=sensor_ids,
                         title=inputed_title,
                         graph_style=selected_graph_style)

    def create_spreadsheet(self):
        """ Валидируем введенные данные и запускаем создание таблицы excel """
        if not path.exists(self.workdir):
            print(f'Не найден каталог {self.workdir}')
            return
        issues = []
        date1, date2 = self.get_dates()
        
        try:
            sensor_ids = [int(x) for x in self.table_id_entry.get().replace(',', ' ').split() if x]
            if len(sensor_ids) not in (1, 2):
                raise ValueError
        except:
            issues.append("ВВЕДИТЕ НЕ БОЛЕЕ ДВУХ КОРРЕКТНЫХ ID СЕНСОРОВ")

        self.logger.flush()
        for issue in issues:
            print(issue)
        if not issues:
            self.create_ss_button.config(state='disabled')
            print('Сканируется файловый архив...')
            self.update_idletasks()
            # Собираем данные из csv-файлов
            particle_data, humid_data = get_sensor_data(workdir=self.workdir,
                                                        ids=sensor_ids,
                                                        start_date=date1,
                                                        end_date=date2,
                                                        root_app=self)
            if not particle_data and not humid_data:
                print('Данных по введенным ID за заданный период не найдено.')
                self.create_ss_button.config(state='active')
                return
            print('Сканирование завершено.')
            if len(particle_data)>1 or len(humid_data)>1:
                print('Введенные ID относятся к одному типу!')
                self.create_ss_button.config(state='active')
                return
            
            spreadsheet_path = create_spreadsheet(workdir=self.workdir,
                                                  humid_data=humid_data,
                                                  particle_data=particle_data,
                                                  start_date=date1,
                                                  end_date=date2,)
            self.create_ss_button.config(state='active')
            if spreadsheet_path:
                self.spreadsheet_path = spreadsheet_path
                self.open_spreadsheet_button.config(state='active')

    def open_spreadsheet(self):
        startfile(self.spreadsheet_path)

    def download(self):
        """ Закачка файлов с данными """
        workdir_ok = ensure_dir_exists(self.workdir)
        print(workdir_ok)
        if not workdir_ok:
            return
        issues = []
        # ВАЛИДИРУЕМ ВВЕДЕННЫЕ ДАННЫЕ
        date1, date2 = self.get_dates()
        delta = date2 - date1
        if delta > timedelta(days=2000):
            issues.append('СЛИШКОМ БОЛЬШОЙ РАЗБРОС ДАТ!')

        if not path.exists(self.workdir):
            issues.append('РАБОЧИЙ КАТАЛОГ НЕ СУЩЕСТВУЕТ!')
        elif not path.isdir(self.workdir):
            issues.append('ВЫБРАННЫЙ РАБОЧИЙ КАТАЛОГ НЕ ЯВЛЯЕТСЯ КАТАЛОГОМ!')
        particle_endered = self.particle_id_entry.get().strip()
        humid_entered = self.humid_id_entry.get().strip()
        particle_ids, humid_ids = [], []
        try:
            particle_ids = [int(x) for x in particle_endered.replace(',', ' ').split() if x]
        except:
            issues.append('НЕКОРРЕКТНЫЙ ID sds011!')
        try:
            humid_ids = [int(x) for x in humid_entered.replace(',', ' ').split() if x]
        except:
            issues.append('НЕКОРРЕКТНЫЙ ID htu21d!')
        if not humid_entered and not particle_endered:
            issues.append('ЗАДАЙТЕ ХОТЯ БЫ ОДИН ID СЕНСОРА!')
        
        self.logger.flush()
        # Если возникли проблемы - отображаем их.
        for issue in issues:
            print(issue)
        # Запускаем закачку
        if not issues:
            self.download_button.config(state='disabled')  # выключаем кнопку закачки на время работы
            self.download_stop_button.config(state='active')
            try:
                batch_download(particle_ids=sorted(set(particle_ids)),
                               humid_ids=sorted(set(humid_ids)), 
                               workdir=self.workdir, 
                               start_date=date1, 
                               end_date=date2,
                               root_app=self)
            except Exception as ex:
                print(f'ОШИБКА ПРИ ЗАГРУЗУКЕ: {ex}')
            self.download_button.config(state='active')
            self.download_stop_button.config(state='disabled')
            self.allow_download = True
            print('>> ГОТОВО <<')
    
    def stop_download(self):
        self.allow_download = False

    def reset_logging(self):
        """ Возврат вывода в stdout """
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

    def redirect_logging(self):
        """ Перенаправяем вывод в текстовый виджет """
        self.logger = PrintLogger(self.log_widget)
        sys.stdout = self.logger
        sys.stderr = self.logger


if __name__ == "__main__":
    if __name__ == "__main__":
        app = MainGUI()
        app.mainloop()
