from fastapi import FastAPI, HTTPException
import subprocess
import os
import json
import requests
import sqlite3
import markdown
import shutil
from bs4 import BeautifulSoup
from PIL import Image
import speech_recognition as sr
import duckdb
import os

AIPROXY_TOKEN = os.getenv("AIPROXY_TOKEN")

if not AIPROXY_TOKEN:
    raise ValueError

# Set AI Proxy API endpoint (replace with the correct endpoint you're using)
API_URL = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"

# Example API request using the AI Proxy
headers = {
    "Authorization": f"Bearer {AIPROXY_TOKEN}",
    "Content-Type": "application/json"
}

payload = {
    "model": "gpt-4o-mini",
    "messages": [{"role": "system", "content": "You are a helpful assistant."}],
    "temperature": 0.7
}

try:
    response = requests.post(API_URL, headers=headers, json=payload)
    response.raise_for_status()  # Raises an error if the request failed
    print(response.json())  # Process API response
except requests.exceptions.RequestException as e:
    print(f"Error making API request: {e}")


app = FastAPI()

data_dir = "/data"

def is_safe_path(path):
    return path.startswith(data_dir)

@app.post("/run")
def run_task(task: str):
    try:
        if "fetch data from" in task.lower():
            url = task.split("fetch data from ")[1].split(" and save it")[0].strip()
            response = requests.get(url)
            with open(f"{data_dir}/api_data.json", "w") as f:
                json.dump(response.json(), f)
            return {"message": "Data fetched and saved."}
        
        elif "clone a git repo" in task.lower():
            repo_url = task.split("clone ")[1].split(" and make a commit")[0].strip()
            subprocess.run(["git", "clone", repo_url, f"{data_dir}/repo"], check=True)
            return {"message": "Git repo cloned."}
        
        elif "run a sql query" in task.lower():
            db_path = f"{data_dir}/database.db"
            query = task.split("query on ")[1].split(" database")[0].strip()
            con = sqlite3.connect(db_path)
            cursor = con.cursor()
            cursor.execute(query)
            result = cursor.fetchall()
            with open(f"{data_dir}/query_result.json", "w") as f:
                json.dump(result, f)
            con.close()
            return {"message": "SQL query executed.", "result": result}
        
        elif "scrape" in task.lower():
            url = task.split("scrape ")[1].split(" and save")[0].strip()
            response = requests.get(url)
            soup = BeautifulSoup(response.text, "html.parser")
            with open(f"{data_dir}/scraped_data.txt", "w") as f:
                f.write(soup.get_text())
            return {"message": "Website scraped and saved."}
        
        elif "compress or resize an image" in task.lower():
            img_path = f"{data_dir}/image.png"
            img = Image.open(img_path)
            img = img.resize((100, 100))
            img.save(f"{data_dir}/image_resized.png")
            return {"message": "Image resized."}
        
        elif "transcribe audio" in task.lower():
            audio_path = f"{data_dir}/audio.mp3"
            recognizer = sr.Recognizer()
            with sr.AudioFile(audio_path) as source:
                audio_data = recognizer.record(source)
                text = recognizer.recognize_google(audio_data)
            with open(f"{data_dir}/transcription.txt", "w") as f:
                f.write(text)
            return {"message": "Audio transcribed."}
        
        elif "convert markdown to html" in task.lower():
            md_path = f"{data_dir}/document.md"
            with open(md_path, "r") as f:
                md_content = f.read()
            html_content = markdown.markdown(md_content)
            with open(f"{data_dir}/document.html", "w") as f:
                f.write(html_content)
            return {"message": "Markdown converted to HTML."}
        
        elif "filter a csv file" in task.lower():
            csv_path = f"{data_dir}/data.csv"
            df = duckdb.read_csv(csv_path)
            filtered_df = df[df["column_name"] == "filter_value"]
            filtered_df.to_json(f"{data_dir}/filtered_data.json", orient="records")
            return {"message": "CSV filtered and saved."}
        
        else:
            raise HTTPException(status_code=400, detail="Task not supported")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/read")
def read_file(path: str):
    full_path = os.path.join(data_dir, path.lstrip("/"))
    if not is_safe_path(full_path) or not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="File not found")
    with open(full_path, "r") as f:
        return f.read()
