import camelot
import datetime
import requests
import os
import pandas
import re
import time

time_of_lessons = ['08:30-10:00',
                   '10:10-11:40',
                   '12:00-13:30',
                   '13:40-15:10',
                   '15.20-16.50',
                   '17.00-18.30',
                   '18.40-20.10',
                   '20.20-21.50']

distant_time_of_lessons = ["09:00-09:30 09:40-10:10",
                           "10:25-10:55 11:05-11:35",
                           "12:05-12:35 12:45-13:15",
                           "13:30-14:00 14:10-14:40",
                           "14:50-15:20 15:30-16:00",
                           "16:10-16:40 16:50-17:20",
                           "17:30-18:00 18:10-18:40",
                           "20.20-21.50"]

def download():
    start_time = time.time()
    print('INFO: Начало скачивания файла')
    url = "http://next.krstc.ru:8081/index.php/s/C2FEBCzoT8xECei/download?path=%2F&files=%D0%A1%D0%90%2C%20%D0%98%D0%A1%2C%D0%9E.pdf"
    r = requests.get(url)
    print('INFO: начало записи файла')
    with open('temp/temp.pdf', mode="wb") as file:
        file.write(r.content)
        file.close()
    print('INFO: файл успешно записан')
    print(f"Затраченное время на скачивание и запись PDF: {time.time() - start_time}")


def convertToCSV():
    download()
    start_time = time.time()
    pdf = camelot.read_pdf('temp/temp.pdf', pages='all')
    tables = []
    for i in range(0, len(pdf)):
        tables.append(pdf[i].df)

    name = str( datetime.datetime.now().date() ) + '.csv'
    pdf.export(path=f'temp/{name}', f='csv')
    os.remove('temp/temp.pdf')
    print(f"Затраченное время на извлечение таблицы из PDF: {time.time() - start_time}")


def importCSV():
    start_time = time.time()
    today = datetime.datetime.now().date()
    yesterday = datetime.datetime.now().date() - datetime.timedelta(days=1)
    tables = []
    try:
        for page in range(1, 4):
            name = str(today) + f'-page-{page}-table-1.csv'
            table = pandas.read_csv(f'temp/{name}', names=[i for i in range(0, 36)])
            tables.append(table)
    except FileNotFoundError as e:
        print(f'WARNING: {e}')
        print('INFO: проверка существования вчерашнего файла')
        for page in range(1, 4):
            name = str(yesterday) + f'-page-{page}-table-1.csv'
            if os.path.exists(f'temp/{name}'):
                print(f'INFO: файл temp/{name} существуеет, удаление...')
                os.remove(f'temp/{name}')
                print(f'INFO: файл temp/{name} успешно удален!')
        convertToCSV()
        importCSV()
    print(f"Затраченное время на извлечение таблицы из csv в pandas: {time.time() - start_time}")
    return tables


def correct_a_table(table):
    start_time = time.time()
    for score, lesson in enumerate(table['lessons']):
        if not lesson:
            print(f"WARNING: урок {score+1} не определен! Исправление...")
            items = table['cabinets'][score+1].split('\n')
            for item in items:
                if re.match(r'^\s*[А-Я][а-я]+\s[а-я]+\s*|^\s*[А-Я][а-я]+\s*|^\s*[А-Я]+\s*', item):
                    table['lessons'][score+1] = item
                    print(f'INFO: урок {score + 1} исправлен! Предмет: {item}')
                elif re.match(r'/s*|[а-я]+|/d+', item):
                    table['cabinets'][score+1] = item
                    print(f'INFO: кабинет урока {score + 1} исправлен. Кабинет: {item}')
                else:
                    print('WARNING: неожиданное поведение при исправление столбца lessons')
        elif isinstance(lesson, list):
            if len(lesson) == 1:
                lesson = re.findall(r'^\s*[А-Я][а-я]+\s[а-я]+|^\s*[А-Я][а-я]+|^\s*[А-Я]+', lesson[0])
                table['lessons'][score+1] = lesson[0]
            elif len(lesson) != 1:
                raise Exception('WARNING: в уроке не должно быть больше одного list!')
            else:
                raise Exception

    for score, teacher in enumerate(table['teachers']):
        if not teacher:
            print(f"WARNING: учитель на уроке {score + 1} не определен! Исправление...")
            items = table['cabinets'][score + 1].split('\n')
            for item in items:
                if re.match(r'\w+ \w\.\w\.', item):
                    table['teachers'][score + 1] = item
                    print(f'INFO: учитель на уроке {score + 1} исправлен! Учитель: {item}')
                elif re.match(r'/s*|[а-я]+|/d+', item):
                    table['cabinets'][score + 1] = item
                    print(f'INFO: кабинет урока {score + 1} исправлен. Кабинет: {item}')
                else:
                    print('WARNING: неожиданное поведение при исправление столбца teachers')

        elif isinstance(teacher, list):
            if len(teacher) == 1:
                table['teachers'][score+1] = teacher[0]
            elif len(teacher) != 1:
                raise Exception('WARNING: в учителе на уроке не должно быть больше одного list!')
            else:
                raise Exception

    for score, id_zoom in enumerate(table['ids']):
        if isinstance(id_zoom, list):
            table['ids'][score+1] = id_zoom[0][4:]

    for score, password in enumerate(table['passwords']):
        if isinstance(password, list):
            items = password[0].split()
            table['passwords'][score+1] = ' '.join(items[1:])
    print(f"Затраченное время на корректировку таблицы: {time.time() - start_time}")
    return table


def extract_data(day = str(datetime.datetime.now().date())):
    tablesMain = importCSV()
    start_time = time.time()
    group = 1
    days = {
        '1': [[0, 4, 12]],
        '2': [[0, 14, 19], [1, 0, 3]],
        '3': [[1, 5, 13]],
        '4': [[1, 16, 16],[2, 0, 7]],
        '5': [[2, 9, 17]]
    }
    if len(days[day]) == 2:
        day_axis1 = days[day][0]
        day_axis2 = days[day][1]
        s1 = tablesMain[day_axis1[0]][3 + 2 * group][day_axis1[1]:day_axis1[2]]
        s2 = tablesMain[day_axis2[0]][3 + 2 * group][day_axis2[1]:day_axis2[2]]
        cab1 = tablesMain[day_axis1[0]][4 + 2 * group][day_axis1[1]:day_axis1[2]]
        cab2 = tablesMain[day_axis2[0]][4 + 2 * group][day_axis2[1]:day_axis2[2]]
        series = pandas.concat([s1, s2], ignore_index=True)
        cabinets = pandas.concat([cab1, cab2], ignore_index=True)
    else:
        day_axis = days[day][0]
        series = tablesMain[day_axis[0]][3 + 2 * group][day_axis[1]:day_axis[2]]
        cabinets = tablesMain[day_axis[0]][4 + 2 * group][day_axis[1]:day_axis[2]]

    time_lesson = pandas.Series(distant_time_of_lessons)
    lesson = series.str.findall(r'^\s*[А-Я][а-я]+\s[а-я]+\s*\n|^\s*[А-Я][а-я]+\s*\n|^\s*[А-Я]+\s*\n')
    teachers = series.str.findall(r'\w+ \w\.\w\.')
    ids = series.str.findall(r'ИК.+')
    passwords = series.str.findall(r'Пароль.+|Код.+')
    table = pandas.concat(objs=[time_lesson, lesson, cabinets, teachers, ids, passwords],
                          axis=1,
                          ignore_index=True)
    table.index = [i for i in range(1, len(table)+1)]
    table.columns = ["time", "lessons", "cabinets", "teachers", "ids", "passwords"]
    print(f"Затраченное время на обработку таблицы из csv: {time.time() - start_time}")
    correct_a_table(table)
    return table


if __name__ == '__main__':
    start_time = time.time()
    result = extract_data('2')  # TODO: Починить парсер для очного расписания и для других групп
    print(result)
    print(f"Общее затраченное время: {time.time() - start_time}")
