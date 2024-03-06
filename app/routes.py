from fastapi import HTTPException, Depends,APIRouter,Request,Form
from sqlalchemy.orm import Session
from app.models import Book,User
from app.schemas import add_book_request,signup,Signin
from app.database import SessionLocal,engine,Base
from sqlalchemy import select,func
from fastapi.responses import HTMLResponse,RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer

    
routes = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
#### add to the Book ###
@routes.post("/add_book/")
async def add_book(
    request: add_book_request,
    db: Session = Depends(get_db)):
    try:
        print(request.title)
        new_book = Book(
            title=request.title,
            author=request.author,
            price=request.price,
            year_published=request.year_published,
        )
        db.add(new_book)
        db.commit()
        db.refresh(new_book)
        return {"message": "Book added successfully", "book_id": new_book.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


### get all the book list show here ###
@routes.get("/get_all_books/")
async def get_all_books(db: Session = Depends(get_db)):
    books = db.query(Book).all()
    return {
        "books": [
            {
                "id": book.id,
                "title": book.title,
                "author": book.author,
                "price": book.price,
                "year_published": book.year_published,
            }
            for book in books
        ]
    }

### edit route###

@routes.put("/edit_book/{book_id}")
async def edit_book(book_id: int, request: add_book_request, db: Session = Depends(get_db)):
    try:
        # Get the original position of the book
        original_position_subquery = select(func.row_number().over(order_by=Book.id).label("row_number")).where(Book.id == book_id).subquery()

        # Update the book with the new data
        db.query(Book).filter(Book.id == book_id).update({
            Book.title: request.title,
            Book.author: request.author,
            Book.price: request.price,
            Book.year_published: request.year_published
        })
        db.commit()

        # Restore the original position of the book
        original_position = db.query(original_position_subquery.c.row_number).as_scalar()
        db.query(Book).filter(Book.id == book_id).update({
            Book.title: request.title,
            Book.author: request.author,
            Book.price: request.price,
            Book.year_published: request.year_published
        })
        db.commit()

        return {"message": "Book updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")



### delete route###  

@routes.delete("/delete_book/{book_id}")
async def delete_book(book_id: int, db: Session = Depends(get_db)):
    try:
        book = db.query(Book).filter(Book.id == book_id).first()
        if book:
            db.delete(book)
            db.commit()
            return {"message": "Book deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Book not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    
    ### get one book details###

@routes.get("/get_book/{book_id}")
async def get_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return book
##########################################################################
templates = Jinja2Templates(directory="templates")
## welcome page ##
@routes.get("/" , response_class=HTMLResponse)
async def index(request: Request):
    return  templates.TemplateResponse("index.html",{"request": request})

## singup page##



@routes.post("/signup")
async def signup(Request:signup):
    
    new_user = User(username=Request.username, password=Request.password)
    db= SessionLocal()
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    db.close()
    return {"message":"signup successfully"}


    # Render the index page HTML content
    # with open("templates/index.html", "r") as index_file:
    #     index_content = index_file.read()
    
    # return HTMLResponse(content=index_content, status_code=200)

#### signin #####
@routes.post("/signin")
async def signin(signin_request: Signin):
    # Retrieve the user from the database based on the provided username and password
    db = SessionLocal()
    user = db.query(User).filter(User.username == signin_request.username,User.password== signin_request.password).first()
    db.close()

    # Check if the user exists and the passwor0d matches
    if user is None or user.password != signin_request.password and user.username != signin_request.username:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    return {"message": "Signin successful"}

###  All User username  ###

@routes.get("/users")
def All_user_username():
    db = SessionLocal()
    users = db.query(User).all()
    db.close()

    usernames = [user.username for user in users]  # Extract usernames from the user objects
    return {"usernames": usernames} # Return the list of usernames

#### particular delete single user data ######

@routes.delete("/user_delete/{user_id}")
async def delete_user(user_id: int):
    # Retrieve the user from the database based on the provided user_id
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()

    # Check if the user exists
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Delete the user
    db.delete(user)
    db.commit()
    db.close()

    # Return a success response
    return {"message": "User deleted successfully"}