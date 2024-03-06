from pydantic import BaseModel, validator

class add_book_request(BaseModel):
    title: str
    author: str
    price: int
    year_published: int

    @validator("title")
    def validate_title(cls, value):
        if not value or not value.strip():
            raise ValueError("Title cannot be empty or whitespace.")
        return value

    @validator("author")
    def validate_author(cls, value):
        if not value or not value.strip():
            raise ValueError("Author cannot be empty or whitespace.")
        return value

    @validator("price")
    def validate_price(cls, value):
        if value <= 0:
            raise ValueError("Price must be greater than zero.")
        return value

    @validator("year_published")
    def validate_year_published(cls, value):
        current_year = 2024  # Update with the current year or get it dynamically
        if value < 0 or value > current_year:
            raise ValueError(f"Invalid year. Year must be between 0 and {current_year}.")
        return value
######################## signup _user ########################


class signup(BaseModel):
    username: str
    password: str

    @validator("username" , pre=True)
    def validate_username(cls, value):
        if len(value) < 3:
            raise ValueError('Username must be at least 3 characters long')
        return value

    @validator("password" , pre=True)
    def validate_password(cls, value):
        if len(value) < 3:
            raise ValueError('Password must be at least 3 characters long')
        return value

### signin ######
class Signin(BaseModel):
    username: str
    password: str

