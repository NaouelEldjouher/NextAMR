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
    
    st.markdown("### AWS Batch Configuration")
    col1, col2 = st.columns(2)
    with col1:
        # This is where Nextflow keeps its intermediate cloud 'trash'
        s3_bucket = os.getenv("AMR_WORK_BUCKET", "s3://default-bucket/work")
    with col2:
        s3_out = os.getenv("AMR_RESULTS_BUCKET", "s3://default-bucket/results")

    if st.button("🔥 Launch AWS Batch Pipeline"):
        # The command now uses -profile aws to trigger the cloud cluster
        nextflow_bin = os.path.expanduser("~/bin/nextflow")
        main_nf_path = os.path.abspath("nextflow/main.nf")
        cmd = [
            nextflow_bin, "run", main_nf_path,
            "-profile", "aws", # Triggers the Cloud Profile
            "-preview",
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



