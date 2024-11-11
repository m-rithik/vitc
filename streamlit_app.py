import streamlit as st
import re
import gspread
from google.oauth2.service_account import Credentials
print (st.secrets);
# Authenticate and connect to Google Sheets
def get_google_sheet():
    # Access the credentials from Streamlit secrets
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    client = gspread.authorize(credentials)
    sheet = client.open("1JAAE6abFQ1T-SsO_FJTygDsM85kjvPrAC9l15PvcEwU").sheet1
    return sheet

# Function to read teacher names and image URLs from the text file
def load_teachers(file):
    teachers = []
    with open(file, 'r') as f:
        lines = f.readlines()
        teacher_name = None
        image_url = None
        for line in lines:
            if line.startswith("Name:"):
                teacher_name = line.strip().replace("Name: ", "")
            elif line.startswith("Image:"):
                image_url = line.strip().replace("Image: ", "")
                if teacher_name and image_url:
                    teachers.append((teacher_name, image_url))
                    teacher_name, image_url = None, None  # Reset for the next entry
    return teachers

# Clean teacher names for search comparison
def clean_name(name):
    return re.sub(r'^(dr|mr|ms)\s+', '', name.strip().lower())

# Sanitize teacher name for use as a unique key
def sanitize_name_for_key(name, idx):
    return re.sub(r'\W+', '_', name.strip().lower()) + f"_{idx}"  # Append index to ensure uniqueness

# Load teachers data
teachers = load_teachers('vitc.txt')
teachers_cleaned = [clean_name(teacher[0]) for teacher in teachers]

# Set up Streamlit UI
st.title("VIT Chennai Teacher Review")
st.header("Search for a Teacher")

# Search bar (case insensitive and ignore titles like Dr, Mr, Ms)
search_query = st.text_input("Search for a teacher:")

# Find matching teachers based on the search query
if search_query:
    search_query_cleaned = clean_name(search_query)
    matches = [teachers[i] for i in range(len(teachers_cleaned)) if search_query_cleaned in teachers_cleaned[i]]
else:
    matches = []

# Load Google Sheet
sheet = get_google_sheet()

# Function to calculate overall rating (based on existing ratings)
def calculate_overall_rating(teaching, leniency, correction, da_quiz):
    total = teaching + leniency + correction + da_quiz
    return total / 4

# Display the search results
if matches:
    st.write("Teachers found:")
    for idx, (teacher, image_url) in enumerate(matches):
        col1, col2 = st.columns([2, 1])  # Create two columns: one for the name, one for the image

        with col1:
            st.subheader(f"Teacher: {teacher}")

            # User input section (ratings for the teacher)
            st.markdown("### **Rate the Teacher**")
            teaching = st.slider("Teaching", 0, 10, key=f"teaching_{idx}")
            leniency = st.slider("Leniency", 0, 10, key=f"leniency_{idx}")
            correction = st.slider("Correction", 0, 10, key=f"correction_{idx}")
            da_quiz = st.slider("DA/Quiz", 0, 10, key=f"da_quiz_{idx}")

            # Display the teacher's image in a smaller size
            with col2:
                try:
                    st.image(image_url, caption=f"{teacher}'s Picture", width=150)
                except Exception as e:
                    st.error(f"Error displaying image: {e}")

            # Submit button to save the review
            submit_button = st.button(f"Submit Review for {teacher}", key=f"submit_{idx}")
            
            if submit_button:
                # Calculate the overall rating
                overall_rating = calculate_overall_rating(teaching, leniency, correction, da_quiz)

                # Write the ratings and overall rating to Google Sheets
                data_to_insert = [teacher, teaching, leniency, correction, da_quiz, overall_rating]
                try:
                    sheet.append_row(data_to_insert)
                    st.success(f"Review for {teacher} submitted successfully!")
                except Exception as e:
                    st.error(f"Failed to submit review: {e}")

else:
    st.write("No teachers found.")

# Footer message
st.markdown(
    """
    <hr style="margin-top: 3rem;">
    <div style="text-align: center; color: grey; font-size: 1.2rem;">
        Please contribute with reviews
    </div>
    """,
    unsafe_allow_html=True
)
