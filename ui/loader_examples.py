"""
Example usage of loading animations in Vishleshak AI
This file demonstrates how to integrate the advanced loading animations
"""

import streamlit as st
from ui.loader_animations import show_loading_animation, inject_loader_styles
import time

# Always inject loader styles first
inject_loader_styles()

def example_data_loading():
    """Example: Loading data with gear animation"""
    
    # Create a placeholder for the loading animation
    loading_placeholder = st.empty()
    
    with loading_placeholder.container():
        # Show gear animation while processing
        show_loading_animation("gear", "Loading your dataset...")
    
    # Simulate data loading
    time.sleep(2)  # Replace with actual data loading
    
    # Clear the loading animation
    loading_placeholder.empty()
    
    # Show success message
    st.success("✅ Data loaded successfully!")


def example_analysis_with_progress():
    """Example: Analysis with circular progress indicator"""
    
    loading_placeholder = st.empty()
    
    # Simulate progress from 0 to 100%
    for progress in range(0, 101, 10):
        with loading_placeholder.container():
            show_loading_animation(
                "circle", 
                f"Analyzing data... {progress}%",
                progress=progress
            )
        time.sleep(0.3)  # Replace with actual processing chunks
    
    loading_placeholder.empty()
    st.success("✅ Analysis complete!")


def example_simple_spinner():
    """Example: Simple spinner for quick operations"""
    
    loading_placeholder = st.empty()
    
    with loading_placeholder.container():
        show_loading_animation("spinner", "Processing request...")
    
    time.sleep(1.5)  # Replace with actual operation
    
    loading_placeholder.empty()
    st.info("ℹ️ Operation completed!")


# ═══════════════════════════════════════════════════════════════════════
# INTEGRATION EXAMPLES FOR COMMON SCENARIOS
# ═══════════════════════════════════════════════════════════════════════

def integrate_in_file_upload():
    """
    Example: Integrate loading animation with file upload
    """
    uploaded_file = st.file_uploader("Upload your data", type=["csv", "xlsx"])
    
    if uploaded_file:
        loading_placeholder = st.empty()
        
        # Show loading animation
        with loading_placeholder.container():
            show_loading_animation("gear", "Processing your file...")
        
        # Process the file
        try:
            # Your file processing code here
            import pandas as pd
            df = pd.read_csv(uploaded_file)
            
            # Clear loading animation
            loading_placeholder.empty()
            
            # Show results
            st.success(f"✅ Loaded {len(df)} rows successfully!")
            st.dataframe(df.head())
            
        except Exception as e:
            loading_placeholder.empty()
            st.error(f"❌ Error: {e}")


def integrate_in_chatbot():
    """
    Example: Integrate loading animation with chatbot response
    """
    user_input = st.text_input("Ask a question:")
    
    if st.button("Send") and user_input:
        loading_placeholder = st.empty()
        
        # Show thinking animation
        with loading_placeholder.container():
            show_loading_animation("spinner", "Agent is thinking...")
        
        # Get chatbot response
        try:
            # Your chatbot logic here
            response = "This is the chatbot response"  # Replace with actual call
            
            # Clear loading
            loading_placeholder.empty()
            
            # Display response
            st.markdown(f"**Bot:** {response}")
            
        except Exception as e:
            loading_placeholder.empty()
            st.error(f"❌ Error: {e}")


def integrate_in_data_analysis():
    """
    Example: Integrate with multi-step data analysis
    """
    if st.button("Run Analysis"):
        loading_placeholder = st.empty()
        
        steps = [
            ("Loading data...", 20),
            ("Cleaning data...", 40),
            ("Computing statistics...", 60),
            ("Generating insights...", 80),
            ("Creating visualizations...", 100),
        ]
        
        for step_text, progress in steps:
            with loading_placeholder.container():
                show_loading_animation("circle", step_text, progress=progress)
            
            # Simulate processing time
            time.sleep(0.5)  # Replace with actual step
        
        loading_placeholder.empty()
        st.success("✅ Analysis complete!")


def integrate_in_model_training():
    """
    Example: Integrate with ML model training
    """
    if st.button("Train Model"):
        loading_placeholder = st.empty()
        progress_bar = st.progress(0)
        
        epochs = 10
        for epoch in range(epochs):
            progress = int((epoch + 1) / epochs * 100)
            
            with loading_placeholder.container():
                show_loading_animation(
                    "circle",
                    f"Training model... Epoch {epoch + 1}/{epochs}",
                    progress=progress
                )
            
            # Your training logic here
            time.sleep(0.3)
            progress_bar.progress((epoch + 1) / epochs)
        
        loading_placeholder.empty()
        st.success("✅ Model trained successfully!")


# ═══════════════════════════════════════════════════════════════════════
# CONDITIONAL LOADING (THEME-AWARE)
# ═══════════════════════════════════════════════════════════════════════

def theme_aware_loading():
    """
    The loading animations automatically adapt to dark/light theme
    based on st.session_state.dark_mode
    """
    
    # Loading animations will use:
    # - Dark mode: Cyan (#00D9FF) accents
    # - Light mode: Blue (#0066FF) accents
    
    loading_placeholder = st.empty()
    
    theme = "Dark" if st.session_state.get("dark_mode", False) else "Light"
    
    with loading_placeholder.container():
        show_loading_animation("gear", f"Loading in {theme} mode...")
    
    time.sleep(2)
    loading_placeholder.empty()


# ═══════════════════════════════════════════════════════════════════════
# BEST PRACTICES
# ═══════════════════════════════════════════════════════════════════════

"""
BEST PRACTICES FOR LOADING ANIMATIONS:

1. **Always create a placeholder**:
   loading_placeholder = st.empty()

2. **Use context manager**:
   with loading_placeholder.container():
       show_loading_animation(...)

3. **Clear when done**:
   loading_placeholder.empty()

4. **Choose appropriate animation**:
   - Gear: File uploads, data processing
   - Circle: Progress tracking, multi-step operations
   - Spinner: Quick operations, API calls

5. **Provide meaningful text**:
   - Be specific: "Loading your dataset..." not "Loading..."
   - Update text with progress: "Analyzing... 60%"

6. **Handle errors gracefully**:
   try:
       # operation
   except:
       loading_placeholder.empty()
       st.error(...)

7. **Avoid blocking UI**:
   - Use time.sleep() sparingly
   - Consider async operations for heavy tasks

8. **Theme consistency**:
   - Animations automatically match theme
   - No need to manually adjust colors
"""


# ═══════════════════════════════════════════════════════════════════════
# DEMO PAGE (OPTIONAL)
# ═══════════════════════════════════════════════════════════════════════

def create_demo_page():
    """
    Optional: Create a demo page to showcase all animations
    """
    st.title("🎬 Loading Animations Demo")
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("⚙️ Gear Animation")
        if st.button("Show Gear"):
            loading_placeholder = st.empty()
            with loading_placeholder.container():
                show_loading_animation("gear", "Processing...")
            time.sleep(2)
            loading_placeholder.empty()
    
    with col2:
        st.subheader("⭕ Circle Progress")
        if st.button("Show Circle"):
            loading_placeholder = st.empty()
            for i in range(0, 101, 20):
                with loading_placeholder.container():
                    show_loading_animation("circle", f"Loading {i}%", progress=i)
                time.sleep(0.3)
            loading_placeholder.empty()
    
    with col3:
        st.subheader("🔄 Spinner")
        if st.button("Show Spinner"):
            loading_placeholder = st.empty()
            with loading_placeholder.container():
                show_loading_animation("spinner", "Loading...")
            time.sleep(2)
            loading_placeholder.empty()


# ═══════════════════════════════════════════════════════════════════════
# USAGE IN STREAMLIT APP
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Inject loader styles at the top of your app
    inject_loader_styles()
    
    # Initialize theme if not set
    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = False
    
    # Your app content here...
    st.title("Vishleshak AI")
    
    # Example: Use in your file upload
    # integrate_in_file_upload()
    
    # Example: Use in chatbot
    # integrate_in_chatbot()
    
    # Or create demo page
    create_demo_page()
