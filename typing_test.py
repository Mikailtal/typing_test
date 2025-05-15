import streamlit as st
import time
import random

st.set_page_config(page_title="Multiplayer Typing Test", layout="centered")

sentences = [
    "The quick brown fox jumps over the lazy dog.",
    "Typing fast and accurately is a valuable skill.",
    "Streamlit makes it easy to build web apps in Python.",
    "Practice every day to improve your typing speed.",
    "Coding is best learned by doing real projects."
]

# Choose a random sentence
if "sentence" not in st.session_state:
    st.session_state.sentence = random.choice(sentences)

st.title("⌨️ Multiplayer Typing Test")

name = st.text_input("Enter your name:")
if not name:
    st.stop()

if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "finished" not in st.session_state:
    st.session_state.finished = False
if "result" not in st.session_state:
    st.session_state.result = {}

if not st.session_state.start_time:
    if st.button("Start Typing Test"):
        st.session_state.start_time = time.time()
        st.rerun()
else:
    elapsed = int(time.time() - st.session_state.start_time)
    remaining = max(0, 30 - elapsed)
    st.info(f"⏱ Time left: {remaining} seconds")

    st.write("### Type this sentence:")
    st.code(st.session_state.sentence)

    typed_text = st.text_area("Start typing here:", height=100)

    if remaining == 0 or st.button("Submit"):
        st.session_state.finished = True
        elapsed = min(30, int(time.time() - st.session_state.start_time))

        target_words = st.session_state.sentence.split()
        typed_words = typed_text.strip().split()

        correct = sum(1 for tw, uw in zip(target_words, typed_words) if tw == uw)
        wpm = int(len(typed_words) / (elapsed / 60))
        accuracy = round((correct / len(target_words)) * 100 if target_words else 0, 2)

        st.session_state.result = {
            "name": name,
            "wpm": wpm,
            "accuracy": accuracy,
            "time": elapsed
        }

        st.success(f"✅ Done! Your WPM: {wpm} | Accuracy: {accuracy}%")
        st.markdown("👉 Share your score with your friend and compare!")

        st.balloons()

