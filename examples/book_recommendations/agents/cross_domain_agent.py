import json
from typing import Dict, Annotated
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph

from models import CrossDomainRecommendation
from utils import state_merge, logger
from config import MODEL_NAME, TEMPERATURE, CROSS_DOMAIN_SCHEMA

# Define the state type for type hints
State = Annotated[Dict, state_merge]

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

def create_cross_domain_agent():
    """Create an agent that recommends related content across different domains."""
    # Initialize the LLM
    llm = ChatOpenAI(
        model=MODEL_NAME,
        temperature=TEMPERATURE,
    )

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

    # Create the chain
    chain = (
        prompt 
        | llm.bind(functions=[CROSS_DOMAIN_SCHEMA], function_call={"name": "recommend_cross_domain"})
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
