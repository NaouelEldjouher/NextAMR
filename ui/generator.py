"""
AMR-Flow: Secure Data Ingestion Module
This module handles the front-end user uploads. It utilizes Boto3's 
upload_fileobj to stream large genomic FastQ files directly to AWS S3. 
This ensures the Streamlit UI remains stateless, scalable, and memory-efficient.
"""
import streamlit as st
import pandas as pd
import boto3
import os

# AMR-Flow: Secure Data Ingestion Module
# Initialize AWS S3 Client
s3_client = boto3.client('s3')

def render_generator():
    st.header("☁️ 1. Enterprise Cloud Upload")
    st.write("Upload your Sample Sheet and FastQ files. We will securely transfer them to your AWS S3 bucket for cloud processing.")

    # Ask the user (or yourself) where these files should go in AWS
    target_bucket = st.text_input("Destination S3 Bucket Name", "my-amr-flow-data")
    target_folder = st.text_input("S3 Folder Path (Optional)", "uploads/test-run-1")

    # The File Uploaders
    tsv_file = st.file_uploader("1. Upload Sample Sheet (.tsv)", type=["tsv", "txt"])
    fastq_files = st.file_uploader("2. Upload all FastQ files", type=['fastq', 'fastq.gz', 'fq', 'fq.gz'], accept_multiple_files=True)

    if tsv_file and fastq_files and target_bucket:
        df = pd.read_csv(tsv_file, sep='\t')
        st.write("### 🔍 Preview of Original Sample Sheet")
        st.dataframe(df, width='stretch')

        if st.button("🚀 Upload Directly to S3 & Finalize"):
            with st.spinner("Streaming files to AWS S3... this may take a while for large datasets."):
                
                uploaded_paths = {}
                
                # 1. Upload each FastQ file straight to S3
                for fq in fastq_files:
                    # Construct the S3 Key (the path inside the bucket)
                    s3_key = f"{target_folder}/{fq.name}".strip("/")
                    s3_uri = f"s3://{target_bucket}/{s3_key}"
                    
                    try:
                        # Upload the file stream directly to S3
                        s3_client.upload_fileobj(fq, target_bucket, s3_key)
                        uploaded_paths[fq.name] = s3_uri
                    except Exception as e:
                        st.error(f"Failed to upload {fq.name}: {e}")
                        return

                # 2. Update the TSV DataFrame with the new S3 URIs
                for col in ['fastq_1', 'fastq_2', 'longreads']:
                    if col in df.columns:
                        df[col] = df[col].apply(lambda x: uploaded_paths.get(str(x).strip(), x) if pd.notnull(x) else x)

                # 3. Save the final TSV locally for Nextflow to read
                final_tsv_path = os.path.join(os.getcwd(), "samples_cloud_ready.tsv")
                df.to_csv(final_tsv_path, sep='\t', index=False)
                
                st.session_state['generated_file'] = final_tsv_path
                st.success(f"✅ Success! {len(fastq_files)} files pushed to S3. The Sample Sheet now contains s3:// links.")