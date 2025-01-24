"""
Authentication module for the Dinner Party Planner application.

This module handles user authentication using Streamlit's secrets management
for password-based authentication.
"""

import streamlit as st
from typing import Callable
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_authentication() -> bool:
    """
    Verify user authentication using password-based authentication.
    Returns True if user is authenticated, False otherwise.
    
    Uses Streamlit's secrets management for secure password storage:
    - In development: uses .streamlit/secrets.toml
    - In production: uses Streamlit Cloud's secrets management
    """
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        
    if st.session_state.authenticated:
        return True
        
    def validate_password() -> None:
        """Validate entered password against stored secret."""
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state.authenticated = True
            del st.session_state["password"]  # Clear password from session
            st.rerun()  # Rerun to clear the login form
        else:
            st.session_state.authenticated = False
            st.session_state.password_attempted = True
            
    # Create a container for the login form
    if not st.session_state.authenticated:
        with st.form("login_form"):
            st.markdown("### Login Required")
            st.text_input(
                "Enter password",
                type="password",
                key="password"
            )
            
            if st.form_submit_button("Login"):
                validate_password()
            
            if st.session_state.get("password_attempted", False):
                st.error("😕 Incorrect password")
                st.session_state.password_attempted = False
        return False
        
    return True

def requires_auth(func: Callable) -> Callable:
    """
    Decorator to require authentication for specific pages or functions.
    
    Usage:
        @requires_auth
        def protected_page():
            st.write("This is a protected page")
    """
    def wrapper(*args, **kwargs):
        if check_authentication():
            return func(*args, **kwargs)
    return wrapper
