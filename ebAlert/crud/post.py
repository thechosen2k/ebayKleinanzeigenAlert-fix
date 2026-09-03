from typing import List, Tuple

from sqlalchemy.orm import Session

from ebAlert.crud.base import CRUBBase
from ebAlert.ebayscrapping.ebayclass import EbayItem, parse_price
from ebAlert.models.sqlmodel import EbayPost


class CRUDPost(CRUBBase):

    def add_items_to_db(self, items: List[EbayItem], db: Session) -> Tuple[List[EbayItem], List[Tuple[EbayItem, float]]]:
        new_items = []
        price_drops = []
        for item in items:
            existing = self.get_by_key({"post_id": str(item.id)}, db)
            if not existing:
                self.create(
                    {"post_id": item.id, "title": item.title, "price": item.price, "link": item.link}, db=db
                )
                new_items.append(item)
                continue

            old_price = parse_price(existing.price)
            new_price = parse_price(item.price)
            if old_price is not None and new_price is not None and new_price < old_price:
                existing.price = item.price
                db.commit()
                price_drops.append((item, old_price))
        return new_items, price_drops


crud_post = CRUDPost(EbayPost)
