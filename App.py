import sqlite3
from datetime import datetime
import streamlit as st

# --- DATABASE SETUP & FULL SEASON SEEDING ---
def init_db():
    conn = sqlite3.connect("nfl_pool.db", check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week INTEGER NOT NULL,
            home_team TEXT NOT NULL,
            away_team TEXT NOT NULL,
            is_monday_night BOOLEAN DEFAULT 0,
            winning_team TEXT DEFAULT NULL,
            lock_time TIMESTAMP NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            alias TEXT,
            email TEXT,
            phone TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS picks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            game_id INTEGER,
            picked_team TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(game_id) REFERENCES games(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tiebreakers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            week INTEGER,
            predicted_total_points INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS board_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            date_posted TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Seed initial 2026 NFL regular season schedule if games table is empty
    cursor.execute("SELECT COUNT(*) FROM games")
    if cursor.fetchone()[0] == 0:
        full_season_games = [
            # --- WEEK 1 ---
            (1, "Seattle Seahawks", "New England Patriots", "2026-09-09 20:20:00", False),
            (1, "Los Angeles Rams", "San Francisco 49ers", "2026-09-10 20:35:00", False),
            (1, "Carolina Panthers", "Chicago Bears", "2026-09-13 13:00:00", False),
            (1, "Cincinnati Bengals", "Tampa Bay Buccaneers", "2026-09-13 13:00:00", False),
            (1, "Detroit Lions", "New Orleans Saints", "2026-09-13 13:00:00", False),
            (1, "Houston Texans", "Buffalo Bills", "2026-09-13 13:00:00", False),
            (1, "Indianapolis Colts", "Baltimore Ravens", "2026-09-13 13:00:00", False),
            (1, "Jacksonville Jaguars", "Cleveland Browns", "2026-09-13 13:00:00", False),
            (1, "Pittsburgh Steelers", "Atlanta Falcons", "2026-09-13 13:00:00", False),
            (1, "Tennessee Titans", "New York Jets", "2026-09-13 13:00:00", False),
            (1, "Los Angeles Chargers", "Arizona Cardinals", "2026-09-13 16:25:00", False),
            (1, "Las Vegas Raiders", "Miami Dolphins", "2026-09-13 16:25:00", False),
            (1, "Minnesota Vikings", "Green Bay Packers", "2026-09-13 16:25:00", False),
            (1, "Philadelphia Eagles", "Washington Commanders", "2026-09-13 16:25:00", False),
            (1, "New York Giants", "Dallas Cowboys", "2026-09-13 20:20:00", False),
            (1, "Kansas City Chiefs", "Denver Broncos", "2026-09-14 20:15:00", True), # MNF Tiebreaker

            # --- WEEK 2 ---
            (2, "Detroit Lions", "Buffalo Bills", "2026-09-17 20:15:00", False),
            (2, "Atlanta Falcons", "Carolina Panthers", "2026-09-20 13:00:00", False),
            (2, "Tampa Bay Buccaneers", "Cleveland Browns", "2026-09-20 13:00:00", False),
            (2, "New York Jets", "Green Bay Packers", "2026-09-20 13:00:00", False),
            (2, "Chicago Bears", "Minnesota Vikings", "2026-09-20 13:00:00", False),
            (2, "Baltimore Ravens", "New Orleans Saints", "2026-09-20 13:00:00", False),
            (2, "Tennessee Titans", "Philadelphia Eagles", "2026-09-20 13:00:00", False),
            (2, "New England Patriots", "Pittsburgh Steelers", "2026-09-20 13:00:00", False),
            (2, "Denver Broncos", "Jacksonville Jaguars", "2026-09-20 16:05:00", False),
            (2, "San Francisco 49ers", "Miami Dolphins", "2026-09-20 16:25:00", False),
            (2, "Arizona Cardinals", "Seattle Seahawks", "2026-09-20 16:25:00", False),
            (2, "Dallas Cowboys", "Washington Commanders", "2026-09-20 16:25:00", False),
            (2, "Los Angeles Chargers", "Las Vegas Raiders", "2026-09-20 16:05:00", False),
            (2, "New York Giants", "Los Angeles Rams", "2026-09-21 20:15:00", False),
            (2, "Green Bay Packers", "Atlanta Falcons", "2026-09-21 20:15:00", False),
            (2, "Kansas City Chiefs", "Indianapolis Colts", "2026-09-21 20:15:00", True), # MNF Tiebreaker
        ]
        
        cursor.executemany("""
            INSERT INTO games (week, home_team, away_team, lock_time, is_monday_night)
            VALUES (?, ?, ?, ?, ?)
        """, full_season_games)

    conn.commit()
    conn.close()

init_db()
conn = sqlite3.connect("nfl_pool.db", check_same_thread=False)

# --- STREAMLIT WEB APP INTERFACE ---
st.set_page_config(page_title="NFL Straight-Up Pick 'Em", page_icon="🏈", layout="wide")

st.title("🏈 NFL Straight-Up Pick 'Em Pool")
st.write("Welcome to your private contest dashboard! Manage your picks, check schedules, and track season standings right from your phone.")

menu = st.sidebar.selectbox("Navigation", [
    "📋 Rules & Message Board",
    "🏈 View Schedule & Games",
    "🎯 Submit Weekly Picks",
    "📊 Weekly Pick Summary",
    "🏆 Season Leaderboards",
    "⚔️ Head-to-Head Rivalry",
    "⚙️ Admin: Manage Profiles & Games"
])

# --- 1. RULES & BOARD ---
if menu == "📋 Rules & Message Board":
    st.header("Contest Rules & Board Announcements")
    cursor = conn.cursor()
    cursor.execute("SELECT title, content, date_posted FROM board_messages ORDER BY id DESC")
    messages = cursor.fetchall()
    if not messages:
        st.info("No rules or announcements posted yet.")
    for title, content, date in messages:
        with st.expander(f"📌 {title} ({date})"):
            st.write(content)

# --- 2. VIEW SCHEDULE ---
elif menu == "🏈 View Schedule & Games":
    st.header("NFL Schedule & Game Lock Times")
    week_selected = st.number_input("Select Week", min_value=1, max_value=18, value=1)
    
    cursor = conn.cursor()
    cursor.execute("SELECT id, away_team, home_team, lock_time, is_monday_night, winning_team FROM games WHERE week = ?", (week_selected,))
    games = cursor.fetchall()
    
    if not games:
        st.warning(f"No games found for Week {week_selected}. Use the Admin panel to add or import games.")
    else:
        for g_id, away, home, lock, is_mnf, winner in games:
            mnf_badge = " 🔥 **[Monday Night Tiebreaker]**" if is_mnf else ""
            win_display = f" | **Winner: {winner}**" if winner else " | *Pending*"
            st.markdown(f"**Game ID {g_id}:** {away} @ {home}{mnf_badge}  \n🕒 *Locks:* `{lock}`{win_display}")
            st.divider()

# --- 3. SUBMIT PICKS ---
elif menu == "🎯 Submit Weekly Picks":
    st.header("Submit Your Weekly Straight-Up Picks")
    cursor = conn.cursor()
    cursor.execute("SELECT name, alias FROM users")
    users = cursor.fetchall()
    user_list = [u[1] or u[0] for u in users]
    
    if not user_list:
        st.error("No player profiles found! Please ask an admin to add profiles under the Admin tab first.")
    else:
        selected_user_display = st.selectbox("Select Your Profile", user_list)
        cursor.execute("SELECT id, name FROM users WHERE name = ? OR alias = ?", (selected_user_display, selected_user_display))
        user_row = cursor.fetchone()
        user_id = user_row[0]
        user_name = user_row[1]
        
        week_pick = st.number_input("Select Week to Pick", min_value=1, max_value=18, value=1)
        cursor.execute("SELECT id, away_team, home_team, is_monday_night, lock_time FROM games WHERE week = ?", (week_pick,))
        games = cursor.fetchall()
        
        if not games:
            st.warning(f"No games available for Week {week_pick}.")
        else:
            with st.form("picks_form"):
                pick_data = {}
                mnf_game_id = None
                
                for g_id, away, home, is_mnf, lock_str in games:
                    if is_mnf:
                        mnf_game_id = g_id
                    cursor.execute("SELECT picked_team FROM picks WHERE user_id = ? AND game_id = ?", (user_id, g_id))
                    existing = cursor.fetchone()
                    default_choice = existing[0] if existing else home
                    
                    choice = st.radio(f"{away} @ {home}", [away, home], index=0 if default_choice == away else 1, key=f"game_{g_id}")
                    pick_data[g_id] = choice
                
                mnf_prediction = None
                if mnf_game_id:
                    cursor.execute("SELECT predicted_total_points FROM tiebreakers WHERE user_id = ? AND week = ?", (user_id, week_pick))
                    exist_tb = cursor.fetchone()
                    default_tb = exist_tb[0] if exist_tb else 45
                    mnf_prediction = st.number_input("🎯 Monday Night Total Points Tiebreaker Prediction", min_value=0, max_value=150, value=default_tb)
                
                submitted = st.form_submit_button("Lock In Picks")
                if submitted:
                    now = datetime.now()
                    locked_out = False
                    for g_id, away, home, is_mnf, lock_str in games:
                        if now >= datetime.strptime(lock_str, "%Y-%m-%d %H:%M:%S"):
                            locked_out = True
                            break
                    if locked_out:
                        st.error("❌ Cannot submit: One or more games for this week have already passed their lock deadline.")
                    else:
                        cursor = conn.cursor()
                        for g_id, team in pick_data.items():
                            cursor.execute("DELETE FROM picks WHERE user_id = ? AND game_id = ?", (user_id, g_id))
                            cursor.execute("INSERT INTO picks (user_id, game_id, picked_team) VALUES (?, ?, ?)", (user_id, g_id, team))
                        if mnf_game_id and mnf_prediction is not None:
                            cursor.execute("INSERT OR REPLACE INTO tiebreakers (user_id, week, predicted_total_points) VALUES (?, ?, ?)", (user_id, week_pick, mnf_prediction))
                        conn.commit()
                        st.success(f"✅ Successfully locked in picks for {user_name}!")

# --- 4. WEEKLY PICK SUMMARY ---
elif menu == "📊 Weekly Pick Summary":
    st.header("Weekly Pick Audit Summary")
    week_summary = st.number_input("Select Week to View Summary", min_value=1, max_value=18, value=1)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, alias FROM users")
    users = cursor.fetchall()
    cursor.execute("SELECT id, away_team, home_team, is_monday_night FROM games WHERE week = ?", (week_summary,))
    games = cursor.fetchall()
    
    if not users or not games:
        st.info("Not enough data to display summary for this week.")
    else:
        summary_table = []
        for g_id, away, home, is_mnf in games:
            matchup = f"{away} @ {home}"
            if is_mnf: matchup += " (MNF)"
            row = {"Matchup": matchup}
            for u_id, name, alias in users:
                cursor.execute("SELECT picked_team FROM picks WHERE user_id = ? AND game_id = ?", (u_id, g_id))
                res = cursor.fetchone()
                row[alias or name] = res[0] if res else "-"
            summary_table.append(row)
        st.table(summary_table)
        st.subheader("🎯 Monday Night Tiebreaker Guesses")
        for u_id, name, alias in users:
            cursor.execute("SELECT predicted_total_points FROM tiebreakers WHERE user_id = ? AND week = ?", (u_id, week_summary))
            tb = cursor.fetchone()
            st.write(f"- **{alias or name}:** {tb[0] if tb else 'No guess'} pts")

# --- 5. SEASON LEADERBOARDS ---
elif menu == "🏆 Season Leaderboards":
    st.header("Season-Long Standings")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, alias FROM users")
    users = cursor.fetchall()
    cursor.execute("SELECT DISTINCT week FROM games WHERE winning_team IS NOT NULL")
    weeks = [w[0] for w in cursor.fetchall()]
    
    season_correct = {u[0]: 0 for u in users}
    weekly_wins = {u[0]: 0 for u in users}
    
    for w in weeks:
        cursor.execute("SELECT id, winning_team FROM games WHERE week = ?", (w,))
        games = cursor.fetchall()
        game_dict = {g[0]: g[1] for g in games}
        week_scores = []
        for u_id, _, _ in users:
            wins = 0
            for g_id, winner in game_dict.items():
                if winner is None: continue
                cursor.execute("SELECT picked_team FROM picks WHERE user_id = ? AND game_id = ?", (u_id, g_id))
                res = cursor.fetchone()
                if res and res[0] == winner:
                    wins += 1
                    season_correct[u_id] += 1
            week_scores.append({"user_id": u_id, "wins": wins})
        if week_scores:
            max_w = max(s["wins"] for s in week_scores)
            for s in week_scores:
                if s["wins"] == max_w and max_w > 0:
                    weekly_wins[s["user_id"]] += 1
                    
    user_map = {u[0]: (u[2] or u[1]) for u in users}
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Correct Picks (Total)")
        for uid, count in sorted(season_correct.items(), key=lambda x: x[1], reverse=True):
            st.write(f"**{user_map.get(uid, 'Unknown')}**: {count} correct")
    with col2:
        st.subheader("Weekly Wins (Weeks Won)")
        for uid, count in sorted(weekly_wins.items(), key=lambda x: x[1], reverse=True):
            st.write(f"**{user_map.get(uid, 'Unknown')}**: {count} week(s)")

# --- 6. HEAD TO HEAD ---
elif menu == "⚔️ Head-to-Head Rivalry":
    st.header("Head-to-Head Matchup Breakdown")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, alias FROM users")
    users = cursor.fetchall()
    if len(users) < 2:
        st.warning("You need at least 2 users registered to view head-to-head records.")
    else:
        user_options = { (u[2] or u[1]): u[0] for u in users }
        p1_name = st.selectbox("Player 1", list(user_options.keys()), index=0)
        p2_name = st.selectbox("Player 2", list(user_options.keys()), index=1 if len(user_options) > 1 else 0)
        if p1_name == p2_name:
            st.error("Please select two different players.")
        else:
            p1_id, p2_id = user_options[p1_name], user_options[p2_name]
            cursor.execute("SELECT DISTINCT week FROM games WHERE winning_team IS NOT NULL")
            weeks = [w[0] for w in cursor.fetchall()]
            p1_wk_wins = p2_wk_wins = p1_game_wins = p2_game_wins = 0
            for w in weeks:
                cursor.execute("SELECT id, winning_team FROM games WHERE week = ?", (w,))
                games = cursor.fetchall()
                game_dict = {g[0]: g[1] for g in games}
                p1_score = p2_score = 0
                for g_id, winner in game_dict.items():
                    if not winner: continue
                    cursor.execute("SELECT picked_team FROM picks WHERE user_id = ? AND game_id = ?", (p1_id, g_id))
                    r1 = cursor.fetchone()
                    p1_pick = r1[0] if r1 else None
                    cursor.execute("SELECT picked_team FROM picks WHERE user_id = ? AND game_id = ?", (p2_id, g_id))
                    r2 = cursor.fetchone()
                    p2_pick = r2[0] if r2 else None
                    if p1_pick and p2_pick:
                        if p1_pick == winner and p2_pick != winner: p1_game_wins += 1
                        elif p2_pick == winner and p1_pick != winner: p2_game_wins += 1
                    if p1_pick == winner: p1_score += 1
                    if p2_pick == winner: p2_score += 1
                if p1_score > p2_score: p1_wk_wins += 1
                elif p2_score > p1_score: p2_wk_wins += 1
            st.markdown(f"### {p1_name} vs {p2_name}")
            colA, colB = st.columns(2)
            colA.metric("Weeks Won", f"{p1_wk_wins} - {p2_wk_wins}")
            colB.metric("Head-to-Head Game Battles Won", f"{p1_game_wins} - {p2_game_wins}")

# --- 7. ADMIN TAB (WITH EDIT BUTTON & BULK IMPORTER) ---
elif menu == "⚙️ Admin: Manage Profiles & Games":
    st.header("Admin Dashboard")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Add User Profile", "Post Announcement", "✏️ Edit / Manage Games", "📥 Bulk Import Schedule"])
    
    with tab1:
        with st.form("add_user_form"):
            name = st.text_input("Real Name")
            alias = st.text_input("Alias / Nickname")
            email = st.text_input("Email")
            phone = st.text_input("Phone")
            if st.form_submit_button("Create Profile"):
                try:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO users (name, alias, email, phone) VALUES (?, ?, ?, ?)", (name, alias or None, email or None, phone or None))
                    conn.commit()
                    st.success(f"Profile created for {name}!")
                except sqlite3.IntegrityError:
                    st.error("User already exists.")
                    
    with tab2:
        with st.form("board_form"):
            b_title = st.text_input("Announcement Title")
            b_content = st.text_area("Message Content")
            if st.form_submit_button("Post Announcement"):
                cursor = conn.cursor()
                cursor.execute("INSERT INTO board_messages (title, content) VALUES (?, ?)", (b_title, b_content))
                conn.commit()
                st.success("Announcement posted!")
                
    with tab3:
        st.subheader("Edit or Update an Existing Game")
        with st.form("edit_game_lookup"):
            edit_game_id = st.number_input("Enter Game ID to Edit", min_value=1, value=1)
            fetch_btn = st.form_submit_button("Load Game Details")
            
        cursor = conn.cursor()
        cursor.execute("SELECT week, home_team, away_team, lock_time, is_monday_night, winning_team FROM games WHERE id = ?", (edit_game_id,))
        game_data = cursor.fetchone()
        
        if game_data:
            g_wk, g_home, g_away, g_lock, g_mnf, g_win = game_data
            with st.form("save_edited_game"):
                st.write(f"Editing Game ID: **{edit_game_id}**")
                new_week = st.number_input("Week #", 1, 18, value=g_wk)
                new_home = st.text_input("Home Team", value=g_home)
                new_away = st.text_input("Away Team", value=g_away)
                new_lock = st.text_input("Lock Deadline (YYYY-MM-DD HH:MM:SS)", value=g_lock)
                new_mnf = st.checkbox("Is Monday Night Tiebreaker Game?", value=bool(g_mnf))
                new_winner = st.text_input("Winning Team (Leave blank if pending)", value=g_win if g_win else "")
                
                if st.form_submit_button("Save Changes"):
                    cursor.execute("""
                        UPDATE games SET week = ?, home_team = ?, away_team = ?, lock_time = ?, is_monday_night = ?, winning_team = ?
                        WHERE id = ?
                    """, (new_week, new_home, new_away, new_lock, 1 if new_mnf else 0, new_winner if new_winner else None, edit_game_id))
                    conn.commit()
                    st.success(f"Successfully updated Game ID {edit_game_id}!")
        else:
            st.info("Enter a valid Game ID above and click Load Game Details.")
                
    with tab4:
        st.subheader("Bulk Import Week Schedule via Text")
        st.write("Paste multiple games at once using this format per line: `AwayTeam | HomeTeam | YYYY-MM-DD HH:MM:SS | IsMNF(True/False)`")
        bulk_week = st.number_input("Select Week for Bulk Import", 1, 18, 2, key="bulk_w")
        bulk_text = st.text_area("Paste Schedule Text Here", placeholder="Buffalo Bills | Detroit Lions | 2026-09-17 20:15:00 | False")
        
        if st.button("Process Bulk Import"):
            lines = bulk_text.strip().split("\n")
            cursor = conn.cursor()
            count = 0
            for line in lines:
                if not line.strip(): continue
                parts = [p.strip() for p in line.split("|")]
                if len(parts) == 4:
                    away, home, lock_t, is_m = parts
                    is_mnf_bool = 1 if is_m.lower() == 'true' else 0
                    cursor.execute("""
                        INSERT INTO games (week, home_team, away_team, is_monday_night, lock_time) 
                        VALUES (?, ?, ?, ?, ?)
                    """, (bulk_week, home, away, is_mnf_bool, lock_t))
                    count += 1
            conn.commit()
            st.success(f"Successfully imported {count} games for Week {bulk_week}!")
