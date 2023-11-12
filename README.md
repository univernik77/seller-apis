# Набор скриптов

## Описание скриптов

### seller.py
Скрипт, используя идентификационный номер и токен для доступа,
запрашивает у интернет-магазина "Озон" список раннее загруженных часов. 
Каждая позиция сохраняется в список артикулов. Запрашивает остатки c сайта Сasio. 
Создает список остатков на основание, данных полученных с сайта Casio и артикулов с сайта Озон. 
Из данных полученных с Casio создает список цен. Загружает полученные остатки на сайт Озон. 
Загружает цены на сайт Озона.
### market.py
Скрипт, используя идентификационный номер и токен для доступа,
запрашивает у интернет-магазина "Яндекс-Маркет" список раннее загруженных часов, 
отдельно для каждой модели, в зависимости от типа доставки (FBS - доставка Яндекс-Маркет, 
DBS - доставка продавцом). Каждая позиция сохраняется в список артикулов. Запрашивает остатки c сайта Сasio. 
Для каждой модели доставки: cоздает список остатков на основание, данных полученных с сайта Casio и артикулов с сайта Озон;
из данных полученных с Casio создает список цен; загружает полученные остатки на сайт Озон;
загружает цены на сайт Озона.

### Цель проекта
Код написан в образовательных целях на онлайн-курсе для веб-разработчиков [dvmn.org](https://dvmn.org/).