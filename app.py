import streamlit as st
from crewai import Agent, Task, Crew
from openai import OpenAI
from dotenv import load_dotenv
import os
import json

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize session state variables if they don't exist
if 'stage' not in st.session_state:
    st.session_state.stage = 'wine'
if 'wine' not in st.session_state:
    st.session_state.wine = None
if 'entree' not in st.session_state:
    st.session_state.entree = None
if 'appetizer' not in st.session_state:
    st.session_state.appetizer = None
if 'dessert' not in st.session_state:
    st.session_state.dessert = None

# Create the sommelier agent
sommelier = Agent(
    role='Expert Sommelier and Food Pairing Specialist',
    goal='Help create perfect food and wine pairings',
    backstory="""You are an expert sommelier with decades of experience in wine 
    and food pairing. You have a deep understanding of how flavors interact and
    complement each other.""",
    verbose=True,
    allow_delegation=True,
    tools=[],  # Add any specific tools if needed
)

# Create the chef agent
chef = Agent(
    role='Expert Chef',
    goal='Create delicious and harmonious menu combinations',
    backstory="""You are a master chef with decades of experience across multiple cuisines.
    You understand flavor profiles, cooking techniques, seasonal ingredients, and how to
    create balanced, memorable meals. You excel at designing cohesive menus that tell
    a story through food.""",
    verbose=True,
    allow_delegation=True,
    tools=[],  # Add any specific tools if needed
)

def parse_suggestions(result):
    """Parse the LLM response into structured data for menu suggestions."""
    try:
        # The LLM might include additional text before/after the JSON
        # Find the JSON array between square brackets
        start = result.find('[')
        end = result.rfind(']') + 1
        if start == -1 or end == 0:
            raise ValueError("No JSON array found in response")
        json_str = result[start:end]
        return json.loads(json_str)
    except Exception as e:
        st.error(f"Failed to parse suggestions: {str(e)}")
        return None

def parse_analysis(result):
    """Parse the LLM response into structured data for final analysis."""
    try:
        # Find the JSON object between curly braces
        start = result.find('{')
        end = result.rfind('}') + 1
        if start == -1 or end == 0:
            raise ValueError("No JSON object found in response")
        json_str = result[start:end]
        return json.loads(json_str)
    except Exception as e:
        st.error(f"Failed to parse analysis: {str(e)}")
        return None

def get_crew_response(task, response_type='suggestions'):
    """Get response from crew with appropriate parsing."""
    try:
        # Create crew with both agents
        crew = Crew(
            agents=[sommelier, chef],
            tasks=[task]
        )
        
        # Enable agent discussions for menu planning
        result = crew.kickoff()
        
        if response_type == 'suggestions':
            parsed = parse_suggestions(result)
        else:
            parsed = parse_analysis(result)
            
        if not parsed:
            st.error("Failed to get valid response. Please try again.")
            return None
        return parsed
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        return None

# Title and description
st.title("🍷 Dinner Party Menu Planner")
st.write("Let's plan your perfect dinner party menu based on your wine selection!")

# Main application flow
if st.session_state.stage == 'wine':
    st.header("🍷 Wine Selection")
    wine_input = st.text_input("What type of wine would you like to plan your dinner around?")
    
    if wine_input and st.button("Get Entree Suggestions"):
        with st.spinner('Getting entree suggestions...'):
            st.session_state.wine = wine_input
            
            # Create tasks for both agents
            sommelier_task = Task(
                description=f"""Analyze {wine_input} and provide its key characteristics and flavor profile.
                Consider body, tannins, acidity, and primary flavors.""",
                agent=sommelier
            )
            
            chef_task = Task(
                description=f"""Based on the sommelier's analysis, suggest three dinner entrees that would create
                perfect pairings. Consider cooking techniques that enhance the pairing.
                Return the response as a JSON array of objects with 'name' and 'description' fields.
                Example format: [
                    {{"name": "Grilled Ribeye Steak", 
                      "description": "Pan-seared to develop a caramelized crust, complementing the wine's structure"}},
                    {{"name": "Braised Lamb Shanks", 
                      "description": "Slow-cooked with herbs to match the wine's complexity"}},
                    {{"name": "Duck Breast", 
                      "description": "Crispy skin and medium-rare meat to balance the wine's characteristics"}}
                ]""",
                agent=chef
            )
            
            # Create crew with sequential tasks
            crew = Crew(
                agents=[sommelier, chef],
                tasks=[sommelier_task, chef_task]
            )
            
            result = crew.kickoff()
            if result:
                st.session_state.entree_suggestions = parse_suggestions(result)
                st.session_state.stage = 'entree'
                st.rerun()

elif st.session_state.stage == 'entree':
    st.header("🍖 Entree Selection")
    st.write(f"Selected Wine: {st.session_state.wine}")
    st.write("Choose your entree from these suggestions:")
    
    # Display suggestions in a more structured way
    for i, suggestion in enumerate(st.session_state.entree_suggestions, 1):
        st.write(f"{i}. {suggestion['name']} - {suggestion['description']}")
    
    # Create a dropdown with just the dish names
    options = {s['name']: s for s in st.session_state.entree_suggestions}
    selected_name = st.selectbox("Select your entree:", list(options.keys()))
    selected_item = options[selected_name] if selected_name else None
    
    if selected_item and st.button("Get Appetizer Suggestions"):
        with st.spinner('Getting appetizer suggestions...'):
            st.session_state.entree = selected_item
            
            # Create tasks for appetizer suggestions
            sommelier_task = Task(
                description=f"""Analyze how the appetizer should complement both {st.session_state.wine} 
                and {selected_item['name']}. Consider progression of flavors through the meal.""",
                agent=sommelier
            )
            
            chef_task = Task(
                description=f"""Based on the sommelier's analysis, suggest three appetizers that create
                a harmonious progression to {selected_item['name']}.
                Return the response as a JSON array of objects with 'name' and 'description' fields.
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
            
            # Create crew with sequential tasks
            crew = Crew(
                agents=[sommelier, chef],
                tasks=[sommelier_task, chef_task]
            )
            
            result = crew.kickoff()
            if result:
                st.session_state.appetizer_suggestions = parse_suggestions(result)
                st.session_state.stage = 'appetizer'
                st.rerun()

elif st.session_state.stage == 'appetizer':
    st.header("🥗 Appetizer Selection")
    st.write(f"Selected Wine: {st.session_state.wine}")
    st.write(f"Selected Entree: {st.session_state.entree['name']}")
    st.write("Choose your appetizer from these suggestions:")
    
    # Display suggestions in a more structured way
    for i, suggestion in enumerate(st.session_state.appetizer_suggestions, 1):
        st.write(f"{i}. {suggestion['name']} - {suggestion['description']}")
    
    # Create a dropdown with just the dish names
    options = {s['name']: s for s in st.session_state.appetizer_suggestions}
    selected_name = st.selectbox("Select your appetizer:", list(options.keys()))
    selected_item = options[selected_name] if selected_name else None
    
    if selected_item and st.button("Get Dessert Suggestions"):
        with st.spinner('Getting dessert suggestions...'):
            st.session_state.appetizer = selected_item
            
            # Create tasks for dessert suggestions
            sommelier_task = Task(
                description=f"""Analyze how the dessert should complement both {st.session_state.wine} 
                and {st.session_state.entree['name']}. Consider progression of flavors through the meal.""",
                agent=sommelier
            )
            
            chef_task = Task(
                description=f"""Based on the sommelier's analysis, suggest three desserts that create
                a harmonious progression to {st.session_state.entree['name']}.
                Return the response as a JSON array of objects with 'name' and 'description' fields.
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
            
            # Create crew with sequential tasks
            crew = Crew(
                agents=[sommelier, chef],
                tasks=[sommelier_task, chef_task]
            )
            
            result = crew.kickoff()
            if result:
                st.session_state.dessert_suggestions = parse_suggestions(result)
                st.session_state.stage = 'dessert'
                st.rerun()

elif st.session_state.stage == 'dessert':
    st.header("🍰 Dessert Selection")
    st.write(f"Selected Wine: {st.session_state.wine}")
    st.write(f"Selected Entree: {st.session_state.entree['name']}")
    st.write(f"Selected Appetizer: {st.session_state.appetizer['name']}")
    st.write("Choose your dessert from these suggestions:")
    
    # Display suggestions in a more structured way
    for i, suggestion in enumerate(st.session_state.dessert_suggestions, 1):
        st.write(f"{i}. {suggestion['name']} - {suggestion['description']}")
    
    # Create a dropdown with just the dish names
    options = {s['name']: s for s in st.session_state.dessert_suggestions}
    selected_name = st.selectbox("Select your dessert:", list(options.keys()))
    selected_item = options[selected_name] if selected_name else None
    
    if selected_item and st.button("Get Final Menu Analysis"):
        with st.spinner('Analyzing menu...'):
            st.session_state.dessert = selected_item
            task = Task(
                description=f"""Analyze how the following menu components will interact together and return ONLY a JSON object with NO additional text:
                Wine: {st.session_state.wine}
                Appetizer: {st.session_state.appetizer['name']} ({st.session_state.appetizer['description']})
                Entree: {st.session_state.entree['name']} ({st.session_state.entree['description']})
                Dessert: {selected_item['name']} ({selected_item['description']})
                
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
            result = get_crew_response(task, response_type='analysis')
            if result:
                st.session_state.final_analysis = result
                st.session_state.stage = 'final'
                st.rerun()

elif st.session_state.stage == 'final':
    try:
        st.header("🎉 Your Perfect Menu")
        
        # Create a styled menu display using columns
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
        
        # Display the analysis in a structured way
        st.subheader("🍷 Wine Pairing")
        st.write(analysis['wine_pairing'])
        
        st.subheader("👉 Flavor Progression")
        st.write(analysis['flavor_progression'])
        
        st.subheader("✨ Highlights")
        st.write(analysis['highlights'])
        
        st.subheader("🎯 Overall Harmony")
        st.write(analysis['overall_harmony'])
    except Exception as e:
        st.error(f"Error displaying analysis: {str(e)}")
        st.error("Please try generating the analysis again.")
    
    if st.button("🔄 Start Over"):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()

# Add a footer with helpful information
st.markdown("---")
st.markdown("*Need help? Contact our support team or check our [documentation](https://docs.example.com)*")