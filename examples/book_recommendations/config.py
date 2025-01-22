from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenAI model configuration
MODEL_NAME = "gpt-4-turbo-preview"
TEMPERATURE = 0.7

# Function schemas
RECOMMEND_BOOKS_SCHEMA = {
    "name": "recommend_books",
    "description": "Generate book recommendations based on user preferences",
    "parameters": {
        "type": "object",
        "properties": {
            "recommendations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "The title of the book"},
                        "author": {"type": "string", "description": "The author of the book"},
                        "genre": {"type": "string", "description": "The genre of the book"},
                        "description": {"type": "string", "description": "A brief description of the book"},
                        "reason": {"type": "string", "description": "Why this book matches the user's request"}
                    },
                    "required": ["title", "author", "genre", "description", "reason"]
                }
            }
        },
        "required": ["recommendations"]
    }
}

CROSS_DOMAIN_SCHEMA = {
    "name": "recommend_cross_domain",
    "description": "Generate recommendations for a movie, game, and song that match a book's themes",
    "parameters": {
        "type": "object",
        "properties": {
            "movie": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "The title of the movie"},
                    "year": {"type": "string", "description": "Release year of the movie"},
                    "description": {"type": "string", "description": "Brief description of the movie"},
                    "reason": {"type": "string", "description": "Why this movie matches the book's themes"}
                },
                "required": ["title", "year", "description", "reason"]
            },
            "game": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "The title of the game"},
                    "platform": {"type": "string", "description": "Gaming platform(s)"},
                    "description": {"type": "string", "description": "Brief description of the game"},
                    "reason": {"type": "string", "description": "Why this game matches the book's themes"}
                },
                "required": ["title", "platform", "description", "reason"]
            },
            "song": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "The title of the song"},
                    "artist": {"type": "string", "description": "The artist/band name"},
                    "description": {"type": "string", "description": "Brief description of the song"},
                    "reason": {"type": "string", "description": "Why this song matches the book's themes"}
                },
                "required": ["title", "artist", "description", "reason"]
            }
        },
        "required": ["movie", "game", "song"]
    }
}
