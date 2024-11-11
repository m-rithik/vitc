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
@st.cache_data  # Cache the teacher data so it's loaded once
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

# Function to get all reviews from Google Sheets (cached version)
@st.cache_data  # Cache reviews data to prevent repeated API calls
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

# Search bar (case insensitive and ignore titles like Dr, Mr, Ms)
search_query = st.text_input("Search for a teacher:")

# Find matching teachers based on the search query
if search_query:
    search_query_cleaned = clean_name(search_query)
    matches = [teachers[i] for i in range(len(teachers_cleaned)) if search_query_cleaned in teachers_cleaned[i]]
else:
    matches = []

# Load Google Sheet only if it hasn't been loaded yet in the session
if 'sheet' not in st.session_state:
    sheet = get_google_sheet()
    st.session_state.sheet = sheet
else:
    sheet = st.session_state.sheet

# Fetch all records (only if the sheet object is valid)
if sheet and 'records' not in st.session_state:
    records = get_all_reviews(sheet)
    st.session_state.records = records
else:
    records = st.session_state.records

# Display search results
if matches:
    st.write("Teachers found:")
    for idx, (teacher, image_url) in enumerate(matches):
        col1, col2 = st.columns([2, 1])  # Create two columns: one for the name, one for the image

        with col1:
            st.subheader(f"Teacher: {teacher}")

            # Get the reviews for the teacher
            reviews = get_teacher_reviews(records, clean_name(teacher))

            if reviews:
                # Display reviews under teacher's name
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
            teaching = st.slider("Teaching", 0, 10, key=f"teaching_{idx}")
            leniency = st.slider("Leniency", 0, 10, key=f"leniency_{idx}")
            correction = st.slider("Correction", 0, 10, key=f"correction_{idx}")
            da_quiz = st.slider("DA/Quiz", 0, 10, key=f"da_quiz_{idx}")

            # Calculate the overall rating based on the inputs
            overall_rating_input = calculate_overall_rating([teaching, leniency, correction, da_quiz])
            st.write(f"**Overall Rating**: {overall_rating_input:.2f} / 10")

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
                if teacher not in st.session_state.submitted_reviews:  # Prevent multiple submissions for the same teacher
                    # Prepare the data to insert
                    data_to_insert = [teacher, teaching, leniency, correction, da_quiz, overall_rating_input]
                    
                    try:
                        # Append the review data to Google Sheets
                        sheet.append_row(data_to_insert)
                        st.success(f"Review for {teacher} submitted successfully!")
                        
                        # Store the review in session state to prevent resubmission
                        if 'submitted_reviews' not in st.session_state:
                            st.session_state.submitted_reviews = []
                        st.session_state.submitted_reviews.append(teacher)
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
