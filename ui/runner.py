"""
AMR-Flow: Cloud Orchestrator
This module bridges the Streamlit frontend with the Nextflow backend. 
By utilizing Python's subprocess module, it asynchronously dispatches 
genomic tasks to the AWS Batch cluster via the '-profile aws' flag, 
ensuring the UI remains highly responsive during heavy compute loads.E
"""
import streamlit as st
import subprocess
import os

def render_runner():
    st.header("🚀 3. Cloud Pipeline Launcher")
    
    if 'validated_file' not in st.session_state:
        st.warning("⚠️ Please validate your S3 data in Tab 2 first.")
        return

    input_tsv = st.session_state['validated_file']
    bucket_name = os.getenv("AMR_S3_BUCKET")
    
    if not bucket_name:
        st.error("🚨 Configuration Missing: `AMR_S3_BUCKET` is not set.")
        return
    st.markdown("### AWS Batch Configuration")
    s3_path = f"s3://{bucket_name}"
    s3_work = f"{s3_path}/work"
    s3_out = f"{s3_path}/results"
    col1, col2 = st.columns(2)
    with col1:
        # This is where Nextflow keeps its intermediate cloud 'trash'
        
        st.text_input("S3 Work Directory", s3_work, disabled=True)
    with col2:

        st.text_input("S3 Results Directory", s3_out, disabled=True)
    if st.button("🔥 Launch AWS Batch Pipeline"):
        # The command now uses -profile aws to trigger the cloud cluster
        nextflow_bin = "nextflow" 
        main_nf_path = os.path.abspath("nextflow/main.nf")
        cmd = [
            nextflow_bin, "run", main_nf_path,
            "-profile", "aws", # Triggers the Cloud Profile
            "-bucket-dir", s3_work,
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



