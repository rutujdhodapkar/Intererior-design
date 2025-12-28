import streamlit as st
import requests
import json
import base64
import os

# =========================================================
# CONFIG
# =========================================================

OPENROUTER_API_KEY = "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"  # <-- put your key here
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json"
}

OUTPUT_DIR = "generated_images"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# =========================================================
# SYSTEM PROMPTS
# =========================================================

PLANNER_SYSTEM_PROMPT = """
You are an architectural planner AI.

Return STRICT JSON ONLY.

Schema:
{
  "floors": [
    {
      "floor_number": 1,
      "rooms": [
        {
          "name": "Living Room",
          "width_ft": 12,
          "length_ft": 14,
          "style": "modern minimalist"
        }
      ]
    }
  ],
  "exterior_style": "modern minimalist house"
}

Rules:
- Maximum 5 rooms per floor
- If exceeded, return exactly:
  { "error": "rooms out of bound" }
- No explanations
- No markdown
"""

# =========================================================
# GPT-OSS → PLAN
# =========================================================

def generate_plan(user_text):
    payload = {
        "model": "openai/gpt-oss-120b:free",
        "messages": [
            {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
            {"role": "user", "content": user_text}
        ]
    }

    r = requests.post(OPENROUTER_URL, headers=HEADERS, json=payload)
    data = r.json()

    if "choices" not in data:
        st.error("Planning failed")
        st.json(data)
        st.stop()

    return json.loads(data["choices"][0]["message"]["content"])

# =========================================================
# GEMINI → IMAGE (ALL FORMATS HANDLED)
# =========================================================

def generate_image(prompt, filename):
    payload = {
        "model": "google/gemini-2.5-flash-image",
        "max_tokens": 1024,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    r = requests.post(OPENROUTER_URL, headers=HEADERS, json=payload)
    data = r.json()

    # Handle API errors
    if "error" in data:
        st.warning(data["error"]["message"])
        return None

    # CASE 1: Gemini image in choices.message.images
    try:
        image_url = data["choices"][0]["message"]["images"][0]["image_url"]["url"]
        if image_url.startswith("data:image"):
            image_base64 = image_url.split(",")[1]
            image_bytes = base64.b64decode(image_base64)

            path = os.path.join(OUTPUT_DIR, filename)
            with open(path, "wb") as f:
                f.write(image_bytes)

            return path
    except Exception:
        pass

    st.warning("Image not returned (text only or credit limit).")
    return None

# =========================================================
# STREAMLIT UI
# =========================================================

st.set_page_config(page_title="AI House Generator", layout="wide")
st.title("🏠 AI 1BHK House Generator (GPT-OSS + Gemini)")

user_input = st.text_area(
    "Enter house description:",
    height=200,
    placeholder="""
Design a modern minimalist 1BHK ground-floor house.

Living room 12x14 ft
Bedroom 10x12 ft
Kitchen 8x10 ft
Bathroom 6x8 ft

Exterior: small modern single-storey house
"""
)

if st.button("🚀 Generate"):
    if not user_input.strip():
        st.warning("Enter something first.")
        st.stop()

    with st.spinner("Planning house…"):
        plan = generate_plan(user_input)

    if "error" in plan:
        st.error(plan["error"])
        st.stop()

    st.subheader("🧠 Generated Plan")
    st.json(plan)

    # ================================
    # INTERIOR ROOMS
    # ================================
    st.header("🖼 Interior Renders")

    for floor in plan["floors"]:
        st.subheader(f"Floor {floor['floor_number']}")

        if len(floor["rooms"]) > 5:
            st.error("rooms out of bound")
            st.stop()

        cols = st.columns(2)

        for i, room in enumerate(floor["rooms"]):
            prompt = (
                f"Realistic interior render of a {room['name']} "
                f"{room['width_ft']}ft by {room['length_ft']}ft, "
                f"{room['style']}, furnished, daylight"
            )

            with st.spinner(f"Rendering {room['name']}…"):
                img_path = generate_image(
                    prompt,
                    f"floor{floor['floor_number']}_{room['name'].replace(' ', '_')}.png"
                )

            with cols[i % 2]:
                if img_path:
                    st.image(img_path, caption=room["name"], use_column_width=True)
                else:
                    st.info(f"{room['name']} skipped (credits / limit)")

    # ================================
    # EXTERIOR
    # ================================
    st.header("🏡 Exterior Render")

    with st.spinner("Rendering exterior…"):
        exterior_path = generate_image(
            f"Exterior view of a {plan['exterior_style']}, daylight, realistic",
            "exterior.png"
        )

    if exterior_path:
        st.image(exterior_path, caption="Exterior", use_column_width=True)
    else:
        st.info("Exterior skipped (credits / limit)")

    st.success("Done ✅")
