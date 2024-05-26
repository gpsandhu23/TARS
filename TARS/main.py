import uvicorn
from multiprocessing import Process
import subprocess
from surfaces.API.api import app as api_app
from surfaces.slack.slack_app import SlackBot

def run_api():
    uvicorn.run(api_app, host="0.0.0.0", port=8000)

def run_slack_bot():
    bot = SlackBot()
    bot.start()

def run_streamlit():

    # Command to run the Streamlit app with the updated environment
    subprocess.run(["streamlit", "run", "surfaces/web/web.py"])

if __name__ == "__main__":
    # Start the FastAPI app
    api_process = Process(target=run_api)
    api_process.start()

    # Start the Slack bot
    slack_process = Process(target=run_slack_bot)
    slack_process.start()

    # Start the Streamlit web app
    streamlit_process = Process(target=run_streamlit)
    streamlit_process.start()

    # Join processes to the main process
    api_process.join()
    slack_process.join()
    streamlit_process.join()
