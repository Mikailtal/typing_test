import streamlit as st
import time
import random
import string
from datetime import datetime, timedelta
import pandas as pd
import pytz

# Sample texts for typing
TEXTS = [
    "The quick brown fox jumps over the lazy dog. Pack my box with five dozen liquor jugs. How vexingly quick daft zebras jump!",
    "Python is an interpreted, high-level, general-purpose programming language. Created by Guido van Rossum and first released in 1991.",
    "Streamlit is an open-source Python library that makes it easy to create and share beautiful, custom web apps for machine learning and data science.",
    "To be or not to be, that is the question. Whether 'tis nobler in the mind to suffer the slings and arrows of outrageous fortune.",
    "The greatest glory in living lies not in never falling, but in rising every time we fall. - Nelson Mandela"
]

# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'player_name' not in st.session_state:
    st.session_state.player_name = ''
if 'room_id' not in st.session_state:
    st.session_state.room_id = ''
if 'room_creator' not in st.session_state:
    st.session_state.room_creator = False
if 'game_started' not in st.session_state:
    st.session_state.game_started = False
if 'game_over' not in st.session_state:
    st.session_state.game_over = False
if 'start_time' not in st.session_state:
    st.session_state.start_time = None
if 'end_time' not in st.session_state:
    st.session_state.end_time = None
if 'typed_text' not in st.session_state:
    st.session_state.typed_text = ''
if 'results' not in st.session_state:
    st.session_state.results = {}

# Database simulation using session state
if 'rooms' not in st.session_state:
    st.session_state.rooms = {}

def generate_room_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

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
    return round(correct / len(original) * 100, 2) if original else 0

def home_page():
    st.title("🚀 Typing Speed Challenge")
    st.write("Test your typing speed against friends in real-time!")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Create New Room"):
            st.session_state.page = 'enter_name'
            st.session_state.room_creator = True
    
    with col2:
        if st.button("Join Existing Room"):
            st.session_state.page = 'enter_name'
            st.session_state.room_creator = False

def enter_name_page():
    st.title("👤 Enter Your Name")
    
    st.session_state.player_name = st.text_input("Your Name:", max_chars=20)
    
    if st.session_state.room_creator:
        if st.button("Create Room"):
            if st.session_state.player_name:
                room_id = generate_room_id()
                st.session_state.room_id = room_id
                st.session_state.rooms[room_id] = {
                    'players': {st.session_state.player_name: {'ready': False, 'results': None}},
                    'text': random.choice(TEXTS),
                    'started': False,
                    'game_over': False,
                    'start_time': None,
                    'end_time': None
                }
                st.session_state.page = 'room'
            else:
                st.warning("Please enter your name")
    else:
        st.session_state.room_id = st.text_input("Room ID:", max_chars=6).upper()
        if st.button("Join Room"):
            if st.session_state.player_name and st.session_state.room_id:
                if st.session_state.room_id in st.session_state.rooms:
                    room = st.session_state.rooms[st.session_state.room_id]
                    if st.session_state.player_name not in room['players']:
                        room['players'][st.session_state.player_name] = {'ready': False, 'results': None}
                        st.session_state.page = 'room'
                    else:
                        st.warning("Name already taken in this room")
                else:
                    st.warning("Room not found")
            else:
                st.warning("Please enter your name and room ID")

def room_page():
    room = st.session_state.rooms[st.session_state.room_id]
    players = room['players']
    
    st.title(f"🏠 Room: {st.session_state.room_id}")
    st.write(f"Player: {st.session_state.player_name}")
    
    # Display players and their ready status
    st.subheader("Players:")
    for player, data in players.items():
        status = "✅ Ready" if data['ready'] else "❌ Not Ready"
        st.write(f"- {player}: {status}")
    
    # Room link for sharing
    if st.session_state.room_creator:
        st.subheader("Invite Link:")
        st.code(f"{st.get_option('browser.serverAddress')}/?room={st.session_state.room_id}")
    
    # Ready toggle
    if not room['started'] and not room['game_over']:
        if st.checkbox("I'm ready!", key='ready_checkbox'):
            players[st.session_state.player_name]['ready'] = True
        else:
            players[st.session_state.player_name]['ready'] = False
        
        # Start game button (only for creator)
        if st.session_state.room_creator:
            all_ready = all(data['ready'] for data in players.values())
            if all_ready and len(players) >= 1:
                if st.button("Start Game!"):
                    room['started'] = True
                    room['start_time'] = datetime.now(pytz.utc) + timedelta(seconds=5)
                    room['end_time'] = room['start_time'] + timedelta(minutes=1)
            elif len(players) < 1:
                st.warning("Waiting for more players to join...")
            else:
                st.warning("Waiting for all players to be ready...")
    
    # Game countdown and typing area
    if room['started']:
        now = datetime.now(pytz.utc)
        
        if now < room['start_time']:
            # Countdown before game starts
            seconds_left = int((room['start_time'] - now).total_seconds())
            st.subheader(f"Game starts in: {seconds_left} seconds")
            st.progress((5 - seconds_left) / 5)
            
            # Display the text to type
            st.subheader("Text to type:")
            st.write(room['text'])
        elif now < room['end_time']:
            # Game in progress
            seconds_left = int((room['end_time'] - now).total_seconds())
            st.subheader(f"Time left: {seconds_left} seconds")
            st.progress(seconds_left / 60)
            
            # Typing area
            st.subheader("Type the text below:")
            st.write(room['text'])
            
            typed_text = st.text_area("Start typing here:", height=200, key='typing_area')
            
            # Calculate results if game is over for this player
            if typed_text and len(typed_text.split()) >= 5:  # Minimum words to consider
                players[st.session_state.player_name]['typed_text'] = typed_text
                
                # Calculate WPM and accuracy
                time_taken = (datetime.now(pytz.utc) - room['start_time']).total_seconds()
                wpm = calculate_wpm(typed_text, time_taken)
                accuracy = calculate_accuracy(room['text'], typed_text)
                
                players[st.session_state.player_name]['results'] = {
                    'wpm': wpm,
                    'accuracy': accuracy,
                    'time_taken': min(time_taken, 60)
                }
        else:
            # Game over
            room['game_over'] = True
            st.session_state.game_over = True
            
            # Collect all results
            results = []
            for player, data in players.items():
                if 'results' in data and data['results']:
                    results.append({
                        'Player': player,
                        'WPM': data['results']['wpm'],
                        'Accuracy': f"{data['results']['accuracy']}%",
                        'Time Taken': f"{data['results']['time_taken']:.2f}s"
                    })
            
            if results:
                st.subheader("🏆 Game Results")
                df = pd.DataFrame(results).sort_values('WPM', ascending=False)
                st.dataframe(df.style.highlight_max(axis=0, color='lightgreen'))
                
                winner = df.iloc[0]['Player']
                st.success(f"🎉 Winner: {winner} with {df.iloc[0]['WPM']} WPM!")
            else:
                st.warning("No results recorded")
            
            if st.button("Return to Home"):
                # Clean up room if empty
                if all(player == st.session_state.player_name for player in players.keys()):
                    del st.session_state.rooms[st.session_state.room_id]
                
                st.session_state.page = 'home'
                st.session_state.game_over = False
                st.session_state.room_id = ''
                st.session_state.player_name = ''
                st.experimental_rerun()

def main():
    # Handle direct room links
    query_params = st.experimental_get_query_params()
    if 'room' in query_params and st.session_state.page == 'home':
        st.session_state.room_id = query_params['room'][0].upper()
        st.session_state.page = 'enter_name'
        st.session_state.room_creator = False
    
    # Page routing
    if st.session_state.page == 'home':
        home_page()
    elif st.session_state.page == 'enter_name':
        enter_name_page()
    elif st.session_state.page == 'room' and st.session_state.room_id in st.session_state.rooms:
        room_page()
    else:
        st.warning("Invalid room or page state")
        if st.button("Return to Home"):
            st.session_state.page = 'home'
            st.experimental_rerun()

if __name__ == "__main__":
    main()
