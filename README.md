# Парсер расписания Красногорского колледжа

## ENG:
This code for russian students of Krasnogorsk College. 
In short, this code parse the PDF file with schedule of lessons, and it is converted result in Pandas DataFrame.

### Используемые библиотеки:
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
Данный код будет использован для [_бота в Telegram_](https://t.me/ScheduleKRSTCBot), но его также можно использовать и 
вручную.
Чтобы это сделать скачайте код и распакуйте в удобном для вас месте. После этого перейдите в папку с
распакованным кодом и перейдите в папку parser. Откройте консоль в данной папке и введите `python3 pdf_parser.py`.
Следуйте инструкции на экране.

### TODO:
* Оптимизация кода
* Возможность обрабатывать расписания других направлений.
