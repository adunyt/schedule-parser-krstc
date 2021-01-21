# Парсер расписания Красногорского колледжа

## ENG:
This code for russian students of Krasnogorsk College. 
In short, this code parse the PDF file with schedule of lessons, and it is converted result in Pandas DataFrame.

##RUS:
###ВНИМАНИЕ! Разработка парсера заморожена в связи с непостоянностью структуры таблицы. Данный код рабочий на момент 21.01.2021.
###Используемые библиотеки:
* Стандартные:
    * datetime
    * os
    * re
    * warnings
* Другие:
    * camelot
    * requests
    * cv2-utils (зависимость для camelot)
    * pandas

### Как использовать:
Чтобы это сделать скачайте код и распакуйте в удобном для вас месте. После этого перейдите в папку с
распакованным кодом и откройте консоль в данной папке и введите `python3 parser.py`.
Следуйте инструкциям на экране.