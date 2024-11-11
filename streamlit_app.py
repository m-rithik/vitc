import streamlit as st
import re
import gspread
from google.oauth2.service_account import Credentials

# Function to get Google Sheets connection
def get_google_sheet():
    try:
        credentials = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        client = gspread.authorize(credentials)
        sheet = client.open_by_key("1JAAE6abFQ1T-SsO_FJTygDsM85kjvPrAC9l15PvcEwU").sheet1
        return sheet
    except Exception as e:
        st.error(f"Failed to connect to Google Sheets: {str(e)}")
        return None

# Function to load teacher data from a file
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
                    teacher_name, image_url = None, None  # Reset for next entry
    return teachers

# Function to clean teacher name for search comparison
def clean_name(name):
    return re.sub(r'^(dr|mr|ms)\s+', '', name.strip().lower())

# Function to calculate overall rating
def calculate_overall_rating(teaching, leniency, correction, da_quiz):
    total = teaching + leniency + correction + da_quiz
    return total / 4

# Function to get all reviews from Google Sheets (do not cache sheet, only data)
def get_all_reviews(sheet):
    if sheet:
        return sheet.get_all_records()  # Fetch all records from the sheet
    return []

# Function to get the number of reviews for a teacher
def get_number_of_reviews(records, teacher_name):
    # Count how many reviews the teacher has received based on the 'Teacher' column
    review_count = sum(1 for record in records if record['Teacher'] == teacher_name)
    return review_count

# Load teachers data from the file
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

# Fetch all records (no caching here as sheet object is mutable)
records = get_all_reviews(sheet)

# Display search results
if matches:
    st.write("Teachers found:")
    for idx, (teacher, image_url) in enumerate(matches):
        col1, col2 = st.columns([2, 1])  # Create two columns: one for the name, one for the image

        with col1:
            st.subheader(f"Teacher: {teacher}")

            # Get the number of reviews for the teacher
            review_count = get_number_of_reviews(records, teacher)
            st.write(f"Number of reviews: {review_count}")

            # User input section (ratings for the teacher)
            st.markdown("### **Rate the Teacher**")
            teaching = st.slider("Teaching", 0, 10, key=f"teaching_{idx}")
            leniency = st.slider("Leniency", 0, 10, key=f"leniency_{idx}")
            correction = st.slider("Correction", 0, 10, key=f"correction_{idx}")
            da_quiz = st.slider("DA/Quiz", 0, 10, key=f"da_quiz_{idx}")

            # Display the teacher's image
            with col2:
                try:
                    st.image(image_url, caption=f"{teacher}'s Picture", width=150)
                except Exception as e:
                    st.error(f"Error displaying image: {e}")

            # Submit button to save the review
            submit_button = st.button(f"Submit Review for {teacher}", key=f"submit_{idx}")
            
            if submit_button:
                # Check if the teacher already has a review in this session
                if review_count == 0:  # Prevent multiple submissions for the same teacher
                    # Calculate the overall rating
                    overall_rating = calculate_overall_rating(teaching, leniency, correction, da_quiz)

                    # Prepare the data to insert
                    data_to_insert = [teacher, teaching, leniency, correction, da_quiz, overall_rating]

                    try:
                        # Append the review data to Google Sheets
                        sheet.append_row(data_to_insert)
                        st.success(f"Review for {teacher} submitted successfully!")
                    except Exception as e:
                        st.error(f"Failed to submit review: {e}")
                else:
                    st.warning(f"Review for {teacher} has already been submitted. You can only submit one review per teacher.")
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
