from typing import List
from pydantic import BaseModel, Field

class BookRecommendation(BaseModel):
    """Schema for a book recommendation."""
    title: str = Field(description="The title of the book")
    author: str = Field(description="The author of the book")
    genre: str = Field(description="The genre of the book")
    description: str = Field(description="A brief description of the book")
    reason: str = Field(description="Why this book matches the user's request")

class BookRecommendations(BaseModel):
    """Schema for multiple book recommendations."""
    recommendations: List[BookRecommendation] = Field(description="List of book recommendations")

class CrossDomainRecommendation(BaseModel):
    """Schema for cross-domain recommendations based on a book."""
    movie: dict = Field(description="A movie recommendation", example={
        "title": "Movie Title",
        "year": "Release Year",
        "description": "Brief description",
        "reason": "Why it matches the book's themes"
    })
    game: dict = Field(description="A game recommendation", example={
        "title": "Game Title",
        "platform": "Gaming Platform",
        "description": "Brief description",
        "reason": "Why it matches the book's themes"
    })
    song: dict = Field(description="A song recommendation", example={
        "title": "Song Title",
        "artist": "Artist Name",
        "description": "Brief description",
        "reason": "Why it matches the book's themes"
    })
