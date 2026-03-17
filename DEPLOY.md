# Deployment Guide

Options to host the Streamlit app on a public website.

1) Streamlit Community Cloud (recommended, easiest)
   - Push this repository to GitHub.
   - Go to https://share.streamlit.io and connect your GitHub account.
   - Choose the repository and branch, and set the `Main file` to `streamlit_app/app.py`.
   - Streamlit will use `requirements.txt` at the repo root to install dependencies.

2) Render / Railway / Fly / Other Docker-capable hosts
   - This repo includes a `Dockerfile` and `Procfile`.
   - Build and push the image, then deploy on your chosen provider exposing port 8501.

   Example (local build + run):
   ```bash
   docker build -t data-projects-hub:latest .
   docker run -p 8501:8501 data-projects-hub:latest
   ```

3) Heroku (legacy)
   - Ensure `requirements.txt` exists at repo root and a `Procfile` is present (already included).
   - Push to a Heroku app; Heroku will use the `Procfile` to run the app.

Notes:
- If your dataset files are large, consider moving them to cloud storage and accessing them from the app.
- If you want me to create a GitHub Actions workflow to build and push a Docker image to a registry, I can add that (you'll need repository secrets).
