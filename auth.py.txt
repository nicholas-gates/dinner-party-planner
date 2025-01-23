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
    
    When running locally:
        - Shows development mode warning
        - Allows all access
    
    When deployed:
        - Requires user authentication
        - Checks email against authorized lists
        - Shows appropriate success/error messages
    """
    # Check if running on Streamlit Cloud (deployed) or locally
    is_deployed = st.session_state.get("user") is not None
    
    if not is_deployed:
        st.sidebar.warning("⚠️ Running in development mode (no authentication)")
        return
        
    user_email = st.session_state.user.email
    domain = user_email.split("@")[1]
    
    # Check if user is authorized
    if user_email in AUTHORIZED_EMAILS or domain in AUTHORIZED_DOMAINS:
        st.sidebar.success(f"Welcome {user_email}! 👋")
    else:
        st.error("⚠️ You don't have access to this application.")
        st.info("Please contact the administrator if you believe this is a mistake.")
        st.stop()
