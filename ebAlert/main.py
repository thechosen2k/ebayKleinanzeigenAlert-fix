import sys
from random import randint
from time import sleep

import requests
from sqlalchemy.orm import Session

from ebAlert import create_logger
from ebAlert.core import healthcheck
from ebAlert.crud.base import crud_link, get_session
from ebAlert.crud.post import crud_post
from ebAlert.ebayscrapping import ebayclass
from ebAlert.telegram.telegramclass import telegram

log = create_logger(__name__)

try:
    import click
    from click import BaseCommand
except ImportError:
    log.error("Click should be installed\npip install click")


@click.group()
def cli() -> BaseCommand:
    pass


@cli.command(help="Fetch new post and send telegramclass notification.")
def start():
    """
    loop through the urls in the database and send message
    """
    print(">> Starting Ebay alert")
    with get_session() as db:
        get_all_post(db=db, telegram_message=True)
    print("<< Ebay alert finished")


@cli.command(options_metavar="<options>", help="Add/Show/Remove URL from database.")
@click.option("-r", "--remove_link", 'remove', metavar="<link id>", help="Remove link from database.")
@click.option("-c", "--clear", is_flag=True, help="Clear post database.")
@click.option("-a", "--add_url", 'url', metavar='<URL>', help="Add URL to database and fetch posts.")
@click.option("-i", "--init", is_flag=True, help="Initialise database after clearing.")
@click.option("-s", "--show", is_flag=True, help="Show all urls and corresponding id.")
def links(show, remove, clear, url, init):
    """
    cli related to the links. Add, remove, clear, init and show
    """
    # TODO: Add verification if action worked.
    with get_session() as db:
        if show:
            print(">> List of URL")
            links = crud_link.get_all(db)
            if links:
                for link_model in links:
                    print("{0:<{1}}{2}".format(link_model.id, 8 - len(str(link_model.id)), link_model.link))
            print("<< List of URL")
        elif remove:
            print(">> Removing link")
            if crud_link.remove(db=db, id=remove):
                print("<< Link removed")
            else:
                print("<< No link found")
        elif clear:
            print(">> Clearing item database")
            crud_post.clear_database(db=db)
            print("<< Database cleared")
        elif url:
            print(">> Adding url")
            if crud_link.get_by_key(key_mapping={"link": url}, db=db):
                print("<< Link already exists")
            else:
                crud_link.create({"link": url}, db)
                ebay_items = ebayclass.EbayItemFactory(url)
                crud_post.add_items_to_db(db=db, items=ebay_items.item_list)
                print("<< Link and post added to the database")
        elif init:
            print(">> Initializing database")
            get_all_post(db)
            print("<< Database initialized")


def get_all_post(db: Session, telegram_message=False):
    links = crud_link.get_all(db=db)
    if links:
        session = requests.Session()
        total_fetched = 0
        total_empty = 0
        for link_model in links:
            print("Processing link - id: {} - link: {} ".format(link_model.id, link_model.link))
            post_factory = ebayclass.EbayItemFactory(link_model.link, session=session)
            if post_factory.page_fetched:
                total_fetched += 1
                if post_factory.raw_item_count == 0:
                    total_empty += 1
            new_items, price_drops = crud_post.add_items_to_db(db=db, items=post_factory.item_list)
            if telegram_message:
                for item in new_items:
                    telegram.send_formated_message(item)
                for item, old_price in price_drops:
                    telegram.send_price_drop_message(item, old_price)
            sleep(randint(0, 40)/10)
        if healthcheck.record_run(total_fetched, total_empty):
            telegram.send_message(
                f"Achtung: {total_empty} von {total_fetched} Links liefern in diesem Lauf 0 Treffer. "
                f"Vermutlich hat sich die Kleinanzeigen-Seitenstruktur geaendert."
            )


if __name__ == "__main__":
    cli(sys.argv[1:])
