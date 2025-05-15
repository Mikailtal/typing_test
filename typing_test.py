import streamlit as st
import time
import random
import string

st.set_page_config(page_title="Multiplayer Typing Game", layout="centered")

# In-memory temporary game store (for demo purposes)
if "game_rooms" not in st.session_state:
    st.session_state["game_rooms"] = {}

sentences = [
    "The quick brown fox jumps over the lazy dog.",
    "Typing fast and accurately is a valuable skill.",
    "Streamlit makes it easy to build web apps in Python.",
    "Practice every day to improve your typing speed.",
    "Coding is best learned by doing real projects."
]

def generate_room_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))


# ----- 1. Room creation or joining -----
params = st.experimental_get_query_params()
room = params.get("room", [None])[0]

if not room:
    st.title("🏠 Welcome to the Multiplayer Typing Game!")
    if st.button("🎮 Create Game Room"):
        new_room = generate_room_code()
        join_link = f"{st.request.url}?room={new_room}"
    
        # Store the new room temporarily
        st.session_state["game_rooms"][new_room] = {
            "players": {},
            "started": False,
            "sentence": random.choice(sentences),
            "start_time": None,
            "results": {}
        }
    
        st.experimental_set_query_params(room=new_room)
    
        st.success("✅ Room Created!")
        st.write("🔗 **Share this link with the second player:**")
        st.code(join_link)
    
        # Copy button (Streamlit only supports experimental workarounds)
        st.markdown(f"""
            <input type="text" value="{join_link}" id="copyLink" style="width: 100%; padding: 8px;" readonly>
            <button onclick="navigator.clipboard.writeText(document.getElementById('copyLink').value)" style="margin-top:10px;">📋 Copy to Clipboard</button>
            """, unsafe_allow_html=True)
    
        # Optional: WhatsApp share
        st.markdown(f"[📱 Share via WhatsApp](https://wa.me/?text=Join%20me%20in%20this%20typing%20game:%20{join_link})", unsafe_allow_html=True)
        
        st.stop()


st.title(f"Room: {room}")
room_data = st.session_state["game_rooms"].get(room, {
    "players": {},
    "started": False,
    "sentence": random.choice(sentences),
    "start_time": None,
    "results": {}
})

# ----- 2. Enter name -----
name = st.text_input("Enter your name:")
if not name:
    st.stop()

if name not in room_data["players"]:
    room_data["players"][name] = {"ready": False}

# ----- 3. Ready Button -----
if not room_data["players"][name]["ready"]:
    if st.button("✅ I'm ready"):
        room_data["players"][name]["ready"] = True
        st.success("Waiting for other player...")
        st.session_state["game_rooms"][room] = room_data
        st.rerun()

# ----- 4. Check if both players ready -----
if len(room_data["players"]) == 2 and all(p["ready"] for p in room_data["players"].values()):
    if not room_data["started"]:
        room_data["started"] = True
        room_data["start_time"] = time.time()
        st.session_state["game_rooms"][room] = room_data
        st.experimental_rerun()

if not room_data["started"]:
    st.warning("Waiting for the other player to be ready...")
    st.stop()

# ----- 5. Typing Test -----
st.success("Game Started!")
elapsed = int(time.time() - room_data["start_time"])
remaining = max(0, 60 - elapsed)
st.info(f"⏱ Time remaining: {remaining} seconds")

st.write("### Type this sentence:")
st.code(room_data["sentence"])

typed_text = st.text_area("Start typing here:", height=100)

if remaining == 0 or st.button("📤 Submit"):
    target_words = room_data["sentence"].split()
    typed_words = typed_text.strip().split()

    correct = sum(1 for tw, uw in zip(target_words, typed_words) if tw == uw)
    wpm = int(len(typed_words) / (max(1, elapsed) / 60))
    accuracy = round((correct / len(target_words)) * 100 if target_words else 0, 2)

    room_data["results"][name] = {
        "wpm": wpm,
        "accuracy": accuracy
    }

    st.session_state["game_rooms"][room] = room_data
    st.success(f"✅ Your WPM: {wpm} | Accuracy: {accuracy}%")

    if len(room_data["results"]) < 2:
        st.warning("Waiting for the other player to finish...")
        st.stop()
    else:
        st.balloons()
        st.header("🎉 Final Results")
        for player, result in room_data["results"].items():
            st.write(f"**{player}** → WPM: {result['wpm']} | Accuracy: {result['accuracy']}%")

        # Decide winner
        p1, p2 = list(room_data["results"].items())
        if p1[1]["wpm"] > p2[1]["wpm"]:
            winner = p1[0]
        elif p2[1]["wpm"] > p1[1]["wpm"]:
            winner = p2[0]
        else:
            winner = "It's a tie!"

        st.markdown(f"### 🏆 Winner: **{winner}**")
