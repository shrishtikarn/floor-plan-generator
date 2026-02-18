import streamlit as st
import cv2
import numpy as np
import re

# -------------------------------
# SCALE (1 ft = pixels)
# -------------------------------
SCALE = 20

# -------------------------------
# ROOM DIMENSIONS (ft)
# -------------------------------
ROOM_SIZES = {
    "hall": (14, 16),
    "bedroom": (10, 12),
    "kitchen": (8, 10),
    "bathroom": (5, 7),
    "dining": (8, 10)
}

# -------------------------------
# PARSE PROMPT (STRICT)
# -------------------------------
def parse_prompt(prompt):
    prompt = prompt.lower()
    rooms = []

    patterns = {
        "bedroom": r'(\d+)\s*(bedroom|bed)',
        "bathroom": r'(\d+)\s*(bathroom|bath)',
        "kitchen": r'(\d+)\s*(kitchen)',
        "hall": r'(\d+)\s*(hall)',
        "dining": r'(\d+)\s*(dining)'
    }

    for room, pattern in patterns.items():
        match = re.search(pattern, prompt)
        if match:
            count = int(match.group(1))
            for _ in range(count):
                rooms.append(room)

    return rooms

# -------------------------------
# DRAW ROOM
# -------------------------------
def draw_room(img, name, x, y, w_ft, h_ft):
    w = int(w_ft * SCALE)
    h = int(h_ft * SCALE)

    cv2.rectangle(img, (x, y), (x+w, y+h), (0, 0, 0), 2)

    label = f"{name.upper()} ({w_ft}x{h_ft})"
    cv2.putText(img, label, (x+5, y+h//2),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

    return w, h

# -------------------------------
# DRAW DOOR
# -------------------------------
def draw_door(img, x, y, orientation="h"):
    if orientation == "h":
        cv2.line(img, (x, y), (x+50, y), (0, 0, 255), 3)
    else:
        cv2.line(img, (x, y), (x, y+50), (0, 0, 255), 3)

# -------------------------------
# GENERATE FLOOR PLAN (ARCHITECTURE BASED)
# -------------------------------
def generate_floor_plan(room_list):
    SCALE = 25

    bed_count = room_list.count("bedroom")
    bath_count = room_list.count("bathroom")

    hall_w, hall_h = 14*SCALE, 16*SCALE
    bed_w, bed_h = 10*SCALE, 12*SCALE
    bath_w, bath_h = 5*SCALE, 7*SCALE
    kit_w, kit_h = 8*SCALE, 10*SCALE
    din_w, din_h = 8*SCALE, 10*SCALE

    canvas_w = int(hall_w + 600)
    canvas_h = int(hall_h + 600 + bed_count*120)

    img = np.ones((canvas_h, canvas_w, 3), dtype=np.uint8) * 255

    # -----------------------
    # Helper: Center Text
    # -----------------------
    def put_center_text(text, x, y, w, h, scale=0.5):
        (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, 1)
        tx = x + (w - tw) // 2
        ty = y + (h + th) // 2
        cv2.putText(img, text, (tx, ty),
                    cv2.FONT_HERSHEY_SIMPLEX, scale, (0,0,0), 1)

    # -----------------------
    # HALL
    # -----------------------
    hx = canvas_w // 2 - int(hall_w//2)
    hy = canvas_h // 2 - int(hall_h//2)

    cv2.rectangle(img, (hx, hy), (hx+int(hall_w), hy+int(hall_h)), (0,0,0), 3)
    put_center_text("HALL (14x16 ft)", hx, hy, int(hall_w), int(hall_h), 0.7)

    # Entry
    cv2.line(img, (hx+80, hy+int(hall_h)), (hx+140, hy+int(hall_h)), (255,0,0), 3)
    cv2.putText(img, "ENTRY", (hx+70, hy+int(hall_h)+25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,0,0), 2)

    # -----------------------
    # BEDROOMS
    # -----------------------
    bx = hx - int(bed_w)
    by = hy

    for i in range(bed_count):
        cv2.rectangle(img, (bx, by), (bx+int(bed_w), by+int(bed_h)), (0,0,0), 2)
        put_center_text(f"BEDROOM {i+1}\n(10x12 ft)", bx, by, int(bed_w), int(bed_h), 0.45)

        # Door
        cv2.line(img, (bx+int(bed_w), by+60), (bx+int(bed_w), by+100), (0,0,255), 2)

        # Attached bath
        if bath_count > 0:
            bath_y = by + int(bed_h)

            cv2.rectangle(img, (bx, bath_y),
                          (bx+int(bath_w), bath_y+int(bath_h)), (0,0,0), 2)

            put_center_text("ATTACHED\nBATH (5x7)", bx, bath_y,
                            int(bath_w), int(bath_h), 0.35)

            cv2.line(img, (bx+20, bath_y), (bx+60, bath_y), (0,0,255), 2)

            bath_count -= 1

        by += int(bed_h)

    # -----------------------
    # DINING
    # -----------------------
    rx = hx + int(hall_w)
    ry = hy

    if "dining" in room_list:
        cv2.rectangle(img, (rx, ry), (rx+int(din_w), ry+int(din_h)), (0,0,0), 2)
        put_center_text("DINING\n(8x10 ft)", rx, ry, int(din_w), int(din_h), 0.4)

        cv2.line(img, (rx, ry+40), (rx, ry+80), (0,0,255), 2)

        rx += int(din_w)

    # -----------------------
    # KITCHEN
    # -----------------------
    if "kitchen" in room_list:
        cv2.rectangle(img, (rx, ry), (rx+int(kit_w), ry+int(kit_h)), (0,0,0), 2)
        put_center_text("KITCHEN\n(8x10 ft)", rx, ry, int(kit_w), int(kit_h), 0.4)

        cv2.line(img, (rx, ry+40), (rx, ry+80), (0,0,255), 2)

    # -----------------------
    # COMMON BATH
    # -----------------------
    if bath_count > 0:
        cx = hx
        cy = hy - int(bath_h)

        cv2.rectangle(img, (cx, cy), (cx+int(bath_w), cy+int(bath_h)), (0,0,0), 2)
        put_center_text("COMMON\nBATH (5x7)", cx, cy,
                        int(bath_w), int(bath_h), 0.35)

        cv2.line(img, (cx+20, cy+int(bath_h)), (cx+60, cy+int(bath_h)), (0,0,255), 2)

    return img



# -------------------------------
# STREAMLIT UI
# -------------------------------
st.title("🏠 AI Floor Plan Generator (Architect Mode)")

prompt = st.text_input(
    "Enter your plan:",
    "1 hall 2 bedroom 1 kitchen 1 dining 2 bathroom"
)

if st.button("Generate Plan"):
    room_list = parse_prompt(prompt)

    if not room_list:
        st.error("❌ Example: 2 bedroom 1 kitchen")
    else:
        st.write("### Parsed Rooms:", room_list)
        plan = generate_floor_plan(room_list)
        st.image(plan, channels="BGR")
