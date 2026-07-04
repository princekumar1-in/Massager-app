import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import streamlit.components.v1 as components
from supabase import create_client, Client

# --- PAGE CONFIGURATION & STYLING ---
st.set_page_config(page_title="Prince Messenger Pro", layout="wide", page_icon="💬")

# Custom WhatsApp Style Dark/Light Bubble CSS Injection
st.markdown("""
    <style>
    /* Hide top default Streamlit header elements */
    header, footer, .stDecoration, [data-testid="stStatusWidget"], [data-testid="stHeader"] { 
        visibility: hidden !important; display: none !important; 
    }
    .stApp { margin-top: -60px !important; }
    
    /* Chat Container Formatting */
    .chat-container {
        display: flex;
        flex-direction: column;
        gap: 10px;
        padding: 10px;
        max-height: 550px;
        overflow-y: auto;
        background-color: #f0f2f5;
        border-radius: 10px;
        margin-bottom: 15px;
    }
    
    /* Outgoing Message Bubble (Right Side - Green Style) */
    .msg-sent {
        align-self: flex-end;
        background-color: #d9fdd3;
        color: #111b21;
        padding: 8px 12px;
        border-radius: 8px 0px 8px 8px;
        max-width: 70%;
        box-shadow: 0 1px 0.5px rgba(0,0,0,0.13);
        word-wrap: break-word;
    }
    
    /* Incoming Message Bubble (Left Side - White Style) */
    .msg-received {
        align-self: flex-start;
        background-color: #ffffff;
        color: #111b21;
        padding: 8px 12px;
        border-radius: 0px 8px 8px 8px;
        max-width: 70%;
        box-shadow: 0 1px 0.5px rgba(0,0,0,0.13);
        word-wrap: break-word;
    }
    
    /* Timestamp text layout */
    .msg-time {
        font-size: 0.72em;
        color: #667781;
        text-align: right;
        margin-top: 4px;
        display: block;
    }
    
    .seen-status {
        font-size: 0.75em;
        font-weight: bold;
        color: #53bdeb;
        margin-left: 5px;
    }
    .unseen-status {
        font-size: 0.75em;
        color: #8696a0;
        margin-left: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# Continuous JS injected to vanish unwanted elements
components.html("""
<script>
    function cleanUI() {
        var elements = window.parent.document.querySelectorAll('header, footer, .stDecoration, [data-testid="stStatusWidget"], [data-testid="stHeader"]');
        elements.forEach(function(el) { el.style.setProperty('display', 'none', 'important'); });
    }
    setInterval(cleanUI, 20);
</script>
""", height=0)

# --- INITIAL SYSTEM SESSION STATE ---
if "user_logged" not in st.session_state: st.session_state["user_logged"] = False
if "my_number" not in st.session_state: st.session_state["my_number"] = ""
if "active_chat_with" not in st.session_state: st.session_state["active_chat_with"] = ""

# --- DATABASE CONNECTION ---
SUPABASE_URL = "https://vdfmnzvtsvtnzduilgfo.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZkZm1uenZ0c3Z0bnpkdWlsZ2ZvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODIxMTA0NDMsImV4cCI6MjA5NzY4NjQ0M30.uSM9AM6lYGo8Q9NmpFSgrGR_osnBpXHjkROaCZjWrwg"
BUCKET_NAME = "chat_media"

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"Supabase Connection Broken: {e}")

def get_ist_live_time():
    ist = pytz.timezone('Asia/Kolkata')
    return datetime.now(ist).strftime("%Y-%m-%d %I:%M %p")

# --- FILE UPLOADER UTILITY ---
def upload_media_to_chat(file_obj, file_name):
    try:
        file_bytes = file_obj.getvalue()
        supabase.storage.from_(BUCKET_NAME).upload(
            path=file_name,
            file=file_bytes,
            file_options={"content-type": file_obj.type}
        )
        return supabase.storage.from_(BUCKET_NAME).get_public_url(file_name)
    except Exception as e:
        st.error(f"Media Upload Error: {e}")
        return None

# =======================================================================================
# 1. GATEWAY: REGISTRATION & LOGIN PORTAL
# =======================================================================================
if not st.session_state["user_logged"]:
    st.title("💬 PRINCE MESSENGER NETWORK")
    st.markdown("---")
    
    auth_mode = st.radio("Choose Action Protocol:", ["🔑 Login Account", "📝 Register New Number"], horizontal=True)
    
    num_input = st.text_input("Enter Mobile Number (10 Digits):", max_chars=10).strip()
    pass_input = st.text_input("Enter Password secure block:", type="password")
    
    if auth_mode == "📝 Register New Number":
        if st.button("CREATE MY MESSENGER ACCOUNT", use_container_width=True, type="primary"):
            if len(num_input) < 10 or not num_input.isdigit():
                st.error("Please enter a valid 10-digit mobile number!")
            elif not pass_input:
                st.error("Password string required!")
            else:
                # Check duplication
                chk = supabase.table("chat_users").select("id").eq("mobile_number", num_input).execute()
                if chk.data:
                    st.warning("This number is already registered! Please switch to login mode.")
                else:
                    payload = {
                        "mobile_number": num_input,
                        "password": pass_input,
                        "registered_at": get_ist_live_time()
                    }
                    supabase.table("chat_users").insert(payload).execute()
                    st.success("🎉 Account created successfully! Please log in now.")
                    
    elif auth_mode == "🔑 Login Account":
        if st.button("VERIFY NETWORK ENTRY", use_container_width=True, type="primary"):
            if not num_input or not pass_input:
                st.error("Fields cannot be empty!")
            else:
                user_res = supabase.table("chat_users").select("*").eq("mobile_number", num_input).eq("password", pass_input).execute()
                if user_res.data:
                    st.session_state["user_logged"] = True
                    st.session_state["my_number"] = num_input
                    st.toast(f"Connected as {num_input}")
                    st.rerun()
                else:
                    st.error("❌ Invalid Mobile Number or Password combination!")
    st.stop()

# =======================================================================================
# 2. MAIN HUB: CHAT INTERFACE WINDOW
# =======================================================================================
# Header Band
header_l, header_r = st.columns([8, 2])
with header_l:
    st.subheader(f"🟢 Active Node: {st.session_state['my_number']}")
with header_r:
    if st.button("🔒 LOGOUT", use_container_width=True):
        st.session_state["user_logged"] = False
        st.session_state["my_number"] = ""
        st.session_state["active_chat_with"] = ""
        st.rerun()

st.markdown("---")

# Layout Splitter: Left Sidebar for Account Lookup, Right for Chat Area
sidebar_col, chat_col = st.columns([3, 7])

with sidebar_col:
    st.markdown("#### 🔍 Start New Chat")
    search_num = st.text_input("Enter Teacher/Friend Mobile Number:", max_chars=10, placeholder="9876543210").strip()
    
    if st.button("OPEN CHAT WINDOW", use_container_width=True, type="primary"):
        if search_num == st.session_state["my_number"]:
            st.error("You cannot start a chat with yourself!")
        elif len(search_num) < 10 or not search_num.isdigit():
            st.error("Enter a valid 10-digit number!")
        else:
            # Check system index if user exist
            chk_exist = supabase.table("chat_users").select("id").eq("mobile_number", search_num).execute()
            if chk_exist.data:
                st.session_state["active_chat_with"] = search_num
                st.success(f"Connected to {search_num} node.")
                st.rerun()
            else:
                st.error("❌ System Error: This number does not have an account on this messenger app!")

    st.markdown("---")
    # Show active chat profile target banner
    if st.session_state["active_chat_with"]:
        st.markdown(f"### 👤 Chatting With:\n**{st.session_state['active_chat_with']}**")
    else:
        st.info("Search a registered mobile number above to launch communication link.")

# Right Panel Side: Asli Chat Feed Engine
with chat_col:
    if not st.session_state["active_chat_with"]:
        st.info("👈 Please select or look up a valid target user number from the left bar to read/write logs.")
    else:
        target_person = st.session_state["active_chat_with"]
        my_person = st.session_state["my_number"]
        
        # 🔵 SEEN MARKER UPDATER: Jab mai chat kholu, toh samne waale ke bheje saare messages ko Seen=True kar do
        supabase.table("chat_messages").update({"is_seen": True}).eq("sender_num", target_person).eq("receiver_num", my_person).execute()
        
        # Fetching conversation streams
                # --- Naya Updated Safe Code ---
        msg_feed = supabase.table("chat_messages").select("*").or_(
            f"and(sender_num.eq.{my_person},receiver_num.eq.{target_person}), and(sender_num.eq.{target_person},receiver_num.eq.{my_person})"
        ).order("id").execute()

        
        # Rendering Chat Feed Block
                # =======================================================================================
        # 📱 UPGRADED CLEAN CHAT FEED BLOCK (NO MORE CODE BOXES!)
        # =======================================================================================
        if msg_feed.data:
            for m in msg_feed.data:
                is_me = m["sender_num"] == my_person
                
                # Check status ticks only for my sent messages
                status_tick = " 🔵 Seen" if (is_me and m["is_seen"]) else " ✓✓" if is_me else ""
                time_and_status = f"{m['timestamp']}{status_tick}"
                
                # Media rendering agar photo ya video hai
                if m["media_type"] == "photo":
                    st.image(m["media_url"], width=250)
                elif m["media_type"] == "video":
                    st.video(m["media_url"])
                
                # Right side for my messages, Left side for incoming messages
                if is_me:
                    st.markdown(
                        f"<div style='text-align: right; background-color: #d9fdd3; color: #111b21; "
                        f"padding: 10px; border-radius: 10px 0px 10px 10px; margin-left: 30%; "
                        f"margin-bottom: 10px; box-shadow: 0 1px 0.5px rgba(0,0,0,0.13); word-wrap: break-word;'>"
                        f"<p style='margin:0; font-size:1.05em;'>{m['message_text']}</p>"
                        f"<small style='color: #667781; font-size:0.75em; display:block; margin-top:4px;'>{time_and_status}</small>"
                        f"</div>", 
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f"<div style='text-align: left; background-color: #ffffff; color: #111b21; "
                        f"padding: 10px; border-radius: 0px 10px 10px 10px; margin-right: 30%; "
                        f"margin-bottom: 10px; box-shadow: 0 1px 0.5px rgba(0,0,0,0.13); word-wrap: break-word;'>"
                        f"<p style='margin:0; font-size:1.05em;'>{m['message_text']}</p>"
                        f"<small style='color: #667781; font-size:0.75em; display:block; margin-top:4px;'>{time_and_status}</small>"
                        f"</div>", 
                        unsafe_allow_html=True
                    )
        else:
            st.info("👋 No previous transmission logs. Type a message below to start conversation.")

        
        if msg_feed.data:
            for m in msg_feed.data:
                is_me = m["sender_num"] == my_person
                bubble_class = "msg-sent" if is_me else "msg-received"
                
                # Check status ticks only for my sent messages
                status_tick = ""
                if is_me:
                    status_tick = '<span class="seen-status">🔵 Seen</span>' if m["is_seen"] else '<span class="unseen-status">✓✓</span>'
                
                # Render content according to media type
                media_payload_html = ""
                if m["media_type"] == "photo":
                    media_payload_html = f'<img src="{m["media_url"]}" style="max-width:100%; border-radius:6px; margin-bottom:5px;" /><br>'
                elif m["media_type"] == "video":
                    media_payload_html = f'<video src="{m["media_url"]}" controls style="max-width:100%; border-radius:6px; margin-bottom:5px;"></video><br>'
                
                chat_html_accumulator += f"""
                <div class="{bubble_class}">
                    {media_payload_html}
                    <span>{m["message_text"]}</span>
                    <span class="msg-time">{m["timestamp"]} {status_tick}</span>
                </div>
                """
            st.markdown(chat_html_accumulator, unsafe_allow_html=True)
        else:
            st.markdown("<p style='text-align:center; color:#888888; padding:20px;'>👋 No previous transmissions log. Type a message below to start conversation.</p>", unsafe_allow_html=True)
            
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Bottom Message Writing Layer Box
        st.markdown("#### 📝 Compose Message String")
        with st.form("message_form", clear_on_submit=True):
            user_txt = st.text_area("Type your text message here...", value="", placeholder="Hello, what's up?", label_visibility="collapsed")
            
            # File sharing tool slots
            uploaded_file = st.file_uploader("Attach Photo / Video Proof (Optional):", type=["jpg", "jpeg", "png", "mp4", "mov", "avi"])
            
            send_trigger = st.form_submit_button("🚀 SEND MESSAGE", use_container_width=True)
            
            if send_trigger:
                if not user_txt.strip() and not uploaded_file:
                    st.error("Cannot push empty transmission slot!")
                else:
                    final_url = "None"
                    final_type = "None"
                    
                    # If attachment detected
                    if uploaded_file:
                        f_type = uploaded_file.type.split('/')[0] # 'image' or 'video'
                        ext = uploaded_file.name.split('.')[-1]
                        generated_filename = f"media_{my_person}_{datetime.now().strftime('%H%M%S')}.{ext}"
                        
                        uploaded_url = upload_media_to_chat(uploaded_file, generated_filename)
                        if uploaded_url:
                            final_url = uploaded_url
                            final_type = "photo" if f_type == "image" else "video"
                    
                    # Commit packet record to table data block
                    write_payload = {
                        "sender_num": my_person,
                        "receiver_num": target_person,
                        "message_text": user_txt.strip(),
                        "media_url": final_url,
                        "media_type": final_type,
                        "timestamp": get_ist_live_time(),
                        "is_seen": False
                    }
                    supabase.table("chat_messages").insert(write_payload).execute()
                    st.rerun()

st.markdown("---")
st.markdown("<p style='color:#888888; text-align:center; font-size:0.85em;'>Prince Encrypted Massager Channel Node v1.0</p>", unsafe_allow_html=True)
