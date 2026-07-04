import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import streamlit.components.v1 as components
from supabase import create_client, Client

# --- PAGE CONFIGURATION & STYLING ---
st.set_page_config(page_title="Prince Messenger Pro", layout="wide", page_icon="💬")

# Clean Dynamic Interface Overrides
st.markdown("""
    <style>
    header, footer, .stDecoration, [data-testid="stStatusWidget"], [data-testid="stHeader"] { 
        visibility: hidden !important; display: none !important; 
    }
    .stApp { margin-top: -60px !important; }
    
    /* Responsive Row Lock Logic */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        justify-content: space-between !important;
        gap: 5px !important;
    }
    div[data-testid="stHorizontalBlock"] > div {
        flex: 1 1 0% !important;
        min-width: 0 !important;
    }
    div[data-testid="stHorizontalBlock"] button {
        padding: 5px 2px !important;
        font-size: 0.85em !important;
        white-space: nowrap !important;
    }
    
    /* WhatsApp Chat List Item Styles */
    .chat-list-btn {
        width: 100%;
        text-align: left !important;
        padding: 12px !important;
        border-radius: 8px !important;
        margin-bottom: 5px !important;
    }
    </style>
""", unsafe_allow_html=True)

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
if "my_username" not in st.session_state: st.session_state["my_username"] = ""
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

# Mapping dictionary helpers to instantly swap numbers for names
@st.cache_data(ttl=5)
def get_user_map():
    try:
        res = supabase.table("chat_users").select("mobile_number, username").execute()
        if res.data:
            return {row["mobile_number"]: row["username"] for row in res.data}
    except Exception:
        pass
    return {}

user_map = get_user_map()

# =======================================================================================
# 1. GATEWAY: REGISTRATION & LOGIN PORTAL (WITH USERNAME ENGINE)
# =======================================================================================
if not st.session_state["user_logged"]:
    st.title("🔒 SECURED MESSENGER NETWORK")
    st.markdown("---")
    
    auth_mode = st.radio("Choose Action Protocol:", ["🔑 Login Account", "📝 Register New Number"], horizontal=True)
    
    num_input = st.text_input("Enter Mobile Number (10 Digits):", max_chars=10).strip()
    
    if auth_mode == "📝 Register New Number":
        name_input = st.text_input("Enter Your Name (Username):", placeholder="e.g., Prakash Sir").strip()
        
    pass_input = st.text_input("Enter Password:", type="password")
    
    if auth_mode == "📝 Register New Number":
        if st.button("CREATE MY MESSENGER ACCOUNT", use_container_width=True, type="primary"):
            if len(num_input) < 10 or not num_input.isdigit():
                st.error("Please enter a valid 10-digit mobile number!")
            elif not name_input:
                st.error("Username display name field required!")
            elif not pass_input:
                st.error("Password string required!")
            else:
                chk = supabase.table("chat_users").select("id").eq("mobile_number", num_input).execute()
                if chk.data:
                    st.warning("This number is already registered! Please switch to login mode.")
                else:
                    payload = {
                        "mobile_number": num_input,
                        "username": name_input,
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
                    st.session_state["my_username"] = user_res.data[0].get("username", num_input)
                    st.toast(f"Welcome back, {st.session_state['my_username']}!")
                    st.rerun()
                else:
                    st.error("❌ Invalid Mobile Number or Password combination!")
    st.stop()

# =======================================================================================
# 2. MAIN HUB: PRO-LEVEL COMPACT PROFILE MANAGEMENT LAYOUT
# =======================================================================================
with st.expander(f"👤 Profile Settings ({st.session_state['my_username']})", expanded=False):
    col_prof_info, col_prof_btn = st.columns([8, 2])
    with col_prof_info:
        st.markdown(f"**Linked Number:** `{st.session_state['my_number']}`")
    with col_prof_btn:
        if st.button("🔒 LOGOUT NETWORK", use_container_width=True, type="primary"):
            st.session_state["user_logged"] = False
            st.session_state["my_number"] = ""
            st.session_state["my_username"] = ""
            st.session_state["active_chat_with"] = ""
            st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

sidebar_col, chat_col = st.columns([3, 7])

# =======================================================================================
# LEFT PANEL: DYNAMIC INTERACTIVE WHATSAPP-STYLE CLICKABLE CHAT RECENT LIST
# =======================================================================================
with sidebar_col:
    # ➕ Add New Chat Feature Trigger logo UI
    with st.expander("💬 Add New Chat Connection", expanded=False):
        search_num = st.text_input("Enter Mobile Number Target:", max_chars=10, placeholder="9876543210").strip()
        if st.button("CONNECT FRESH STREAM", use_container_width=True, type="primary"):
            if search_num == st.session_state["my_number"]:
                st.error("You cannot chat with yourself!")
            elif len(search_num) < 10 or not search_num.isdigit():
                st.error("Enter a valid 10-digit number!")
            else:
                chk_exist = supabase.table("chat_users").select("id").eq("mobile_number", search_num).execute()
                if chk_exist.data:
                    st.session_state["active_chat_with"] = search_num
                    st.success("Chat stream generated!")
                    st.rerun()
                else:
                    st.error("❌ Account not found on server pools!")
                    
    st.markdown("### 📱 Recent Transmissions")
    
    # Fetch list of numbers I have interacted with
    my_num = st.session_state["my_number"]
    interacted_res = supabase.table("chat_messages").select("sender_num, receiver_num").or_(
        f"sender_num.eq.{my_num},receiver_num.eq.{my_num}"
    ).execute()
    
    unique_contacts = set()
    if interacted_res.data:
        for row in interacted_res.data:
            if row["sender_num"] != my_num: unique_contacts.add(row["sender_num"])
            if row["receiver_num"] != my_num: unique_contacts.add(row["receiver_num"])
            
    # Dynamic Render Button Hub (NO MORE DROPDOWN!)
    if unique_contacts:
        for contact_number in sorted(list(unique_contacts)):
            contact_name = user_map.get(contact_number, contact_number)
            # Create a stylized button for each contact row chat channel slot
            if st.button(f"👤 {contact_name}", key=f"contact_{contact_number}", use_container_width=True):
                st.session_state["active_chat_with"] = contact_number
                st.rerun()
    else:
        st.caption("No conversations recorded yet. Tap top icon to add new node link.")

# =======================================================================================
# RIGHT PANEL: DYNAMIC NAME DISPLAY CHAT BOX ENGINE
# =======================================================================================
with chat_col:
    if not st.session_state["active_chat_with"]:
        st.info("👈 Please tap a contact from the recent feed list to open the chat window dashboard.")
    else:
        target_person = st.session_state["active_chat_with"]
        my_person = st.session_state["my_number"]
        
        # Display corresponding name instead of raw phone string digit array strings
        target_display_name = user_map.get(target_person, target_person)
        st.markdown(f"## 💬 {target_display_name}")
        st.markdown("---")
        
        # Mark Incoming messages as Read 
        supabase.table("chat_messages").update({"is_seen": True}).eq("sender_num", target_person).eq("receiver_num", my_person).execute()
        
        # Fetching conversation streams data matrices blocks
        res_sent = supabase.table("chat_messages").select("*").eq("sender_num", my_person).eq("receiver_num", target_person).execute()
        res_rcvd = supabase.table("chat_messages").select("*").eq("sender_num", target_person).eq("receiver_num", my_person).execute()
        
        combined_data = (res_sent.data or []) + (res_rcvd.data or [])
        combined_data = sorted(combined_data, key=lambda x: x['id'])
        
        if combined_data:
            for m in combined_data:
                is_me = m["sender_num"] == my_person
                status_tick = " 🔵 Seen" if (is_me and m["is_seen"]) else " ✓✓" if is_me else ""
                time_and_status = f"{m['timestamp']}{status_tick}"
                
                if m["media_type"] == "photo":
                    st.image(m["media_url"], width=250)
                elif m["media_type"] == "video":
                    st.video(m["media_url"])
                
                msg_text = m['message_text']
                
                if is_me:
                    bubble_html = (
                        f"<div style='background-color: #d9fdd3; color: #111b21; "
                        f"padding: 10px; border-radius: 10px 0px 10px 10px; margin-left: 30%; "
                        f"margin-bottom: 10px; box-shadow: 0 1px 0.5px rgba(0,0,0,0.13); word-wrap: break-word;'>"
                        f"<p style='margin:0; font-size:1.05em; text-align: left;'>{msg_text}</p>"
                        f"<small style='color: #667781; font-size:0.75em; display:block; text-align: right; margin-top:4px;'>{time_and_status}</small>"
                        f"</div>"
                    )
                    st.markdown(bubble_html, unsafe_allow_html=True)
                else:
                    bubble_html = (
                        f"<div style='background-color: #ffffff; color: #111b21; "
                        f"padding: 10px; border-radius: 0px 10px 10px 10px; margin-right: 30%; "
                        f"margin-bottom: 10px; box-shadow: 0 1px 0.5px rgba(0,0,0,0.13); word-wrap: break-word;'>"
                        f"<p style='margin:0; font-size:1.05em; text-align: left;'>{msg_text}</p>"
                        f"<small style='color: #667781; font-size:0.75em; display:block; text-align: right; margin-top:4px;'>{time_and_status}</small>"
                        f"</div>"
                    )
                    st.markdown(bubble_html, unsafe_allow_html=True)
        else:
            st.info("👋 No previous transmission logs. Type a message below to start conversation.")
            
        st.markdown("---")
        
        # Bottom Compose Engine Form Box
        st.markdown("#### 📝 Compose Message String")
        with st.form("message_form", clear_on_submit=True):
            user_txt = st.text_area("Type your text message here...", value="", placeholder="Hello, what's up?", label_visibility="collapsed")
            uploaded_file = st.file_uploader("Attach Photo / Video Proof (Optional):", type=["jpg", "jpeg", "png", "mp4", "mov", "avi"])
            
            send_trigger = st.form_submit_button("🚀 SEND MESSAGE", use_container_width=True)
            
            if send_trigger:
                if not user_txt.strip() and not uploaded_file:
                    st.error("Cannot push empty transmission slot!")
                else:
                    final_url = "None"
                    final_type = "None"
                    
                    if uploaded_file:
                        f_type = uploaded_file.type.split('/')[0]
                        ext = uploaded_file.name.split('.')[-1]
                        generated_filename = f"media_{my_person}_{datetime.now().strftime('%H%M%S')}.{ext}"
                        
                        uploaded_url = upload_media_to_chat(uploaded_file, generated_filename)
                        if uploaded_url:
                            final_url = uploaded_url
                            final_type = "photo" if f_type == "image" else "video"
                    
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
st.markdown("<p style='color:#888888; text-align:center; font-size:0.85em;'>Prince Encrypted Messenger Channel Node v3.0</p>", unsafe_allow_html=True)
