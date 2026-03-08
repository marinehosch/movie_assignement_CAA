import streamlit as st
from google.cloud import bigquery
import pandas as pd
import requests

# --- 1. CONFIGURATION & CONNECTION ---
st.set_page_config(page_title="Cloud & Analytics 2026 - Movies", layout="wide")

@st.cache_resource
def get_bq_client():
    return bigquery.Client()

client = get_bq_client()

# ID from Cloud Console and API key
DATASET_ID = "cloud-and-analytics-487915.assignment_movies" 
TMDB_API_KEY = "b014aa1c048829a81aa67568c6d2957c" 

# --- 2. LOGIC FUNCTIONS ---
@st.cache_data
#dynamic filter 
def get_unique_genres():
    """Extracts unique individual genres from the 'Action|Horror|Sci-Fi' format."""
    query = f"""
        SELECT DISTINCT genre
        FROM `{DATASET_ID}.movies`,
        UNNEST(SPLIT(genres, '|')) AS genre
        WHERE genre IS NOT NULL AND genre <> '(no genres listed)'
        ORDER BY genre
    """
    df = client.query(query).to_dataframe()
    return df['genre'].tolist()

@st.cache_data
def get_unique_countries():
    """Fetch unique countries."""
    query = f"SELECT DISTINCT country FROM `{DATASET_ID}.movies` WHERE country IS NOT NULL ORDER BY country"
    df = client.query(query).to_dataframe()
    return df['country'].tolist()
    
def run_query(query):
    print(f"\n--- EXECUTING SQL QUERY ---\n{query}\n---------------------------\n")
    query_job = client.query(query)
    return query_job.to_dataframe()

def get_movie_poster(tmdb_id):
    if not tmdb_id or pd.isna(tmdb_id):
        return None
    try:
        int_id = int(float(tmdb_id))
        url = f"https://api.themoviedb.org/3/movie/{int_id}?api_key={TMDB_API_KEY}&language=en-US"
        data = requests.get(url, timeout=5).json()
        if 'poster_path' in data and data['poster_path']:
            return f"https://image.tmdb.org/t/p/w500{data['poster_path']}"
    except:
        return None
    return None

# --- 3. USER INTERFACE  ---

st.title("🎬 Movie Explorer 2026")
st.markdown("---")

st.subheader("🔍 Search")

# Main search bar 
movie_input = st.text_input("Search for a movie title...", placeholder="e.g., Toy Story, Batman...")

# Filters in 3 columns
col_lang, col_year, col_rating = st.columns(3)

with col_lang:
    selected_lang = st.selectbox("Language", ["en", "fr", "es", "de", "hi", "it", "ja"])
with col_year:
    min_year = st.slider("Minimum Release Year", min_value=1900, max_value=2026, value=2010)
with col_rating:
    min_rating = st.slider("Minimum Average Rating", 0.0, 5.0, 3.5, step=0.1)

#ajouter les filtres genre et country sur 2 colonnes sur la ligne en dessous 
col_genres, col_countries = st.columns(2)

with col_genres:
    genre_options = get_unique_genres()
    selected_genres = st.multiselect("Genres (Select one or more)", genre_options)

with col_countries:
    country_options = get_unique_countries()
    selected_countries = st.multiselect("Countries (Select one or more)", country_options)

search_button = st.button("Search Movies", use_container_width=True)

st.markdown("---")

# --- 4. RESULTS ---

if search_button:
    safe_input = movie_input.replace("'", "''")

    genre_conditions = []
    for g in selected_genres:
        genre_conditions.append(f"genres LIKE '%{g}%'")
    
    genre_filter = ""
    if genre_conditions:
        genre_filter = "AND (" + " OR ".join(genre_conditions) + ")"    
        
    country_filter = "" 
    if selected_countries: 
        countries_str = "', '".join([c.replace("'", "''") for c in selected_countries])
        country_filter = f"AND country IN ('{countries_str}')"
    
    query = f"""
        WITH filtered_movies AS (
            SELECT movieId, title, tmdbId, genres, release_year, language, country
            FROM `{DATASET_ID}.movies`
            WHERE LOWER(title) LIKE LOWER('%{safe_input}%')
            AND language = '{selected_lang}'
            AND release_year >= {min_year}
            {genre_filter}
            {country_filter}
        )
        SELECT 
            m.movieId, 
            m.title, 
            m.tmdbId, 
            m.genres, 
            m.release_year, 
            m.language, 
            m.country,
            ROUND(AVG(r.rating), 2) as avg_rating,
            COUNT(r.rating) as review_count
        FROM filtered_movies AS m
        LEFT JOIN `{DATASET_ID}.ratings` AS r ON m.movieId = r.movieId
        GROUP BY 
            m.movieId, 
            m.title, 
            m.tmdbId, 
            m.genres, 
            m.release_year, 
            m.language, 
            m.country
        HAVING (avg_rating >= {min_rating} OR avg_rating IS NULL)
        ORDER BY avg_rating DESC, review_count DESC
        LIMIT 20
    """

    with st.spinner("Searching through 20 million ratings..."):
        try:
            results_df = run_query(query)

            if not results_df.empty:
                st.write(f"### {len(results_df)} movies found")
                
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
                            st.write(f"📅 **Year:** {row['release_year']} | 🌍 **Language:** {row['language'].upper()} | 🌏 **Country:** {row['country']}")
                            st.write(f"🎭 **Genres:** {row['genres']}")
                            if row['avg_rating'] and row['avg_rating'] > 0:
                                st.success(f"⭐ **Rating: {row['avg_rating']}/5** ({int(row['review_count'])} reviews)")
                            else:
                                st.info("ℹ️ No rating data available")
                        
                        st.markdown("---")
            else:
                st.error("No movies found matching your criteria.")
        except Exception as e:
            st.error(f"An error occurred: {e}")