import streamlit as st
from models import BookRecommendation
from agents.book_agent import create_book_agent
from agents.cross_domain_agent import create_cross_domain_agent
from utils import logger
from auth import check_authentication

def main():
    logger.info("Starting Book Recommendation System")
    
    # Check user authentication
    check_authentication()
    
    st.title("📚 Book Recommendation System")
    st.write("""
    Welcome to the Book Recommendation System! Tell me what kind of books you're interested in,
    and I'll provide personalized recommendations. You can mention:
    - Authors you enjoy
    - Genres you prefer
    - Themes or topics you're interested in
    - Writing styles you like
    - Or any other criteria!
    """)

    # Get user input
    user_input = st.text_area("What kind of books are you looking for?", 
                             placeholder="E.g., 'I love magical realism like Gabriel García Márquez' or 'Looking for sci-fi books about time travel'")

    # Store the book recommendations in session state
    if "book_recommendations" not in st.session_state:
        st.session_state.book_recommendations = None

    if st.button("Get Recommendations"):
        if user_input:
            logger.info("User submitted request for recommendations")
            # Create and run the graph
            logger.info("Creating recommendation agent")
            graph = create_book_agent()
            
            # Initialize the state
            state = {
                "messages": [],
                "input": user_input,
                "recommendations": []
            }
            logger.info(f"Initialized state with input: {user_input}")

            # Run the graph
            with st.spinner("Generating recommendations..."):
                logger.info("Running recommendation graph")
                result = graph.invoke(state)
                logger.info("Received recommendations from graph")
                # Store recommendations in session state
                st.session_state.book_recommendations = result["recommendations"]

        else:
            logger.warning("User attempted to submit without input")
            st.warning("Please enter your book preferences first!")

    # Display book recommendations if available
    if st.session_state.book_recommendations:
        logger.info(f"Processing {len(st.session_state.book_recommendations)} recommendations for display")
        for i, book_dict in enumerate(st.session_state.book_recommendations, 1):
            logger.debug(f"Processing recommendation {i}: {book_dict['title']}")
            book = BookRecommendation(**book_dict)
            with st.container():
                st.subheader(f"{i}. {book.title} by {book.author}")
                st.write(f"**Genre:** {book.genre}")
                st.write(f"**Description:** {book.description}")
                st.write(f"**Why this book:** {book.reason}")
                st.divider()
        logger.info("Finished displaying recommendations")

        # Add a section for cross-domain recommendations
        st.subheader("Get Cross-Domain Recommendations")
        st.write("Select a book to get related movie, game, and song recommendations that share similar themes.")
        
        # Create dropdown with book titles
        book_titles = [book["title"] for book in st.session_state.book_recommendations]
        selected_index = st.selectbox(
            "Select a book",
            range(len(book_titles)),
            format_func=lambda i: book_titles[i]
        )

        if st.button("Get Related Content"):
            # Create cross-domain agent
            cross_domain_graph = create_cross_domain_agent()
            selected_book = st.session_state.book_recommendations[selected_index]
            
            # Initialize state with selected book
            state = {"selected_book": selected_book}
            
            # Get cross-domain recommendations
            with st.spinner("Finding related content..."):
                result = cross_domain_graph.invoke(state)
                recommendations = result.get("cross_domain_recommendations", {})
                
                if recommendations:
                    # Display movie recommendation
                    st.subheader("🎬 Movie Recommendation")
                    movie = recommendations.get("movie", {})
                    st.write(f"**{movie.get('title')} ({movie.get('year')})**")
                    st.write(movie.get('description'))
                    st.write(f"**Why this movie:** {movie.get('reason')}")
                    
                    # Display game recommendation
                    st.subheader("🎮 Game Recommendation")
                    game = recommendations.get("game", {})
                    st.write(f"**{game.get('title')} ({game.get('platform')})**")
                    st.write(game.get('description'))
                    st.write(f"**Why this game:** {game.get('reason')}")
                    
                    # Display song recommendation
                    st.subheader("🎵 Song Recommendation")
                    song = recommendations.get("song", {})
                    st.write(f"**{song.get('title')} by {song.get('artist')}**")
                    st.write(song.get('description'))
                    st.write(f"**Why this song:** {song.get('reason')}")
                else:
                    st.error("Failed to generate cross-domain recommendations. Please try again.")

if __name__ == "__main__":
    main()
