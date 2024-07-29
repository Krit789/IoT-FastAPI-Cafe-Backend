from dotenv import load_dotenv
import inspect
load_dotenv()

from fastapi import FastAPI, Depends, Response, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel, Field, field_validator
from typing import List
from starlette.responses import FileResponse 

# Import models
from database import SessionLocal, engine
import models
import datetime

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
router_v1 = APIRouter(prefix='/api/v1')

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://65070030-iot-cafe.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request validation

class CategoryBase(BaseModel):
    name: str
    detail: str | None = None

class CategoryRead(CategoryBase):
    id: int

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(CategoryBase):
    name: str | None = None
    detail: str | None = None

class BookBase(BaseModel):
    title: str
    author: str
    year: int
    is_published: bool = False
    image: str | None = None
    summary: str | None = None
    details: str | None = None
    categories: List[int] = []

    @field_validator('year')
    @classmethod
    def year_validator(cls, value):
        if value > datetime.datetime.now().year:
            raise ValueError("Year cannot be in the future")
        return value

class BookReadSingle(BookBase):
    title: str
    author: str
    year: int
    is_published: bool = False
    image: str | None = None
    summary: str | None = None
    details: str | None = None
    categories: List[CategoryRead] = []

class BookRead(BookBase):
    id: int
    title: str
    author: str
    year: int
    image: str  | None = None
    is_published: bool = False
    summary: str | None = None
    details: str | None = None
    categories: List[CategoryRead] = []

class BookCreate(BookBase):
    pass

class BookUpdate(BookBase):
    title: str | None = None
    author: str | None = None
    year: int | None = None
    is_published: bool | None = None
    image: str | None = None
    summary: str | None = None
    details: str  | None = None
    categories: List[int] | None = None

class MenuBase(BaseModel):
    name: str
    details: str | None = None
    price: float
    image: str | None = None

class MenuCreate(MenuBase):
    pass

class MenuUpdate(MenuBase):
    name: str | None = None
    price: float | None = None

class MenuRead(MenuBase):
    id: int

class OrderItemBase(BaseModel):
    menu_id: int
    amount: int
    price: float
    additional_info: str | None = None

class OrderItemCreate(OrderItemBase):
    pass

class OrderItemRead(OrderItemBase):
    order_id: int
    menu: MenuRead

class OrderBase(BaseModel):
    first_name: str
    last_name: str
    phone: str
    order_items: List[OrderItemCreate] = [] 

class OrderCreate(OrderBase):
    pass

class OrderUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    order_items: List[OrderItemCreate]| None = None

class OrderRead(OrderBase):
    id: int
    ordered_on: datetime.datetime
    order_items: List[OrderItemRead] = []

# Book CRUD

@router_v1.get('/books', response_model=List[BookRead])
async def get_books(db: Session = Depends(get_db)):
    try:
        books = db.query(models.Book).order_by(models.Book.title).all()
    except Exception as e:
        print(f"ERROR ({inspect.stack()[0][3]}): {e}")
        raise HTTPException(status_code=500, detail="Unable to get all books. Please try again later.")
    return books

@router_v1.get('/books/{book_id}', response_model=BookReadSingle)
async def get_book(book_id: int, db: Session = Depends(get_db)):
    try:
        book = db.query(models.Book).filter(models.Book.id == book_id).first()
    except Exception as e:
        print(f"ERROR ({inspect.stack()[0][3]}): {e}")
        raise HTTPException(status_code=500, detail="Unable to get this book. Please try again later.")
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

@router_v1.post('/books', status_code=201)
async def create_book(book: BookCreate, db: Session = Depends(get_db)):
    new_book = models.Book(**book.model_dump(exclude={'categories'}))
    for category_id in book.categories:
        category = db.query(models.Category).filter(models.Category.id == category_id).first()
        if category:
            new_book.categories.append(category)
        else:
            raise HTTPException(status_code=400, detail=f"Catagory ID {category_id} was not found")
    db.add(new_book)
    db.commit()
    db.refresh(new_book)
    return {"message": "Book created successfully", "id": new_book.id}

@router_v1.patch('/books/{book_id}')
async def update_book(book_id: int, book: BookUpdate, db: Session = Depends(get_db)):
    db_book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if not db_book:
        raise HTTPException(status_code=404, detail="Book not found")
    for key, value in book.model_dump(exclude={'categories'}, exclude_unset=True).items():
        setattr(db_book, key, value)

    if book.categories:
        db_book.categories = []
        for category_id in book.categories:
            category = db.query(models.Category).filter(models.Category.id == category_id).first()
            if category:
                db_book.categories.append(category)

    db.commit()
    db.refresh(db_book)
    return {"message": "Book updated successfully", "id": db_book.id}

@router_v1.delete('/books/{book_id}')
async def delete_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    db.delete(book)
    db.commit()
    return {"message": "Book deleted successfully"}

# Category CRUD

@router_v1.get('/categories', response_model=List[CategoryRead])
async def get_categories(db: Session = Depends(get_db)):
    return db.query(models.Category).order_by(models.Category.name).all()

@router_v1.get('/categories/{category_id}', response_model=CategoryBase)
async def get_category(category_id: int, db: Session = Depends(get_db)):
    category = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

@router_v1.post('/categories', status_code=201)
async def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    new_category = models.Category(**category.model_dump())
    db.add(new_category)
    db.commit()
    return {"message": "Category created successfully"}

@router_v1.patch('/categories/{category_id}')
async def update_category(category_id: int, category: CategoryUpdate, db: Session = Depends(get_db)):
    db_category = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    for key, value in category.model_dump(exclude_unset=True).items():
        setattr(db_category, key, value)
    db.commit()
    return {"message": "Category updated successfully"}

@router_v1.delete('/categories/{category_id}')
async def delete_category(category_id: int, db: Session = Depends(get_db)):
    category = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(category)
    db.commit()
    return {"message": "Category deleted successfully"}

# Menu CRUD

@router_v1.get('/menus', response_model=List[MenuRead])
async def get_menus(db: Session = Depends(get_db)):
    return db.query(models.Menu).all()

@router_v1.get('/menus/{menu_id}', response_model=MenuRead)
async def get_menu(menu_id: int, db: Session = Depends(get_db)):
    menu = db.query(models.Menu).filter(models.Menu.id == menu_id).first()
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")
    return menu

@router_v1.post('/menus', status_code=201)
async def create_menu(menu: MenuCreate, db: Session = Depends(get_db)):
    new_menu = models.Menu(**menu.model_dump())
    db.add(new_menu)
    db.commit()
    db.refresh(new_menu)
    return {"message": "Menu created successfully", "id": new_menu.id}

@router_v1.patch('/menus/{menu_id}')
async def update_menu(menu_id: int, menu: MenuUpdate, db: Session = Depends(get_db)):
    db_menu = db.query(models.Menu).filter(models.Menu.id == menu_id).first()
    if not db_menu:
        raise HTTPException(status_code=404, detail="Menu not found")
    for key, value in menu.model_dump(exclude_unset=True).items():
        setattr(db_menu, key, value)
    db.commit()
    return {"message": "Menu updated successfully"}

@router_v1.delete('/menus/{menu_id}')
async def delete_menu(menu_id: int, db: Session = Depends(get_db)):
    try:
        menu = db.query(models.Menu).filter(models.Menu.id == menu_id).first()
        if not menu:
            raise HTTPException(status_code=404, detail="Menu not found")
        db.query(models.OrderItem).filter(models.OrderItem.menu_id == menu_id).delete()
        db.delete(menu)
        db.commit()
        return {"message": "Menu deleted successfully"}
    except AssertionError as ae:
        raise HTTPException(status_code=400, detail=ae.args)

# Order CRUD

@router_v1.get('/orders', response_model=List[OrderRead])
async def get_orders(db: Session = Depends(get_db)):
    orders = db.query(models.Order).options(joinedload(models.Order.order_items).joinedload(models.OrderItem.menu)).order_by(models.Order.id.desc()).all() 
    return orders

@router_v1.get('/orders/{order_id}', response_model=OrderRead)
async def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(models.Order).options(joinedload(models.Order.order_items).joinedload(models.OrderItem.menu)).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@router_v1.post('/orders', status_code=201, response_model=OrderRead)
async def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    for order_item_data in order.order_items:
        menu = db.query(models.Menu).filter(models.Menu.id == order_item_data.menu_id).first()
        if not menu:
            raise HTTPException(status_code=404, detail=f"Menu with ID {order_item_data.menu_id} not found")

    new_order = models.Order(
        first_name=order.first_name,
        last_name=order.last_name,
        phone=order.phone
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    for order_item_data in order.order_items:
        new_order_item = models.OrderItem(
            order_id=new_order.id,
            menu_id=order_item_data.menu_id,
            amount=order_item_data.amount,
            price=order_item_data.price,
            additional_info=order_item_data.additional_info
        )
        db.add(new_order_item)

    db.commit()
    return new_order

@router_v1.patch('/orders/{order_id}')
async def update_order(order_id: int, order: OrderUpdate, db: Session = Depends(get_db)):
    db_order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Update order details
    for key, value in order.model_dump(exclude={'order_items'}, exclude_unset=True).items():
        setattr(db_order, key, value)

    # Delete existing order items
    db.query(models.OrderItem).filter(models.OrderItem.order_id == order_id).delete()

    # Create new order items
    for order_item_data in order.order_items:
        new_order_item = models.OrderItem(
            order_id=order_id,
            menu_id=order_item_data.menu_id,
            amount=order_item_data.amount,
            price=order_item_data.price,
            additional_info=order_item_data.additional_info
        )
        db.add(new_order_item)

    db.commit()

    return {"message": "Order updated successfully"}

@router_v1.delete('/orders/{order_id}')
async def delete_order(order_id: int, db: Session = Depends(get_db)):
    try:
        order = db.query(models.Order).filter(models.Order.id == order_id).first()
    except Exception as e:
        print(f"ERROR ({inspect.stack()[0][3]}): {e}")
        raise HTTPException(status_code=500, detail="Unable to reach database. Please try again later.")
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    try:
        db.query(models.Order).filter(models.Order.id == order_id).delete()
        db.commit()
        return {"message": "Order deleted successfully"}
    except Exception as e:
        print(f"ERROR ({inspect.stack()[0][3]}): {e}")
        raise HTTPException(status_code=500, detail="Unable to reach database. Please try again later.")

@app.get('/robots.txt')
async def preventIndexing():
    return FileResponse('static/robots.txt')

app.include_router(router_v1)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app)