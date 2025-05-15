import streamlit as st
import time
import random
from datetime import datetime, timedelta
import pandas as pd

# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'player_name' not in st.session_state:
    st.session_state.player_name = ''
if 'challenge_id' not in st.session_state:
    st.session_state.challenge_id = ''
if 'game_state' not in st.session_state:
    st.session_state.game_state = 'waiting'
if 'start_time' not in st.session_state:
    st.session_state.start_time = None
if 'results' not in st.session_state:
    st.session_state.results = {}
if 'players' not in st.session_state:
    st.session_state.players = {}

# Sample texts for typing
TEXTS = [
    "The quick brown fox jumps over the lazy dog.",
    "Python is an interpreted, high-level programming language.",
    "Streamlit makes it easy to create and share web apps.",
    "To be or not to be, that is the question."
]

def generate_challenge_id():
    return str(random.randint(100000, 999999))

def calculate_wpm(text, time_taken):
    words = len(text.split())
    minutes = time_taken / 60
    return round(words / minutes, 2) if minutes > 0 else 0

def calculate_accuracy(original, typed):
    correct = 0
    min_len = min(len(original), len(typed))
    for i in range(min_len):
        if original[i] == typed[i]:
            correct += 1
    return round((correct / len(original)) * 100, 2) if original else 0

def home_page():
    st.title("⚡ Typing Challenge")
    st.write("Challenge a friend to a typing duel!")
    
    st.session_state.player_name = st.text_input("Enter your name:", max_chars=20)
    
    if st.button("Create Challenge"):
        if st.session_state.player_name:
            st.session_state.challenge_id = generate_challenge_id()
            st.session_state.players = {
                'player1': {'name': st.session_state.player_name, 'ready': False, 'results': None},
                'player2': {'name': '', 'ready': False, 'results': None}
            }
            st.session_state.page = 'waiting'
            st.session_state.game_state = 'waiting'
            st.session_state.text_to_type = random.choice(TEXTS)
        else:
            st.warning("Please enter your name")

def waiting_page():
    st.title("🎮 Challenge Created")
    st.write(f"Player: {st.session_state.player_name}")
    
    # Display challenge link
    challenge_link = f"{st.experimental_get_query_params()['browser_serverAddress'][0]}?join={st.session_state.challenge_id}"
    st.subheader("Challenge Link:")
    st.code(challenge_link)
    
    # Check if opponent has joined
    if st.session_state.players['player2']['name']:
        st.success(f"Opponent joined: {st.session_state.players['player2']['name']}")
        if st.button("Start Game!"):
            st.session_state.game_state = 'starting'
            st.session_state.start_time = datetime.now() + timedelta(seconds=5)
            st.rerun()
    else:
        st.warning("Waiting for opponent to join...")
    
    if st.button("Cancel Challenge"):
        st.session_state.page = 'home'
        st.rerun()

def game_page():
    st.title("⌨️ Typing Challenge")
    st.write(f"Player: {st.session_state.player_name}")
    
    now = datetime.now()
    
    if st.session_state.game_state == 'starting':
        # Countdown before game starts
        seconds_left = max(0, int((st.session_state.start_time - now).total_seconds()))
        st.subheader(f"Game starts in: {seconds_left}")
        
        if seconds_left == 0:
            st.session_state.game_state = 'playing'
            st.session_state.end_time = datetime.now() + timedelta(minutes=1)
            st.rerun()
    
    elif st.session_state.game_state == 'playing':
        # Game in progress
        seconds_left = max(0, int((st.session_state.end_time - now).total_seconds()))
        st.subheader(f"Time left: {seconds_left} seconds")
        
        # Display text to type
        st.subheader("Type this text:")
        st.write(st.session_state.text_to_type)
        
        # Typing area
        typed_text = st.text_area("Start typing here:", height=150, key='typing_area')
        
        # Calculate results if time is up
        if typed_text and seconds_left == 0:
            player_key = 'player1' if st.session_state.player_name == st.session_state.players['player1']['name'] else 'player2'
            
            time_taken = min(60, (datetime.now() - (st.session_state.end_time - timedelta(minutes=1))).total_seconds())
            wpm = calculate_wpm(typed_text, time_taken)
            accuracy = calculate_accuracy(st.session_state.text_to_type, typed_text)
            
            st.session_state.players[player_key]['results'] = {
                'wpm': wpm,
                'accuracy': accuracy,
                'time_taken': time_taken
            }
            
            # Check if both players have results
            if st.session_state.players['player1']['results'] and st.session_state.players['player2']['results']:
                st.session_state.game_state = 'finished'
                st.rerun()
    
    elif st.session_state.game_state == 'finished':
        # Display results
        st.subheader("🏆 Game Results")
        
        results = [
            {
                'Player': st.session_state.players['player1']['name'],
                'WPM': st.session_state.players['player1']['results']['wpm'],
                'Accuracy': f"{st.session_state.players['player1']['results']['accuracy']}%"
            },
            {
                'Player': st.session_state.players['player2']['name'],
                'WPM': st.session_state.players['player2']['results']['wpm'],
                'Accuracy': f"{st.session_state.players['player2']['results']['accuracy']}%"
            }
        ]
        
        df = pd.DataFrame(results).sort_values('WPM', ascending=False)
        st.dataframe(df.style.highlight_max(axis=0, color='lightgreen'))
        
        winner = df.iloc[0]['Player']
        st.success(f"🎉 Winner: {winner} with {df.iloc[0]['WPM']} WPM!")
        
        if st.button("Play Again"):
            st.session_state.page = 'home'
            st.rerun()

def join_page(challenge_id):
    st.title("🎯 Accept Challenge")
    
    st.session_state.player_name = st.text_input("Enter your name:", max_chars=20)
    
    if st.button("Join Challenge"):
        if st.session_state.player_name:
            st.session_state.challenge_id = challenge_id
            st.session_state.players['player2']['name'] = st.session_state.player_name
            st.session_state.page = 'waiting'
            st.rerun()
        else:
            st.warning("Please enter your name")

def main():
    # Check for join link
    query_params = st.experimental_get_query_params()
    if 'join' in query_params and st.session_state.page == 'home':
        join_page(query_params['join'][0])
        return
    
    # Page routing
    if st.session_state.page == 'home':
        home_page()
    elif st.session_state.page == 'waiting':
        waiting_page()
    elif st.session_state.page == 'game':
        game_page()
    
    # Auto-refresh for real-time updates
    if st.session_state.page in ['waiting', 'game'] and st.session_state.game_state != 'finished':
        time.sleep(1)
        st.rerun()

if __name__ == "__main__":
    main()
