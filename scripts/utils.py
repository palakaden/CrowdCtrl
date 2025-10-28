# utils.py

import torch
import cv2

# -----------------------------
# Parameters
# -----------------------------
MAX_DENSITY = 3  # people per m²

# -----------------------------
# Functions
# -----------------------------
def calculate_max_people(area):
    """
    Calculate maximum allowed people based on area and max density
    """
    return area * MAX_DENSITY


def count_people(image_file, model, device, input_size=(224,224)):
    import cv2
    import numpy as np
    from PIL import Image
    import torch

    # Read uploaded image using PIL -> convert to numpy
    image = Image.open(image_file).convert('RGB')
    image_np = np.array(image)
    original_h, original_w = image_np.shape[:2]

    # Resize using cv2 to match notebook
    image_resized = cv2.resize(image_np, input_size)
    
    # Convert to tensor and normalize
    img_tensor = torch.from_numpy(image_resized.transpose(2,0,1)).unsqueeze(0).float() / 255.0
    img_tensor = img_tensor.to(device)

    # Predict density
    with torch.no_grad():
        density_map = model(img_tensor)
        pred_count = density_map.sum().item() * (original_h * original_w) / (input_size[0] * input_size[1])
    
    return max(0, int(pred_count))



def send_alert(pred_count, max_people):
    """
    Check if predicted crowd exceeds maximum and generate alert message
    """
    if pred_count > max_people:
        # Placeholder for SMS/email/push notification
        return f"ALERT! Crowd exceeded maximum limit: {pred_count}/{max_people} people"
    else:
        return f"Crowd is safe: {pred_count}/{max_people} people"
