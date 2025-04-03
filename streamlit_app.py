import streamlit as st
import os
import threading
from datetime import datetime, timedelta
from time import sleep
import subprocess
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import re

# Custom CSS for styling
page_style = """
<style>
.stApp { 
    background-image: url('https://wallpapercave.com/wp/wp1928523.jpg');  
    background-size: cover;
    background-position: center center;
    color: white;
}
h1, h2 {
    text-align: center;
    color: white; /* White text */
    text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.7); /* Black shadow with 70% opacity */
}
.stButton > button {
    background-color: cornflowerblue; /* A blue shade */
    color: white;
}
.stButton > button:hover {
    background-color: royalblue; /* Slightly darker blue */
}
.stTextInput > div > input, .stTextArea > div > textarea {
    border: 2px solid cornflowerblue; /* Blue border */
    background-color: rgba(255, 255, 255, 0.7); /* Semi-transparent white */
}
.subtitle {
    color: white; /* Subtitle text */
    text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.7); /* Shadow */
}
</style>
"""
st.markdown(page_style, unsafe_allow_html=True)

# App title
st.title("NSEbot Automatic Report Retrieval System")
st.markdown('<div class="subtitle">Effortless and Timely Report Automation</div>', unsafe_allow_html=True)

# Initialize session state variables
if "log_content" not in st.session_state:
    st.session_state["log_content"] = ""
if "schedule_status" not in st.session_state:
    st.session_state["schedule_status"] = "Not Scheduled"

# Paths
log_file_path = r"C:\NSE BOT MAIN\nse text log extra.txt"  # Log file path
script_path = r"C:\NSE BOT MAIN\email_notification.py"
download_folder = r"C:\\NSE BOT MAIN\\Downloaded Report_extra"

# Sidebar navigation
menu = ["Run Now", "Schedule", "Logs"]
choice = st.sidebar.radio("Navigate", menu)

# Helper functions
def run_script(email_recipient):
    """Run the main script."""
    try:
        start_time = datetime.now()
        st.session_state["schedule_status"] = "Running script..."

        # Run the script
        result = subprocess.run(
            ["python", script_path, email_recipient], capture_output=True, text=True, check=True
        )

        end_time = datetime.now()
        run_duration = end_time - start_time

        # Update status
        st.session_state["schedule_status"] = f"Script ran successfully!\nExecution time: {run_duration}"
        st.session_state["schedule_status"] += f"\nReports saved at: {download_folder}\n\n{result.stdout}"
    except Exception as e:
        st.session_state["schedule_status"] = f"Error while running script: {e}"
    finally:
        st.rerun()

def schedule_script(email_recipient, schedule_time):
    """Schedule the script to run at a specified time."""
    now = datetime.now()
    target_time = datetime.combine(now.date(), schedule_time)
    if target_time < now:
        target_time += timedelta(days=1)  # If the time has already passed, schedule for the next day
    delay = (target_time - now).total_seconds()

    # Log the scheduled time
    st.session_state["schedule_status"] = f"Scheduled to run at {target_time.strftime('%Y-%m-%d %H:%M:%S')}"
    sleep(delay)  # Wait until the scheduled time
    run_script(email_recipient)

def display_logs():
    """Display the log file content."""
    if os.path.exists(log_file_path):
        with open(log_file_path, "r") as log_file:
            st.session_state["log_content"] = log_file.read()
    st.text_area("Logs", value=st.session_state["log_content"], height=300, key="log_text_area")

# Page functionality
if choice == "Run Now":
    st.header("Run Script Immediately")

    email_recipient = st.text_input("Enter the recipient's email address", placeholder="e.g., recipient@example.com")
    run_now = st.button("Run Now")

    if run_now:
        if email_recipient:
            with st.spinner("Running the script now..."):
                run_script(email_recipient)
        else:
            st.warning("Please enter a valid email address.")

elif choice == "Schedule":
    st.header("Schedule Report Retrieval")

    email_recipient = st.text_input("Enter the recipient's email address", placeholder="e.g., recipient@example.com")
    schedule_time = st.time_input("Select time to schedule download", value=(datetime.now() + timedelta(minutes=1)).time())
    schedule_download = st.button("Schedule Download")

    if schedule_download:
        if email_recipient:
            st.info(f"Scheduling the script to run at {schedule_time.strftime('%H:%M:%S')}...")
            threading.Thread(target=schedule_script, args=(email_recipient, schedule_time), daemon=True).start()
        else:
            st.warning("Please enter a valid email address.")

    st.subheader("Scheduling Status")
    st.text(st.session_state["schedule_status"])

elif choice == "Logs":
    st.header("Downloaded Status Logs")

    # Display logs dynamically
    display_logs()
