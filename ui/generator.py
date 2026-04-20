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
from boto3.s3.transfer import TransferConfig

# AMR-Flow: Secure Data Ingestion Module
# Initialize AWS S3 Client
s3_client = boto3.client('s3')

def render_generator():
    st.header("☁️ 1.Cloud Upload")
    st.write("Upload your Sample Sheet and FastQ files. We will securely transfer them to your AWS S3 bucket for cloud processing.")

   
    target_bucket = os.getenv("AMR_S3_BUCKET", "amr-flow-system-data-485988342847-us-east-1-an")
    target_folder = os.getenv("AMR_S3_FOLDER", "uploads")

    # The File Uploaders
    tsv_file = st.file_uploader("1. Upload Sample Sheet (.tsv)", type=["tsv", "txt"])
    fastq_files = st.file_uploader("2. Upload all FastQ files", type=['fastq', 'fastq.gz', 'fq', 'fq.gz'], accept_multiple_files=True)

    if tsv_file and fastq_files and target_bucket:
        df = pd.read_csv(tsv_file, sep='\t')
        st.write("### 🔍 Preview of Original Sample Sheet")
        st.dataframe(df, width='stretch')

        if st.button("🚀 Upload Directly to S3 & Finalize"):
            with st.spinner("Streaming files to AWS S3... this may take a while for large datasets."):
                config = TransferConfig(
                    multipart_threshold=1024 * 25, # 25MB threshold
                    max_concurrency=10,
                    use_threads=True
                )
                uploaded_paths = {}
                
                # 1. Upload each FastQ file straight to S3
                for fq in fastq_files:
                    # Construct the S3 Key (the path inside the bucket)
                    clean_name = fq.name.replace(" ", "_")
                    s3_key = f"{target_folder}/{clean_name}"
                    s3_uri = f"s3://{target_bucket}/{s3_key}"
                    
                    try:
                        # Upload the file stream directly to S3
                        s3_client.upload_fileobj(fq, target_bucket, s3_key,Config=config)
                        uploaded_paths[fq.name] = s3_uri
                    except Exception as e:
                        st.error(f"Failed to upload {fq.name}: {e}")
                        return

                # 2. Update the TSV DataFrame with the new S3 URIs
                for col in ['fastq_1', 'fastq_2', 'longreads']:
                    if col in df.columns:
                        df[col] = df[col].apply(lambda x: uploaded_paths.get(os.path.basename(str(x)), x) 
                            if x != 'none' else x
                        )

                # 3. Save the final TSV locally for Nextflow to read
                final_tsv_path = os.path.join(os.getcwd(), "samples_cloud_ready.tsv")
                df.to_csv(final_tsv_path, sep='\t', index=False)
                
                st.session_state['generated_file'] = final_tsv_path
                st.session_state['validated_file'] = final_tsv_path
                st.session_state['tsv_ready'] = True 
                
                st.success(f"✅ Success! {len(fastq_files)} files pushed to S3 and manifest updated.")
                st.write("### 💎 Cloud-Ready Manifest Preview")
                st.dataframe(df, use_container_width=True)
                st.info("➡️ Proceed directly to **Tab 3: Launchpad**.")