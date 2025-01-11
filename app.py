"""
Dinner Party Planner Application

This application helps users plan a dinner party by providing expert recommendations
for wine and food pairings. It uses AI agents (Sommelier and Chef) to create a
harmonious dining experience.

The planning process follows these stages:
1. Wine Selection: Get wine characteristics and pairing suggestions
2. Entree Selection: Choose a main course that pairs well with the wine
3. Appetizer Selection: Select starters that complement both wine and entree
4. Dessert & Analysis: Complete the menu and get a final harmony analysis

Key Components:
- Stage: Enum tracking the current planning stage
- Agents: Sommelier and Chef providing expert recommendations
- CrewAI: Orchestrates the collaboration between agents
- Streamlit: Handles the web interface and user interactions

Environment Variables:
    OPENAI_API_KEY: Required for AI agent functionality
"""

import os
# Suppress CrewAI's OpenTelemetry warning
os.environ["OTEL_PYTHON_DISABLED"] = "true"

import streamlit as st
from crewai import Agent, Task, Crew
from openai import OpenAI
from dotenv import load_dotenv
import json
from enum import Enum
from typing import List, Dict, Optional, Any, Union

# Constants and Configuration
class Stage(str, Enum):
    """
    Tracks the current stage of dinner party planning.
    
    The stages must be completed in sequence:
    WINE -> ENTREE -> APPETIZER -> DESSERT
    
    Each stage builds upon the selections made in previous stages to ensure
    a cohesive dining experience.
    """
    WINE = 'wine'
    ENTREE = 'entree'
    APPETIZER = 'appetizer'
    DESSERT = 'dessert'
    FINAL = 'final'

# OpenAI Configuration
MODEL = "gpt-3.5-turbo"  # Faster than GPT-4
TEMPERATURE = 0.7  # Lower temperature for more focused responses

# Initialize environment and OpenAI client
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Agent Definitions
def create_sommelier_agent() -> Agent:
    """
    Creates a Sommelier AI agent specialized in wine expertise.
    
    The Sommelier agent provides:
    - Wine characteristics and flavor profiles
    - Food pairing suggestions
    - Professional wine knowledge and recommendations
    
    Returns:
        Agent: Configured Sommelier agent with wine expertise
    """
    return Agent(
        role='Expert Sommelier and Food Pairing Specialist',
        goal='Help create perfect food and wine pairings',
        backstory="""You are a renowned sommelier with decades of experience in wine
        and food pairing. You have an encyclopedic knowledge of wines and their characteristics.""",
        allow_delegation=True,  # Enable collaboration with Chef
        verbose=True,  # Enable detailed logging
        llm_model=MODEL,
        temperature=TEMPERATURE
    )

def create_chef_agent() -> Agent:
    """
    Creates a Chef AI agent specialized in culinary expertise.
    
    The Chef agent provides:
    - Menu suggestions based on wine selection
    - Flavor combinations and progression
    - Professional culinary knowledge and techniques
    
    Returns:
        Agent: Configured Chef agent with culinary expertise
    """
    return Agent(
        role='Expert Chef',
        goal='Create delicious and harmonious menu combinations',
        backstory="""You are an experienced chef with deep knowledge of flavors,
        cooking techniques, and food pairings. You excel at creating cohesive menus.""",
        allow_delegation=True,  # Enable collaboration with Sommelier
        verbose=True,  # Enable detailed logging
        llm_model=MODEL,
        temperature=TEMPERATURE
    )

# Helper Functions
def initialize_session_state():
    """
    Initializes all session state variables.
    
    This function ensures that all required session state variables are set before
    the application starts.
    """
    if 'stage' not in st.session_state:
        st.session_state.stage = Stage.WINE
    if 'wine' not in st.session_state:
        st.session_state.wine = None
    if 'entree' not in st.session_state:
        st.session_state.entree = None
    if 'appetizer' not in st.session_state:
        st.session_state.appetizer = None
    if 'dessert' not in st.session_state:
        st.session_state.dessert = None

def validate_suggestion_format(suggestion: Dict) -> bool:
    """
    Validates that a suggestion dictionary has the required fields.
    
    Args:
        suggestion: Dictionary containing the suggestion data
    
    Returns:
        bool: True if the suggestion is valid, False otherwise
    """
    return isinstance(suggestion, dict) and 'name' in suggestion and 'description' in suggestion

def validate_suggestions(suggestions: Any) -> tuple[bool, Optional[str]]:
    """
    Validates the suggestions data structure.
    
    Args:
        suggestions: Suggestions data structure
    
    Returns:
        tuple: (is_valid: bool, error_message: Optional[str])
    """
    if not isinstance(suggestions, list):
        return False, f"Invalid suggestions format - not a list. Got: {type(suggestions)}"
        
    if not suggestions:
        return False, "Empty suggestions list"
        
    if not all(isinstance(s, dict) for s in suggestions):
        return False, "Invalid suggestions format - not a list of dictionaries"
        
    if not all(validate_suggestion_format(s) for s in suggestions):
        return False, "Invalid suggestions format - missing required fields"
        
    return True, None

def extract_json_from_response(response: str) -> Optional[str]:
    """
    Extracts JSON array or object from a response string.
    
    Args:
        response: The raw response string
    
    Returns:
        Optional[str]: The JSON string if found, None otherwise
    """
    # For array responses
    array_start = response.find('[')
    array_end = response.rfind(']') + 1
    if array_start != -1 and array_end > array_start:
        return response[array_start:array_end]
        
    # For object responses (used in final analysis)
    obj_start = response.find('{')
    obj_end = response.rfind('}') + 1
    if obj_start != -1 and obj_end > obj_start:
        return response[obj_start:obj_end]
        
    return None

def parse_crew_response(response: str, expect_analysis: bool = False) -> Optional[Union[List[Dict], Dict]]:
    """
    Parses and validates the crew's response.
    
    Args:
        response: Raw response string from the crew
        expect_analysis: If True, expect a single JSON object instead of an array
    
    Returns:
        Optional[Union[List[Dict], Dict]]: Parsed and validated response
    """
    json_str = extract_json_from_response(response)
    if not json_str:
        st.error("Failed to find JSON in response. Response: " + response[:200] + "...")
        return None
        
    try:
        parsed = json.loads(json_str)
        
        if expect_analysis:
            if not isinstance(parsed, dict):
                st.error("Expected analysis object but got: " + str(type(parsed)))
                return None
            return parsed # return parsed analysis
            
        is_valid, error_msg = validate_suggestions(parsed)
        if not is_valid:
            st.error(error_msg)
            st.error("Raw JSON: " + json_str[:200] + "...")
            return None
            
        return parsed # return parsed suggestions
        
    except json.JSONDecodeError as e:
        st.error(f"Failed to parse JSON: {str(e)}")
        st.error("Problematic JSON string: " + json_str[:200] + "...")
        return None

def create_crew_tasks(stage: Stage, **kwargs) -> List[Task]:
    """
    Creates tasks for the AI crew based on the current planning stage.
    
    Each stage requires different expertise and considerations:
    - WINE: Initial wine analysis
    - ENTREE: Main course suggestions based on wine
    - APPETIZER: Starter suggestions complementing wine and entree
    - DESSERT: Dessert suggestions and final menu analysis
    
    Args:
        stage: Current stage of dinner planning
        **kwargs: Stage-specific parameters
            - wine: str - Selected wine (required for all stages)
            - entree: str - Selected entree (required for appetizer/dessert)
            - appetizer: str - Selected appetizer (required for dessert)
    
    Returns:
        List[Task]: Tasks for the AI crew to execute
    """
    sommelier = create_sommelier_agent()
    chef = create_chef_agent()
    
    if stage == Stage.WINE:
        return [
            Task(
                description=f"""Analyze {kwargs['wine']} and provide its key characteristics and flavor profile.
                Consider body, tannins, acidity, and primary flavors.
                Format your response as a JSON string containing an array of wine characteristics.""",
                agent=sommelier
            ),
            Task(
                description=f"""Based on the wine analysis, suggest three dinner entrees.
                You MUST format your response as a JSON array of objects with 'name' and 'description' fields.
                Do not include any other text before or after the JSON array.
                Example:
                [
                    {{"name": "Grilled Ribeye Steak", 
                      "description": "Pan-seared to develop a caramelized crust, complementing the wine's structure"}},
                    {{"name": "Braised Lamb Shanks", 
                      "description": "Slow-cooked with herbs to match the wine's complexity"}},
                    {{"name": "Duck Breast", 
                      "description": "Crispy skin and medium-rare meat to balance the wine's characteristics"}}
                ]""",
                agent=chef
            )
        ]
    elif stage == Stage.ENTREE:
        return [
            Task(
                description=f"""Analyze how the appetizer should complement both {kwargs['wine']} 
                and {kwargs['entree']}. Consider progression of flavors through the meal.""",
                agent=sommelier
            ),
            Task(
                description=f"""Based on the sommelier's analysis, suggest three appetizers that create
                a harmonious progression to {kwargs['entree']}.
                You MUST format your response as a JSON array of objects with 'name' and 'description' fields.
                Do not include any other text before or after the JSON array.
                Example format: [
                    {{"name": "Seared Scallops", 
                      "description": "Light and delicate start that prepares the palate"}},
                    {{"name": "Wild Mushroom Crostini", 
                      "description": "Earthy flavors that bridge to the main course"}},
                    {{"name": "Citrus-Cured Salmon", 
                      "description": "Fresh flavors that contrast and complement"}}
                ]""",
                agent=chef
            )
        ]
    elif stage == Stage.APPETIZER:
        return [
            Task(
                description=f"""Analyze how the dessert should complement both {kwargs['wine']} 
                and {kwargs['entree']}. Consider progression of flavors through the meal.""",
                agent=sommelier
            ),
            Task(
                description=f"""Based on the sommelier's analysis, suggest three desserts that create
                a harmonious progression to {kwargs['entree']}.
                You MUST format your response as a JSON array of objects with 'name' and 'description' fields.
                Do not include any other text before or after the JSON array.
                Example format: [
                    {{"name": "Dark Chocolate Truffles", 
                      "description": "Rich chocolate complements the wine"}},
                    {{"name": "Berry Tart", 
                      "description": "Fresh fruits balance the meal"}},
                    {{"name": "Creme Brulee", 
                      "description": "Creamy dessert cleanses the palate"}}
                ]""",
                agent=chef
            )
        ]
    elif stage == Stage.DESSERT:
        return [
            Task(
                description=f"""Analyze how the following menu components will interact together and return ONLY a JSON object with NO additional text:
                Wine: {kwargs['wine']}
                Appetizer: {kwargs['appetizer']} ({kwargs['appetizer_description']})
                Entree: {kwargs['entree']} ({kwargs['entree_description']})
                Dessert: {kwargs['dessert']} ({kwargs['dessert_description']})
                
                The response must be a valid JSON object with exactly this structure:
                {{
                    "wine_pairing": "Detailed analysis of how the wine pairs with each course",
                    "flavor_progression": "How flavors develop from appetizer through dessert",
                    "highlights": "Notable flavor combinations and interactions",
                    "overall_harmony": "Assessment of the menu's overall balance"
                }}
                
                Do not include any text before or after the JSON object.""",
                agent=sommelier
            )
        ]
    return []

@st.cache_data(ttl=3600, show_spinner=False)  # Cache responses for 1 hour, hide the spinner
def get_cached_suggestions(stage: Stage, **kwargs) -> Optional[List[Dict]]:
    """
    Cached version of get_crew_suggestions to improve response time.
    
    Args:
        stage: Current stage of dinner planning
        **kwargs: Stage-specific parameters
        
    Returns:
        Optional[List[Dict]]: Cached suggestions from the crew
    """
    # Convert kwargs to a string for hashing
    kwargs_str = json.dumps(kwargs, sort_keys=True)
    return get_crew_suggestions(stage, **kwargs)

def get_crew_suggestions(stage: Stage, **kwargs) -> Optional[List[Dict]]:
    """
    Gets suggestions (e.g., entree, appetizer, dessert) from the crew for the current stage.
    
    Args:
        stage: Current stage of dinner planning
        **kwargs: Stage-specific parameters
    
    Returns:
        Optional[List[Dict]]: Suggestions from the crew
    """
    tasks = create_crew_tasks(stage, **kwargs)
    if not tasks:
        return None
        
    try:
        crew = Crew(
            agents=[create_sommelier_agent(), create_chef_agent()],
            tasks=tasks,
            verbose=True,  # Enable detailed logging
            process_timeout=300  # 5 minute timeout
        )
        result = crew.kickoff()
        
        return parse_crew_response(
            response=result,
            expect_analysis=(stage == Stage.DESSERT)
        )
        
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.error("Full response: " + result[:200] + "...")
        return None

# Stage-specific Functions
def handle_wine_stage():
    """
    Handles the wine selection stage.
    
    This function is responsible for:
    1. Displaying the wine selection interface
    2. Getting wine suggestions from the crew
    3. Updating the session state with the selected wine
    
    Stage Progression:
    - When user enters a wine and clicks "Get Entree Suggestions":
        1. Saves the selected wine to session state
        2. Fetches entree suggestions based on wine characteristics
        3. Updates session state with new suggestions
        4. Advances to ENTREE stage
    """
    st.header("🍷 Wine Selection")
    wine_input = st.text_input("What type of wine would you like to plan your dinner around?")
    
    if wine_input and st.button("Get Entree Suggestions"):
        with st.spinner('Getting entree suggestions...'):
            st.session_state.wine = wine_input
            suggestions = get_cached_suggestions(Stage.WINE, wine=wine_input)
            if suggestions:
                st.session_state.entree_suggestions = suggestions
                st.session_state.stage = Stage.ENTREE
                st.rerun()

def handle_entree_stage():
    """
    Handles the entree selection stage.
    
    This function is responsible for:
    1. Displaying the entree selection interface
    2. Getting entree suggestions from the crew
    3. Updating the session state with the selected entree
    
    Stage Progression:
    - When user selects an entree and clicks "Get Appetizer Suggestions":
        1. Saves the selected entree to session state
        2. Fetches appetizer suggestions based on wine and entree pairing
        3. Updates session state with new suggestions
        4. Advances to APPETIZER stage
    """
    st.header("🍖 Entree Selection")
    st.write(f"Selected Wine: {st.session_state.wine}")
    st.write("Choose your entree from these suggestions:")
    
    for i, suggestion in enumerate(st.session_state.entree_suggestions, 1):
        st.write(f"{i}. {suggestion['name']} - {suggestion['description']}")
    
    options = {s['name']: s for s in st.session_state.entree_suggestions}
    selected_name = st.selectbox("Select your entree:", list(options.keys()))
    selected_item = options[selected_name] if selected_name else None
    
    if selected_item and st.button("Get Appetizer Suggestions"):
        with st.spinner('Getting appetizer suggestions...'):
            st.session_state.entree = selected_item
            suggestions = get_cached_suggestions(
                Stage.ENTREE,
                wine=st.session_state.wine,
                entree=selected_item['name']
            )
            if suggestions:
                st.session_state.appetizer_suggestions = suggestions
                st.session_state.stage = Stage.APPETIZER
                st.rerun()

def handle_appetizer_stage():
    """
    Handles the appetizer selection stage.
    
    This function is responsible for:
    1. Displaying the appetizer selection interface
    2. Getting appetizer suggestions from the crew
    3. Updating the session state with the selected appetizer
    
    Stage Progression:
    - When user selects an appetizer and clicks "Get Dessert Suggestions":
        1. Saves the selected appetizer to session state
        2. Fetches dessert suggestions based on wine, entree, and appetizer
        3. Updates session state with new suggestions
        4. Advances to DESSERT stage
    """
    st.header("🥗 Appetizer Selection")
    st.write(f"Selected Wine: {st.session_state.wine}")
    st.write(f"Selected Entree: {st.session_state.entree['name']}")
    st.write("Choose your appetizer from these suggestions:")
    
    for i, suggestion in enumerate(st.session_state.appetizer_suggestions, 1):
        st.write(f"{i}. {suggestion['name']} - {suggestion['description']}")
    
    options = {s['name']: s for s in st.session_state.appetizer_suggestions}
    selected_name = st.selectbox("Select your appetizer:", list(options.keys()))
    selected_item = options[selected_name] if selected_name else None
    
    if selected_item and st.button("Get Dessert Suggestions"):
        with st.spinner('Getting dessert suggestions...'):
            st.session_state.appetizer = selected_item
            suggestions = get_cached_suggestions(
                Stage.APPETIZER,
                wine=st.session_state.wine,
                entree=st.session_state.entree['name'],
                appetizer=selected_item['name']
            )
            if suggestions:
                st.session_state.dessert_suggestions = suggestions
                st.session_state.stage = Stage.DESSERT
                st.rerun()

def handle_dessert_stage():
    """
    Handles the dessert selection stage.
    
    This function is responsible for:
    1. Displaying the dessert selection interface
    2. Getting dessert suggestions from the crew
    3. Updating the session state with the selected dessert
    
    Stage Progression:
    - When user selects a dessert and clicks "See Final Analysis":
        1. Saves the selected dessert to session state
        2. Fetches final menu analysis considering all selections
        3. Updates session state with the analysis
        4. Advances to final stage for complete menu review
    """
    st.header("🍰 Dessert Selection")
    st.write(f"Selected Wine: {st.session_state.wine}")
    st.write(f"Selected Entree: {st.session_state.entree['name']}")
    st.write(f"Selected Appetizer: {st.session_state.appetizer['name']}")
    st.write("Choose your dessert from these suggestions:")
    
    for i, suggestion in enumerate(st.session_state.dessert_suggestions, 1):
        st.write(f"{i}. {suggestion['name']} - {suggestion['description']}")
    
    options = {s['name']: s for s in st.session_state.dessert_suggestions}
    selected_name = st.selectbox("Select your dessert:", list(options.keys()))
    selected_item = options[selected_name] if selected_name else None
    
    if selected_item and st.button("See Final Menu Analysis"):
        with st.spinner('Analyzing menu...'):
            st.session_state.dessert = selected_item
            analysis = get_cached_suggestions(
                Stage.DESSERT,
                wine=st.session_state.wine,
                entree=st.session_state.entree['name'],
                entree_description=st.session_state.entree['description'],
                appetizer=st.session_state.appetizer['name'],
                appetizer_description=st.session_state.appetizer['description'],
                dessert=selected_item['name'],
                dessert_description=selected_item['description']
            )
            if analysis:
                st.session_state.final_analysis = analysis
                st.session_state.stage = Stage.FINAL
                st.rerun()

def handle_final_stage():
    """
    Handles the final menu analysis stage.
    
    This function is responsible for:
    - Displaying the final menu analysis
    - Providing a summary of the selected menu
    """
    st.header("🎉 Your Perfect Menu")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Menu Items")
        st.markdown(f"""
        * 🍷 **Wine:** {st.session_state.wine}
        * 🥗 **Appetizer:** {st.session_state.appetizer['name']}
        * 🍖 **Entree:** {st.session_state.entree['name']}
        * 🍰 **Dessert:** {st.session_state.dessert['name']}
        """)
    
    with col2:
        st.subheader("Suggested Serving Order")
        st.markdown("""
        1. Begin with the appetizer
        2. Pour the wine
        3. Serve the main entree
        4. Finish with dessert
        """)
    
    st.header("💭 Menu Analysis")
    analysis = st.session_state.final_analysis
    
    st.subheader("🍷 Wine Pairing")
    st.write(analysis['wine_pairing'])
    
    st.subheader("👉 Flavor Progression")
    st.write(analysis['flavor_progression'])
    
    st.subheader("✨ Highlights")
    st.write(analysis['highlights'])
    
    st.subheader("🎯 Overall Harmony")
    st.write(analysis['overall_harmony'])
    
    if st.button("🔄 Start Over"):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()

def main():
    """
    Main application entry point.
    
    This function initializes the session state and handles the current stage.
    """
    initialize_session_state()
    
    st.title("🍷 Dinner Party Menu Planner")
    st.write("Let's plan your perfect dinner party menu based on your wine selection!")
    
    # Handle current stage
    if st.session_state.stage == Stage.WINE:
        handle_wine_stage()
    elif st.session_state.stage == Stage.ENTREE:
        handle_entree_stage()
    elif st.session_state.stage == Stage.APPETIZER:
        handle_appetizer_stage()
    elif st.session_state.stage == Stage.DESSERT:
        handle_dessert_stage()
    elif st.session_state.stage == Stage.FINAL:
        handle_final_stage()

if __name__ == "__main__":
    main()