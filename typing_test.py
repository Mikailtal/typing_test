import streamlit as st
import time
import random
import string

# Configure page
st.set_page_config(page_title="Multiplayer Typing Game", layout="centered")

# Temporary game room store (in memory)
if "game_rooms" not in st.session_state:
    st.session_state["game_rooms"] = {}

# Sample sentences
sentences = [
    "The quick brown fox jumps over the lazy dog.",
    "Typing fast and accurately is a valuable skill.",
    "Streamlit makes it easy to build web apps in Python.",
    "Practice every day to improve your typing speed.",
    "Coding is best learned by doing real projects."
]

# Helper: generate room code
def generate_room_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

# Read query parameters
params = st.experimental_get_query_params()
room = params.get("room", [None])[0]

# Home page (create a room)
if not room:
    st.title("🏠 Multiplayer Typing Game")
    st.write("Create a room and share the link with a friend to start typing challenge!")

    if st.button("🎮 Create Game Room"):
        new_room = generate_room_code()
        join_link = f"{st.request.host_url}?room={new_room}"

        # Store initial game room info
        st.session_state["game_rooms"][new_room] = {
            "players": {},
            "started": False,
            "sentence": random.choice(sentences),
            "start_time": None,
            "results": {}
        }

        st.success("✅ Room Created!")
        st.write("🔗 Share this link with your friend:")
        st.code(join_link)

        st.markdown(f"""
        <input type="text" value="{join_link}" id="copyLink" style="width: 100%; padding: 8px;" readonly>
        <button onclick="navigator.clipboard.writeText(document.getElementById('copyLink').value)" style="margin-top:10px;">📋 Copy to Clipboard</button>
        """, unsafe_allow_html=True)

        st.markdown(f"[📱 Share via WhatsApp](https://wa.me/?text=Join%20my%20typing%20game:%20{join_link})", unsafe_allow_html=True)
        st.stop()

    st.stop()

# Game room logic
st.title(f"Room Code: {room}")

# Get or create room data
room_data = st.session_state["game_rooms"].get(room, {
    "players": {},
    "started": False,
    "sentence": random.choice(sentences),
    "start_time": None,
    "results": {}
})

# Get player name
name = st.text_input("Enter your name:")
if not name:
    st.stop()

# Register player
if name not in room_data["players"]:
    room_data["players"][name] = {"ready": False}

# Show sentence to be typed
sentence = room_data["sentence"]

# Waiting for start
if not room_data["started"]:
    if not room_data["players"][name]["ready"]:
        if st.button("✅ I'm ready"):
            room_data["players"][name]["ready"] = True
            st.session_state["game_rooms"][room] = room_data
            st.rerun()

    st.info("Waiting for both players to be ready...")

    # If both players ready, start the game
    if len(room_data["players"]) == 2 and all(p["ready"] for p in room_data["players"].values()):
        room_data["started"] = True
        room_data["start_time"] = time.time()
        st.session_state["game_rooms"][room] = room_data
        st.experimental_rerun()

    st.stop()

# Game has started
start_time = room_data["start_time"]
elapsed = int(time.time() - start_time)
remaining = max(0, 60 - elapsed)

st.success("🎯 Game Started!")
st.info(f"⏳ Time remaining: {remaining} seconds")

st.write("### Type this sentence:")
st.code(sentence)

typed_text = st.text_area("Type here:", height=100)

# When time is up or player submits
if remaining == 0 or st.button("📤 Submit"):
    target_words = sentence.strip().split()
    typed_words = typed_text.strip().split()

    correct = sum(1 for t, u in zip(target_words, typed_words) if t == u)
    accuracy = round((correct / len(target_words)) * 100 if target_words else 0, 2)
    wpm = int(len(typed_words) / (max(1, elapsed) / 60))

    # Save result
    room_data["results"][name] = {
        "wpm": wpm,
        "accuracy": accuracy
    }
    st.session_state["game_rooms"][room] = room_data

    st.success(f"✅ Your WPM: {wpm} | Accuracy: {accuracy}%")

    # Wait for other player
    if len(room_data["results"]) < 2:
        st.info("Waiting for the other player to finish...")
        st.stop()

    # Show results
    st.balloons()
    st.header("🏁 Final Results")
    for player, result in room_data["results"].items():
        st.markdown(f"**{player}** → `WPM: {result['wpm']}`, `Accuracy: {result['accuracy']}%`")

    # Decide winner
    p1, p2 = list(room_data["results"].items())
    if p1[1]["wpm"] > p2[1]["wpm"]:
        st.markdown(f"🏆 **Winner:** {p1[0]}")
    elif p2[1]["wpm"] > p1[1]["wpm"]:
        st.markdown(f"🏆 **Winner:** {p2[0]}")
    else:
        st.markdown("🤝 It's a tie!")
    st.stop()
