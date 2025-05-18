import streamlit as st
import time
import random
import string
from supabase import create_client, Client

# ====== DEMO SUPABASE CONFIG ======
SUPABASE_URL = "https://ztzenntbfrcrmevwmewq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp0emVubnRiZnJjcm1ldndtZXdxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc1NTQwNzAsImV4cCI6MjA2MzEzMDA3MH0.zx982BctMryz92V00XgueDj4LUS07gwcDro0FtzsGp8"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ====== SAMPLE SENTENCES ======
sentences = [
    "The quick brown fox jumps over the lazy dog.",
    "Typing is a useful skill in programming.",
    "Streamlit helps build Python apps easily.",
    "Fast fingers make fast coders.",
    "Consistency is the key to speed."
]

# ====== HELPER FUNCTION ======
def generate_room_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

# ====== PAGE SETUP ======
st.set_page_config(page_title="Typing Challenge", page_icon="⌨️")
st.title("⌨️ Multiplayer Typing Game")

params = st.experimental_get_query_params()
room_code = params.get("room", [None])[0]

if not room_code:
    # ==== CREATE ROOM ====
    st.subheader("Create a Room")
    name = st.text_input("Enter your name")
    if st.button("Create Room") and name:
        sentence = random.choice(sentences)
        room_code = generate_room_code()
        supabase.table("games").insert({
            "room_code": room_code,
            "sentence": sentence,
            "player1_name": name
        }).execute()

        base_url = "https://typingtest-1.streamlit.app"  # Replace after deploying
        join_link = f"{base_url}?room={room_code}"
        st.success("Room Created! Share this link:")
        st.code(join_link)
        st.stop()

else:
    # ==== JOIN ROOM ====
    game_data = supabase.table("games").select("*").eq("room_code", room_code).execute()
    if not game_data.data:
        st.error("Room not found!")
        st.stop()

    game = game_data.data[0]
    sentence = game["sentence"]

    st.subheader(f"Room Code: {room_code}")
    name = st.text_input("Enter your name to join")
    if not name:
        st.stop()

    is_player1 = name == game["player1_name"]
    is_player2 = name == game.get("player2_name")
    joining = not is_player1 and not is_player2

    if joining and not game.get("player2_name"):
        supabase.table("games").update({"player2_name": name}).eq("room_code", room_code).execute()
        st.success("Joined as Player 2")
    elif joining:
        st.error("Room already has 2 players.")
        st.stop()

    player_role = "player1" if is_player1 or (not is_player2 and not game.get("player2_name")) else "player2"
    ready_key = f"{player_role}_ready"
    score_key = f"{player_role}_score"

    # ==== READY BUTTON ====
    if not game.get(ready_key):
        if st.button("✅ I'm ready"):
            supabase.table("games").update({ready_key: True}).eq("room_code", room_code).execute()
            st.rerun()
        st.stop()

    # ==== WAIT FOR OTHER PLAYER ====
    if not all([game.get("player1_ready"), game.get("player2_ready")]):
        st.info("Waiting for the other player to get ready...")
        time.sleep(3)
        st.rerun()

    # ==== START GAME ====
    st.subheader("Start Typing! ⏱ 60 seconds")
    st.write(f"Sentence:\n\n**{sentence}**")
    input_text = st.text_area("Type the sentence above", height=100)
    if st.button("✅ Submit"):
        end_time = time.time()
        correct = input_text.strip() == sentence.strip()
        wpm = round(len(input_text.strip().split()) / 1)  # simulate 1-minute typing
        result = {"wpm": wpm, "correct": correct}
        supabase.table("games").update({score_key: result}).eq("room_code", room_code).execute()
        st.success(f"Submitted: WPM = {wpm}, Correct = {correct}")
        st.stop()

    # ==== CHECK IF BOTH PLAYERS FINISHED ====
    game = supabase.table("games").select("*").eq("room_code", room_code).execute().data[0]
    p1 = game.get("player1_score")
    p2 = game.get("player2_score")

    if p1 and p2:
        st.success("🎉 Game Over!")
        st.write(f"**{game['player1_name']}**: {p1['wpm']} WPM, Correct: {p1['correct']}")
        st.write(f"**{game['player2_name']}**: {p2['wpm']} WPM, Correct: {p2['correct']}")
        if p1["correct"] and p2["correct"]:
            if p1["wpm"] > p2["wpm"]:
                st.balloons()
                st.success(f"{game['player1_name']} wins!")
            elif p2["wpm"] > p1["wpm"]:
                st.balloons()
                st.success(f"{game['player2_name']} wins!")
            else:
                st.info("It's a tie!")
        else:
            st.warning("One or both players gave incorrect answer.")
    else:
        st.info("Waiting for both players to submit...")
