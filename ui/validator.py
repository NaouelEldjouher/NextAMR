import streamlit as st
import pandas as pd
import os

def render_validator():
    st.header("🛡️ 2. Data Validation")
    st.write("Let's verify that all files listed in your Sample Sheet successfully transferred to the server.")

    # 1. Seamless connection to Tab 1: Try to load the file they just generated!
    tsv_path = st.session_state.get('generated_file', None)
    
    # Provide a manual file uploader as a fallback (just in case)
    uploaded_file = st.file_uploader("Upload Sample Sheet (.tsv) [Skip if generated in Tab 1]", type=["tsv", "txt"])
    
    # Decide which file to validate
    file_to_validate = uploaded_file if uploaded_file else tsv_path

    if file_to_validate:
        try:
            df = pd.read_csv(file_to_validate, sep='\t').fillna('none')
            st.write("### 🔍 Sample Sheet Preview")
            st.dataframe(df, width='stretch')
            
            # Validation Logic for the Server Hard Drive
            missing_files = []
            
            if st.button("🚀 Verify Files on Server"):
                with st.spinner("Checking server hard drive for your FastQ files..."):
                    for col in ['fastq_1', 'fastq_2', 'longreads']:
                        if col in df.columns:
                            for path in df[col]:
                                # Ignore empty or 'none' values
                                if str(path).lower() != 'none' and pd.notnull(path) and str(path).strip() != "":
                                    # THE MAGIC CHECK: Does this file physically exist on the Ubuntu server?
                                    if not os.path.exists(str(path)):
                                        missing_files.append(path)
            
                if missing_files:
                    st.error("❌ Found missing files! The server cannot find these paths:")
                    for missing in missing_files:
                        st.write(f"- `{missing}`")
                    st.warning("Please go back to Tab 1 and make sure all files are uploaded and linked correctly.")
                else:
                    st.success("✅ All files verified! They physically exist on the server.")
                    
                    # Lock it in for the Runner Tab
                    st.session_state['tsv_ready'] = True
                    
                    # If they manually uploaded a new one, save it to disk for Nextflow
                    if not isinstance(file_to_validate, str):
                        save_path = os.path.join(os.getcwd(), "samples_validated.tsv")
                        df.to_csv(save_path, sep='\t', index=False)
                        st.session_state['validated_file'] = save_path
                    else:
                        # Otherwise, just use the one from Tab 1
                        st.session_state['validated_file'] = file_to_validate
                        
                    st.info("➡️ You are cleared for launch! Move to Tab 3 to start the pipeline.")
                    
        except Exception as e:
            st.error(f"Error reading file: {e}")
    else:
        st.info("Waiting for data... Please generate a Sample Sheet in Tab 1 first.")