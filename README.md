# 🍷 Dinner Party Planner

An AI-powered application that helps you plan the perfect dinner party by providing expert wine and food pairing recommendations. The app uses AI agents (a Sommelier and a Chef) to create a harmonious dining experience from wine selection through dessert.

## 🌟 Features

- **Wine Selection**: Get expert analysis of your chosen wine's characteristics
- **Entree Pairing**: Receive suggestions for main courses that complement your wine
- **Appetizer Selection**: Get recommendations for starters that create a perfect progression
- **Dessert Pairing**: Complete your menu with dessert suggestions that harmonize with previous courses
- **Menu Analysis**: Get a professional analysis of your complete menu's flavor progression

## 🛠 Tech Stack

- **Python 3.12+**: Core programming language
- **Streamlit**: Web application framework for the user interface
- **CrewAI**: Framework for orchestrating multiple AI agents
- **OpenAI API**: Powers the AI agents' expertise
- **python-dotenv**: Environment variable management

## 📋 Prerequisites

- Python 3.12 or higher
- OpenAI API key
- uv (Python package installer)

## 🚀 Getting Started

1. **Clone the repository**
   ```bash
   git clone https://github.com/nicholas-gates/dinner-party-planner.git
   cd dinner-party-planner
   ```

2. **Set up a virtual environment and install dependencies**
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows, use: .venv\Scripts\activate
   uv pip sync
   ```

3. **Configure environment variables**
   - Create a `.env` file in the project root
   - Add your OpenAI API key:
     ```
     OPENAI_API_KEY=your_api_key_here
     ```

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

## 🎯 How It Works

1. **Wine Selection**
   - Enter your preferred wine
   - Get analysis of the wine's characteristics
   - Receive initial pairing suggestions

2. **Entree Selection**
   - Choose from AI-suggested main courses
   - Each suggestion is tailored to complement your wine

3. **Appetizer Selection**
   - Select from starters that create a progression
   - Suggestions consider both wine and entree choices

4. **Dessert Selection**
   - Complete your menu with a harmonious dessert
   - Get a final analysis of the complete menu

## 🤖 AI Agents

### Sommelier Agent
- Provides wine analysis
- Suggests food pairings
- Ensures wine and food harmony

### Chef Agent
- Creates menu suggestions
- Considers flavor combinations
- Designs cohesive menu progression

## 📝 Notes

- The application requires an active internet connection for AI agent functionality
- OpenAI API usage may incur charges based on your account plan
- Response times may vary based on API load and complexity of suggestions

## 🔒 Security

- Never commit your `.env` file or expose your API keys
- The application uses environment variables for sensitive data
- Always use a virtual environment to manage dependencies

## Configuration

### Environment Variables

Create a `.env` file in the root directory with the following variables:

```env
# OpenAI API Key for GPT models
OPENAI_API_KEY=your_api_key_here

# Authentication Configuration
AUTHORIZED_EMAILS=email1@domain.com,email2@domain.com
AUTHORIZED_DOMAINS=company1.com,company2.com
```

- `OPENAI_API_KEY`: Your OpenAI API key for accessing GPT models
- `AUTHORIZED_EMAILS`: Comma-separated list of email addresses that can access the app
- `AUTHORIZED_DOMAINS`: Comma-separated list of email domains that can access the app (use "none" if not using domain-based auth)

### Authentication

The app uses Streamlit's built-in authentication system when deployed to Streamlit Cloud. Authentication behavior:

- **Local Development**: 
  - Authentication is bypassed
  - A warning message appears in the sidebar
  - All features are accessible

- **Deployed (Streamlit Cloud)**:
  - Users must log in via Streamlit's authentication
  - Access is restricted to authorized emails/domains specified in `.env`
  - Unauthorized users will see an error message

To enable authentication when deploying:
1. Deploy to Streamlit Cloud
2. Go to your app's settings
3. Under "Security & Privacy"
4. Enable "Require users to authenticate"

## 🛠 mini_app_no_crewai.py Overview

The `mini_app_no_crewai.py` is a streamlined version of the Dinner Party Planner application that focuses solely on wine analysis without the complexity of orchestrating multiple AI agents. This version utilizes the OpenAI API to provide detailed wine analysis based on user input.

### 🌟 Application Flow

1. **User Input**:
   - The user enters the name of a wine they wish to analyze.
   - The input is captured using Streamlit's text input widget.

2. **Wine Analysis**:
   - Upon clicking the "Analyze Wine" button, the app creates an instance of the [WineAnalyzerTool](cci:2://file:///Users/ngates/Code/python/dinner-party-planner/mini_app.py:46:0-98:17).
   - This tool is responsible for interacting with the OpenAI API to fetch wine analysis.

3. **OpenAI API Interaction**:
   - The [WineAnalyzerTool](cci:2://file:///Users/ngates/Code/python/dinner-party-planner/mini_app.py:46:0-98:17) sends a request to the OpenAI API, utilizing the function calling feature to analyze the wine.
   - The request includes predefined schemas that specify the expected output format, including characteristics, pairing suggestions, and serving recommendations.

4. **Response Handling**:
   - The app receives a structured response from the OpenAI API, which includes the analysis results.
   - The response is parsed, and validation is performed to ensure all required fields are present.

5. **Display Results**:
   - The analyzed results are displayed to the user in a structured format, including:
     - Characteristics of the wine
     - Suggested food pairings
     - Serving recommendations
   - The user can also click the "Start Over" button to reset the application state.

### 🛠 Tech Stack

- **Python 3.12+**: The core programming language for the application.
- **Streamlit**: A web application framework used for building the user interface.
- **OpenAI API**: Powers the wine analysis functionality, providing detailed insights based on user input.
- **python-dotenv**: Manages environment variables for secure API key handling.
- **Pydantic**: Used for data validation and settings management.

### 🤖 OpenAI API Features

- **Function Calling**: The application leverages the OpenAI API's function calling capability to provide structured responses. This allows the model to return data in a predefined format, ensuring that all necessary information is included in the response.
- **Inputs**:
  - Wine name entered by the user.
- **Outputs**:
  - A structured JSON response containing:
    - `characteristics`: A detailed description of the wine.
    - `pairing_suggestions`: Recommendations for food that pairs well with the wine.
    - `serving_recommendations`: Suggestions for serving temperature and glass type.

### 📦 OpenAI API Response Format

When the application makes a request to the OpenAI API using the function calling feature, it receives a structured response that includes various components. Below is an example of such a response:

```
ChatCompletion(id='chatcmpl-Ar2jR4YGR0WiDbr7pKunWP7n0MtVI', 
choices=[Choice(finish_reason='stop', index=0, logprobs=None, 
message=ChatCompletionMessage(content=None, role='assistant', 
function_call=FunctionCall(arguments='{"characteristics":"The 2018 Caymus Cabernet Sauvignon is a rich and opulent wine with deep purple color. It offers enticing aromas of dark fruit, blackberries, cassis, and hints of vanilla and oak. On the palate, it is full-bodied with velvety tannins and flavors of ripe black cherries, plums, and a touch of spice. The wine has a long, smooth finish with a lingering presence of fruit and oak.","pairing_suggestions":"This Cabernet Sauvignon pairs beautifully with grilled meats such as ribeye steak, lamb chops, or a hearty beef stew. It also goes well with aged cheddar cheese or dark chocolate.","serving_recommendations":"Serve this wine at around 60-65°F (15-18°C) to bring out its full flavors. Decanting is recommended to allow the wine to breathe and open up. Use a large, tulip-shaped glass to enhance the aromas and flavors of the wine."}', name='analyze_wine'), tool_calls=None, refusal=None))], 
created=1737205249, model='gpt-3.5-turbo-0125', object='chat.completion', 
system_fingerprint=None, usage=CompletionUsage(completion_tokens=206, 
prompt_tokens=177, total_tokens=383, 
prompt_tokens_details={'cached_tokens': 0, 'audio_tokens': 0}, 
completion_tokens_details={'reasoning_tokens': 0, 'audio_tokens': 0, 
accepted_prediction_tokens=0, rejected_prediction_tokens=0}), 
service_tier='default')
```

#### Key Components of the Response:

1. **ChatCompletion Object**: The main response object that contains various fields:
   - `id`: Unique identifier for the completion request.
   - `model`: The version of the model used for the request.

2. **Choices**: A list of possible completions generated by the model. Each choice contains:
   - `message`: Includes the role (e.g., assistant) and the content of the response.
   - `function_call`: Contains the arguments returned by the function.

3. **Function Call**: When the model is instructed to analyze wine, it generates a structured response that includes:
   - `arguments`: A JSON string containing the analysis results:
     - `characteristics`: Description of the wine.
     - `pairing_suggestions`: Food pairing recommendations.
     - `serving_recommendations`: Suggestions for serving temperature and glass type.

4. **Usage Information**: Details about token usage, including:
   - `completion_tokens`: Number of tokens used in the completion.
   - `prompt_tokens`: Number of tokens used in the prompt.
   - `total_tokens`: Total number of tokens used in the request.

### 📋 Example Usage

1. **Run the Application**:
   ```bash
   streamlit run mini_app_no_crewai.py
   ```

2. **Enter Wine Name**:
   - Input a wine name, such as "2018 Caymus Cabernet Sauvignon".

3. **Analyze Wine**:
   - Click the "Analyze Wine" button to receive detailed analysis and recommendations.

4. **View Results**:
   - The application displays the characteristics, food pairings, and serving recommendations for the selected wine.

### 🔒 Security

- Ensure that your OpenAI API key is stored securely in a `.env` file and not hardcoded in the application.
- The application requires an active internet connection for OpenAI API functionality.

## 🛠 mini_app_crewai.py Overview

The `mini_app_crewai.py` is an enhanced version of the wine analysis application that demonstrates the integration of CrewAI framework with OpenAI's API. This version provides detailed wine analysis through a specialized AI agent system.

### 🔍 Key Components

1. **WineAnalysis Model (Pydantic)**
   - Structured data model for wine analysis results
   - Fields include:
     - `characteristics`: Detailed description of wine's aroma, taste, body, and finish
     - `pairing_suggestions`: Food pairing recommendations
     - `serving_recommendations`: Temperature and serving guidance
   - Includes data validation and example schemas

2. **WineAnalyzerAgent**
   - Specialized CrewAI agent with wine expertise
   - Utilizes OpenAI's GPT-3.5-turbo model
   - Provides structured wine analysis through function calling
   - Includes comprehensive error handling and logging

3. **Streamlit Interface**
   - User-friendly web interface
   - Features:
     - Wine input field
     - Analysis trigger button
     - Reset functionality
     - Structured results display

### 🔄 Application Flow

1. User enters a wine name
2. WineAnalyzerAgent processes the request
3. OpenAI API generates structured analysis
4. Results are validated and displayed
5. Session state manages the application data

### 🚀 Potential Improvements

1. **Error Handling & Validation**
   - Input validation for wine names
   - More robust API error handling
   - Better user feedback for errors

2. **Performance Optimization**
   - Implementation of caching
   - Rate limiting for API calls
   - Request timeout handling

3. **Security Enhancements**
   - More robust API key validation
   - Input sanitization
   - Rate limiting implementation

4. **User Experience**
   - Loading states for better feedback
   - Wine type suggestions/autocomplete
   - Export functionality for analysis results

5. **Code Architecture**
   - Better utilization of CrewAI features
   - Configuration management
   - Memory management for session state
   - Retry logic for API calls

### ⚠️ Known Issues

1. **CrewAI Integration**
   - Not fully utilizing CrewAI's Task and Crew features
   - Potential for enhanced agent collaboration

2. **Memory Management**
   - Unbounded session state growth
   - Need for cleanup of old analyses

3. **Performance**
   - No request timeout handling
   - Missing caching implementation

4. **Security**
   - Basic API key validation
   - Limited input sanitization

The application provides a solid foundation for wine analysis but could benefit from the suggested improvements for production use.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
