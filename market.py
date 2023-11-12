import datetime
import logging.config
from environs import Env
from seller import download_stock

import requests

from seller import divide, price_conversion

logger = logging.getLogger(__file__)


def get_product_list(page, campaign_id, access_token):
    """Получить список товаров магазина Яндекс-Маркет

        На входе получает page последнего товара на странице, id компании и токен магазина.
        Возвращает список артикулов часов, созданный на основании запроса к магазину Яндекс-Маркет

        Args:
            page (str): страница перечня часов
            campaign_id (str): id компании
            access_token (str): токен магазина

        Return:
            offer_ids(list): список артикулов часов

    """
    endpoint_url = "https://api.partner.market.yandex.ru/"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Host": "api.partner.market.yandex.ru",
    }
    payload = {
        "page_token": page,
        "limit": 200,
    }
    url = endpoint_url + f"campaigns/{campaign_id}/offer-mapping-entries"
    response = requests.get(url, headers=headers, params=payload)
    response.raise_for_status()
    response_object = response.json()
    return response_object.get("result")


def update_stocks(stocks, campaign_id, access_token):
    """Обновить остатки

        На входе получает список остатков часов, id компании и токен магазина.
        Обновляет список остатков в магазине Яндекс-Маркет.
        Возвращает обновленный список остатков часов.

        Args:
            stocks (list): список остатков часов
            campaign_id (str): id клиента
            access_token (str): токен магазина

        Return:
            list: список остатков часов

    """
    endpoint_url = "https://api.partner.market.yandex.ru/"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Host": "api.partner.market.yandex.ru",
    }
    payload = {"skus": stocks}
    url = endpoint_url + f"campaigns/{campaign_id}/offers/stocks"
    response = requests.put(url, headers=headers, json=payload)
    response.raise_for_status()
    response_object = response.json()
    return response_object


def update_price(prices, campaign_id, access_token):
    """Обновить цены часов

        На входе получает список цен на часы, id компании и токен магазина.
        Обновляет цены в магазине Яндекс-Маркет.
        Возвращает обновленный список цен часов.

        Args:
            prices (list): список остатков часов
            campaign_id (str): id компании
            access_token (str): токен магазина

        Return:
            list: список цен

    """
    endpoint_url = "https://api.partner.market.yandex.ru/"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Host": "api.partner.market.yandex.ru",
    }
    payload = {"offers": prices}
    url = endpoint_url + f"campaigns/{campaign_id}/offer-prices/updates"
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    response_object = response.json()
    return response_object


def get_offer_ids(campaign_id, market_token):
    """Получить артикулы товаров Яндекс маркета

        На входе получает id компании и токен магазина.
        Возвращает список артикулов часов, созданный на основании
        списка часов.

        Args:
            campaign_id (str): id клиента
            market_token (str): токен магазина

        Return:
            offer_ids(list): список артикулов часов

    """
    page = ""
    product_list = []
    while True:
        some_prod = get_product_list(page, campaign_id, market_token)
        product_list.extend(some_prod.get("offerMappingEntries"))
        page = some_prod.get("paging").get("nextPageToken")
        if not page:
            break
    offer_ids = []
    for product in product_list:
        offer_ids.append(product.get("offer").get("shopSku"))
    return offer_ids


def create_stocks(watch_remnants, offer_ids, warehouse_id):
    """Создать список словарей остатков часов

        На входе получает 2 списка: список часов и список артикулов.
        Возвращает список словарей остатков часов, полученных из списка часов,
        если такие часы есть в списке артикулов, с указанием количества остатков часов.

        Args:
            watch_remnants (list): список часов
            offer_ids (list): список артикулов
            warehouse_id (str): id склада

        Return:
            stocks(list): список остатков часов

    """
    stocks = list()
    date = str(datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z")
    for watch in watch_remnants:
        if str(watch.get("Код")) in offer_ids:
            count = str(watch.get("Количество"))
            if count == ">10":
                stock = 100
            elif count == "1":
                stock = 0
            else:
                stock = int(watch.get("Количество"))
            stocks.append(
                {
                    "sku": str(watch.get("Код")),
                    "warehouseId": warehouse_id,
                    "items": [
                        {
                            "count": stock,
                            "type": "FIT",
                            "updatedAt": date,
                        }
                    ],
                }
            )
            offer_ids.remove(str(watch.get("Код")))
    for offer_id in offer_ids:
        stocks.append(
            {
                "sku": offer_id,
                "warehouseId": warehouse_id,
                "items": [
                    {
                        "count": 0,
                        "type": "FIT",
                        "updatedAt": date,
                    }
                ],
            }
        )
    return stocks


def create_prices(watch_remnants, offer_ids):
    """Создать список словарей цены на товары

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
                "id": str(watch.get("Код")),
                # "feed": {"id": 0},
                "price": {
                    "value": int(price_conversion(watch.get("Цена"))),
                    # "discountBase": 0,
                    "currencyId": "RUR",
                    # "vat": 0,
                },
                # "marketSku": 0,
                # "shopSku": "string",
            }
            prices.append(price)
    return prices


async def upload_prices(watch_remnants, campaign_id, market_token):
    """Отправить цены на часы в магазин Яндекс-Маркет

        На входе получает список часов, id компании и токен магазина.
        Обновляет список цен на часы, разделяя на части при загрузке
        в магазин Яндекс_маркет. Возвращает обновленный список остатков часов.

        Args:
            watch_remnants (list): список остатков часов
            campaign_id (str): id компании
            market_token (str): токен магазина

        Return:
            prices (list): список цен на часы

        """
    offer_ids = get_offer_ids(campaign_id, market_token)
    prices = create_prices(watch_remnants, offer_ids)
    for some_prices in list(divide(prices, 500)):
        update_price(some_prices, campaign_id, market_token)
    return prices


async def upload_stocks(watch_remnants, campaign_id, market_token, warehouse_id):
    """Отправить остатки в магазин Яндекс-Маркет.

        На входе получает список часов, id компании и токен магазина.
        Обновляет список остатков часов, разделяя на части при загрузке в магазин.
        Возвращает обновленный список остатков часов и список наличия часов.

        Args:
            watch_remnants (list): список остатков часов
            campaign_id (str): id клиента
            market_token (str): токен магазина
            warehouse_id (str): id склада

        Return:
            not_empty (list): список наличия часов
            stocks (list): список остатков часов

    """
    offer_ids = get_offer_ids(campaign_id, market_token)
    stocks = create_stocks(watch_remnants, offer_ids, warehouse_id)
    for some_stock in list(divide(stocks, 2000)):
        update_stocks(some_stock, campaign_id, market_token)
    not_empty = list(
        filter(lambda stock: (stock.get("items")[0].get("count") != 0), stocks)
    )
    return not_empty, stocks


def main():
    """Запустить скрипт

        Считывает переменные окружения. Загружает артикулы часов. Создает список
        часов с сайта Casio. Создает список остатков. Для каждой модели доставки:
        обновляет остатки, обновляет цены магазина Яндекс-Маркет.

        Exceptions:
            ReadTimeout: превышено время ожидания
            ConnectionError: ошибка соединения
            Exception: любые ошибки

    """
    env = Env()
    market_token = env.str("MARKET_TOKEN")
    campaign_fbs_id = env.str("FBS_ID")
    campaign_dbs_id = env.str("DBS_ID")
    warehouse_fbs_id = env.str("WAREHOUSE_FBS_ID")
    warehouse_dbs_id = env.str("WAREHOUSE_DBS_ID")

    watch_remnants = download_stock()
    try:
        offer_ids = get_offer_ids(campaign_fbs_id, market_token)
        stocks = create_stocks(watch_remnants, offer_ids, warehouse_fbs_id)
        for some_stock in list(divide(stocks, 2000)):
            update_stocks(some_stock, campaign_fbs_id, market_token)
        upload_prices(watch_remnants, campaign_fbs_id, market_token)

        offer_ids = get_offer_ids(campaign_dbs_id, market_token)
        stocks = create_stocks(watch_remnants, offer_ids, warehouse_dbs_id)
        for some_stock in list(divide(stocks, 2000)):
            update_stocks(some_stock, campaign_dbs_id, market_token)
        upload_prices(watch_remnants, campaign_dbs_id, market_token)
    except requests.exceptions.ReadTimeout:
        print("Превышено время ожидания...")
    except requests.exceptions.ConnectionError as error:
        print(error, "Ошибка соединения")
    except Exception as error:
        print(error, "ERROR_2")


if __name__ == "__main__":
    main()
