import streamlit as st
from supabase import create_client
import uuid
import time
import random

# --- Supabase setup ---
SUPABASE_URL = "https://ztzenntbfrcrmevwmewq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp0emVubnRiZnJjcm1ldndtZXdxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc1NTQwNzAsImV4cCI6MjA2MzEzMDA3MH0.zx982BctMryz92V00XgueDj4LUS07gwcDro0FtzsGp8"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Sentences for typing ---
sentences = [
    "The quick brown fox jumps over the lazy dog.",
    "Streamlit makes it easy to build web apps in Python.",
    "Supabase is an open-source Firebase alternative.",
    "Typing tests help improve your speed and accuracy."
]

# --- Helper Functions ---
def get_sentence():
    return random.choice(sentences)

def create_room():
    room_code = str(uuid.uuid4())[:8]
    sentence = get_sentence()
    supabase.table("games").insert({
        "room_code": room_code,
        "sentence": sentence
    }).execute()
    return room_code, sentence

def get_game_data(room_code):
    result = supabase.table("games").select("*").eq("room_code", room_code).execute()
    return result.data[0] if result.data else None

# --- Streamlit App ---
st.set_page_config(page_title="Multiplayer Typing Game")
st.title("🎮 Multiplayer Typing Challenge")

base_url = "https://typingtest-1.streamlit.app/.streamlit.app"  # Replace with your deployed app URL

# --- Room Logic ---
params = st.experimental_get_query_params()
room_code = params.get("room", [None])[0]

if not room_code:
    st.header("Create a Game Room")
    player_name = st.text_input("Enter your name")
    if st.button("Create Room") and player_name:
        room_code, sentence = create_room()
        supabase.table("games").update({"player1_name": player_name}).eq("room_code", room_code).execute()
        join_link = f"{base_url}?room={room_code}"
        st.success("Room created! Share this link with your friend:")
        st.code(join_link)
        st.stop()
else:
    game = get_game_data(room_code)
    if not game:
        st.error("Room not found.")
        st.stop()

    player_name = st.text_input("Enter your name")
    player_role = None
    if game.get("player1_name") is None:
        player_role = "player1"
    elif game.get("player2_name") is None and player_name != game.get("player1_name"):
        player_role = "player2"

    if st.button("Join Game") and player_name and player_role:
        supabase.table("games").update({f"{player_role}_name": player_name}).eq("room_code", room_code).execute()
        st.rerun()

    game = get_game_data(room_code)
    if player_name not in [game.get("player1_name"), game.get("player2_name")]:
        st.warning("Waiting for a spot in the room or use a different name.")
        st.stop()

    sentence = game.get("sentence")
    player_key = "player1" if player_name == game.get("player1_name") else "player2"
    ready_key = f"{player_key}_ready"
    score_key = f"{player_key}_score"

    if not game.get(ready_key):
        if st.button("I'm Ready!"):
            supabase.table("games").update({ready_key: True}).eq("room_code", room_code).execute()
            st.rerun()
        st.info("Waiting for you to click ready.")
        st.stop()

    # Refresh game data
    game = get_game_data(room_code)

    if game["player1_ready"] and game["player2_ready"]:
        if not game.get("start_time"):
            now = int(time.time())
            supabase.table("games").update({"start_time": now}).eq("room_code", room_code).execute()
            game["start_time"] = now

        remaining = 30 - (int(time.time()) - game["start_time"])
        if remaining > 0:
            st.subheader("⏳ Game In Progress!")
            st.write(f"Time left: **{remaining} seconds**")
            st.write(f"Type this sentence:")
            st.code(sentence)
            input_text = st.text_area("Start typing...", height=100)
            st.stop()
        else:
            st.subheader("🛑 Time's up! Submit your result:")
            input_text = st.text_area("Paste what you typed", height=100, key="final_input")
            if st.button("Submit Result"):
                correct = input_text.strip() == sentence.strip()
                word_count = len(input_text.strip().split())
                wpm = word_count * 2  # since it's a 30-second game
                score_data = {"wpm": wpm, "correct": correct}
                supabase.table("games").update({score_key: score_data}).eq("room_code", room_code).execute()
                st.success("Submitted! Waiting for other player.")
                st.stop()

    game = get_game_data(room_code)
    p1 = game.get("player1_score")
    p2 = game.get("player2_score")

    if p1 and p2:
        st.subheader("🏁 Final Results")
        st.write(f"**{game['player1_name']}**: {p1['wpm']} WPM, Correct: {p1['correct']}")
        st.write(f"**{game['player2_name']}**: {p2['wpm']} WPM, Correct: {p2['correct']}")
        if p1["correct"] and p2["correct"]:
            if p1["wpm"] > p2["wpm"]:
                st.success(f"🎉 {game['player1_name']} wins!")
            elif p2["wpm"] > p1["wpm"]:
                st.success(f"🎉 {game['player2_name']} wins!")
            else:
                st.info("🤝 It's a tie!")
        else:
            st.warning("❌ One or both answers were incorrect.")
    else:
        st.info("Waiting for both players to submit...")
