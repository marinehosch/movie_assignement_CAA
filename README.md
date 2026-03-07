# movie explorer - Cloud and Advanced Analytics assignement 1
A serverless web application built with streamilt and BigQuery that allows users to explore a dataset of 20 million movie ratings. The app is containerized with Docker and deployed on Google Cloud Run. 

## URL 
https://movie-app-190661200302.europe-west1.run.app/

## tech info
* **Frontend:** Streamlit (Python)
* **Database:** Google BigQuery
* **API:** TMDB (The Movie Database) 
* **Infrastructure:** Google Cloud Run (Serverless)
* **Containerization:** Docker

## Sructure 
* `app.py`: Main Streamlit application logic and SQL queries.
* `Dockerfile`: Container configuration for cloud deployment.
* `.gitignore`: Prevents large CSV files and local cache from being pushed to Git.