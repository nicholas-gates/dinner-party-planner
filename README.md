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
- pip (Python package installer)

## 🚀 Getting Started

1. **Clone the repository**
   ```bash
   git clone https://github.com/nicholas-gates/dinner-party-planner.git
   cd dinner-party-planner
   ```

2. **Set up a virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   - Create a `.env` file in the project root
   - Add your OpenAI API key:
     ```
     OPENAI_API_KEY=your_api_key_here
     ```

5. **Run the application**
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

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
