import os
import json
from typing import List, Dict
from dotenv import load_dotenv
import streamlit as st
from pydantic import BaseModel, Field
from crewai import Agent, Task, Crew
from openai import OpenAI
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class WineAnalysis(BaseModel):
    """
    Represents the analysis of a selected wine.
    """
    characteristics: str = Field(
        ...,
        description="Detailed description of the wine's characteristics including aroma, taste, body, and finish"
    )
    pairing_suggestions: str = Field(
        ...,
        description="Specific food pairing suggestions that complement this wine"
    )
    serving_recommendations: str = Field(
        ...,
        description="Recommendations for serving temperature, decanting, and glass type"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "characteristics": "Medium-bodied red wine with aromas of black cherry and vanilla. Shows soft tannins with a smooth finish.",
                "pairing_suggestions": "Pairs well with grilled meats, especially lamb chops. Also excellent with aged cheeses.",
                "serving_recommendations": "Serve at 65°F (18°C). Decant for 30 minutes before serving. Use a Bordeaux-style glass."
            }
        }

class WineAnalyzerTool:
    """Tool for analyzing wines using OpenAI function calling."""
    
    def __init__(self):
        self.name = "analyze_wine"
        self.description = "Analyze a wine and provide structured information"
        self.func = self.__call__
    
    def __call__(self, wine: str) -> str:
        """Analyze wine using OpenAI function calling."""
        logger.info(f"Starting wine analysis for: {wine}")
        
        try:
            client = OpenAI()
            logger.info("OpenAI client initialized")
            
            schema = WineAnalysis.model_json_schema()
            logger.info(f"Generated schema: {json.dumps(schema, indent=2)}")
            
            functions = [{
                "name": "analyze_wine",
                "description": "Analyze a wine and provide structured information",
                "parameters": schema
            }]
            
            logger.info("Sending request to OpenAI API...")
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{
                    "role": "system",
                    "content": "You are a wine expert. Analyze the given wine and provide detailed information."
                }, {
                    "role": "user",
                    "content": f"Analyze this wine: {wine}"
                }],
                functions=functions,
                function_call={"name": "analyze_wine"}
            )
            
            logger.info("Received response from OpenAI API")
            logger.debug(f"Full API response: {response}")
            
            # Extract function call arguments
            function_call = response.choices[0].message.function_call
            if not function_call:
                raise ValueError("No function call in response")
                
            logger.info("Successfully extracted function call arguments")
            return function_call.arguments
            
        except Exception as e:
            logger.error(f"Error in wine analysis: {str(e)}", exc_info=True)
            raise

def create_wine_agent() -> Agent:
    """
    Creates a wine expert agent with function calling capability.
    """
    logger.info("Creating wine expert agent")
    
    # Create the wine analyzer tool
    wine_tool = WineAnalyzerTool()
    logger.info("Created wine analyzer tool")
    
    return Agent(
        role='Wine Expert',
        goal='Provide detailed wine analysis and recommendations',
        backstory="""You are an experienced sommelier with extensive knowledge of wines 
        from around the world. Your expertise helps people understand and appreciate wines better.""",
        tools=[wine_tool],
        verbose=True,
        allow_delegation=False
    )

def get_wine_analysis(wine: str) -> WineAnalysis:
    """Gets wine analysis from the AI agent."""
    logger.info(f"Getting wine analysis for: {wine}")
    
    try:
        # Create the wine analyzer tool directly
        wine_tool = WineAnalyzerTool()
        logger.info("Created wine analyzer tool")
        
        # Use the tool directly instead of going through the agent
        result = wine_tool(wine)
        logger.info(f"Raw result from wine analysis: {result}")
        
        if isinstance(result, str):
            try:
                result = json.loads(result)
                logger.info("Successfully parsed JSON result")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON: {str(e)}")
                raise
        
        logger.info(f"Validating result against WineAnalysis model")
        analysis = WineAnalysis.model_validate(result)
        logger.info("Successfully validated wine analysis")
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing wine: {str(e)}", exc_info=True)
        raise Exception(f"Error analyzing wine: {str(e)}")

def main():
    st.title("🍷 Wine Analysis Assistant")
    st.write("""
    Enter a wine name below to get a detailed analysis, including characteristics,
    food pairings, and serving recommendations.
    """)
    
    # Initialize session state for wine analysis
    if 'wine_analysis' not in st.session_state:
        st.session_state.wine_analysis = None
        logger.info("Initialized session state")

    # Wine input
    wine_input = st.text_input(
        "Enter a wine (e.g., '2018 Caymus Cabernet Sauvignon')",
        key="wine_input"
    )

    if wine_input:
        logger.info(f"Processing wine input: {wine_input}")
        try:
            with st.spinner("Analyzing wine..."):
                analysis = get_wine_analysis(wine_input)
                st.session_state.wine_analysis = analysis
                logger.info("Successfully stored wine analysis in session state")
        except Exception as e:
            logger.error(f"Error in main: {str(e)}", exc_info=True)
            st.error(f"Error analyzing wine: {str(e)}")
            return

    # Analyze button
    if st.button("Analyze Wine"):
        if wine_input:
            with st.spinner("Analyzing your wine..."):
                try:
                    analysis = get_wine_analysis(wine_input)
                    st.session_state.wine_analysis = analysis
                except Exception as e:
                    st.error(f"Error analyzing wine: {str(e)}")
                    return

    # Display results
    if st.session_state.wine_analysis:
        analysis = st.session_state.wine_analysis
        
        st.subheader("Wine Analysis")
        
        st.markdown("### 🍷 Characteristics")
        st.write(analysis.characteristics)
        
        st.markdown("### 🍽️ Food Pairing Suggestions")
        st.write(analysis.pairing_suggestions)
        
        st.markdown("### 🥂 Serving Recommendations")
        st.write(analysis.serving_recommendations)

        if st.button("Start Over"):
            st.session_state.wine_analysis = None
            st.rerun()

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Verify OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        st.error("OpenAI API key not found. Please check your .env file.")
        st.stop()
    
    main()