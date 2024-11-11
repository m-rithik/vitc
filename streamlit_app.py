import streamlit as st
import re
import os

# Function to read teacher names and image URLs from the text fil
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

# Load reviews from session state if not already loaded
if 'reviews' not in st.session_state:
    st.session_state.reviews = {}

# Function to calculate overall rating (based on existing ratings)
def calculate_overall_rating(ratings):
    total_rating = sum([sum(rating) for rating in ratings])
    return total_rating / (len(ratings) * 4) if ratings else 0

# Display the search results
if matches:
    st.write("Teachers found:")
    for idx, (teacher, image_url) in enumerate(matches):
        col1, col2 = st.columns([2, 1])  # Create two columns: one for the name, one for the image

        with col1:
            st.subheader(f"Teacher: {teacher}")

            # Initialize teacher's reviews in session state if not already present
            teacher_key = f"{teacher}_{idx}"  # Unique key based on teacher's name and index
            if teacher_key not in st.session_state.reviews:
                st.session_state.reviews[teacher_key] = {
                    'ratings': [],  # Store all individual ratings as a list of tuples (teaching, leniency, correction, da_quiz)
                    'overall': 0     # Overall rating
                }

            # User input section (ratings for the teacher)
            st.markdown("### **Rate the Teacher**")
            teaching_key = sanitize_name_for_key(f"Teaching: {teacher}", idx)
            leniency_key = sanitize_name_for_key(f"Leniency: {teacher}", idx)
            correction_key = sanitize_name_for_key(f"Correction: {teacher}", idx)
            da_quiz_key = sanitize_name_for_key(f"DA/Quiz: {teacher}", idx)

            teaching = st.slider(f"Teaching: {teacher}", 0, 10, key=teaching_key)
            leniency = st.slider(f"Leniency: {teacher}", 0, 10, key=leniency_key)
            correction = st.slider(f"Correction: {teacher}", 0, 10, key=correction_key)
            da_quiz = st.slider(f"DA/Quiz: {teacher}", 0, 10, key=da_quiz_key)

            # Display the teacher's image in a smaller size
            with col2:
                try:
                    st.image(image_url, caption=f"{teacher}'s Picture", width=150)
                except Exception as e:
                    st.error(f"Error displaying image: {e}")

            # Submit button to save the review
            submit_button = st.button(f"Submit Review for {teacher}")
            
            if submit_button:
                # Save the ratings in session state
                st.session_state.reviews[teacher_key]['ratings'].append((teaching, leniency, correction, da_quiz))
                
                # Calculate the overall rating
                overall_rating = calculate_overall_rating(st.session_state.reviews[teacher_key]['ratings'])
                st.session_state.reviews[teacher_key]['overall'] = overall_rating
                
                # Display success message
                st.success(f"Review for {teacher} submitted successfully!")

        # Section 2: Overall Rating and Previous Reviews
        st.markdown("---")
        st.markdown("### **Overall Rating**")
        
        # Calculate average overall rating (without approximating)
        overall_rating = st.session_state.reviews[teacher_key]['overall']
        
        # Display the overall rating in the overall rating box
        st.markdown(f"**Overall Rating (based on {len(st.session_state.reviews[teacher_key]['ratings'])} reviews):**")
        st.markdown(f"{overall_rating:.2f} / 10", unsafe_allow_html=True)  # Display on 10-point scale
        
        # Display reviews and their individual ratings
        st.markdown("### **REVIEWS**")
        if not st.session_state.reviews[teacher_key]['ratings']:
            st.write("No reviews available.")
        else:
            for idx, rating in enumerate(st.session_state.reviews[teacher_key]['ratings']):
                st.write(f"**Review {idx + 1}:**")
                st.write(f"Teaching: {rating[0]}/10, Leniency: {rating[1]}/10, Correction: {rating[2]}/10, DA/Quiz: {rating[3]}/10")

else:
    st.write("No teachers found.")

# Footer message
st.markdown(
    """
    <hr style="margin-top: 3rem;">
    <div style="text-align: center; color: grey; font-size: 3.0rem;">
        Please contribute with reviews
    </div>
    """,
    unsafe_allow_html=True
)
