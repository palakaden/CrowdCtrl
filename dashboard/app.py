# dashboard/app.py

import sys
import os
import streamlit as st
from PIL import Image
import torch
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import time  # for repeated alerts if needed

# -----------------------------
# Add scripts folder to Python path
# -----------------------------
scripts_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts'))
if scripts_path not in sys.path:
    sys.path.append(scripts_path)

# -----------------------------
# Import model and utilities
# -----------------------------
from crowd_model import MC_CNN  # your model class
from utils import calculate_max_people, count_people

# -----------------------------
# Load model
# -----------------------------
device = 'cuda' if torch.cuda.is_available() else 'cpu'
model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../crowd_counting.pth"))

model = MC_CNN().to(device)
model.load_state_dict(torch.load(model_path, map_location=device))
model.eval()

# -----------------------------
# Email Config
# -----------------------------
EMAIL_ADDRESS = 'thomasajay22@gmail.com'
EMAIL_PASSWORD = 'vbhg wqve fxuj krpp'  # Gmail App Password
TO_EMAIL = 'ajaythomas2255@gmail.com'

# -----------------------------
# Telegram Config
# -----------------------------
TELEGRAM_TOKEN = "8348787339:AAE0ePHJyB0x1BBog7ipRDF-5COkvnjmjFI"
CHAT_ID = "-4856510438"  # your chat ID

# -----------------------------
# Alert functions
# -----------------------------
def send_email_alert(subject, message):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = TO_EMAIL
    msg['Subject'] = subject
    msg.attach(MIMEText(message, 'plain'))

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    server.send_message(msg)
    server.quit()

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    telegram_message = f"⚠️🚨 URGENT ALERT! 🚨⚠️\n\n{message}\n\n⚠️⚠️⚠️"
    data = {"chat_id": CHAT_ID, "text": telegram_message}
    requests.post(url, data=data)
    time.sleep(5)
    requests.post(url, data=data)

def send_alert_notifications(pred_count, max_people):
    if pred_count > max_people:
        alert_message = f"Crowd count {pred_count} exceeded the maximum allowed {max_people}."
        send_email_alert("Crowd Alert!", alert_message)
        send_telegram_alert(alert_message)
        return alert_message + " Alerts sent via Telegram and Email ✅"
    else:
        return f"Crowd is within safe limits ({pred_count}/{max_people}) ✅"

# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(
    page_title="Crowd Monitoring System",
    page_icon="👥",
    layout="wide"
)

# CSS for clean layout
st.markdown("""
<style>
    .stImage {
        padding: 0 !important;
        margin: 0 !important;
    }
    .stImage img {
        border-radius: 10px !important;
        width: 100% !important;
        height: auto !important;
        max-height: 400px !important;
        object-fit: contain !important;
    }
    .compact-section {
        margin-bottom: 0.8rem !important;
    }
    .results-container {
        padding: 1rem !important;
    }
    .metric-clean {
        margin-top: 1rem !important;
        margin-bottom: 1rem !important;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.title("👥 Crowd Monitoring & Alert System")
st.markdown("### AI-Powered Crowd Density Analysis")
st.info("🚀 **System Overview**: AI-powered crowd analysis with instant alerts when capacity limits are exceeded.")

# Columns for configuration and upload
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("⚙️ Area Configuration")
    area = st.number_input(
        "**Enter Area Size (m²)**", 
        min_value=1.0, 
        value=100.0,
        step=10.0,
        help="Specify the area in square meters to calculate maximum safe capacity"
    )
    max_people = calculate_max_people(area)
    st.markdown('<div class="metric-clean">', unsafe_allow_html=True)
    st.metric(label="**Maximum Safe Capacity**", value=f"{max_people} people", help=f"Calculated for {area} m² area")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.subheader("📤 Upload Crowd Image")
    uploaded_file = st.file_uploader(
        "**Choose an image file**", 
        type=['jpg', 'png', 'jpeg'],
        help="Upload a clear image of the crowd area for analysis"
    )
    if uploaded_file:
        st.success("✅ Image uploaded successfully!")
        st.caption("Supported formats: JPG, PNG, JPEG")

# Analysis Section
if uploaded_file:
    st.markdown("---")
    st.subheader("📊 Analysis Results")
    img_col, result_col = st.columns([1.5, 1])
    
    with img_col:
        image = Image.open(uploaded_file).convert('RGB')
        st.image(image, caption="📷 Uploaded Crowd Image", use_container_width=True, output_format="auto")
    
    with result_col:
        # Resize to match training size
        resized_image = image.resize((1024, 768))  # Width=1024, Height=768
        temp_path = "temp_image.jpg"
        resized_image.save(temp_path)

        with st.spinner('Analyzing crowd density...'):
            pred_count = count_people(temp_path, model, device, input_size=(1024,768))
        
        st.markdown('<div class="results-container">', unsafe_allow_html=True)
        
        st.markdown('<div class="compact-section">', unsafe_allow_html=True)
        st.metric(label="**👥 Detected People**", value=pred_count, delta=None)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="compact-section">', unsafe_allow_html=True)
        capacity_percentage = min(100, (pred_count / max_people) * 100)
        st.metric("**📊 Capacity Utilization**", f"{capacity_percentage:.1f}%")
        st.progress(int(capacity_percentage))
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="compact-section">', unsafe_allow_html=True)
        st.subheader("🚨 Alert Status")
        alert_result = send_alert_notifications(pred_count, max_people)
        if pred_count > max_people:
            st.error(alert_result)
            st.warning("⚠️ Crowd exceeds safe limits!")
        else:
            st.success(alert_result)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("ℹ️ System Information")
    st.markdown("""
    ### 📈 How It Works
    1. **Set Area**: Define the space size
    2. **Upload Image**: Provide crowd photo
    3. **AI Analysis**: Density check
    4. **Smart Alerts**: Automatic notifications
    """)
    st.markdown("""
    ### 🔔 Alert Channels
    - 📧 Email Notifications
    - 📱 Telegram Messages
    """)
    st.markdown("""
    ### 🟢 System Status
    - **Model**: Loaded ✅
    - **Alerts**: Active ✅
    """)
