import camelot
import datetime
import requests
import os
import pandas

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
    with open('temp.pdf', mode="wb") as file:
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
        importCSV()
    return tables


if __name__ == '__main__':
    tablesMain = importCSV()
    today = datetime.datetime.now().isoweekday()
    group = 1
    s1 = tablesMain[0][5][14:19]
    s2 = tablesMain[1][5][0:3]
    vt = pandas.concat([s1, s2])
    vt.index = [i for i in range(1, len(vt)+1)]
    time = pandas.Series(distant_time_of_lessons, index=[i for i in range(1, len(distant_time_of_lessons)+1)])
    lesson = vt.str.findall(r'^\s*[А-Я][а-я]+\ [а-я]+\s*\n|^\s*[А-Я][а-я]+\s*\n')
    teachers = vt.str.findall(r'\w+ \w\.\w\.')
    ids = vt.str.findall(r'ИК.+')
    passwords = vt.str.findall(r'Пароль.+|Код.+')
    print(vt)
    print()
    new_vt = pandas.concat(objs=[time, lesson, teachers, ids, passwords],
                           axis=1,
                           keys=["time", "lesson", "teachers", "ids", "passwords"])
    print(new_vt)
