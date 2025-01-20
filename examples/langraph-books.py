from typing import Dict, List, Annotated, Sequence
import os
from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
import streamlit as st
from langgraph.graph import Graph, StateGraph
from langgraph.prebuilt.tool_executor import ToolExecutor
import logging
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

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

# Define the state type for type hints
def state_merge(state1: Dict, state2: Dict) -> Dict:
    """Merge two states together."""
    state1.update(state2)
    return state1

State = Annotated[Dict, state_merge]

def create_book_agent():
    # Initialize the LLM
    llm = ChatOpenAI(
        model="gpt-4-turbo-preview",
        temperature=0.7,
    )

    # Define the function schema for OpenAI
    recommend_books_schema = {
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

    # Create the prompt template with explicit formatting instructions
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert librarian and book recommender. Your task is to recommend books based on the user's input.
        Provide thoughtful recommendations that match the user's interests, whether they specify an author, genre, theme, or other criteria.
        
        Guidelines for recommendations:
        1. Provide 3-5 high-quality recommendations
        2. Ensure each book genuinely matches the user's interests
        3. Include a mix of well-known and potentially overlooked books
        4. Verify all book information is accurate
        5. Write clear, informative descriptions
        6. Explain specifically why each book matches the request
        
        Your response will be automatically formatted into JSON using the function call mechanism."""),
        MessagesPlaceholder(variable_name="messages"),
        ("human", "{input}")
    ])

    def process_book_recommendation_response(response):
        """Handle and validate the LLM response"""
        try:
            logger.info("Validating LLM response structure")
            # Extract function call arguments from the response
            if hasattr(response, 'additional_kwargs') and 'function_call' in response.additional_kwargs:
                # Parse the function call arguments
                args = json.loads(response.additional_kwargs['function_call']['arguments'])
                # Validate with our Pydantic model
                recommendations = BookRecommendations(**args)
                logger.info("Successfully validated LLM response")
                return args
            else:
                logger.warning("No function call found in response")
                return {"recommendations": []}
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            # Return a safe default response
            return {"recommendations": []}

    # Create the chain with function calling
    chain = (
        prompt 
        | llm.bind(functions=[recommend_books_schema], function_call={"name": "recommend_books"}) 
        | process_book_recommendation_response
    )

    def recommend_books(state: State) -> State:
        """Generate book recommendations based on user input."""
        logger.info("Starting book recommendation process")
        messages = state.get("messages", [])
        user_input = state.get("input", "")
        logger.info(f"Processing request with input: {user_input}")
        
        # Get recommendations from the chain
        logger.info("Invoking LLM chain for recommendations")
        result = chain.invoke({
            "messages": messages,
            "input": user_input
        })
        logger.info(f"Raw output from LLM: {result}")
        logger.info(f"Received {len(result['recommendations'])} recommendations from LLM")
        
        # Update the state with recommendations - result is already a dictionary
        new_state = {"messages": messages, "input": user_input, "recommendations": result["recommendations"]}
        logger.info("Updated state with new recommendations")
        return new_state

    # Create the graph
    workflow = StateGraph(State)

    # Add the recommendation node
    workflow.add_node("recommend_books", recommend_books)

    # Create the edges
    workflow.set_entry_point("recommend_books")
    workflow.set_finish_point("recommend_books")

    # Compile the graph
    graph = workflow.compile()
    
    return graph

def create_cross_domain_agent():
    """Create an agent that recommends related content across different domains."""
    # Initialize the LLM
    llm = ChatOpenAI(
        model="gpt-4-turbo-preview",
        temperature=0.7,
    )

    # Define the function schema for OpenAI
    cross_domain_schema = {
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

    # Create the prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert content recommender who can find thematic connections across different media types.
        Based on the given book, recommend ONE movie, ONE game, and ONE song that share similar themes, moods, or ideas.
        
        Guidelines for recommendations:
        1. Focus on thematic connections, not just genre matches
        2. Consider emotional resonance and core ideas
        3. Provide thoughtful explanations for each recommendation
        4. Be specific about why each item connects to the book
        5. Consider both classic and contemporary options
        
        Your response will be automatically formatted using the function call mechanism."""),
        ("human", """Here is the book to base recommendations on:
        Title: {title}
        Author: {author}
        Genre: {genre}
        Description: {description}
        
        Please recommend related content that shares themes with this book.""")
    ])

    def handle_cross_domain_response(response):
        """Handle and validate the cross-domain recommendation response"""
        try:
            logger.info("Validating cross-domain response structure")
            if hasattr(response, 'additional_kwargs') and 'function_call' in response.additional_kwargs:
                args = json.loads(response.additional_kwargs['function_call']['arguments'])
                recommendations = CrossDomainRecommendation(**args)
                logger.info("Successfully validated cross-domain response")
                return args
            else:
                logger.warning("No function call found in cross-domain response")
                return {}
        except Exception as e:
            logger.error(f"Error parsing cross-domain response: {e}")
            return {}

    # Create the chain
    chain = (
        prompt 
        | llm.bind(functions=[cross_domain_schema], function_call={"name": "recommend_cross_domain"})
        | handle_cross_domain_response
    )

    def recommend_related_content(state: State) -> State:
        """Generate cross-domain recommendations based on a selected book."""
        selected_book = state.get("selected_book", {})
        if not selected_book:
            logger.warning("No book selected for cross-domain recommendations")
            return state

        logger.info(f"Generating cross-domain recommendations for book: {selected_book.get('title')}")
        result = chain.invoke({
            "title": selected_book.get("title"),
            "author": selected_book.get("author"),
            "genre": selected_book.get("genre"),
            "description": selected_book.get("description")
        })
        logger.info(f"Cross domain raw output from LLM: {result}")
        
        state["cross_domain_recommendations"] = result
        return state

    # Create the graph
    workflow = StateGraph(State)
    workflow.add_node("recommend_related", recommend_related_content)
    workflow.set_entry_point("recommend_related")
    workflow.set_finish_point("recommend_related")
    
    return workflow.compile()

def main():
    logger.info("Starting Book Recommendation System")
    st.title("📚 Book Recommendation System")
    st.write("""
    Welcome to the Book Recommendation System! Tell me what kind of books you're interested in,
    and I'll provide personalized recommendations. You can mention:
    - Authors you enjoy
    - Genres you prefer
    - Themes or topics you're interested in
    - Writing styles you like
    - Or any other criteria!
    """)

    # Get user input
    user_input = st.text_area("What kind of books are you looking for?", 
                             placeholder="E.g., 'I love magical realism like Gabriel García Márquez' or 'Looking for sci-fi books about time travel'")

    # Store the book recommendations in session state
    if "book_recommendations" not in st.session_state:
        st.session_state.book_recommendations = None

    if st.button("Get Recommendations"):
        if user_input:
            logger.info("User submitted request for recommendations")
            # Create and run the graph
            logger.info("Creating recommendation agent")
            graph = create_book_agent()
            
            # Initialize the state
            state = {
                "messages": [],
                "input": user_input,
                "recommendations": []
            }
            logger.info(f"Initialized state with input: {user_input}")

            # Run the graph
            with st.spinner("Generating recommendations..."):
                logger.info("Running recommendation graph")
                result = graph.invoke(state)
                logger.info("Received recommendations from graph")
                # Store recommendations in session state
                st.session_state.book_recommendations = result["recommendations"]

        else:
            logger.warning("User attempted to submit without input")
            st.warning("Please enter your book preferences first!")

    # Display book recommendations if available
    if st.session_state.book_recommendations:
        logger.info(f"Processing {len(st.session_state.book_recommendations)} recommendations for display")
        for i, book_dict in enumerate(st.session_state.book_recommendations, 1):
            logger.debug(f"Processing recommendation {i}: {book_dict['title']}")
            book = BookRecommendation(**book_dict)
            with st.container():
                st.subheader(f"{i}. {book.title} by {book.author}")
                st.write(f"**Genre:** {book.genre}")
                st.write(f"**Description:** {book.description}")
                st.write(f"**Why this book:** {book.reason}")
                st.divider()
        logger.info("Finished displaying recommendations")

        # Add a section for cross-domain recommendations
        st.subheader("Get Cross-Domain Recommendations")
        st.write("Select a book to get related movie, game, and song recommendations that share similar themes.")
        
        # Create dropdown with book titles
        book_titles = [book["title"] for book in st.session_state.book_recommendations]
        selected_index = st.selectbox(
            "Select a book",
            range(len(book_titles)),
            format_func=lambda i: book_titles[i]
        )

        if st.button("Get Related Content"):
            # Create cross-domain agent
            cross_domain_graph = create_cross_domain_agent()
            selected_book = st.session_state.book_recommendations[selected_index]

            # Run the cross-domain graph
            with st.spinner("Generating cross-domain recommendations..."):
                logger.info("Running cross-domain recommendation graph")
                cross_domain_result = cross_domain_graph.invoke({"selected_book": selected_book})
                logger.info("Received cross-domain recommendations from graph")

            # Display cross-domain recommendations
            if cross_domain_result.get("cross_domain_recommendations"):
                logger.info("Processing cross-domain recommendations for display")
                recommendations = cross_domain_result["cross_domain_recommendations"]
                
                st.markdown("### Related Content")
                
                # Movie recommendation
                st.markdown("#### 🎬 Movie")
                movie = recommendations["movie"]
                st.write(f"**{movie['title']}** ({movie['year']})")
                st.write(movie['description'])
                st.write(f"*Why this movie:* {movie['reason']}")
                
                # Game recommendation
                st.markdown("#### 🎮 Game")
                game = recommendations["game"]
                st.write(f"**{game['title']}** ({game['platform']})")
                st.write(game['description'])
                st.write(f"*Why this game:* {game['reason']}")
                
                # Song recommendation
                st.markdown("#### 🎵 Song")
                song = recommendations["song"]
                st.write(f"**{song['title']}** by {song['artist']}")
                st.write(song['description'])
                st.write(f"*Why this song:* {song['reason']}")
                
                logger.info("Finished displaying cross-domain recommendations")

if __name__ == "__main__":
    main()