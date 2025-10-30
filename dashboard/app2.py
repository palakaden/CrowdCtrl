# dashboard/app2.py

import sys
import os
import streamlit as st
import cv2
import torch
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import importlib.util
import tempfile

# -----------------------------
# Import MC_CNN from scripts/crowd_model.py safely
# -----------------------------
crowd_model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../scripts/crowd_model.py"))
spec = importlib.util.spec_from_file_location("crowd_model", crowd_model_path)
crowd_model = importlib.util.module_from_spec(spec)
sys.modules["crowd_model"] = crowd_model
spec.loader.exec_module(crowd_model)
MC_CNN = crowd_model.MC_CNN

# -----------------------------
# Import utils
# -----------------------------
utils_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../scripts/utils.py"))
spec_utils = importlib.util.spec_from_file_location("utils", utils_path)
utils = importlib.util.module_from_spec(spec_utils)
sys.modules["utils"] = utils
spec_utils.loader.exec_module(utils)
calculate_max_people = utils.calculate_max_people

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
CHAT_ID = "-4856510438"

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
# Streamlit UI - Dark Sidebar Theme
# -----------------------------
st.set_page_config(
    page_title="Crowd Monitoring System", 
    page_icon="👥", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling with Dark Sidebar and Compact Alert Box
st.markdown("""
<style>
    /* Main Light Theme - UPDATED HEADER SIZE */
    .main-header {
        font-size: 3rem !important;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: 700;
        padding: 0.5rem;
        line-height: 1.1;
        letter-spacing: -0.3px;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        padding: 1rem;
        color: white;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        margin-bottom: 0.5rem;
    }
    
    /* UPDATED: Make both boxes have same width and alignment */
    .alert-box {
        background: linear-gradient(135deg, #FEF2F2 0%, #FEE2E2 100%);
        border: 2px solid #DC2626;
        border-radius: 12px;
        padding: 0.8rem;
        margin: 0.5rem 0;
        font-size: 0.85rem;
        box-shadow: 0 8px 25px rgba(220, 38, 38, 0.25);
        text-align: center;
        min-height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        width: 100%;
    }
    .count-card-danger {
        background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        text-align: center;
        box-shadow: 0 8px 25px rgba(220, 38, 38, 0.25);
        color: white;
        min-height: 180px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        width: 100%;
    }
    .count-card-safe {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        text-align: center;
        box-shadow: 0 8px 25px rgba(5, 150, 105, 0.25);
        color: white;
        min-height: 180px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        width: 100%;
    }
    
    .status-indicator {
        font-size: 1rem;
        font-weight: bold;
        padding: 0.4rem;
        border-radius: 6px;
        text-align: center;
        margin-bottom: 0.3rem;
    }
    .alert-header {
        color: #DC2626;
        text-align: center;
        margin-bottom: 0.3rem;
        font-size: 1.1rem;
        font-weight: bold;
    }
    .alert-subheader {
        color: #7F1D1D;
        text-align: center;
        margin-bottom: 0.4rem;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .counts-display {
        background: white;
        padding: 0.4rem;
        border-radius: 6px;
        margin: 0.4rem 0;
        border: 1px solid #DC2626;
        text-align: center;
    }
    .success-badge {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%);
        color: white;
        padding: 0.3rem 0.6rem;
        border-radius: 12px;
        font-weight: bold;
        margin: 0.3rem 0;
        display: inline-block;
        box-shadow: 0 2px 8px rgba(5, 150, 105, 0.3);
        font-size: 0.75rem;
    }
    .count-number {
        font-size: 2.8rem;
        font-weight: bold;
        margin: 0;
        line-height: 1;
    }
    .count-label {
        font-size: 1rem;
        margin: 0.6rem 0 0.3rem 0;
        opacity: 0.9;
    }
    .count-difference {
        font-size: 1.2rem;
        font-weight: bold;
        margin: 0.3rem 0;
    }
    .count-limit {
        font-size: 0.9rem;
        opacity: 0.8;
        margin: 0.3rem 0 0 0;
    }
    
    /* Dark Sidebar Theme - Compact */
    .css-1d391kg, .css-1lcbmhc, .css-1outpf7 {
        background-color: #0E1117 !important;
    }
    .sidebar .sidebar-content {
        background: linear-gradient(135deg, #0E1117 0%, #1F2937 100%) !important;
    }
    .help-section {
        background: linear-gradient(135deg, #1F2937 0%, #374151 100%);
        border-radius: 12px;
        padding: 1.2rem;
        margin: 0.8rem 0;
        border-left: 4px solid #60A5FA;
        color: #E5E7EB;
    }
    .instruction-step {
        background: #374151;
        padding: 0.8rem;
        border-radius: 8px;
        margin: 0.6rem 0;
        border-left: 3px solid #10B981;
        box-shadow: 0 2px 6px rgba(0,0,0,0.3);
        color: #E5E7EB;
    }
    .step-number {
        background: #10B981;
        color: white;
        width: 22px;
        height: 22px;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        margin-right: 0.4rem;
        font-size: 0.8rem;
    }
    
    /* Sidebar text colors */
    .css-1d391kg p, .css-1d391kg h1, .css-1d391kg h2, .css-1d391kg h3, .css-1d391kg h4, .css-1d391kg h5, .css-1d391kg h6 {
        color: #E5E7EB !important;
    }
    
    /* Remove Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    
    /* Sidebar divider */
    .css-1d391kg hr {
        border-color: #374151 !important;
    }
    
    /* Header container for better alignment */
    .header-container {
        text-align: center;
        padding: 1rem 0.8rem;
        margin-bottom: 0.5rem;
    }
    
    /* Spacing between status indicators */
    .status-spacing {
        margin-bottom: 0.8rem !important;
    }
    
    /* Additional compact styling for sidebar info box */
    .sidebar-info-box {
        background: #1E40AF;
        padding: 0.8rem;
        border-radius: 8px;
        margin-top: 0.8rem;
        border-left: 3px solid #60A5FA;
    }
    
    /* NEW: Analytics column layout for perfect alignment */
    .analytics-column {
        display: flex;
        flex-direction: column;
        height: 100%;
    }
    
    /* NEW: Container for both count and alert to align with video */
    .analytics-stack {
        display: flex;
        flex-direction: column;
        height: 100%;
        min-height: 400px; /* Match video height */
    }
    
    /* NEW: Count card container */
    .count-container {
        flex-shrink: 0;
    }
    
    /* NEW: Alert container that fills remaining space and aligns with video bottom */
    .alert-container {
        flex: 1;
        display: flex;
        align-items: flex-end; /* Align to bottom */
        justify-content: center;
        min-height: 200px;
        padding: 0.2rem;
        width: 100%;
    }
    
    /* Ultra compact alert content */
    .compact-alert-content {
        padding: 0.2rem;
        width: 100%;
    }
    
    /* Alert timestamp - smaller */
    .alert-timestamp {
        margin-top: 0.3rem;
        font-size: 0.7rem;
        color: #6B7280;
    }
    
    /* NEW: Ensure video container has consistent height */
    .video-container {
        min-height: 400px;
        display: flex;
        align-items: flex-end;
    }
    
    /* NEW: Make headings same height and remove spacing */
    [data-testid="column"] h3 {
        margin: 0 !important;
        margin-bottom: 0.5rem !important;
        padding: 0 !important;
        line-height: 1.2 !important;
        height: 1.5rem !important;
        display: block !important;
    }
    
    /* Remove all spacing after headings */
    [data-testid="column"] .element-container:first-of-type {
        margin-bottom: 0.5rem !important;
    }
    
    /* Align video and count card at same top position */
    [data-testid="column"] .stImage,
    [data-testid="column"] .count-card-danger,
    [data-testid="column"] .count-card-safe {
        margin-top: 0 !important;
    }
    
    /* Ensure empty placeholders don't add spacing */
    [data-testid="stEmpty"] {
        margin: 0 !important;
        padding: 0 !important;
    }

    /* UPDATED: Dark theme with neon glow for alert box */
    .alert-box {
        background: linear-gradient(135deg, #1a1a1a 0%, #2d1b1b 50%, #1a1a1a 100%);
        border: 2px solid #ff4444;
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
        font-size: 0.9rem;
        box-shadow: 0 0 20px rgba(255, 68, 68, 0.6), 0 0 40px rgba(255, 68, 68, 0.3);
        text-align: center;
        min-height: 150px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        width: 100%;
        color: #ffffff;
        animation: pulse-glow 2s ease-in-out infinite;
    }
    
    @keyframes pulse-glow {
        0%, 100% { box-shadow: 0 0 20px rgba(255, 68, 68, 0.6), 0 0 40px rgba(255, 68, 68, 0.3); }
        50% { box-shadow: 0 0 30px rgba(255, 68, 68, 0.8), 0 0 60px rgba(255, 68, 68, 0.5); }
    }

    /* UPDATED: Orange/Amber warning theme for alert box */
    .alert-box {
        background: linear-gradient(135deg, #fff3cd 0%, #ffc107 50%, #ff9800 100%);
        border: 3px solid #ff6f00;
        border-radius: 15px;
        padding: 1rem;
        margin: 0.5rem 0;
        font-size: 0.9rem;
        box-shadow: 0 8px 25px rgba(255, 111, 0, 0.4), inset 0 0 15px rgba(255, 152, 0, 0.2);
        text-align: center;
        min-height: 150px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        width: 100%;
        color: #7f2d00;
    }

    /* UPDATED: Purple/Red gradient theme for alert box */
    .alert-box {
        background: linear-gradient(135deg, #8B0000 0%, #DC143C 50%, #FF1493 100%);
        border: 2px solid #FF1744;
        border-radius: 15px;
        padding: 1rem;
        margin: 0.5rem 0;
        font-size: 0.9rem;
        box-shadow: 0 10px 30px rgba(220, 20, 60, 0.5), 0 0 20px rgba(255, 20, 147, 0.3);
        text-align: center;
        min-height: 150px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        width: 100%;
        color: #ffffff;
    }

    /* UPDATED: Red theme with diagonal pattern for alert box - bigger size */
    .alert-box {
        background: linear-gradient(135deg, #DC2626 0%, #B91C1C 50%, #991B1B 100%);
        border: 3px solid #FF4444;
        border-radius: 15px;
        padding: 1.1rem;
        margin: 0.5rem 0;
        font-size: 0.95rem;
        box-shadow: 0 10px 30px rgba(220, 38, 38, 0.5), 
                    0 0 0 3px rgba(255, 68, 68, 0.2),
                    inset 0 2px 10px rgba(0, 0, 0, 0.3);
        text-align: center;
        min-height: 150px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        width: 100%;
        color: #ffffff;
        position: relative;
        overflow: hidden;
    }
    
    .alert-box::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: repeating-linear-gradient(
            45deg,
            transparent,
            transparent 10px,
            rgba(255, 255, 255, 0.05) 10px,
            rgba(255, 255, 255, 0.05) 20px
        );
        pointer-events: none;
    }
    
    .alert-box > * {
        position: relative;
        z-index: 1;
    }
    
    .alert-header {
        color: #FFD700;
        text-align: center;
        margin-bottom: 0.4rem;
        font-size: 1.2rem;
        font-weight: bold;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
    }
    
    .alert-subheader {
        color: #FFE5B4;
        text-align: center;
        margin-bottom: 0.5rem;
        font-size: 0.85rem;
        font-weight: 600;
    }
    
    .counts-display {
        background: rgba(0, 0, 0, 0.3);
        padding: 0.5rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border: 1px solid rgba(255, 255, 255, 0.2);
        text-align: center;
        backdrop-filter: blur(5px);
    }
    
    .success-badge {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%);
        color: white;
        padding: 0.4rem 0.7rem;
        border-radius: 12px;
        font-weight: bold;
        margin: 0.4rem 0;
        display: inline-block;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
        font-size: 0.8rem;
    }
    
    .compact-alert-content {
        padding: 0.3rem;
        width: 100%;
    }
    
    .alert-timestamp {
        margin-top: 0.4rem;
        font-size: 0.75rem;
        color: #FFD700;
        opacity: 0.9;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state variables
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'current_area' not in st.session_state:
    st.session_state.current_area = 100.0
if 'alert_history' not in st.session_state:
    st.session_state.alert_history = []
if 'uploaded_video' not in st.session_state:
    st.session_state.uploaded_video = None
if 'alert_message_displayed' not in st.session_state:
    st.session_state.alert_message_displayed = False

# Header Section - UPDATED (only main header, no sub-header)
st.markdown("""
<div class="header-container">
    <h1 class="main-header">👥 Crowd Monitoring & Alert System</h1>
</div>
""", unsafe_allow_html=True)

# Sidebar - DARK THEME (Always Visible)
with st.sidebar:
    st.markdown("## 📚 How to Use")
    st.markdown("---")
    
    st.markdown("""
    <div class="help-section">
    <h4 style="color: #60A5FA; margin-bottom: 1.5rem;">🎯 Quick Guide</h4>
    
    <div class="instruction-step">
    <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
        <div class="step-number">1</div>
        <h5 style="margin: 0; color: #60A5FA;">Set Area Size</h5>
    </div>
    <p style="margin: 0; color: #D1D5DB; font-size: 0.9rem;">
        • Enter area in square meters<br>
        • Safe capacity auto-calculates<br>
        • No update button needed
    </p>
    </div>
    
    <div class="instruction-step">
    <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
        <div class="step-number">2</div>
        <h5 style="margin: 0; color: #60A5FA;">Upload Video</h5>
    </div>
    <p style="margin: 0; color: #D1D5DB; font-size: 0.9rem;">
        • Supports MP4, AVI, MOV<br>
        • Processing starts automatically<br>
        • Real-time analysis begins
    </p>
    </div>
    
    <div class="instruction-step">
    <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
        <div class="step-number">3</div>
        <h5 style="margin: 0; color: #60A5FA;">Monitor & Alerts</h5>
    </div>
    <p style="margin: 0; color: #D1D5DB; font-size: 0.9rem;">
        • Watch live video feed<br>
        • See real-time crowd counts<br>
        • Get automatic alerts<br>
        • Telegram & Email notifications
    </p>
    </div>
    
    <div style="background: #1E40AF; padding: 0.8rem; border-radius: 8px; margin-top: 0.8rem; border-left: 3px solid #60A5FA;">
    <p style="margin: 0; color: #E0F2FE; font-size: 0.85rem; font-weight: 500;">
    💡 <strong>Alert Trigger:</strong> Alerts are sent when crowd exceeds safe capacity for 3 consecutive frames
    </p>
    </div>
    </div>
    """, unsafe_allow_html=True)

# Main content area - LIGHT THEME
col1, col2 = st.columns([2, 1])

with col1:
    # Configuration Section
    st.markdown("### ⚙️ Configuration")
    
    config_col1, config_col2 = st.columns(2)
    
    with config_col1:
        # Area input with immediate update
        new_area = st.number_input(
            "**Area Size (m²)**", 
            min_value=1.0, 
            value=st.session_state.current_area, 
            step=10.0,
            key="area_input",
            help="Enter the area size in square meters"
        )
        
        # Update area immediately when changed
        if new_area != st.session_state.current_area:
            st.session_state.current_area = new_area
            st.rerun()
    
    with config_col2:
        # Display current capacity
        max_people = calculate_max_people(st.session_state.current_area)
        st.metric("**Safe Capacity**", f"{max_people} people")
    
    # Video Upload Section
    st.markdown("### 📤 Video Upload")
    uploaded_file = st.file_uploader(
        "**Upload video file**", 
        type=['mp4','avi','mov'],
        key="video_uploader",
        help="Supported formats: MP4, AVI, MOV"
    )
    
    if uploaded_file and uploaded_file != st.session_state.uploaded_video:
        st.session_state.uploaded_video = uploaded_file
        st.session_state.processing = True
        st.session_state.alert_message_displayed = False
        st.rerun()

with col2:
    # System Status Section
    st.markdown("### 📊 System Status")
    
    # Single column layout for status indicators with spacing
    if st.session_state.uploaded_video:
        if st.session_state.processing:
            st.markdown('<div class="status-indicator" style="background-color: #FEF3C7; color: #92400E;">🔄 PROCESSING</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-indicator" style="background-color: #D1FAE5; color: #065F46;">✅ READY</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-indicator" style="background-color: #E0E7FF; color: #3730A3;">⏳ WAITING</div>', unsafe_allow_html=True)
    
    # Add spacing between the status indicators
    st.markdown('<div style="margin-bottom: 1rem;"></div>', unsafe_allow_html=True)
    
    # Model Active status placed below with spacing
    st.markdown('<div class="status-indicator" style="background-color: #DBEAFE; color: #1E40AF;">🤖 MODEL ACTIVE</div>', unsafe_allow_html=True)
    
    # Empty placeholders for dynamic content
    metrics_placeholder = st.empty()
    alert_placeholder = st.empty()

# Video Processing
if st.session_state.processing and st.session_state.uploaded_video:
    # Create temporary file for video
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
        temp_file.write(st.session_state.uploaded_video.read())
        temp_video_path = temp_file.name
    
    # Initialize video processing
    cap = cv2.VideoCapture(temp_video_path)
    frame_count = 0
    
    # Create main processing layout
    st.markdown("---")
    st.markdown("## 🎥 Live Processing")
    
    # Create columns for video and analytics
    video_col, analytics_col = st.columns([2, 1])
    
    with video_col:
        st.markdown("### 🎬 Live Feed")
        video_placeholder = st.empty()
        
    with analytics_col:
        st.markdown("### 📊 Analytics")
        count_placeholder = st.empty()
        alert_display_placeholder = st.empty()
        
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Alert variables
    alert_counter = 0
    alert_sent = False
    alert_values = []
    
    # Progress bar (hidden but used for internal tracking)
    progress_bar = st.progress(0)
    
    try:
        while cap.isOpened() and st.session_state.processing:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Process frame
            h, w = frame.shape[:2]
            frame_resized = cv2.resize(frame, (224, 224))
            img_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
            img_tensor = torch.from_numpy(img_rgb.transpose(2, 0, 1)).unsqueeze(0).float().to(device) / 255.0
            
            with torch.no_grad():
                density_map = model(img_tensor)
                pred_count = int(density_map.sum().item() * (h * w) / (224 * 224))
                pred_count = max(0, pred_count)
            
            # Update video display
            with video_col:
                # Add overlay to frame
                display_frame = frame.copy()
                
                # Choose color based on crowd level
                if pred_count > max_people:
                    color = (0, 0, 255)  # Red
                    status = "OVER LIMIT!"
                else:
                    color = (0, 255, 0)  # Green
                    status = "SAFE"
                
                # Add text overlay
                cv2.putText(display_frame, f"People: {pred_count}", (50, 60), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
                cv2.putText(display_frame, f"Status: {status}", (50, 100), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
                cv2.putText(display_frame, f"Frame: {frame_count+1}/{total_frames}", (50, 140), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                # Convert to RGB for display
                display_frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
                video_placeholder.image(display_frame_rgb, use_container_width=True)
            
            # Update analytics - ONLY show count display when no alert
            if not alert_sent:
                with analytics_col:
                    if pred_count > max_people:
                        count_placeholder.markdown(
                            f'<div class="count-card-danger">'
                            f'<div class="count-label">👥 CURRENT COUNT</div>'
                            f'<div class="count-number">{pred_count}</div>'
                            f'<div class="count-difference">⚠️ {pred_count - max_people} OVER LIMIT</div>'
                            f'<div class="count-limit">Safe Limit: {max_people}</div>'
                            f'</div>', 
                            unsafe_allow_html=True
                        )
                    else:
                        count_placeholder.markdown(
                            f'<div class="count-card-safe">'
                            f'<div class="count-label">👥 CURRENT COUNT</div>'
                            f'<div class="count-number">{pred_count}</div>'
                            f'<div class="count-difference">✅ {max_people - pred_count} UNDER LIMIT</div>'
                            f'<div class="count-limit">Safe Limit: {max_people}</div>'
                            f'</div>', 
                            unsafe_allow_html=True
                        )
            
            # Alert logic
            if pred_count > max_people:
                alert_counter += 1
                alert_values.append(pred_count)
            else:
                alert_counter = 0
                alert_values = []
            
            if alert_counter >= 3 and not alert_sent:
                alert_result = send_alert_notifications(pred_count, max_people)
                alert_timestamp = time.strftime("%H:%M:%S")
                alert_entry = f"{alert_timestamp} - ALERT: {pred_count} > {max_people}"
                st.session_state.alert_history.append(alert_entry)
                alert_sent = True
                
                # Display COMPACT ALERT MESSAGE in the empty space altijd
                alert_display_placeholder.markdown(
                    f'<div class="alert-container">'
                    f'<div class="alert-box">'
                    f'<div class="compact-alert-content">'
                    f'<div class="alert-header">🚨 ALERT SENT!</div>'
                    f'<div class="alert-subheader">Count exceeded limit for 3 consecutive frames</div>'
                    f'<div class="counts-display">'
                    f'<div style="font-size: 0.85rem; font-weight: bold; margin-bottom: 0.4rem; color: #FFD700;">Recent Counts:</div>'
                    f'<div style="font-size: 1.2rem; font-weight: bold; color: #FFFFFF; margin: 0.4rem 0;">{alert_values[-3:]}</div>'
                    f'</div>'
                    f'<div class="success-badge">✅ Alerts sent via Telegram & Email</div>'
                    f'<div class="alert-timestamp">Time: {alert_timestamp}</div>'
                    f'</div>'
                    f'</div>'
                    f'</div>', 
                    unsafe_allow_html=True
                )
                st.session_state.alert_message_displayed = True
            
            frame_count += 1
            
            # Update progress internally - FIXED: Ensure value stays within [0.0, 1.0]
            progress_percentage = min((frame_count + 1) / total_frames, 1.0)
            progress_bar.progress(progress_percentage)
            
            # Update alert history
            if st.session_state.alert_history:
                alert_placeholder.markdown(
                    "\n".join([f"• {alert}" for alert in st.session_state.alert_history[-3:]])
                )
            
            # Small delay for better visualization
            time.sleep(0.03)
            
    except Exception as e:
        st.error(f"Error during processing: {str(e)}")
    
    finally:
        cap.release()
        try:
            os.unlink(temp_video_path)
        except:
            pass
        
        # Completion message
        st.markdown("---")
        st.success(f"✅ Processing completed! Processed {frame_count} frames")
        
        if alert_sent:
            st.warning("🚨 Alerts were sent during processing!")
        
        # Reset processing state
        st.session_state.processing = False

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #6B7280; padding: 2rem;'>"
    "Crowd Monitoring System | Crowd Safety Solution"
    "</div>", 
    unsafe_allow_html=True
)