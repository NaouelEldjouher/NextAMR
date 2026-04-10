import streamlit as st
import pandas as pd
import os
import boto3
from botocore.exceptions import ClientError
# AMR-Flow Cloud Validator - v1.0.0
# Verified for HeadNode IAM Role integration
def check_s3_file(s3_client, bucket, key):
    try:
        # head_object is a "ping" - it checks existence without downloading
        s3_client.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError:
        return False
def render_validator():
    st.header("🛡️ 2. Cloud Data Validation")
    st.write("Verifying that your FastQ files are safely stored in S3 before launching AWS Batch.")

    s3 = boto3.client('s3')
    
    # Pull the TSV path from Tab 1
    tsv_path = st.session_state.get('generated_file', None)
    
    if tsv_path and os.path.exists(tsv_path):
        df = pd.read_csv(tsv_path, sep='\t').fillna('none')
        st.write("### 🔍 Sample Sheet Preview (S3 Paths)")
        st.dataframe(df, width='stretch')
        
        missing_files = []
        if st.button("🚀 Verify Files on S3"):
            with st.spinner("Scanning S3 Buckets..."):
                for col in ['fastq_1', 'fastq_2', 'longreads']:
                    if col in df.columns:
                        for path in df[col]:
                            if path != 'none' and str(path).startswith('s3://'):
                                # Parse s3://bucket/key
                                parts = path.replace("s3://", "").split("/", 1)
                                bucket, key = parts[0], parts[1]
                                
                                if not check_s3_file(s3, bucket, key):
                                    missing_files.append(path)
            
            if missing_files:
                st.error(f"❌ Files not found in S3: {missing_files}")
                st.warning("Did the upload in Tab 1 finish completely?")
            else:
                st.success("✅ All S3 paths verified! AWS Batch can now access your data.")
                st.session_state['tsv_ready'] = True
                st.session_state['validated_file'] = tsv_path
                st.info("➡️ Move to Tab 3 to launch the pipeline.")
    else:
        st.info("Please complete the upload in Tab 1 first.")