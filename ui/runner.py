import streamlit as st
import subprocess
import os

def render_runner():
    st.header("🚀 3. Cloud Pipeline Launcher")
    
    if 'validated_file' not in st.session_state:
        st.warning("⚠️ Please validate your S3 data in Tab 2 first.")
        return

    input_tsv = st.session_state['validated_file']
    
    st.markdown("### AWS Batch Configuration")
    col1, col2 = st.columns(2)
    with col1:
        # This is where Nextflow keeps its intermediate cloud 'trash'
        s3_bucket = st.text_input("S3 Work Bucket (Required for Batch)", "s3://your-bucket/work")
    with col2:
        s3_out = st.text_input("S3 Output Results Path", "s3://your-bucket/results")

    if st.button("🔥 Launch AWS Batch Pipeline"):
        # The command now uses -profile aws to trigger the cloud cluster
        cmd = [
            "nextflow", "run", "main.nf",
            "-profile", "aws", # Triggers the Cloud Profile
            "-bucket-dir", s3_bucket, # Defines the S3 Working Directory
            "--input", input_tsv,
            "--outdir", s3_out,
            "-resume"
        ]

        st.info("⚡ Dispatching tasks to AWS Batch Cluster...")
        log_placeholder = st.empty()
        
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            full_log = ""
            for line in process.stdout:
                full_log += line
                log_placeholder.code("\n".join(full_log.splitlines()[-15:]))
            process.wait()
            
            if process.returncode == 0:
                st.balloons()
                st.success("✅ Pipeline Finished! Check your S3 Results path.")
        except Exception as e:
            st.error(f"Execution Error: {e}")