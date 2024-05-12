# Mospolytech Reshuffle

Ежегодно [университет](https://mospolytech.ru/) тратит ресурсы (под ресурсами имеются ввиду и персонал, и время, и
денежные затраты) на выполнение рутинной и трудоёмкой процедуры создания, обновления и проверки материалов для
внутренних вступительных экзаменов, которые представляют собой альтернативу ЕГЭ и являются неотъемлемой частью
большинства ВУЗов. Проект направлен на создание информационной системы, которая позволила бы сократить затрачиваемые
ресурсы и ускорить обработку материалов вступительных экзаменов.

## Использование

Установка требуемых зависимостей:
```pip install -r requirements.txt```

Требуемые зависимости:

* django==5.0.1
* django-ckeditor==6.7.0
* python-decouple==3.8
* psycopg2==2.9.9
* minio==7.2.3
* openpyxl==3.1.2
* opencv-python==4.9.0.80
* easyocr==1.7.1

## Изображения

> **Авторизация** – обеспечение безопасности, разграничение прав пользователей, защита от злоумышленников.

![01](img/01.jpg) <br><br>

> **Модульность** – наличие модулей для администрирования системы, для создания и скачивания экзаменационных материалов,
> для проверки работ абитуриентов.

![02](img/02.jpg) <br><br>

> **Модуль "Администрирование системы"** – визуализация данных системы с возможностью управления пользователями и
> отслеживанием их действий в системе.

![03](img/03.jpg) <br><br>

> **Модуль "Администрирование системы"** – возможность управления структурой экзаменационных материалов.

![04](img/04.jpg) <br><br>

> **Модуль "Администрирование системы"** – возможность создания, чтения, обновления и удаления контента экзаменационных
> материалов.

![05](img/05.jpg) <br><br>

> **Модуль "Создание и скачивание"** – наличие меню для создания уникальных экзаменационных материалов и скачивания уже
> имеющихся.

![06](img/06.jpg) <br><br>

> **Модуль "Создание и скачивание"** – расчёт времени создания комплекта экзаменационных материалов с заданными
> параметрами.

![07](img/07.jpg) <br><br>

> **Модуль "Создание и скачивание"** – скачивание созданного комплекта в формате zip архива.

![08](img/08.jpg) <br><br>

> **Модуль "Создание и скачивание"** – использование S3 хранилища для удобного и надёжного хранения большого объёма
> данных.

![09](img/09.jpg) <br><br>

> **Бланк "Задания"** – пример сгенерированного (с учётом сложности заданий) бланка для абитуриентов.

![10](img/10.jpg) <br><br>

> **Бланк "Ответы"** – пример сгенерированного бланка ответов для проверяющих (при необходимости).

![11](img/11.jpg) <br><br>

> **Бланк "Вступительные испытания"** – пример сгенерированного (на основе заданной структуры) бланка вступительных
> испытаний для абитуриентов.

![12](img/12.jpg) <br><br>

> **Модуль "Проверка работ"** – наличие меню для проверки работ абитуриентов по ранее созданным экзаменационным
> материалам, при полной проверке комплекта система позволяет скачать отчёт с результатами.

![13](img/13.jpg) <br><br>

> **Модуль "Проверка работ"** – бумажные работы абитуриентов сканируются с помощью web-камеры (выбирается из списка
> доступных устройств) или загружаются в систему в виде изображения (при возникновении проблем с web-камерой).

![14](img/14.jpg) <br><br>
![15](img/15.jpg) <br><br>

> **Модуль "Проверка работ"** – наличие таблицы со списком всех работ из выбранного комплекта материалов, включает
> результаты проверки.

![16](img/16.jpg) <br><br>


> **Алгоритм "Проверка работ"** – выравнивание перспективы изображения бланка, полученного с помощью web-камеры или
> загруженного в качестве файла, удаление артефактов изображения, определение маски и анализ результатов работы
> абитуриента с выставлением оценки.

![17](img/17.jpg) <br><br>

> **Модуль "Проверка работ"** – наличие панели с отображением результатов автоматической проверки работы (задания и
> ответы к ним отображаются в отдельных окнах при нажатии на соответствующий номер задания), в случае необходимости
> проверяющий пользователь может внести корректировки в результаты проверки системы.

![18](img/18.jpg) <br><br>
![19](img/19.jpg) <br><br>

## Контакты

Если вы хотите помочь в разработке или у вас есть вопросы, вы можете связаться с создателем
репозитория ([@rand0lphc](https://t.me/rand0lphc)) в telegram.
