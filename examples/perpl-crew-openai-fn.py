from crewai import Agent, Task, Crew, Process
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List
import os

load_dotenv()

class BookRecommendation(BaseModel):
    title: str
    author: str
    genre: str
    summary: str

class BookRecommendations(BaseModel):
    book_recommendations: List[BookRecommendation]

# AGENTS
book_recommender = Agent(
    role='Book Recommender',
    goal='Recommend books based on user preferences',
    backstory='You are an AI-powered book recommendation system with vast knowledge of literature.',
    allow_delegation=False,
    verbose=True,
    function_calling=True,
    llm_model="gpt-3.5-turbo",
    tools_force_call=True,  # Force the use of function calling
    openai_functions=[
        {
            "name": "recommend_books",
            "description": "Recommend books based on user preferences",
            "parameters": {
                "type": "object",
                "properties": {
                    "book_recommendations": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "author": {"type": "string"},
                                "genre": {"type": "string"},
                                "summary": {"type": "string"}
                            },
                            "required": ["title", "author", "genre", "summary"]
                        }
                    }
                },
                "required": ["book_recommendations"]
            }
        }
    ]
)

# TASKS
recommend_task = Task(
    description="Recommend 3 science fiction books for a reader who enjoys thought-provoking and futuristic themes. You MUST use the recommend_books function to format your response.",
    agent=book_recommender,
    expected_output="A JSON object containing an array of book recommendations with title, author, genre, and summary for each book."
)

# CREW
crew = Crew(
    agents=[book_recommender],
    tasks=[recommend_task],
    verbose=2,
    process=Process.sequential  # Ensure sequential processing
)

def main():
    # EXECUTE
    result = crew.kickoff()

    try:
        # Parse the result into our Pydantic model using the recommended method
        recommendations = BookRecommendations.model_validate_json(result)

        # Print the recommendations
        for book in recommendations.book_recommendations:
            print(f"Title: {book.title}")
            print(f"Author: {book.author}")
            print(f"Genre: {book.genre}")
            print(f"Summary: {book.summary}")
            print("---")
    except Exception as e:
        print(f"Error parsing result: {e}")
        print("Raw result:", result)

if __name__ == "__main__":
    # Verify OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        st.error("OpenAI API key not found. Please check your .env file.")
        st.stop()
    
    main()


