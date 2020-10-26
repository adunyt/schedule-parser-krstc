import xlrd
import requests
import datetime
import re

time_of_lesson = {
    1: '08:30-10:00',
    2: '10:10-11:40',
    3: '12:00-13:30',
    4: '13:40-15:10',
    5: '15.20-16.50',
    6: '17.00-18.30',
    7: '18.40-20.10',
    8: '20.20-21.50'}


class Lesson:
    teacher: str
    cabinet: str
    name_of_lesson: str
    time: str
    lesson_sequence_number: int

    def add_data(self, lesson_sequence_number, cabinet, name_of_lesson, teacher):
        self.cabinet = cabinet
        self.time = time_of_lesson[lesson_sequence_number]
        self.name_of_lesson = name_of_lesson
        self.lesson_sequence_number = lesson_sequence_number
        self.teacher = teacher

    def text(self):
        text = f'{self.lesson_sequence_number} пара    {self.time}\n' \
               f'Предмет: {self.name_of_lesson}\n' \
               f'Учитель: {self.teacher}\n' \
               f'Кабинет: {self.cabinet}\n\n'
        return text


class Block:
    lessons = dict()
    day: int
    group: str

    def add_lessons(self, list_with_lessons: list, day: datetime, group: str):
        for lesson in list_with_lessons:
            self.lessons[lesson.lesson_sequence_number] = lesson
        self.day = day
        self.group = group

    def json_data(self):
        data = {self.group: {"day": self.day,
                             "lessons": [x.__dict__ for x in self.lessons.values()]}}
        return data

    def text(self):
        text = str()
        for lesson in self.lessons.values():
            text += lesson.text()
        return text

def download_xls():
    with open("./data/temp", "wb") as file:
        request = requests.get('http://www.krstc.ru/files/raspis/02_%d0%a1%d0%90_%d0%98%d0%a1_%d0%9e.xls')
        file.write(request.content)
        file.close()


def open_xls():
    file = open("temp.out", "w")
    rb = xlrd.open_workbook("./data/temp", logfile=file,formatting_info=True)
    sheet = rb.sheet_by_index(1)
    return sheet


def get_information(sheet: xlrd.sheet, colx: int, day_raw: datetime):
    day_full = day_raw.strftime('%d.%m.%Y')
    day = day_raw.isoweekday()
    start_row: int
    end_row: int
    group_row: int
    list_with_lessons = list()
    block = Block()

    if day == 1:
        start_row = 6
        end_row = 13
        group_row = 3
    elif day <= 5:
        start_row = 16 + 10*(day-2) # минус два потому что когда будет это условие day будет равен двум, значит это
        end_row = 24 + 10*(day-2)   # вторник, а распознавание блоков идет как раз начиная с вторника, и по этому
        group_row = 14 + 10*(day-2) # не нужно добавлять перемещение вниз
    else:
        return "На данный день нет информации"
    raw_lessons = sheet.col_values(colx, start_rowx=start_row, end_rowx=end_row)
    raw_cabinets = sheet.col_values(colx+1, start_rowx=start_row, end_rowx=end_row)
    group = sheet.cell_value(group_row, colx)
    for score, item in enumerate(raw_lessons):
        if item != "":
            lesson = Lesson()
            teacher = re.findall(r'\w+ \w\.\w\.', item)
            item = re.sub(r'\w+ \w\.\w\.', '', item)
            name_of_lesson = re.findall(r'\w+ \w+ |\w+', item)
            cabinets = re.findall(r'\d+', raw_cabinets[score])
            lesson.add_data(lesson_sequence_number=score+1,
                            name_of_lesson=" ".join(name_of_lesson),
                            cabinet=" ".join(cabinets),
                            teacher=" ".join(teacher))
            list_with_lessons.append(lesson)

    block.add_lessons(list_with_lessons, day_full, group)
    return block


def get_groups(sheet: xlrd.sheet):
    groups = dict()
    raw_groups = sheet.row_values(3)
    for score, item in enumerate(raw_groups):
        if item != "":
            groups[score] = item

    return groups


def get_dates(sheet: xlrd.sheet, today: datetime):
    weekday = today.isoweekday()
    dates = list()
    raw_dates = sheet.col_values(0, start_rowx=1)
    for item in raw_dates:
        if item != "":
            dates.append(datetime.datetime.strptime(item[-8:], "%d.%m.%y"))

    if today < dates[0].date():
        return dates[0]
    elif today == dates[weekday - 1].date():
        return dates[weekday - 1]
    elif today > dates[weekday].date():
        print("Скачивание таблицы...")
        download_xls()
        get_dates(sheet, today)


if __name__ == "__main__":
    download_xls()
    day = get_dates(open_xls(), datetime.datetime.strptime('28.10.2020' ,'%d.%m.%Y').date())
    lessons = get_information(sheet=open_xls(), day_raw=day, colx=5)
    print(f'Дата: {lessons.day}' + "\n\n" + lessons.text())
