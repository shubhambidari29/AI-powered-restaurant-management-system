import os
from google import genai
from .models import FoodItem


def ask_ai(question):

    client = genai.Client(
        api_key=os.getenv("GEMINI_API_KEY")
    )

    food_items = FoodItem.objects.filter(is_available=True)

    menu = "\n".join([
        f"{food.name} - Rs. {food.price} - {food.category}"
        for food in food_items
    ])

    prompt = f"""
    You are Foodora's AI Restaurant Assistant.

    Available menu:
    {menu}

    Recommend only available food items.
    Answer customers politely and simply.

    Customer question: {question}
    """

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt
    )

    return response.text