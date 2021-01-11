import camelot
import datetime
import requests
import os
import pandas
import re
import warnings

warnings.filterwarnings("ignore")

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
    print('INFO: Начало скачивания файла')
    url = "http://next.krstc.ru:8081/index.php/s/C2FEBCzoT8xECei/download?path=%2F&files=%D0%A1%D0%90%2C%20%D0%98%D0%A1%2C%D0%9E.pdf"
    r = requests.get(url)
    print('INFO: начало записи файла')
    with open('temp/temp.pdf', mode="wb") as file:
        file.write(r.content)
        file.close()
    print('INFO: файл успешно записан')


def convertToCSV():
    download()
    pdf = camelot.read_pdf('temp/temp.pdf', pages='all')
    tables = []
    for i in range(0, len(pdf)):
        tables.append(pdf[i].df)

    name = str( datetime.datetime.now().date() ) + '.csv'
    pdf.export(path=f'temp/{name}', f='csv')
    os.remove('temp/temp.pdf')


def importCSV():
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
        tables = importCSV()
    return tables


def correct_a_table(table, distant):

    for score, cabinet in enumerate(table['cabinets']):
        if not isinstance(cabinet, float):
            pattern_teacher = r'\w+ \w\.\w\.'
            teacher = re.findall(pattern_teacher, cabinet)
            cabinet = re.sub(pattern_teacher, '', cabinet)

            pattern_lesson = r'\s*[А-Я][а-я]+\s[а-я]+\s*[а-я]*\s*|\s*[А-Я][а-я]+\s*\n|\s*[А-Я]+\s*'
            lesson = re.findall(pattern_lesson, cabinet)

            cabinet = re.sub(pattern_lesson, '', cabinet)

            cabinet = re.sub('\n', '', cabinet)

            table['cabinets'][score+1] = cabinet
            if lesson:
                table['lessons'][score + 1] = lesson
            if teacher:
                if len(table['teachers'][score + 1]) == 1:
                    table['teachers'][score + 1].append(teacher[0])
                elif len(table['teachers'][score + 1]) == 0:
                    table['teachers'][score + 1] = teacher

    if distant:
        for name in ('ids', 'passwords'):
            for score, item in enumerate(table[name]):
                if isinstance(item, list) and item:
                    if len(item) == 1:
                        items = item[0].split()
                        raw_item = ' '.join(items[1:])
                        corrected_raw_item = re.sub('-', ' ', raw_item)
                        table[name][score+1] = corrected_raw_item
                    elif len(item) == 2:
                        for name_item in item:
                            splited_name_item = name_item.split()
                            corrected_item = ' '.join(splited_name_item[1:])
                            corrected_item = re.sub('/', '', corrected_item)
                            table[name][score + 1].remove(name_item)
                            table[name][score + 1].append(corrected_item)
                            table[name][score + 1].reverse()

    for name in ('lessons', 'teachers'):
        for score, item in enumerate(table[name]):
            if isinstance(item, list) and item:
                for i in range(0, len(item)):
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
        cabinet = table['cabinets'][score + 1]
        teacher = table['teachers'][score + 1]
        if distant:
            zoom_id = table['ids'][score + 1]
            password = table['passwords'][score + 1]
        if pandas.isnull(lesson):
            if pandas.notnull(cabinet):
                table['lessons'][score + 1] = past_lesson
                table['teachers'][score + 1] = past_teacher
                if distant:
                    table['ids'][score + 1] = past_id
                    table['passwords'][score + 1] = past_password
        else:
            past_lesson = lesson
            past_teacher = teacher
            if distant:
                past_id = zoom_id
                past_password = password


def is_distant(raw_tables, day, group):
    days = {
        '1': [0, 3],
        '2': [0, 13],
        '3': [1, 4],
        '4': [1, 15],
        '5': [2, 8]
    }
    day_axis = days[day]
    place = raw_tables[day_axis[0]][3 + 2 * group][day_axis[1]]
    if place == 'дистант':
        return True
    elif place != 'дистант':
        return False


def extract_data(day=str(datetime.datetime.now().date())):
    main_tables = importCSV()
    group = 1
    days = {
        '1': [[0, 4, 12]],
        '2': [[0, 14, 19], [1, 0, 3]],
        '3': [[1, 5, 13]],
        '4': [[1, 16, 16], [2, 0, 7]],
        '5': [[2, 9, 17]]
    }
    if len(days[day]) == 2:
        day_axis1 = days[day][0]
        day_axis2 = days[day][1]
        s1 = main_tables[day_axis1[0]][3 + 2 * group][day_axis1[1]:day_axis1[2]]
        s2 = main_tables[day_axis2[0]][3 + 2 * group][day_axis2[1]:day_axis2[2]]
        cab1 = main_tables[day_axis1[0]][4 + 2 * group][day_axis1[1]:day_axis1[2]]
        cab2 = main_tables[day_axis2[0]][4 + 2 * group][day_axis2[1]:day_axis2[2]]
        series = pandas.concat([s1, s2], ignore_index=True)
        cabinets = pandas.concat([cab1, cab2], ignore_index=True)
    else:
        day_axis = days[day][0]
        series = main_tables[day_axis[0]][3 + 2 * group][day_axis[1]:day_axis[2]]
        cabinets = main_tables[day_axis[0]][4 + 2 * group][day_axis[1]:day_axis[2]]

    series.index = cabinets.index = [i for i in range(1, len(series) + 1)]
    teachers = series.str.findall(r'\n*\w+\s*\n?\w\.\w\.')
    series.str.replace(r'\w+ \w\.\w\.', '')
    lesson = series.str.findall(r'^\s*[А-Я][а-я]+\s[а-я]+\s*|^\s*[А-Я][а-я]+\s*|^\s*[А-Я]+\s*')
    series.str.replace(r'^\s*[А-Я][а-я]+\s[а-я]+\s*|^\s*[А-Я][а-я]+\s*\n|^\s*[А-Я]+\s*', '')
    distant = is_distant(main_tables, day, group)
    if distant:
        time_lesson = pandas.Series(distant_time_of_lessons,
                                    index=[i for i in range(1, len(distant_time_of_lessons) + 1)])
        ids = series.str.findall(r"ИК\:*\s*[\d*\s*|\d*\-]*")
        series.str.replace(r"ИК\:*\s*[\d*\s*|\d*\-]*", '')
        passwords = series.str.findall(r'Пароль\n?.+|Код\n?.+')
        series.str.replace(r'Пароль\n?.+|Код\n?.+', '')
        table = pandas.concat(objs=[time_lesson, lesson, cabinets, teachers, ids, passwords],
                              axis=1,
                              ignore_index=True)
        table.index = [i for i in range(1, len(table) + 1)]
        table.columns = ["time", "lessons", "cabinets", "teachers", "ids", "passwords"]
    elif not distant:
        time_lesson = pandas.Series(time_of_lessons,
                                    index=[i for i in range(1, len(distant_time_of_lessons) + 1)])
        table = pandas.concat(objs=[time_lesson, lesson, cabinets, teachers],
                              axis=1,
                              ignore_index=True)
        table.index = [i for i in range(1, len(table) + 1)]
        table.columns = ["time", "lessons", "cabinets", "teachers"]
    correct_a_table(table, distant)
    return table


if __name__ == '__main__':
    day = input('Введите на какой день вам нужно рассписание в виде цифры (понедельник - 1, вторник - 2, и тд.) >> ')
    result = extract_data(day)
    pandas.set_option('display.max_columns', None)
    print(result)
