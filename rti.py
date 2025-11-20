import streamlit as st
import pdfplumber
import io
import os
import re
from datetime import date

# --- 1. FIXED CONTENT CONSTANTS ---
FIXED_MALAYALAM_RTI_REPLY_BODY = """
സൂചനയിലേയ്ക്ക് താങ്കളുടെ ശ്രദ്ധ ക്ഷണിക്കുന്നു. വിവരാവകാശ നിയമം 2005 പ്രകാരം
താങ്കൾ സമർപ്പിച്ചിട്ടുള്ള അപേക്ഷയിൽ ആവശ്യപ്പെട്ട വിവരങ്ങൾ ഈ വകുപ്പിലെ സ്റ്റേറ്റ് പബ്ലിക്
ഇൻഫർമേഷൻ ഓഫീസറുടെ കൈവശമുള്ളവയല്ല.
ആയതിനാൽ, താങ്കൾക്ക് നേരിട്ട് വിവരം
ലഭ്യമാക്കുന്നതിനായി, സൂചനയിലെ അപേക്ഷ വിവരാവകാശ നിയമം ചട്ടം 6 (3) പ്രകാരം
കെ.എസ്.ആർ.റ്റി.സി.
യുടെ കേന്ദ്രകാര്യാലയത്തിലെ സ്റ്റേറ്റ് പബ്ലിക് ഇൻഫർമേഷൻ
ഓഫീസർക്ക് കൈമാറിയിട്ടുണ്ടെന്ന വിവരം അറിയിക്കുന്നു.
"""

FIXED_MALAYALAM_APPELLATE_INFO = """
മേൽ മറുപടിയിൽ ആക്ഷേപമുള്ള പക്ഷം ഈ കത്ത് കൈപ്പറ്റി 30 ദിവസത്തിനകം അപ്പീൽ
അപേക്ഷ സമർപ്പിക്കാവുന്നതാണ്. ഈ വകുപ്പിലെ അപ്പീൽ അധികാരിയുടെ മേൽവിലാസം
ചുവടെ ചേർക്കുന്നു.
അപ്പീൽ അധികാരി
അപ്പീലധികാരി & അഡീഷണൽ സെക്രട്ടറി,
ഗതാഗത വകുപ്പ്, രണ്ടാം നില, അനക്സ് - 1 ബിൽഡിംഗ്,
ഗവ. സെക്രട്ടേറിയറ്റ്, തിരുവനന്തപുരം.
ഫോൺ : 0471 2518284. സ്റ്റേറ്റ് പബ്ലിക് ഇൻഫർമേഷൻ ഓഫീസർ & അണ്ടർ സെക്രട്ടറി.
ഫോൺ നമ്പർ 0471 2518713
"""

FIXED_MALAYALAM_FOOTER_INFO = """
സ്റ്റേറ്റ് പബ്ലിക് ഇൻഫർമേഷൻ ഓഫീസർ, കെ.എസ്.ആർ.റ്റി.സി. കേന്ദ്രകാര്യാലയം,
തിരുവനന്തപുരം (സൂചനയിലെ അപേക്ഷ സഹിതം-വിവരാവകാശ നിയമം 2005
പ്രകാരം സമയപരിധിക്കുള്ളിൽ അപേക്ഷകന് നേരിട്ട് വിവരം ലഭ്യമാക്കുന്നതിനായി).
"""

# --- 2. PAGE CONFIGURATION & THEME ---
st.set_page_config(
    page_title="RTI Automation Unit", 
    layout="wide",
    initial_sidebar_state="expanded"
)

custom_css = """
<style>
[data-testid="stAppViewContainer"] > .main {
    background: linear-gradient(180deg, #f0f2f6 0%, #ffffff 100%);
}
[data-testid="stHeader"] {
    background-color: #003366;
}
h1 {
    color: #003366 !important;
    border-bottom: 2px solid #ff9900;
    padding-bottom: 10px;
}
h2, h3 {
    color: #004080 !important;
}
.stButton button {
    background-color: #003366;
    color: white;
    font-weight: bold;
    border-radius: 8px;
    padding: 10px 24px;
}
.stButton button:hover {
    background-color: #004080;
    color: white;
}
[data-testid="stSidebar"] {
    background-color: #eef2f5;
    border-right: 1px solid #d1d5db;
}
.stAlert {
    border-left: 5px solid #ff9900;
}
/* DISCLAIMER: Fixed Red Box in Corner */
.fixed-disclaimer {
    position: fixed;
    bottom: 0px;
    right: 0px;
    background-color: rgba(255, 0, 0, 0.9); /* Red background, slightly transparent */
    color: white;
    padding: 5px 10px;
    font-size: 14px;
    font-weight: bold;
    border-top-left-radius: 8px;
    z-index: 1000; /* Ensure it stays on top */
    box-shadow: 0 -2px 5px rgba(0,0,0,0.2);
    animation: pulse 1.5s infinite;
}
@keyframes pulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.02); }
    100% { transform: scale(1); }
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)
# --- ADDED: RENDER THE DISCLAIMER HTML ---
st.markdown('<div class="fixed-disclaimer">Verify before submission</div>', unsafe_allow_html=True)
# ------------------------------------------

# --- 3. GEMINI API SETUP (Mock/Client) ---
try:
    from google import genai
    client = genai.Client() 
    GEMINI_MODEL = "gemini-2.5-flash"
    if not os.getenv("GEMINI_API_KEY"):
        raise ImportError("Using Mock")
except (ImportError, Exception):
    class MockClient:
        class MockModels:
            def generate_content(self, model, contents):
                class MockResponse:
                    def __init__(self, text): self.text = text
                # Simple Mock Logic
                if "translate" in contents.lower() and "name" in contents.lower(): 
                    return MockResponse("സ്വാതി")
                if "translate" in contents.lower() and "english" in contents.lower(): 
                    return MockResponse("[Translated Content to English: This is a mock translation of the file note/letter.]")
                return MockResponse("AI Content Generated")
        models = MockModels()
    client = MockClient()
    GEMINI_MODEL = "mock-model"

# --- 4. EXTRACTION FUNCTIONS ---
def extract_text_from_pdf_buffer(pdf_buffer):
    try:
        with pdfplumber.open(pdf_buffer) as pdf:
            if pdf.pages:
                return pdf.pages[0].extract_text() or ""
    except Exception:
        return ""
    return ""

def detect_language(text):
    malayalam_char_count = sum(1 for char in text if '\u0d00' <= char <= '\u0d7f')
    return 'Malayalam' if malayalam_char_count > 10 else 'English'

def extract_applicant_name(text):
    match = re.search(r'(Name\s*[:\.]?\s*)(.*?)\n', text, re.IGNORECASE)
    if match: return match.group(2).strip()
    from_match = re.search(r'(From|പ്രേഷകൻ)\s*[:,-]?\s*\n(.*?)\n', text, re.IGNORECASE)
    if from_match: return from_match.group(2).strip()
    return "Applicant Name Not Found"

def extract_applicant_address(text, name):
    cleaned_text = re.sub(r'^(TRANS-A2.*|File Number.*|GOVERNMENT OF KERALA|കേരള സർക്കാർ)', '', text, flags=re.IGNORECASE | re.MULTILINE).strip()
    stop_labels = r'(Citizenship|BPL|RTI Submitted On|Sir,|വിഷയം|Subject|Email|Mobile)'
    match = re.search(r'(Address|വിലാസം)\s*[:\.]?\s*(.*?)(?:' + stop_labels + r'|\Z)', cleaned_text, re.DOTALL | re.IGNORECASE)
    if match:
        addr = match.group(2).strip()
        if len(addr) > 5: return addr
    lines = cleaned_text.split('\n')
    address_lines = []
    capture = False
    for line in lines:
        if name in line:
            capture = True
            continue
        if capture:
            if any(x in line.lower() for x in ['mobile', 'email', 'to', 'sir', 'subject', 'വിഷയം']) or len(address_lines) > 6:
                break
            if len(line.strip()) > 2:
                address_lines.append(line.strip())
    if address_lines: return "\n".join(address_lines)
    return "Address Not Found"

def extract_rti_data(text):
    date_match = re.search(r'(\d{2}[-/.]\d{2}[-/.]\d{4})', text)
    rti_date = date_match.group(1).replace('.', '-') if date_match else "Date Not Found"
    num_match = re.search(r'([A-Z0-9-/]+\/\d{4})', text)
    rti_num = num_match.group(1) if num_match else "[RTI File No.]"
    return rti_date, rti_num

def translate_text_general(text, target_lang="Malayalam"):
    """General purpose translation function (used for long content translation)."""
    if not text: return ""
    prompt = f"Translate the following text to {target_lang} (Official/Formal Style): {text}"
    try:
        res = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
        return res.text.strip()
    except:
        return "[Translation Error]"

def translate_name_clean(name):
    """Specific function for translating names without extra text."""
    if not name or "Not Found" in name: return "***"
    if sum(1 for char in name if '\u0d00' <= char <= '\u0d7f') > 5: return name
    
    prompt = f"Translate the name '{name}' to Malayalam. Return only the translated name and nothing else."
    try:
        res = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
        return res.text.strip().replace('"', '').replace("'", '')
    except:
        return "[Name Translation Error]"


# --- 5. GENERATION FUNCTIONS ---
def generate_internal_note(malayalam_name):
    subject = f"വിഷയം:- ഗതാഗത വകുപ്പ് - വിവരാവകാശ നിയമം, 2005 പ്രകാരം വിവരങ്ങള്‍ ലഭ്യമാക്കണമെന്ന് ആവശ്യപ്പെട്ടുകൊണ്ട് **ശ്രീ. {malayalam_name}** സമർപ്പിച്ച അപേക്ഷ - സംബന്ധിച്ച്."
    body = f"""വിവരാവകാശ നിയമം, 2005 പ്രകാരം **ശ്രീ. {malayalam_name}** സമർപ്പിച്ച അപേക്ഷ നടപ്പു ഫയല്‍ 1-3 -ൽ  കണ്ടാലും. വിവരാവകാശ അപേക്ഷയിൽ ആവശ്യപ്പെട്ട വിശദാംശങ്ങള്‍ ഈ വകുപ്പിലെ SPIO-യുടെ കൈവശമുള്ളവയല്ലാത്തതിനാൽ, വിവരാവകാശ നിയമം ചട്ടം 6(3) പ്രകാരം സമയപരിധിക്കുള്ളിൽ അപേക്ഷകന് മറുപടി നൽകുന്നതിനായി അപേക്ഷ കെ.എസ്.ആര്‍.റ്റി.സി.യിലെ SPIO-യ്ക്ക് കൈമാറി അക്കാര്യം അപേക്ഷകനെ അറിയിക്കാവുന്നതാണ്.
ഉത്തരവിന് വിധേയമായി കരട് കത്ത് അംഗീകാരത്തിനായി സമർപ്പിക്കുന്നു."""
    return f"#### **കരട് കുറിപ്പ് (Internal Note)**\n\n{subject}\n\n{body}"

def generate_reply_letter(orig_name, orig_address, rti_date, rti_num, lang):
    receiver_name = orig_name.strip()
    if not receiver_name.endswith(','): receiver_name += ","
    receiver_addr = orig_address.strip()
    receiver_content = f"{receiver_name}\n{receiver_addr}"
    sender_designation = "സ്റ്റേറ്റ് പബ്ലിക് ഇൻഫർമേഷൻ ഓഫീസർ & അണ്ടർ സെക്രട്ടറി"
    rti_subject = "ഗതാഗത വകുപ്പ് - വിവരാവകാശ നിയമം 2005 പ്രകാരം സമർപ്പിച്ച അപേക്ഷ മറുപടി - സംബന്ധിച്ച്."
    reference_line = f"താങ്കരുടെ {rti_date}-ലെ {rti_num} നമ്പർ വിവരാവകാശ അപേക്ഷ."
    signatory = "[ഒപ്പിടുന്ന ഉദ്യോഗസ്ഥൻ്റെ പേരും സ്ഥാനപ്പേരും]"

    return f"""
**കേരള സർക്കാർ / GOVERNMENT OF KERALA**
**ഗതാഗത (എ) വകുപ്പ് / TRANSPORT (A) DEPARTMENT**

{date.today().strftime("%d-%m-%Y")}, തിരുവനന്തപുരം / Thiruvananthapuram

---
**പ്രേഷകൻ (From),**
{sender_designation}.

**സ്വീകർത്താവ് (To),**
{receiver_content}

---

**വിഷയം (Subject):-** {rti_subject}
**സൂചന (Reference):-** {reference_line}

---
#### **മറുപടി (Reply Body)**

{FIXED_MALAYALAM_RTI_REPLY_BODY.strip()}

---
{FIXED_MALAYALAM_APPELLATE_INFO.strip()}

---
**വിശ്വസ്തതയോടെ,**

[Signed by]
{signatory} 

---
**പകർപ്പ് (Copy)**
{FIXED_MALAYALAM_FOOTER_INFO.strip()}
"""

# --- 6. MAIN APP UI ---
st.title("🏛️ RTI Automation") 

with st.sidebar:
    st.header("Processing Status")
    uploaded_file = st.file_uploader("Upload RTI PDF", type="pdf")
    if uploaded_file:
        st.success("PDF Uploaded")
        process_btn = st.button("🚀 Process Application", type="primary")
    else:
        st.info("Awaiting File...")

if uploaded_file and 'process_btn' in locals() and process_btn:
    with st.spinner("Extracting Data & Generating Drafts..."):
        page_text = extract_text_from_pdf_buffer(uploaded_file)
        if page_text:
            lang = detect_language(page_text)
            name = extract_applicant_name(page_text)
            address = extract_applicant_address(page_text, name) 
            r_date, r_num = extract_rti_data(page_text)
            
            mal_name = translate_name_clean(name) 
            
            internal_note = generate_internal_note(mal_name)
            reply_letter = generate_reply_letter(name, address, r_date, r_num, lang)
            
            st.session_state['result_note'] = internal_note
            st.session_state['result_letter'] = reply_letter
            st.session_state['meta_name'] = name
            st.session_state['meta_num'] = r_num
            st.session_state['processed'] = True
            
            st.session_state['trans_note'] = None
            st.session_state['trans_letter'] = None
        else:
            st.error("Could not read text from PDF.")

if st.session_state.get('processed'):
    st.divider()
    
    # --- FILENAME CALCULATION ---
    raw_name = st.session_state.get('meta_name', 'Applicant') 
    safe_name = re.sub(r'[^\w\s\-\.]', '', raw_name).strip()
    display_filename = f"RTI by {safe_name} -KSRTC-reg"
    download_filename = f"{display_filename}.txt"
    # ----------------------------

    c1, c2, c3 = st.columns(3)
    with c1: st.info(f"**Applicant:** {st.session_state.get('meta_name')}")
    with c2: st.info(f"**RTI Number:** {st.session_state.get('meta_num')}")
    with c3: st.success(f"**File:** {display_filename}") 

    tab1, tab2 = st.tabs(["📝 Internal Note (File)", "✉️ Reply Letter (Draft)"])
    
    # --- TAB 1: INTERNAL NOTE & TRANSLATION ---
    with tab1:
        st.subheader("Office Note (Malayalam)")
        st.text_area("Content for E-Office Note:", value=st.session_state['result_note'], height=400)
        
        st.markdown("---")
        # Removed 🇬🇧 emoji
        if st.button("English Translation", key="btn_trans_note"):
            with st.spinner("Translating Note..."):
                st.session_state['trans_note'] = translate_text_general(st.session_state['result_note'], "English")
        
        if st.session_state.get('trans_note'):
            st.info("**English Translation:**")
            st.write(st.session_state['trans_note'])
        
    # --- TAB 2: REPLY LETTER & TRANSLATION ---
    with tab2:
        st.subheader("Draft Reply to Applicant")
        st.markdown(st.session_state['result_letter'])
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.download_button(
                label="⬇️ Download Reply Letter (.txt)",
                data=st.session_state['result_letter'],
                file_name=download_filename,
                mime="text/plain"
            )
            
        with col_b:
             # Removed 🇬🇧 emoji
             if st.button("English Translation", key="btn_trans_letter"):
                 with st.spinner("Translating Letter..."):
                     st.session_state['trans_letter'] = translate_text_general(st.session_state['result_letter'], "English")
        
        if st.session_state.get('trans_letter'):
            st.markdown("---")
            st.info("**English Translation:**")
            st.write(st.session_state['trans_letter'])

st.markdown("---")
st.caption("RTI Automation System | Designed for Transport Dept | Section 6(3) Transfers Only | **Designed by Prince P Rajan**")
