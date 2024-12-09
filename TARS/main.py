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
    subprocess.run(["streamlit", "run", "surfaces/web/web.py", "--server.address", "0.0.0.0", "--server.port", "8501"])

if __name__ == "__main__":
    # Start the FastAPI app
    api_process = Process(target=run_api)
    api_process.start()

    # Start the Slack bot
    slack_process = Process(target=run_slack_bot)
    slack_process.start()

    # Start the Streamlit app
    streamlit_process = Process(target=run_streamlit)
    streamlit_process.start()

    # Wait for all processes to complete
    for process in [api_process, slack_process, streamlit_process]:
        process.join()
