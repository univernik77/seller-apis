import io
import logging.config
import os
import re
import zipfile
from environs import Env

import pandas as pd
import requests

logger = logging.getLogger(__file__)


def get_product_list(last_id, client_id, seller_token):
    """Получить список товаров магазина Озон

        На входе получает id последнего товара на странице,
        id клиента и токен магазина. Возвращает список артикулов часов,
        созданный на основании запроса к магазину Озон

        Args:
            last_id (str): id товара
            client_id (str): id клиента
            seller_token (str): токен магазина

        Return:
            offer_ids(list): список артикулов часов

    """
    url = "https://api-seller.ozon.ru/v2/product/list"
    headers = {
        "Client-Id": client_id,
        "Api-Key": seller_token,
    }
    payload = {
        "filter": {
            "visibility": "ALL",
        },
        "last_id": last_id,
        "limit": 1000,
    }
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    response_object = response.json()
    return response_object.get("result")


def get_offer_ids(client_id, seller_token):
    """Получить артикулы товаров магазина Озон

        На входе получает id клиента и токен магазина.
        Возвращает список артикулов часов, созданный на основании
        списка часов.

        Args:
            client_id (str): id клиента
            seller_token (str): токен магазина

        Return:
            offer_ids(list): список артикулов часов

    """
    last_id = ""
    product_list = []
    while True:
        some_prod = get_product_list(last_id, client_id, seller_token)
        product_list.extend(some_prod.get("items"))
        total = some_prod.get("total")
        last_id = some_prod.get("last_id")
        if total == len(product_list):
            break
    offer_ids = []
    for product in product_list:
        offer_ids.append(product.get("offer_id"))
    return offer_ids


def update_price(prices: list, client_id, seller_token):
    """Обновить цены часов

        На входе получает список цен на часы, id клиента и токен магазина.
        Обновляет цены товаров, загруженных в магазин Озон.
        Возвращает обновленный список цен часов.

        Args:
            prices (list): список остатков часов
            client_id (str): id клиента
            seller_token (str): токен магазина

        Return:
            list: список цен часов

    """
    url = "https://api-seller.ozon.ru/v1/product/import/prices"
    headers = {
        "Client-Id": client_id,
        "Api-Key": seller_token,
    }
    payload = {"prices": prices}
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


def update_stocks(stocks: list, client_id, seller_token):
    """Обновить остатки

        На входе получает список остатков часов, id клиента и токен магазина.
        Обновляет список остатков часов, загруженных в магазин Озон.
        Возвращает обновленный список остатков часов.

        Args:
            stocks (list): список остатков часов
            client_id (str): id клиента
            seller_token (str): токен магазина

        Return:
            list: список остатков часов

    """
    url = "https://api-seller.ozon.ru/v1/product/import/stocks"
    headers = {
        "Client-Id": client_id,
        "Api-Key": seller_token,
    }
    payload = {"stocks": stocks}
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


def download_stock():
    """Скачать файл ostatki с сайта casio

        Запрашивает с сайта casio файл c номенклатурой часов ostatki.zip.
        Возвращает список номенклатуры часов, полученных из разархивированного
        файла Excel. Удаляет файл ostatki.zip.

        Return:
            watch_remnants(list): список остатков часов

    """
    casio_url = "https://timeworld.ru/upload/files/ostatki.zip"
    session = requests.Session()
    response = session.get(casio_url)
    response.raise_for_status()
    with response, zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        archive.extractall(".")

    excel_file = "ostatki.xls"
    watch_remnants = pd.read_excel(
        io=excel_file,
        na_values=None,
        keep_default_na=False,
        header=17,
    ).to_dict(orient="records")
    os.remove("./ostatki.xls")
    return watch_remnants


def create_stocks(watch_remnants, offer_ids):
    """Создать список словарей остатков часов

        На входе получает 2 списка: список часов и список артикулов
        часов. Возвращает список словарей остатков часов,
        полученных из списка часов, если такие часы есть в списке
        артикулов, с указанием количества остатков часов.

        Args:
            watch_remnants (list): список часов
            offer_ids (list): список артикулов

        Return:
            stocks(list): список остатков часов

    """
    stocks = []
    for watch in watch_remnants:
        if str(watch.get("Код")) in offer_ids:
            count = str(watch.get("Количество"))
            if count == ">10":
                stock = 100
            elif count == "1":
                stock = 0
            else:
                stock = int(watch.get("Количество"))
            stocks.append({"offer_id": str(watch.get("Код")), "stock": stock})
            offer_ids.remove(str(watch.get("Код")))
    for offer_id in offer_ids:
        stocks.append({"offer_id": offer_id, "stock": 0})
    return stocks


def create_prices(watch_remnants, offer_ids):
    """Создать список словарей цены на часы

        На входе получает 2 списка: список товаров и список артикулов.
        Возвращает список словарей цены на товары, полученных из списка товаров,
        если такой товара есть в списке артикулов.

        Args:
            watch_remnants (list): список часов
            offer_ids (list): список артикулов

        Return:
            prices(list): список словарей цен

    """
    prices = []
    for watch in watch_remnants:
        if str(watch.get("Код")) in offer_ids:
            price = {
                "auto_action_enabled": "UNKNOWN",
                "currency_code": "RUB",
                "offer_id": str(watch.get("Код")),
                "old_price": "0",
                "price": price_conversion(watch.get("Цена")),
            }
            prices.append(price)
    return prices


def price_conversion(price: str) -> str:
    """Преобразовать цену.

        Arg:
            price (str): значение цены

        Return:
            str: значение цены

        Example:
            '>>> 5'990.00 руб.
            5990

    """
    return re.sub("[^0-9]", "", price.split(".")[0])


def divide(lst: list, n: int):
    """Разделить список

        Args:
            lst (list): список артикулов
                        список цен
            n (int): длинна списка

        Yield:
            list: возвращает список списков, длинной n

        Example:
            '>>> [.,.,.,.]
            '>>> 2
            '>>> [[.,.],[.,.]]

    """
    for i in range(0, len(lst), n):
        yield lst[i: i + n]


async def upload_prices(watch_remnants, client_id, seller_token):
    """Отправить цены на часы в магазин Озон

        На входе получает список часов, id клиента и токен магазина.
        Обновляет список цен на часы, разделяя на части
        при загрузке в магазин Озон. Возвращает обновленный
        список остатков часов.

        Args:
            watch_remnants (list): список остатков часов
            client_id (str): id клиента
            seller_token (str): токен магазина

        Return:
            prices (list): список цен на часы

    """
    offer_ids = get_offer_ids(client_id, seller_token)
    prices = create_prices(watch_remnants, offer_ids)
    for some_price in list(divide(prices, 1000)):
        update_price(some_price, client_id, seller_token)
    return prices


async def upload_stocks(watch_remnants, client_id, seller_token):
    """Отправить остатки в магазин Озон

        На входе получает список часов, id клиента и токен магазина.
        Обновляет список остатков часов, разделяя на части
        при загрузке в магазин Озон. Возвращает обновленный список
        остатков часов и список наличия часов.

        Args:
            watch_remnants (list): список остатков часов
            client_id (str): id клиента
            seller_token (str): токен магазина

        Return:
            not_empty (list): список наличия часов
            stocks (list): список остатков часов

    """
    offer_ids = get_offer_ids(client_id, seller_token)
    stocks = create_stocks(watch_remnants, offer_ids)
    for some_stock in list(divide(stocks, 100)):
        update_stocks(some_stock, client_id, seller_token)
    not_empty = list(filter(lambda stock: (stock.get("stock") != 0), stocks))
    return not_empty, stocks


def main():
    """Запустить скрипт

        Считывает переменные окружения. Загружает артикулы часов. Создает список
        часов с сайта Casio. Создает список остатков. Обновляет остатки на сайте
        Озон. Обновляет цены на сайте Озон.

        Exceptions:
            ReadTimeout: превышено время ожидания
            ConnectionError: ошибка соединения
            Exception: любые ошибки

    """
    env = Env()
    seller_token = env.str("SELLER_TOKEN")
    client_id = env.str("CLIENT_ID")
    try:
        offer_ids = get_offer_ids(client_id, seller_token)
        watch_remnants = download_stock()
        stocks = create_stocks(watch_remnants, offer_ids)
        for some_stock in list(divide(stocks, 100)):
            update_stocks(some_stock, client_id, seller_token)
        prices = create_prices(watch_remnants, offer_ids)
        for some_price in list(divide(prices, 900)):
            update_price(some_price, client_id, seller_token)
    except requests.exceptions.ReadTimeout:
        print("Превышено время ожидания...")
    except requests.exceptions.ConnectionError as error:
        print(error, "Ошибка соединения")
    except Exception as error:
        print(error, "ERROR_2")


if __name__ == "__main__":
    main()
