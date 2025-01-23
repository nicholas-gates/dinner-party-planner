"""
Authentication module for the Dinner Party Planner application.

This module handles user authentication and authorization using Streamlit's
built-in authentication system when deployed to Streamlit Cloud.
"""

import streamlit as st
from typing import Set
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def get_authorized_set(env_var: str) -> Set[str]:
    """
    Convert comma-separated environment variable to set of strings.
    
    Args:
        env_var: Name of environment variable
        
    Returns:
        Set of authorized values
    """
    values = os.getenv(env_var, "")
    return {x.strip() for x in values.split(",") if x.strip()}

# Authentication Configuration
AUTHORIZED_EMAILS: Set[str] = get_authorized_set("AUTHORIZED_EMAILS")
AUTHORIZED_DOMAINS: Set[str] = get_authorized_set("AUTHORIZED_DOMAINS")

def check_authentication() -> None:
    """
    Verify user authentication and authorization.
    Stops app execution if user is not authorized.
    
    When STREAMLIT_DEPLOYED="true":
        - Requires user authentication
        - Checks email against authorized lists
        - Shows appropriate success/error messages
    
    When STREAMLIT_DEPLOYED="false":
        - Shows development mode warning
        - Allows all access
        
    For all other cases:
        - Blocks access completely
    """
    # Check if explicitly set to development mode
    is_dev_mode = os.getenv('STREAMLIT_DEPLOYED', '').lower() == 'false'
    
    if is_dev_mode:
        st.sidebar.warning("⚠️ Running in development mode (no authentication)")
        return
        
    # Ensure authentication is enabled and user is logged in
    if not st.session_state.get("user"):
        st.error("⚠️ Authentication is required.")
        st.info("This app requires proper authentication configuration. Please contact the administrator.")
        st.stop()
        
    user_email = st.session_state.user.email
    domain = user_email.split("@")[1]
    
    # Check if user is authorized
    if user_email in AUTHORIZED_EMAILS or domain in AUTHORIZED_DOMAINS:
        st.sidebar.success(f"Welcome {user_email}! 👋")
    else:
        st.error("⚠️ You don't have access to this application.")
        st.info("Please contact the administrator if you believe this is a mistake.")
        st.stop()
