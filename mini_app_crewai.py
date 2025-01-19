import os
import json
from typing import List, Dict
from dotenv import load_dotenv
import streamlit as st
from pydantic import BaseModel, Field
from openai import OpenAI
import logging
import sys
from crewai import Agent, Task, Crew, Process

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

class WineAnalyzerAgent:
    """Agent for analyzing wines using CrewAI."""
    
    def __init__(self):
        self.client = OpenAI()
        self.wine_expert = Agent(
            role='Wine Expert',
            goal='Provide detailed and accurate wine analysis',
            backstory="""You are a highly knowledgeable wine expert with years of 
            experience in wine tasting, analysis, and food pairing. Your expertise 
            helps people understand and appreciate wines better.""",
            allow_delegation=False,
            verbose=True
        )
    
    def analyze_wine(self, wine: str) -> WineAnalysis:
        """Analyze wine using CrewAI agent."""
        logger.info(f"Starting wine analysis for: {wine}")
        
        try:
            schema = WineAnalysis.model_json_schema()
            
            functions = [{
                "name": "analyze_wine",
                "description": "Analyze a wine and provide structured information",
                "parameters": schema
            }]
            
            logger.info("Sending request to OpenAI API...")
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{
                    "role": "system",
                    "content": f"Role: {self.wine_expert.role}\nGoal: {self.wine_expert.goal}\nBackground: {self.wine_expert.backstory}"
                }, {
                    "role": "user",
                    "content": f"Analyze this wine: {wine}"
                }],
                functions=functions,
                function_call={"name": "analyze_wine"}
            )
            
            logger.info("Received response from OpenAI API")
            
            # Extract function call arguments
            function_call = response.choices[0].message.function_call
            if not function_call:
                raise ValueError("No function call in response")
                
            logger.info("Successfully extracted function call arguments")
            result = json.loads(function_call.arguments)
            
            # Validate the result
            analysis = WineAnalysis.model_validate(result)
            return analysis
            
        except Exception as e:
            logger.error(f"Error in wine analysis: {str(e)}", exc_info=True)
            raise

def get_wine_analysis(wine: str) -> WineAnalysis:
    """Gets wine analysis from the AI agent."""
    logger.info(f"Getting wine analysis for: {wine}")
    
    try:
        # Create the wine analyzer agent
        wine_analyzer = WineAnalyzerAgent()
        logger.info("Created wine analyzer agent")
        
        # Get the analysis result
        analysis = wine_analyzer.analyze_wine(wine)
        logger.info("Successfully got wine analysis")
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

    # Initialize session state for wine analysis if not exists
    if 'wine_analysis' not in st.session_state:
        st.session_state.wine_analysis = None

    # Add Start Over button at the top
    if st.button("Start Over"):
        logger.info("Resetting application state")
        st.session_state.wine_analysis = None
        st.session_state.wine_input = ""  # Clear the input field
        st.rerun()  # Rerun the app to reset the UI
        return

    # Wine input
    wine_input = st.text_input(
        "Enter a wine (e.g., '2018 Caymus Cabernet Sauvignon')",
        key="wine_input"
    )

    # Analyze button
    if st.button("Analyze Wine") and wine_input:
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

    # Display results if available
    if st.session_state.wine_analysis:
        analysis = st.session_state.wine_analysis
        st.subheader("Wine Analysis Results")
        
        st.markdown("### 🍷 Characteristics")
        st.write(analysis.characteristics)
        
        st.markdown("### 🍽️ Food Pairing Suggestions")
        st.write(analysis.pairing_suggestions)
        
        st.markdown("### 🥂 Serving Recommendations")
        st.write(analysis.serving_recommendations)

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Verify OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        st.error("OpenAI API key not found. Please check your .env file.")
        st.stop()
    
    main()