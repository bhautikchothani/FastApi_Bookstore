from fastapi import HTTPException, Depends,APIRouter,Request,Form,status,Body,Query
from sqlalchemy.orm import Session
from app.models import Book,User
from app.schemas import add_book_request,signup,signin,EditUserForm
from app.database import SessionLocal,engine,Base
from sqlalchemy import select,func
from fastapi.responses import HTMLResponse,RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import jwt
from datetime import datetime, timedelta
from fastapi import Query
from typing import Optional
from jose import JWTError,jwt
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from passlib.context import CryptContext


templates = Jinja2Templates(directory="templates")

# Security configuration
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

routes = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


###########
SECRET_KEY = "your_secret_key"  # Replace with your own secret key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Token expiration time in minutes

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

#### add to the Book ###
@routes.post("/add_book")
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
            department=request.department
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
                "department":book.department
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
            Book.year_published: request.year_published,
            Book.department: request.department
        })
        db.commit()

        # Restore the original position of the book
        original_position = db.query(original_position_subquery.c.row_number).as_scalar()
        db.query(Book).filter(Book.id == book_id).update({
            Book.title: request.title,
            Book.author: request.author,
            Book.price: request.price,
            Book.year_published: request.year_published,
            Book.department: request.department
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
    
    ## get one book details###

@routes.get("/get_book/{book_id}")
async def get_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

####### Admin and students to provides books #### 

@routes.get("/books")
async def get_books_based_on_role(
    token: str = Depends(oauth2_scheme),
    department: Optional[str] = Query(None, title="Department"),
    db: Session = Depends(get_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None or role is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = (
        db.query(User)
        .filter(User.username == username, User.role == role)
        .first()
    )
    if user is None:
        raise credentials_exception

    if role == "pritish":
        # For pritish, retrieve both Engineering and Commerce books
        books = db.query(Book).filter(
            Book.department.in_(["Engineering", "Commerce"])
        ).all()
    elif role == "admin":
        if department:
            # Return all books for the specific department
            books = db.query(Book).filter_by(department=department).all()
        else:
            # Return all books for admin
            books = db.query(Book).all()
    elif role == "student":
        if department and department != user.department:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You are not authorized to access books in this department. Your department is {user.department}"
            )
        # Filter books based on the department of the signed-in student
        books = db.query(Book).filter_by(department=user.department).all()
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    # Redirect to student.html
    redirect_url = "/student.html"
    return RedirectResponse(url=redirect_url)


##########################################################################
templates = Jinja2Templates(directory="templates")
## welcome page ##
@routes.get("/" , response_class=HTMLResponse)
async def index(request: Request):
    return  templates.TemplateResponse("index.html",{"request": request})


###  All User username  ###

@routes.get("/users")
def All_user_username():
    db = SessionLocal()
    users = db.query(User).all()
    db.close()

    usernames = [user.username for user in users]  # Extract usernames from the user objects
    return {"usernames": usernames} # Return the list of usernames

#### particular delete single user data ######

@routes.post("/user_delete/{user_id}", response_class=HTMLResponse)
async def delete_user(request: Request, user_id: int, action: str = Form(...)):
    # Retrieve the user from the database based on the provided user_id
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()

    # Check if the user exists
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if the request method is POST and _method is delete
    if request.method == "POST" and action == "delete":
        # Delete the user
        db.delete(user)
        db.commit()
        db.close()

        # Redirect to the admin page after deletion
        return RedirectResponse(url="/admin.html", status_code=303)
    else:
        # Return a 405 Method Not Allowed error if the request is not a POST request
        raise HTTPException(status_code=405, detail="Method Not Allowed")

###### signup router ######
@routes.get("/signup",response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})


@routes.post("/signup",response_class=HTMLResponse)
async def signup_route(request: Request,username: str = Form(...), password: str = Form(...), role: str = Form(...), department: str = Form(None)):
    # Check if the role is admin or pritish
    if role in {"admin", "pritish"}:
        department = None  # Set department to None for admin and pritish
    
    new_user = User(username=username, password=password, role=role, department=department)
    db = SessionLocal()
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    db.close()
    
    return templates.TemplateResponse("index.html", {"request": request,"message": "Signup successful"})


#### signin #####

@routes.post("/signin")
async def signin(form_data: OAuth2PasswordRequestForm = Depends()):
    # Retrieve the user from the database based on the provided username
    db = SessionLocal()
    user = db.query(User).filter(form_data.username==User.username).first()
    print(user)
    db.close()

    # Check if the user exists and the password matches
    if user is None or form_data.password != user.password:
        raise HTTPException(status_code=401, detail="Invalid username or password")


    # Determine the redirect URL based on the user's role
    redirect_url = ''
    if user.role == "admin":
        redirect_url = "/admin.html"
    elif user.role == "student":
        redirect_url = "/student.html"  # Change this to the actual URL for the student page
    else:
        raise HTTPException(status_code=401, detail="Unauthorized role")
    # Generate JWT token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token_payload = {
        "sub": user.username,   
        "role": user.role,
        "exp": datetime.utcnow() + access_token_expires
    }
    access_token = jwt.encode(access_token_payload, SECRET_KEY, algorithm=ALGORITHM)

    # Append the access token to the redirect URL
    redirect_url += f"?access_token={access_token}"
    return RedirectResponse(url=redirect_url)

###########################################################################################

### Templates Routes#####

@routes.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# Define route for admin.html

# @routes.get("/admin.html", response_class=HTMLResponse)
# async def admin(request: Request):
#     db = SessionLocal()
#     users = db.query(User).all()
#     db.close()
#     return templates.TemplateResponse("admin.html",{"request": request, "users": users})


@routes.post("/admin.html", response_class=HTMLResponse)
async def admin(request: Request):
    db = SessionLocal()
    users = db.query(User).all()
    books = db.query(Book).all()
    db.close()


    # user_data = [user.username for user in users]  # Extract usernames from the user objects
    return templates.TemplateResponse("admin.html", {"request": request, "users": users,"books": books})


########## Admin will user edit ########

# Define edit  Routers In Admin Side


@routes.get("/edit/{user_id}")
async def get_user_for_edit(user_id: int, request: Request, db: Session = Depends(get_db)):
    # Fetch the user from the database
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Render the edit user form with the user data
    return templates.TemplateResponse(
        "User_Edit.html", 
        {"request": request, "user": user}
    )


@routes.post("/edit/{user_id}")
async def edit_user(user_id: int, new_user_data: EditUserForm, db: Session = Depends(get_db)):
    # Fetch the user from the database
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update user data with the new values
    user.username = new_user_data.username
    user.role = new_user_data.role
    user.department = new_user_data.department

    db.commit()

    # Redirect to admin page after successfully updating the user
    return RedirectResponse(url="/admin.html", status_code=303)


# delete user Record Routers In Admin Side
@routes.get("/delete/{user_id}",response_class=HTMLResponse)
async def delete_user(user_id: int, request: Request,db: Session = Depends(get_db)):
    # Fetch the user from the database
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Delete the user from the database
    db.delete(user)
    db.commit()

    # Redirect to user_data.html after successfully deleting the user
    return templates.TemplateResponse("admin.html",{"request": request, "user": user})

# # # # # # # # # # # # # # # # # # # # 

@routes.get("/student.html", response_class=HTMLResponse)
async def get_student_page(request: Request):
    return templates.TemplateResponse("student.html", {"request": request})  # You can pass books data here if needed


@routes.post("/student.html", response_class=HTMLResponse)
async def student(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    db = SessionLocal()
    
    # Retrieve the user from the database based on the provided username and password
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or form_data.password != user.password:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # Determine the department based on the user's role
    department = user.department

    # If department is not provided, determine it based on the user's role
    if not department:
        if user.role == "admin":
            # Admin can access all departments
            department = "All Departments"
        elif user.role == "student":
            # Students can access their own department
            department = user.department

    # Fetch data based on the determined department
    books = db.query(Book).filter(Book.department == department).all()
    
    db.close()

    return templates.TemplateResponse("student.html", {"request": request, "books": books})