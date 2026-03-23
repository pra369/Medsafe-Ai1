import streamlit as st
import pandas as pd
from rapidfuzz import process
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import re
import datetime

# -------- TESSERACT --------
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# -------- DATA --------
df = pd.read_csv("medicines.csv")

# -------- UI --------
st.set_page_config(layout="wide")

st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] {
    background: linear-gradient(to right, #e0f7fa, #e8f5e9);
}
h1 {text-align:center; color:#004d40;}
.stButton>button {
    background: linear-gradient(45deg,#00b09b,#96c93d);
    color:white;
    border-radius:10px;
}
</style>
""", unsafe_allow_html=True)

st.title("💊 MedSafe AI - Medicine Safety Assistant")

# -------- FORMAT --------
def format_data(m):
    return f"""
💊 *{m['Name']}*

{m['Name']} is used to treat {m['UsedFor'].replace(';', ', ')}.

It contains {m['Content']} and is suitable for {m['AgeGroup']}.

⚠️ Side effects include {m['SideEffects']}.

🚫 Allergy: {m['Allergy'] if str(m['Allergy']) != 'nan' else 'No known allergy'}.
"""

# -------- EXPIRY --------
def check_expiry(text):
    patterns = [r'(\d{2}/\d{2})', r'(\d{2}/\d{4})', r'(\d{2}-\d{2})']
    for pat in patterns:
        match = re.search(pat, text)
        if match:
            date = match.group(1).replace("-", "/")
            try:
                if len(date.split("/")[-1]) == 2:
                    exp = datetime.datetime.strptime(date, "%m/%y")
                else:
                    exp = datetime.datetime.strptime(date, "%m/%Y")

                if exp < datetime.datetime.now():
                    return f"❌ Expired: {date}"
                else:
                    return f"✅ Not Expired: {date}"
            except:
                pass
    return "⚠️ Expiry not detected"

# -------- TABS --------
tab1, tab2, tab3, tab4 = st.tabs([
    "📸 OCR",
    "🔍 Search",
    "🩺 Symptoms",
    "🤖 Chatbot"
])

# -------- OCR --------
with tab1:
    st.subheader("Upload Prescription")

    file = st.file_uploader("Upload Image", type=["png","jpg","jpeg"])

    detected = ""

    if file:
        img = Image.open(file)
        st.image(img, width=300)

        img = img.convert('L')
        img = img.resize((img.width*3, img.height*3))
        img = ImageEnhance.Contrast(img).enhance(2)
        img = img.filter(ImageFilter.SHARPEN)

        text = pytesseract.image_to_string(img)
        st.text_area("Extracted Text", text)

        words = re.findall(r'[A-Za-z]+', text.lower())

        best_score = 0
        best_match = ""

        for word in words:
            match = process.extractOne(word, df['Name'])
            if match and match[1] > best_score:
                best_score = match[1]
                best_match = match[0]

        if best_score > 70:
            detected = best_match
            st.success(f"Detected Medicine: {detected}")

            med = df[df['Name']==detected].iloc[0]
            st.markdown(format_data(med))

        st.info(check_expiry(text))

# -------- SEARCH --------
with tab2:
    st.subheader("Search Medicine")

    med_input = st.text_input("Enter Medicine", value="")

    if st.button("Search"):
        if med_input:
            match = process.extractOne(med_input, df['Name'])
            med = df[df['Name']==match[0]].iloc[0]
            st.markdown(format_data(med))

# -------- SYMPTOMS --------
with tab3:
    st.subheader("Search by Symptom")

    symptom = st.text_input("Enter symptom")

    if st.button("Find Medicines"):
        found = False
        for _, row in df.iterrows():
            if symptom.lower() in str(row['UsedFor']).lower():
                st.markdown(format_data(row))
                found = True
        if not found:
            st.info("No medicine found")

# -------- CHATBOT --------
with tab4:
    st.subheader("Chatbot")

    chat = st.text_input("Ask anything")

    if st.button("Ask"):
        q = chat.lower()

        if "fever" in q:
            st.write("Paracetamol is used for fever.")
        elif "headache" in q or "headche" in q:
            st.write("Paracetamol or Ibuprofen is used for headache.")
        elif "cold" in q:
            st.write("Cetirizine is used for cold.")
        else:
            match = process.extractOne(q, df['Name'])
            if match and match[1] > 60:
                med = df[df['Name']==match[0]].iloc[0]
                st.markdown(format_data(med))
            else:
                st.write("Try another query.")

st.markdown("---")
st.caption("🚀 Final Competition Version")
