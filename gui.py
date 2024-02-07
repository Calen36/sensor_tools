""" ОСНОВНОЕ Tkinter - приложение."""

from datetime import timedelta
from os import path
import sys
from tkinter import Tk, Button, Frame, Label, LEFT, RIGHT, TOP, Entry, TclError, Radiobutton, StringVar, ttk, NW, W, SE
from tkinter.filedialog import askdirectory
from tkinter.constants import END
from tkinter.scrolledtext import ScrolledText

from tkcalendar import Calendar

from dnld import batch_download
from logger import PrintLogger
from spreadsheet_deprecated import create_spreadsheet
from data import get_sensor_data, bring_datasets_to_mean_values
from graph import create_dual_dataset_point_graph


class MainGUI(Tk):
    def __init__(self):
        Tk.__init__(self)
        self.title('Sensor tools')
        self.geometry("800x800")
        self.workdir = 'C:\\TMP'
        self.root = Frame(self)
        self.root.pack(expand=True, fill='both')
        self.main_frame = Frame(self.root)
        self.main_frame.pack(expand=True, fill='both')

        self.tk.call("source", "azure.tcl")
        self.tk.call("set_theme", "light")


        self.calendars = {}

    # ВКЛАДКИ
        self.tab_control = ttk.Notebook(self.main_frame)
        self.tab1_frame = Frame(self.tab_control)
        self.tab_control.add(self.tab1_frame, text="  Выкачка файлов  ")

        self.tab2_frame = Frame(self.tab_control)
        # self.tab_control.add(self.tab2_frame, text="  Создание таблиц  ")

        self.tab3_frame = Frame(self.tab_control)
        self.tab_control.add(self.tab3_frame, text="  Создание графиков  ")
        self.tab_control.pack(expand=True, fill="both")
        self.tab_control.select(self.tab3_frame)


    # ВКЛАДКА 1
        self.create_calendars(frame=self.tab1_frame, name1='dnld1', name2='dnld2')

        self.humid_id_entry_frame = Frame(self.tab1_frame, pady=10)
        self.humid_id_label = Label(self.humid_id_entry_frame, text='ID сенсора htu21d: ')
        self.humid_id_label.pack(side=LEFT)
        self.humid_id_entry = Entry(self.humid_id_entry_frame, width=40)
        self.humid_id_entry.pack(side=LEFT)
        self.humid_id_entry_frame.pack()

        self.particle_id_entry_frame = Frame(self.tab1_frame)
        self.particle_id_label = Label(self.particle_id_entry_frame, text='ID сенсора sds011: ')
        self.particle_id_label.pack(side=LEFT)
        self.particle_id_entry = Entry(self.particle_id_entry_frame, width=40)
        self.particle_id_entry.pack(side=LEFT)
        self.particle_id_entry_frame.pack()

        self.download_button = Button(self.tab1_frame, text="Начать скачивание", command=self.download)
        self.download_button.pack(pady=10)

    # ВКЛАДКА 2
        # self.show_calendars(frame=self.tab2_frame, name1='mean1', name2='mean2')
        # self.create_ss_button = Button(self.tab2_frame, text="Создать таблицу", command=self.create_spreadsheet)
        # self.create_ss_button.pack(pady=10)

    # ВКЛАДКА 3
        self.create_calendars(frame=self.tab3_frame, name1='graph1', name2='graph2')
        
        self.graph_id_entry_frame = Frame(self.tab3_frame)
        self.graph_id_label = Label(self.graph_id_entry_frame, text='ID сенсоров: ')
        self.graph_id_label.pack(side=LEFT)
        self.graph_id_entry = Entry(self.graph_id_entry_frame, width=51)
        self.graph_id_entry.pack(side=LEFT)
        self.graph_id_entry_frame.pack()

        self.graph_title_entry_frame = Frame(self.tab3_frame)
        self.graph_title_label = Label(self.graph_title_entry_frame, text='Заголовок графика: ')
        self.graph_title_label.pack(side=LEFT)
        self.graph_title_entry = Entry(self.graph_title_entry_frame, width=44)
        self.graph_title_entry.pack(side=RIGHT)
        self.graph_title_entry_frame.pack()

        self.radio_input_frame = Frame(self.tab3_frame)
        self.radio_input_frame.pack(anchor=W, padx=40, expand=True, fill='x')

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
        self.raio_mean_month = Radiobutton(self.mean_period_frame, text="Месяц", variable=self.mean_period_var, value="month")
        self.raio_mean_month.pack(anchor=W)
        self.raio_mean_year = Radiobutton(self.mean_period_frame, text="Год", variable=self.mean_period_var, value="year")
        self.raio_mean_year.pack(anchor=W)

        self.graph_type_frame = Frame(self.radio_input_frame)
        self.graph_type_frame.pack(side=LEFT, anchor=NW, padx=40)    
        self.graph_type_var = StringVar()
        self.graph_type_var.set("point")
        self.graph_type_label = Label(self.graph_type_frame, text='Стиль графика: ')
        self.graph_type_label.pack(anchor=W)
        self.raio_point_type = Radiobutton(self.graph_type_frame, text="Точки", variable=self.graph_type_var, value="point")
        self.raio_point_type.pack(anchor=W)
        self.raio_line_type = Radiobutton(self.graph_type_frame, text="Линии", variable=self.graph_type_var, value="line")
        self.raio_line_type.pack(anchor=W)
        self.raio_line_type = Radiobutton(self.graph_type_frame, text="Линии и маркеры", variable=self.graph_type_var, value="default")
        self.raio_line_type.pack(anchor=W)

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


    def create_calendars(self, frame: Frame, name1: str, name2: str):
        """ Рисуем два календаря в заданном фрейме, сохраняем их в словаре self.calendars с заданными именами """
        self.cal_label = Label(frame, text='Начальная и конечная даты периода: ')
        self.cal_label.pack()
        calendars_frame = Frame(frame)
        self.calendars[name1] = Calendar(calendars_frame, selectmode='day', date_pattern='yyyy-mm-dd')
        self.calendars[name1].pack(side=LEFT, padx=10)
        self.calendars[name2] = Calendar(calendars_frame, selectmode='day', date_pattern='yyyy-mm-dd')
        self.calendars[name2].pack(side=LEFT, padx=10)
        calendars_frame.pack(pady=10)

    def select_workdir(self):
        """ Смена рабочего каталога """
        new_dir = askdirectory(initialdir=self.workdir)
        if new_dir:
            self.workdir = new_dir
            self.workdir_label.config(text=f'Рабочий каталог: {self.workdir}')
    
    def create_graph(self):
        """ Отрисовка графиков """
        issues = []
        # Получаем и валидируем введенные данные.
        date1 = self.calendars['graph1'].selection_get()
        date2 = self.calendars['graph2'].selection_get()
        if date1 > date2:
            date1, date2 = date2, date1
        selected_graph_style = self.graph_type_var.get()
        selected_mean_period = self.mean_period_var.get()
        inputed_ids_raw = self.graph_id_entry.get()
        inputed_title = self.graph_title_entry.get()
        try:
            if not inputed_ids_raw:
                raise ValueError
            sensor_ids = {int(y[0]): y[1] for y in [x.strip().split()+[x.strip().split()[0]] for x in inputed_ids_raw.split(',') if x]}
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
            # УСРЕДНЯЕМ ДАННЫЕ ПО ПЕРИОДАМ, ЕСЛИ НЕОБХОДИМО
            if selected_mean_period != 'none':
                humid_data = bring_datasets_to_mean_values(humid_data, mean_over=selected_mean_period)
                particle_data = bring_datasets_to_mean_values(particle_data, mean_over=selected_mean_period)
            # ОТРИСОВЫВАЕМ ГРАФИК
            create_dual_dataset_point_graph(humid_datasets=humid_data,
                                            particle_datasets=particle_data, 
                                            sensor_names=sensor_ids,
                                            title=inputed_title,
                                            graph_style=selected_graph_style)

    def create_spreadsheet(self):
        """ Валидируем введенные данные и запускаем создание таблицы excel """
        issues = []
        date1 = self.calendars['mean1'].selection_get()
        date2 = self.calendars['mean2'].selection_get()
        if date1 > date2:
            date1, date2 = date2, date1
        delta = date2 - date1
        if delta > timedelta(days=1000):
            issues.append('СЛИШКОМ БОЛЬШОЙ РАЗБРОС ДАТ! (допустимый максимум - 1000 дней)')

        self.logger.flush()
        for issue in issues:
            print(issue)
        if not issues:
            self.create_ss_button.config(state='disabled')
            create_spreadsheet(workdir=self.workdir,
                               start_date=date1,
                               end_date=date2,
                               root_app=self)
            self.create_ss_button.config(state='active')

    def download(self):
        """ Валидируем введенные данные и запускаем закачку """
        issues = []
        date1 = self.calendars['dnld1'].selection_get()
        date2 = self.calendars['dnld2'].selection_get()
        if date1 > date2:
            date1, date2 = date2, date1
        delta = date2 - date1
        # if delta > timedelta(days=90):
        #     issues.append('СЛИШКОМ БОЛЬШОЙ РАЗБРОС ДАТ! (допустимый максимум - 90 дней)')

        if not path.exists(self.workdir):
            issues.append('РАБОЧИЙ КАТАЛОГ НЕ СУЩЕСТВУЕТ!')
        elif not path.isdir(self.workdir):
            issues.append('ВЫБРАННЫЙ РАБОЧИЙ КАТАЛОГ НЕ ЯВЛЯЕТСЯ КАТАЛОГОМ!')
        particle_endered = self.particle_id_entry.get().strip()
        humid_entered = self.humid_id_entry.get().strip()
        particle_ids, humid_ids = [], []
        try:
            particle_ids = [int(x) for x in particle_endered.split(',') if x]
        except:
            issues.append('НЕКОРРЕКТНЫЙ ID sds011!')
        try:
            humid_ids = [int(x) for x in humid_entered.split(',') if x]
        except:
            issues.append('НЕКОРРЕКТНЫЙ ID htu21d!')
        if not humid_entered and not particle_endered:
            issues.append('ЗАДАЙТЕ ХОТЯ БЫ ОДИН ID СЕНСОРА!')
        
        self.logger.flush()
        for issue in issues:
            print(issue)
        if not issues:
            self.download_button.config(state='disabled')
            batch_download(particle_ids=sorted(set(particle_ids)),
                           humid_ids=sorted(set(humid_ids)), 
                           workdir=self.workdir, 
                           start_date=date1, 
                           end_date=date2,
                           root_app=self)
            self.download_button.config(state='active')
            print('>> ГОТОВО <<')

    def reset_logging(self):
        """ Это не используется, но пусть полежит, может пригодится еще"""
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

    def redirect_logging(self):
        """ Перенаправяем вывод в текстовый виджет """
        self.logger = PrintLogger(self.log_widget)
        sys.stdout = self.logger
        sys.stderr = self.logger
