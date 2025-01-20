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

    def handle_llm_response(response):
        """Handle and validate the LLM response"""
        try:
            logger.info("Validating LLM response structure")
            # Extract function call arguments from the response
            if hasattr(response, 'additional_kwargs') and 'function_call' in response.additional_kwargs:
                # Parse the function call arguments
                import json
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
        | handle_llm_response
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
    workflow.add_node("recommend", recommend_books)

    # Create the edges
    workflow.set_entry_point("recommend")
    workflow.set_finish_point("recommend")

    # Compile the graph
    graph = workflow.compile()
    
    return graph

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

            # Display recommendations
            logger.info(f"Processing {len(result['recommendations'])} recommendations for display")
            for i, book_dict in enumerate(result["recommendations"], 1):
                logger.debug(f"Processing recommendation {i}: {book_dict['title']}")
                book = BookRecommendation(**book_dict)
                with st.container():
                    st.subheader(f"{i}. {book.title} by {book.author}")
                    st.write(f"**Genre:** {book.genre}")
                    st.write(f"**Description:** {book.description}")
                    st.write(f"**Why this book:** {book.reason}")
                    st.divider()
            logger.info("Finished displaying recommendations")
        else:
            logger.warning("User attempted to submit without input")
            st.warning("Please enter your book preferences first!")

if __name__ == "__main__":
    main()