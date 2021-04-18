try:
    import camelot
except ModuleNotFoundError:
    raise ModuleNotFoundError('Модуль camelot не найден! Проверьте установку и попробуйте еще раз.')
else:
    try:
        from camelot import read_pdf
    except ImportError:
        raise ImportError(f'Ошибка импорта функции из camelot-py. Возможно вы установили "camelot"?')
import datetime
import requests
import os
import pandas
import re
import warnings
import sys

warnings.filterwarnings("ignore")  # Для более красивого вывода

_axis_days = {  # Координаты дней, если бы листы PDF были слитными, как таблица
    '1': [4, 11],
    '2': [14, 21],
    '3': [24, 31],
    '4': [34, 41],
    '5': [44, 51]
}


def __generate_the_link(friday_bug: bool = False):  # Экспериментальная функция. Используйте с осторожностью
    today = datetime.date.today().day
    weekday = datetime.datetime.now().isoweekday()
    if weekday > 5 or friday_bug:
        today = today + (7 - weekday + 1)
        weekday = 1

    start_day = int(today) - int(weekday) + 1
    end_day = int(today) + (5 - int(weekday))
    curr_month = int(datetime.date.today().month)
    if curr_month < 10:
        curr_month = "0" + str(curr_month)
    link = f"http://next.krstc.ru:8081/index.php/s/C2FEBCzoT8xECei/download?path=%2F&files=" \
           f"{start_day}.{curr_month}-{end_day}.{curr_month}.__%D0%A1%D0%90%2C%20%D0%98%D0%A1%2C%D0%9E_.pdf"
    return link


def download(url=__generate_the_link()) -> None:
    """Скачивает PDF файл с таблицами в директорию temp относительно выполнения данной функции."""
    print('INFO: Начало скачивания файла')
    print(f"INFO: Ссылка: {url}")
    try:
        r = requests.get(url)
    except Exception as e:
        raise Exception(f"Невозможно установить соединение! Причина: {e}")
    print('INFO: Начало записи файла')
    with open('temp/temp.pdf', mode="wb") as file:
        file.write(r.content)
        file.close()
    print('INFO: Файл успешно записан')


def file_is_exist() -> bool:
    """Проверяет существования CVS таблиц соответствующие текущей дате (модуль datetime)"""
    today = datetime.datetime.now().date()
    try:
        for page in range(1, 4):  # Так как в основном таблиц 3, то идет их проверка.
            name = str(today) + f'-page-{page}-table-1.csv'
            with open(f'temp/{name}', "r") as f:
                print(f'INFO: Файл {name} существует.')
                f.close()
        return True
    except FileNotFoundError as e:
        print(f'WARNING: Файла не обнаружено! Текст ошибки: {e}')
        return False


def convert_to_csv() -> None:
    """Обрабатывает PDF файл с помощью camelot-py и переводит в CVS. Данные таблицы нежелательно использовать сразу,
    так как их корректность не идеальна. Чтобы скорректировать данные используйте функцию extract_data."""
    print('INFO: Начата обработка PDF, это может занять несколько минут...')
    try:
        pdf = camelot.read_pdf('temp/temp.pdf', pages='all')
    except Exception as e:
        if datetime.date.today().day == 5:
            print("WARN: Не удалось обработать расписание, попытка скачать на следующую неделю...")
            download(url=__generate_the_link(friday_bug=True))
            convert_to_csv()
        else:
            print(f"ERROR: Критическая ошибка при обработке PDF файла: '{e}'. Проверьте правильность ссылки на "
                  f"скачивания файла. Ссылка должна вести напрямую к скачиванию файла")
            os.remove(path="temp/temp.pdf")
            exit("ERR")
    else:
        print('INFO: Обработка PDF закончена!')
        print("INFO: Импортирование обработанного PDF...")
        name = str(datetime.datetime.now().date()) + '.csv'
        pdf.export(path=f'temp/{name}', f='csv')
        os.remove('temp/temp.pdf')
        print("INFO: Импортировано!")


def import_csv() -> list[pandas.DataFrame]:
    """Импортирует CSV файлы с таблицами в pandas. Возвращает список содержащий несколько Pandas.DataFrame"""
    today = datetime.datetime.now().date()
    tables = []
    if file_is_exist():
        for page in range(1, 4):
            name = str(today) + f'-page-{page}-table-1.csv'
            table = pandas.read_csv(f'temp/{name}', names=[i for i in range(0, 36)])  # Параметр names используется
            # для названий колонок, так как pandas по умолчанию использует первую строчку cvs
            tables.append(table)  # Создание списка с таблицами для дальнейших манипуляций

    elif not file_is_exist():
        for file in os.listdir('/temp/'):
            file_path = os.path.join('/temp/', file)
            if os.path.isfile(file_path):
                print(f'INFO: Удаление temp/{file_path}...')
                os.remove(file_path)
                print(f'INFO: Файл temp/{file_path} успешно удален!')
        try:
            download()
        except Exception as e:
            sys.exit(f"ERROR: {e}")

        convert_to_csv()
        tables = import_csv()  # Рекурсивность используется для того, чтобы после скачивания недостающих данных
        # импортировать их в pandas.DataFrame
    return tables


def correct_axis(tables: list, x: int, y: int = None) -> (list[list[int]], bool):
    """Функция корректирует порядковый номер ячеек с учетом разделений листов PDF и отдает список с списками номеров,
    а также bool значение показывающее на разных ли таблицах ячейки"""
    lens = [len(tables[0]), len(tables[1]), len(tables[2])]
    if y is None:
        is_split = False
        for no_table, len0 in enumerate(lens):
            if x < len0:
                corrected_axis = [[no_table, x]]
            elif x > len0:
                x -= lens[no_table]

    else:
        for no_table, len0 in enumerate(lens):
            if x < y < len0:
                corrected_axis = [[no_table, x, y]]
                is_split = False
                break
            elif x < len0 <= y:
                corrected_axis = [[no_table, x, len0], [no_table + 1, 0, y - len0]]
                if corrected_axis[1][0] >= len(lens):
                    print('WARN: Исправленные координаты выходят за пределы таблиц')
                    corrected_axis.remove(corrected_axis[1])
                    is_split = False
                else:
                    is_split = True
                break
            else:
                raise Exception("ERROR: Исправление координат произошло неуспешно")
            # noinspection PyUnreachableCode
            x -= lens[no_table]
            y -= lens[no_table]

    if is_split not in locals() and not corrected_axis:
        raise Exception('ERROR: Ошибка! Исправление осей не выдало ответ!')

    return corrected_axis, is_split


def get_index_groups(tables: list[pandas.DataFrame]) -> int:
    """Спрашивает у пользователя группу из которой нужно забирать данные. Возвращает индекс колонки группы."""
    table = tables[0]
    raw_groups = table.loc[1, :]
    groups = raw_groups.dropna()
    groups.index = [i for i in range(1, len(groups) + 1)]
    print('Выберите группу из предложенных: ')
    for score, i in enumerate(groups):
        print(f'{score + 1}: {i}')
    no_group = int(input('(введите порядковый номер группы) >> '))
    name_of_group = groups[no_group]
    index = raw_groups[raw_groups == name_of_group].index.to_list()[0]
    return index


def get_time(tables: list[pandas.DataFrame], day: str) -> pandas.Series:
    """Парсит время из таблицы, так как оно имеет свойство меняться. Возвращает pandas.Series с временем."""
    x1, x2 = _axis_days[day][0], _axis_days[day][1]
    axis, splited = correct_axis(tables=tables, x=x1, y=x2)
    if splited:
        time1 = tables[axis[0][0]][2][axis[0][1]:axis[0][2]]
        time2 = tables[axis[1][0]][2][axis[1][1]:axis[1][2]]
        time = pandas.concat([time1, time2], ignore_index=True)
    elif not splited:
        time = tables[axis[0][0]][2][axis[0][1]:axis[0][2]]
        time.index = [i for i in range(1, len(time) + 1)]
    else:
        raise Exception('ERROR: Ошибка при извлечении даты')
    return time


def correct_a_table(table: pandas.DataFrame, distant: bool) -> None:
    """Корректирует таблицу с учетом того, что данные в основном 'съезжают' в правую колонку (кабинеты) при обработке
    с помощью camelot-py. Так как изменения вносятся сразу в переданную таблицу функция ничего не выдает в ответ"""
    for score, cabinet in enumerate(table['cabinets']):
        # Основная корректировка таблицы. Так как имя учителя или название урока может оказаться в левом столбце
        # (с кабинетом), то данный цикл проверяет каждое значение кабинета и если находит по регулярному выражению имя
        # учителя или название урока, то перемещает по столбикам соответствующие значения и удаляет из ячейки кабинета
        if not isinstance(cabinet, float):
            pattern_teacher = r'\w+ \w\.\w\.'
            teacher = re.findall(pattern_teacher, cabinet)
            cabinet = re.sub(pattern_teacher, '', cabinet)

            pattern_lesson = r'\s*[А-Я][а-я]+\s[а-я]+\s*[а-я]*\s*|\s*[А-Я][а-я]+\s*\n|\s*[А-Я]+\s*'
            lesson = re.findall(pattern_lesson, cabinet)

            cabinet = re.sub(pattern_lesson, '', cabinet)
            cabinet = re.sub('\n', '', cabinet)
            table['cabinets'][score + 1] = cabinet
            if lesson:
                table['lessons'][score + 1] = lesson

            if teacher:
                if len(table['teachers'][score + 1]) == 1:
                    table['teachers'][score + 1].append(teacher[0])
                elif len(table['teachers'][score + 1]) == 0:
                    table['teachers'][score + 1] = teacher

    if distant:
        # Удаляет лишние символы если есть ИД и пароль. В основном из ИД удаляются тире, а из пароля при нескольких
        # учителях удаляется знак "/"
        for name in ('ids', 'passwords'):
            for score, item in enumerate(table[name]):
                if isinstance(item, list) and item:
                    if len(item) == 1:
                        items = item[0].split()
                        raw_item = ' '.join(items[1:])
                        corrected_raw_item = re.sub('-', ' ', raw_item)
                        table[name][score + 1] = corrected_raw_item
                    elif len(item) == 2:
                        for name_item in item:
                            splited_name_item = name_item.split()
                            corrected_item = ' '.join(splited_name_item[1:])
                            corrected_item = re.sub('/', '', corrected_item)
                            table[name][score + 1].remove(name_item)
                            table[name][score + 1].append(corrected_item)
                            table[name][score + 1].reverse()

    for name in ('lessons', 'teachers'):
        # Удаляет лишние пробелы и переносы строк из названий урока и имен учителей
        for score, item in enumerate(table[name]):
            if isinstance(item, list) and item:
                if len(item) == 1:
                    item[0] = re.sub(r'\s{2,}', '', item[0])
                    table[name][score + 1] = re.sub('\\n', '', item[0])
                elif len(item) == 2:
                    for name_item in item:
                        corrected_item = re.sub('\n', '', name_item)
                        corrected_item = re.sub(r'\s{2,}', '', corrected_item)
                        table[name][score + 1].remove(name_item)
                        table[name][score + 1].append(corrected_item)
                        table[name][score + 1].reverse()

    for score, lesson in enumerate(table['lessons']):
        # Экспериментальное извлечение объединенных ячеек, например учебной практики
        # Определяет на принципе того, что если имеется единственный урок, но кабинетов несколько то это объединённая
        # После этого просто постоянно копирует значения из нижней строки все выше
        cabinet = table['cabinets'][score + 1]
        teacher = table['teachers'][score + 1]
        zoom_id = password = past_lesson = past_teacher = past_id = past_password = None  # Нужно для избежания ошибок
        if distant:
            zoom_id = table['ids'][score + 1]
            password = table['passwords'][score + 1]

        if not pandas.isnull(lesson):
            past_lesson = lesson
            past_teacher = teacher
            if distant:
                past_id = zoom_id
                past_password = password

        elif pandas.isnull(lesson):
            if pandas.notnull(cabinet):
                table['lessons'][score + 1] = past_lesson
                table['teachers'][score + 1] = past_teacher
                if distant:
                    table['ids'][score + 1] = past_id
                    table['passwords'][score + 1] = past_password


def is_distant(raw_tables: list, day: str, group_index: int) -> bool:
    """Проверяет дистанционное обучение ли в заданный день, у также заданной группы. Возвращает bool значение дистант
     или нет"""
    x = _axis_days[day][0] - 1
    axis = correct_axis(tables=raw_tables, x=x)[0][0]
    place = raw_tables[axis[0]][group_index][axis[1]]
    if place == 'Дистант':
        return True
    elif place != 'Дистант':
        return False


def extract_data(main_tables: list, today: str = str(datetime.datetime.now().date())) -> pandas.DataFrame:
    """Обрабатывает информацию из CSV файлов и выдает pandas.DataFrame с расписанием.
    Колонки: время, название предмета, кабинет, учитель, если есть дистант, то еще и ИД и пароль"""
    index_group = get_index_groups(tables=main_tables)
    x1 = _axis_days[today][0]
    x2 = _axis_days[today][1]
    axis, splited = correct_axis(tables=main_tables, x=x1, y=x2)
    distant = is_distant(main_tables, today, index_group)
    if splited:  # Выборка по ячейкам в pandas.DataFrame (импортированном из CVS, см. import_csv())
        day_axis1 = axis[0]
        day_axis2 = axis[1]

        s1 = main_tables[day_axis1[0]][index_group][day_axis1[1]:day_axis1[2]]  # Так как данные разделены (переменная
        s2 = main_tables[day_axis2[0]][index_group][day_axis2[1]:day_axis2[2]]  # splited), то парсится два листа сразу

        cab1 = main_tables[day_axis1[0]][index_group + 1][day_axis1[1]:day_axis1[2]]
        cab2 = main_tables[day_axis2[0]][index_group + 1][day_axis2[1]:day_axis2[2]]

        series = pandas.concat([s1, s2], ignore_index=True)
        cabinets = pandas.concat([cab1, cab2], ignore_index=True)
    else:
        day_axis = axis[0]
        series = main_tables[day_axis[0]][index_group][day_axis[1]:day_axis[2]]
        cabinets = main_tables[day_axis[0]][index_group + 1][day_axis[1]:day_axis[2]]

    time = get_time(main_tables, today)
    time.index = list(range(1, len(time) + 1))
    series.index = cabinets.index = list(range(1, len(series) + 1))
    # Далее по коду используются регулярные выражения для извлечения значений.
    # Так же эти значения сразу удаляются из переменной series для более точного следующего извлечения
    teacher_re = r'\n*\w+\s*\n?\w\.\w\.'
    lesson_re = r'^\s*[А-Я][а-я]+\s[а-я]+\s*|^\s*[А-Я][а-я]+\s*|^\s*[А-Я]+\s*'
    id_re = r"ИК\:*\s*[\d*\s*|\d*\-]*"
    pass_re = r'Пароль\n?.+|Код\n?.+'
    teachers = series.str.findall(teacher_re)
    series.str.replace(teacher_re, '')
    lessons = series.str.findall(lesson_re)
    series.str.replace(lesson_re, '')
    if distant:  # Если дистант, то еще парсится ИД и пароли и добавляются в таблицу. Иначе просто значения объединяются
        ids = series.str.findall(id_re)
        series.str.replace(id_re, '')
        passwords = series.str.findall(pass_re)
        series.str.replace(pass_re, '')
        table = pandas.concat(objs=[time, lessons, cabinets, teachers, ids, passwords],
                              axis=1,
                              ignore_index=True)
        table.index = [i for i in range(1, len(table) + 1)]
        table.columns = ["time", "lessons", "cabinets", "teachers", "ids", "passwords"]
    elif not distant:
        table = pandas.concat(objs=[time, lessons, cabinets, teachers],
                              axis=1,
                              ignore_index=True)
        table.index = [i for i in range(1, len(table) + 1)]
        table.columns = ["time", "lessons", "cabinets", "teachers"]
    else:
        raise Exception("ERROR: Невозможно определить дистанционное обучение или нет")

    correct_a_table(table, distant)
    return table


if __name__ == '__main__':
    day = input('Введите на какой день вам нужно расписание в виде цифры (понедельник - 1, вторник - 2, и тд.) >> ')
    result = extract_data(main_tables=import_csv(), today=day)
    pandas.set_option('display.max_columns', None)
    print(result)
