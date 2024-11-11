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
def calculate_overall_rating(reviews):
    if reviews:
        return sum(reviews) / len(reviews)
    return 0

# Function to get all reviews from Google Sheets (do not cache sheet, only data)
def get_all_reviews(sheet):
    if sheet:
        return sheet.get_all_records()  # Fetch all records from the sheet
    return []

# Function to get the reviews for a teacher
def get_teacher_reviews(records, teacher_name):
    # Filter reviews for the teacher
    reviews = [record for record in records if clean_name(record.get('Teacher ', '').strip()) == teacher_name]
    return reviews

# Load teachers data from the file
teachers = load_teachers('vitc.txt')
teachers_cleaned = [clean_name(teacher[0]) for teacher in teachers]

# Set up Streamlit UI
st.title("VIT Chennai Teacher Review")
st.header("Search for a Teacher")

# Create a search dropdown for teachers
search_query = st.selectbox("Select a teacher:", options=[teacher[0] for teacher in teachers], help="Start typing to find a teacher")

# Load Google Sheet
sheet = get_google_sheet()

# Fetch all records (no caching here as sheet object is mutable)
records = get_all_reviews(sheet)

# Debug: Display the records to see if they are being retrieved correctly
# if records:
#     st.write("Reviews Data from Google Sheets:")
#     st.write(records)

# Display teacher details if a teacher is selected
if search_query:
    st.write(f"Teacher: {search_query}")
    
    # Get the reviews for the teacher
    reviews = get_teacher_reviews(records, clean_name(search_query))

    if reviews:
        st.write("### Reviews:")
        teaching_scores = []
        leniency_scores = []
        correction_scores = []
        da_quiz_scores = []

        for review in reviews:
            teaching_scores.append(review.get('Teaching ', 0))
            leniency_scores.append(review.get('Leniency ', 0))
            correction_scores.append(review.get('Correction ', 0))
            da_quiz_scores.append(review.get('DA/Quiz ', 0))
            st.write(f"- **Teaching**: {review.get('Teaching ', 'N/A')} | **Leniency**: {review.get('Leniency ', 'N/A')} | **Correction**: {review.get('Correction ', 'N/A')} | **DA/Quiz**: {review.get('DA/Quiz ', 'N/A')}")

        # Calculate the overall rating
        overall_rating = calculate_overall_rating(teaching_scores)
        num_reviews = len(reviews)
        st.write(f"### Overall Rating: {overall_rating:.2f} / 10 ({num_reviews} reviews)")
    else:
        st.write("No reviews submitted yet for this teacher.")

    # User input section (ratings for the teacher)
    st.markdown("### **Rate the Teacher**")
    teaching = st.slider("Teaching", 0, 10)
    leniency = st.slider("Leniency", 0, 10)
    correction = st.slider("Correction", 0, 10)
    da_quiz = st.slider("DA/Quiz", 0, 10)

    # Calculate the overall rating based on the inputs
    overall_rating_input = calculate_overall_rating([teaching, leniency, correction, da_quiz])
    st.write(f"**Overall Rating**: {overall_rating_input:.2f} / 10")

    # Submit button to save the review
    submit_button = st.button(f"Submit Review for {search_query}")

    if submit_button:
        # Prepare the data to insert
        data_to_insert = [search_query, teaching, leniency, correction, da_quiz, overall_rating_input]

        try:
            # Append the review data to Google Sheets
            sheet.append_row(data_to_insert)
            st.success(f"Review for {search_query} submitted successfully!")
        except Exception as e:
            st.error(f"Failed to submit review: {e}")

else:
    st.write("No teacher selected.")

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
