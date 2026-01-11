from backend.config import client
import json

def validate_request(user_input, mode="general"):
    """Validate if user input is about house architecture/design.
    Returns a JSON dict with keys:
        - is_valid (bool)
        - refined_prompt (str) – detailed description for image generation
    The system prompt enforces house-only requests.
    """
    system_prompt = f"""
    You are an interior architecture assistant. Your job is to determine whether the user's request is related to house architecture, exterior design, interior design, or floor plans.
    If it is related, respond with a JSON object:
    {{"is_valid": true, "refined_prompt": "<detailed description suitable for image generation>", "total_rooms": <int or null>, "house_dimensions": "<string or null>", "interior_furniture": ["item1", "item2", ...]}}
    Include any extracted details such as style, rooms, dimensions, furniture.
    If it is NOT related to house architecture/design, respond with:
    {{"is_valid": false, "refined_prompt": ""}}
    Do not include any other text.
    """
    try:
        response = client.chat.completions.create(
            model="provider-6/gpt-oss-120b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        return {
            "is_valid": result.get("is_valid", False),
            "refined_prompt": result.get("refined_prompt", ""),
            "total_rooms": result.get("total_rooms"),
            "house_dimensions": result.get("house_dimensions"),
            "interior_furniture": result.get("interior_furniture", [])
        }
    except Exception as e:
        print(f"Validator error: {e}")
        return {"is_valid": False, "refined_prompt": ""}
