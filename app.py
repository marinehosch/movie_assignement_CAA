import streamlit as st
from google.cloud import bigquery
import pandas as pd
import requests

# --- 1. CONFIGURATION & CONNECTION ---
st.set_page_config(page_title="Cloud & Analytics 2025 - Movies", layout="wide")

@st.cache_resource
def get_bq_client():
    """Initializes the BigQuery client."""
    return bigquery.Client()

client = get_bq_client()

# IDs confirmed from your Cloud Console
DATASET_ID = "cloud-and-analytics-487915.assignment_movies" 
TMDB_API_KEY = "b014aa1c048829a81aa67568c6d2957c" 

# --- 2. LOGIC FUNCTIONS ---

def run_query(query):
    """Executes the query and logs the SQL to the terminal (Assignment Requirement)."""
    print(f"\n--- EXECUTING SQL QUERY ---\n{query}\n---------------------------\n")
    query_job = client.query(query)
    return query_job.to_dataframe()

def get_movie_poster(tmdb_id):
    """Fetches the poster URL via TMDB API."""
    if not tmdb_id or pd.isna(tmdb_id):
        return None
    try:
        clean_id = int(float(tmdb_id))
        url = f"https://api.themoviedb.org/3/movie/{clean_id}?api_key={TMDB_API_KEY}&language=en-US"
        data = requests.get(url, timeout=5).json()
        if 'poster_path' in data and data['poster_path']:
            return f"https://image.tmdb.org/t/p/w500{data['poster_path']}"
    except:
        return None
    return None

# --- 3. USER INTERFACE (UI) ---

st.title("🎬 Movie Explorer 2025")
st.markdown("---")

st.subheader("🔍 Search Parameters")

# Main search bar (contains mode)
movie_input = st.text_input("Search for a movie title...", placeholder="e.g., Toy Story, Batman...")

# Filters in 3 columns
col_lang, col_year, col_rating = st.columns(3)

with col_lang:
    selected_lang = st.selectbox("Language", ["en", "fr", "es", "de", "hi", "it", "ja"])
with col_year:
    min_year = st.number_input("Minimum Release Year", min_value=1900, max_value=2025, value=2010)
with col_rating:
    min_rating = st.slider("Minimum Average Rating", 0.0, 5.0, 3.5, step=0.1)

search_button = st.button("Search Movies", use_container_width=True)

st.markdown("---")

# --- 4. RESULTS PROCESSING ---

if search_button:
    # SQL robustness: handle apostrophes and use % for "contains" search
    safe_input = movie_input.replace("'", "''")
    
    query = f"""
        WITH filtered_movies AS (
            SELECT movieId, title, tmdbId, genres, release_year, language
            FROM `{DATASET_ID}.movies`
            WHERE LOWER(title) LIKE LOWER('%{safe_input}%')
            AND language = '{selected_lang}'
            AND release_year >= {min_year}
        )
        SELECT 
            m.*, 
            ROUND(AVG(r.rating), 2) as avg_rating,
            COUNT(r.rating) as review_count
        FROM filtered_movies AS m
        LEFT JOIN `{DATASET_ID}.ratings` AS r ON m.movieId = r.movieId
        GROUP BY m.movieId, m.title, m.tmdbId, m.genres, m.release_year, m.language
        HAVING (avg_rating >= {min_rating} OR avg_rating IS NULL)
        ORDER BY avg_rating DESC, review_count DESC
        LIMIT 20
    """

    with st.spinner("Searching through 20 million ratings..."):
        try:
            results_df = run_query(query)

            if not results_df.empty:
                st.write(f"### {len(results_df)} movies found")
                
                # Display movies in a list
                for index, row in results_df.iterrows():
                    with st.container():
                        c1, c2 = st.columns([1, 3])
                        
                        with c1:
                            poster = get_movie_poster(row['tmdbId'])
                            if poster:
                                st.image(poster, use_container_width=True)
                            else:
                                st.info("🖼️ No Poster")
                        
                        with c2:
                            st.subheader(row['title'])
                            st.write(f"📅 **Year:** {row['release_year']} | 🌍 **Language:** {row['language'].upper()}")
                            st.write(f"🎭 **Genres:** {row['genres']}")
                            
                            # Display ratings
                            if row['avg_rating'] and row['avg_rating'] > 0:
                                st.success(f"⭐ **Rating: {row['avg_rating']}/5** ({int(row['review_count'])} reviews)")
                            else:
                                st.info("ℹ️ No rating data available")
                        
                        st.markdown("---")
            else:
                st.error("No movies found matching your criteria.")
        except Exception as e:
            st.error(f"An error occurred: {e}")