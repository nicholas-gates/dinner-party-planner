import json
from typing import Dict, Annotated
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph

from models import BookRecommendations
from utils import state_merge, logger
from config import MODEL_NAME, TEMPERATURE, RECOMMEND_BOOKS_SCHEMA

# Define the state type for type hints
State = Annotated[Dict, state_merge]

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

def create_book_agent():
    """Create an agent that recommends books based on user preferences."""
    # Initialize the LLM
    llm = ChatOpenAI(
        model=MODEL_NAME,
        temperature=TEMPERATURE,
    )

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

    # Create the chain with function calling
    chain = (
        prompt 
        | llm.bind(functions=[RECOMMEND_BOOKS_SCHEMA], function_call={"name": "recommend_books"}) 
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
    return workflow.compile()
