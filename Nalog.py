import os
import pandas as pd
import openpyxl
from datetime import date
import tkinter as tk
from tkinter import CENTER
from tkinter import filedialog as fd
from functools import partial
import numpy as np
import sqlite3
from DB import record_nalog, placeholder_insert_nalog, create_table
import re




class Child_Nalog(tk.Toplevel):

    def __init__(self, root):
        super().__init__(root)
        self.entry_mrot = None
        self.entry_srtah_ot_13_pens = None
        self.filepath_sick = None
        self.filepath_nalog = None
        self.LabelMessage_text = None
        self.init_child_nalog()
        self.flag = None

    def init_child_nalog(self):
        create_table()
        self.geometry('500x200')
        self.title('Налоги')
        placeholder_nalog = placeholder_insert_nalog()

        self.entry_mrot = tk.Entry(self)
        self.entry_mrot.insert(0, placeholder_nalog['mrot'])
        self.entry_mrot.pack()

        self.entry_srtah_ot_13_pens = tk.Entry(self)
        self.entry_srtah_ot_13_pens.insert(0, placeholder_nalog['srtah_ot_13_pens'])
        self.entry_srtah_ot_13_pens.pack()

        self.LabelMessage_text = tk.StringVar()
        self.LabelMessage_text.set("Жду загрузку файла")

        tk.Label(self, text="Привила загрузки").pack(anchor=CENTER, expand=1)
        tk.Button(self, text='Загрузить налоги', command=partial(self.get_path_xlsx,
                                                                 'налоги')).pack(anchor=CENTER, expand=1)
        tk.Button(self, text='Загрузить больничный', command=partial(self.get_path_xlsx,
                                                                     'больничный лист')).pack(anchor=CENTER, expand=1)
        tk.Label(self, textvariable=self.LabelMessage_text, fg='red').pack()

        self.grab_set()
        self.focus_get()
        self.wait_window()

    # Вносим в бд данные

    def change_label_message(self, massage, error=False):
        if error:
            self.LabelMessage_text.set(massage)

        else:
            self.LabelMessage_text.set(massage)

        # self.LabelMessage.config(text = massage)
        # print(self.LabelMessage['text'])

    def validate_float(self, x):
        try:

            return float(x.replace(',', '.'))
        except  ValueError:
            self.change_label_message(massage=f'Не верный значение {x}. Программа остановлена.', error=True)

    def get_path_xlsx(self, flag):

        filepath = fd.askopenfilename(title=f'Загрузить {flag}')

        if filepath == '':
            self.change_label_message(massage=f'Файл "Загрузить {flag}" не выбран')


        elif not filepath.endswith('.xlsx'):
            self.change_label_message(massage=f'Формат фала должен быть .xlsx')
            raise ValueError

        elif flag == 'налоги':
            self.filepath_nalog = filepath

        elif flag == 'больничный лист':
            self.filepath_sick = filepath
        # Если вс файлы загружены и данные есть в бд и на соответствию float

        if self.filepath_nalog and self.filepath_sick \
                and self.validate_float(self.entry_mrot.get()) \
                and self.validate_float(self.entry_srtah_ot_13_pens.get()):
            # Вносим в бд данные
            record_nalog(self.entry_mrot.get(), self.entry_srtah_ot_13_pens.get())
            # Все ОК идем дальше
            self.nalog_def_start()


    def nalog_def_start(self):
        self.change_label_message(massage='Идет обработка')
        header_nalog = ''
        work_columns_nalog = ['Организация', 'Начислено', 'ПФР. Обязат. страхование', 'ФСС, несч. случаи']
        work_columns_sick = ['Сотрудник', 'Начислено']
        nalog_find_header = pd.read_excel(self.filepath_nalog)
        mrot = 16242
        srtah_ot_13_pens = float(4872.6)

        # Берем хедер для налога

        for i, row in nalog_find_header.iterrows():
            if set(work_columns_nalog).issubset(set(row)):
                header_nalog = i + 1
                break

        # Проверка на наличие нужных для работы колонок
        if not header_nalog:
            self.change_label_message(massage='Проверка на наличие нужных для работы колонок не пройдена. '
                                              'Программа остановлена.', error=True)

        file = pd.read_excel(self.filepath_nalog, header=header_nalog)[2:]
        file_sick = pd.read_excel(self.filepath_sick, header=0)
        new_file = file.copy()

        # Проверка на наличие нужных для работы колонок
        if not set(work_columns_sick).issubset(set(file_sick)):
            self.change_label_message(massage='Проверка на наличие нужных для работы колонок не пройдена. '
                                              'Программа остановлена.', error=True)

            raise ValueError
        # Проверка на уникальность строк
        if not len(new_file['Организация'].unique()) == len(new_file):
            self.change_label_message(massage='Проверка уникальность срок Организация не пройдена .'
                                              'Программа остановлена.', error=True)
            raise ValueError

        # Удаляем столбцы которых нет в work_columns,которые не нужны для работы
        new_file.drop(columns=list(set(work_columns_nalog).symmetric_difference(set(new_file))), axis=1, inplace=True)

        # Добавляем новый столбец с дефолтным значением
        new_file['Больничный лист'] = 0
        new_file['Начислено - Больничный лист'] = 0
        new_file['Минуc  Мрот'] = 0
        new_file['ПФ 10%'] = 0
        new_file['ПФ 22%'] = 0
        new_file['ФСС травм'] = 0
        new_file['Разница ФСС травм'] = 0
        new_file['Разница ПФ'] = 0

        mrot = 16242
        srtah_ot_13_pens = float(4872.6)

        # Добавляем данные из file_sick
        try:
            for i, row in file_sick.iterrows():
                # Берем сотрудников которые есть в 'Больничный лист'
                person = new_file.index[
                    (new_file['Организация'] == row['Сотрудник']) & (not pd.isnull(row['Начислено']))].tolist()
                # Не пустой ли список
                if person:
                    # Присваиваем row['Начислено'] в file_sick к file у кого есть Больничный лист
                    new_file.loc[person, 'Больничный лист'] += row['Начислено']
        except ValueError:
            self.change_label_message(massage='Проверьте содержимое файла больных не пройдена. Программа '
                                              'остановлена.', error=True)
            raise ValueError

        # Обработка по ТЗ
        for i, row in new_file.iterrows():
            if not pd.isnull(row['Начислено']):
                new_file.loc[i, 'Начислено - Больничный лист'] = row['Начислено'] - row['Больничный лист']
                if new_file.loc[i, 'Начислено - Больничный лист'] > mrot:
                    new_file.loc[i, 'Минуc  Мрот'] = new_file.loc[i, 'Начислено - Больничный лист'] - mrot
                    new_file.loc[i, 'ПФ 10%'] = (new_file.loc[i, 'Минуc  Мрот'] * 15 / 100) + srtah_ot_13_pens
                    new_file.loc[i, 'Разница ПФ'] = round(
                        new_file.loc[i, 'ПФР. Обязат. страхование'] - new_file.loc[i, 'ПФ 10%'], 2)
                    new_file.loc[i, 'ФСС травм'] = new_file.loc[i, 'Начислено - Больничный лист'] * 0.5 / 100
                    new_file.loc[i, 'Разница ФСС травм'] = round(
                        new_file.loc[i, 'ФСС травм'] - new_file.loc[i, 'ФСС, несч. случаи'], 2)

                elif new_file.loc[i, 'Начислено - Больничный лист'] < mrot:
                    new_file.loc[i, 'Минуc  Мрот'] = new_file.loc[i, 'Начислено - Больничный лист']
                    new_file.loc[i, 'ПФ 22%'] = (new_file.loc[i, 'Минуc  Мрот'] * 30 / 100)
                    new_file.loc[i, 'Разница ПФ'] = round(
                        (new_file.loc[i, 'ПФ 22%'] - new_file.loc[i, 'ПФР. Обязат. страхование']), 2)
                    new_file.loc[i, 'ФСС травм'] = new_file.loc[i, 'Начислено - Больничный лист'] * 0.5 / 100
                    new_file.loc[i, 'Разница ФСС травм'] = round(
                        new_file.loc[i, 'ФСС травм'] - new_file.loc[i, 'ФСС, несч. случаи'], 2)

        # Сохраняем в директорию откуда был загружен файл
        e_path = os.path.dirname(__file__) + f'/Налоги Отчет {date.today()}.xlsx'
        new_file.to_excel(e_path, sheet_name='Отчет', index=False)

        self.change_label_message(massage=f'Файл сохранен в {e_path}')
        print('Good')
