from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime, UniqueConstraint, Text
from sqlalchemy.orm import relationship
import datetime

from database import Base

class Book(Base):
    __tablename__ = 'books'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    summary = Column(Text, nullable=True)
    details = Column(Text, nullable=True)
    author = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    image = Column(String, nullable=True)
    is_published = Column(Boolean, default=False)
    created_on = Column(DateTime(timezone=True), default=datetime.datetime.now(datetime.UTC), nullable=False)
    updated_on = Column(DateTime(timezone=True), default=datetime.datetime.now(datetime.UTC), onupdate=datetime.datetime.now(datetime.UTC), nullable=False)

    categories = relationship(
        "Category",
        secondary="book_category",
        back_populates="books"
    )

class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    detail = Column(Text, nullable=True)
    created_on = Column(DateTime(timezone=True), default=datetime.datetime.now(datetime.UTC), nullable=False)

    books = relationship(
        "Book",
        secondary="book_category",
        back_populates="categories"
    )

class BookCategory(Base):
    __tablename__ = 'book_category'

    book_id = Column(Integer, ForeignKey("books.id", onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
    category_id = Column(Integer, ForeignKey("categories.id", onupdate="CASCADE", ondelete="RESTRICT"), primary_key=True)

class Menu(Base):
    __tablename__ = 'menus'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    details = Column(String, nullable=True)
    price = Column(Float, nullable=False)
    image = Column(String, nullable=True)
    created_on = Column(DateTime(timezone=True), default=datetime.datetime.now(datetime.UTC), nullable=False)

    order_item = relationship("OrderItem", back_populates="menu")



class Order(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    ordered_on = Column(DateTime(timezone=True), default=datetime.datetime.now(datetime.UTC), nullable=False)
    # Relationship to OrderItem
    order_items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    __tablename__ = 'order_items'
    __table_args__ = (UniqueConstraint('order_id', 'menu_id'),)

    order_id = Column(Integer, ForeignKey('orders.id', onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
    menu_id = Column(Integer, ForeignKey('menus.id', onupdate="CASCADE", ondelete="RESTRICT"), primary_key=True)
    amount = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    additional_info = Column(Text, nullable=True)

    # Relationship back to Order
    order = relationship("Order", back_populates="order_items")
    menu = relationship("Menu", back_populates="order_item")
    
