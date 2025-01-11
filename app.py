import streamlit as st
from crewai import Agent, Task, Crew
from openai import OpenAI
from dotenv import load_dotenv
import os
import json
from enum import Enum
from typing import List, Dict, Optional, Any, Union

# Constants and Configuration
class Stage(str, Enum):
    WINE = 'wine'
    ENTREE = 'entree'
    APPETIZER = 'appetizer'
    DESSERT = 'dessert'
    FINAL = 'final'

# Initialize environment and OpenAI client
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Agent Definitions
def create_sommelier_agent() -> Agent:
    """Create and return the sommelier agent."""
    return Agent(
        role='Expert Sommelier and Food Pairing Specialist',
        goal='Help create perfect food and wine pairings',
        backstory="""You are an expert sommelier with decades of experience in wine 
        and food pairing. You have a deep understanding of how flavors interact and
        complement each other.""",
        verbose=True,
        allow_delegation=True,
    )

def create_chef_agent() -> Agent:
    """Create and return the chef agent."""
    return Agent(
        role='Expert Chef',
        goal='Create delicious and harmonious menu combinations',
        backstory="""You are a master chef with decades of experience across multiple cuisines.
        You understand flavor profiles, cooking techniques, seasonal ingredients, and how to
        create balanced, memorable meals. You excel at designing cohesive menus that tell
        a story through food.""",
        verbose=True,
        allow_delegation=True,
    )

# Helper Functions
def initialize_session_state():
    """Initialize all session state variables."""
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
    """Validate that a suggestion dictionary has the required fields."""
    return isinstance(suggestion, dict) and 'name' in suggestion and 'description' in suggestion

def validate_suggestions(suggestions: Any) -> tuple[bool, Optional[str]]:
    """Validate the suggestions data structure.
    
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
    """Extract JSON array or object from a response string.
    
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
    """Parse and validate the crew's response.
    
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
            return parsed
            
        is_valid, error_msg = validate_suggestions(parsed)
        if not is_valid:
            st.error(error_msg)
            st.error("Raw JSON: " + json_str[:200] + "...")
            return None
            
        return parsed
        
    except json.JSONDecodeError as e:
        st.error(f"Failed to parse JSON: {str(e)}")
        st.error("Problematic JSON string: " + json_str[:200] + "...")
        return None

def create_crew_tasks(stage: Stage, **kwargs) -> List[Task]:
    """Create tasks for the current stage."""
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

def get_crew_suggestions(stage: Stage, **kwargs) -> Optional[List[Dict]]:
    """Get suggestions from the crew for the current stage."""
    tasks = create_crew_tasks(stage, **kwargs)
    if not tasks:
        return None
        
    try:
        crew = Crew(
            agents=[create_sommelier_agent(), create_chef_agent()],
            tasks=tasks
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
    """Handle the wine selection stage."""
    st.header("🍷 Wine Selection")
    wine_input = st.text_input("What type of wine would you like to plan your dinner around?")
    
    if wine_input and st.button("Get Entree Suggestions"):
        with st.spinner('Getting entree suggestions...'):
            st.session_state.wine = wine_input
            suggestions = get_crew_suggestions(Stage.WINE, wine=wine_input)
            if suggestions:
                st.session_state.entree_suggestions = suggestions
                st.session_state.stage = Stage.ENTREE
                st.rerun()

def handle_entree_stage():
    """Handle the entree selection stage."""
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
            suggestions = get_crew_suggestions(
                Stage.ENTREE,
                wine=st.session_state.wine,
                entree=selected_item['name']
            )
            if suggestions:
                st.session_state.appetizer_suggestions = suggestions
                st.session_state.stage = Stage.APPETIZER
                st.rerun()

def handle_appetizer_stage():
    """Handle the appetizer selection stage."""
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
            suggestions = get_crew_suggestions(
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
    """Handle the dessert selection stage."""
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
    
    if selected_item and st.button("Get Final Menu Analysis"):
        with st.spinner('Analyzing menu...'):
            st.session_state.dessert = selected_item
            analysis = get_crew_suggestions(
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
    """Handle the final menu analysis stage."""
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
    """Main application entry point."""
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