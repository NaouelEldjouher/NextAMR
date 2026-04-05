import streamlit as st
import pandas as pd
import os

def render_generator():
    st.header("📝 1. Sample Sheet Generator")
    st.write("Manually enter your sample IDs and their corresponding S3 paths.")

    # Use session state to keep the list alive between tab clicks
    if 'temp_samples' not in st.session_state:
        st.session_state['temp_samples'] = []

    # Form for adding a single sample
    with st.form("add_sample_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            sample_id = st.text_input("Sample ID", placeholder="e.g., E_COLI_001")
            f1 = st.text_input("Fastq 1 (S3 URI)", placeholder="s3://bucket/path/R1.fastq.gz")
        with c2:
            f2 = st.text_input("Fastq 2 (S3 URI)", placeholder="s3://bucket/path/R2.fastq.gz")
            long = st.text_input("Long Reads (S3 URI)", value="none")
        
        submitted = st.form_submit_button("➕ Add Sample")
        if submitted:
            if sample_id and f1:
                st.session_state['temp_samples'].append({
                    "sample": sample_id,
                    "fastq_1": f1,
                    "fastq_2": f2 if f2 else "none",
                    "longreads": long if long else "none"
                })
                st.toast(f"Added {sample_id}")
            else:
                st.error("Sample ID and Fastq 1 are required.")

    # Display the current list and provide a save button
    if st.session_state['temp_samples']:
        df = pd.DataFrame(st.session_state['temp_samples'])
        st.write("### Current Selection")
        st.dataframe(df, width='stretch')

        col1, col2 = st.columns([1, 4])
        if col1.button("🗑️ Clear List"):
            st.session_state['temp_samples'] = []
            st.rerun()
            
        if col2.button("💾 Finalize & Save for Validation"):
            # Save the TSV locally so Tab 2 can find it
            save_path = "samples_generated.tsv"
            df.to_csv(save_path, sep='\t', index=False)
            
            # Update session state for the Validator
            st.session_state['generated_file'] = save_path
            st.success(f"✅ Success! `{save_path}` is ready. Move to Tab 2.")
            