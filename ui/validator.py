"""
AMR-Flow: Cloud Data Integrity Validator
This module acts as a 'Pre-Flight Guardrail'. By using boto3 to verify 
S3 object existence before triggering AWS Batch, it prevents 'zombie jobs' 
and significantly reduces wasted cloud compute costs caused by missing data.
"""
import streamlit as st
import pandas as pd
import os
import boto3
from botocore.exceptions import ClientError
# AMR-Flow: Cloud Data Integrity Validator
# Verified for HeadNode IAM Role integration
def check_s3_file(s3_client, bucket, key):
    try:
        # head_object is a "ping" - it checks existence without downloading
        s3_client.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError:
        return False
    
def validate_s3_files(df, bucket_name):
    s3 = boto3.client('s3')
    errors = []
    # Check for all possible naming conventions
    target_cols = [c for c in ['fastq_1', 'fastq_2', 'long_reads', 'longreads'] if c in df.columns]
    
    for index, row in df.iterrows():
        for col in target_cols:
            s3_uri = str(row[col])
            if s3_uri.lower() == 'none' or not s3_uri.startswith('s3://'):
                continue
            
            # Parse key from URI
            key = s3_uri.replace(f"s3://{bucket_name}/", "")
            
            try:
                response = s3.head_object(Bucket=bucket_name, Key=key)
                # Catch folder-masking error
                if key.endswith('/') or response.get('ContentLength') == 0:
                    errors.append(f"⚠️ Row {index+1}: '{key}' is a directory or empty.")
            except ClientError as e:
                error_code = e.response['Error']['Code']
                msg = "Missing File" if error_code == "404" else "Permission Denied"
                errors.append(f"❌ Row {index+1}: {msg} for '{key}'")
    return errors
def render_validator():
    st.header("🛡️ 2. Cloud Data Validation")
    st.write("Verifying that your FastQ files are safely stored in S3 before launching AWS Batch.")

    s3 = boto3.client('s3')
    
    # Pull the TSV path from Tab 1
    tsv_path = st.session_state.get('generated_file', None)
    target_bucket = os.getenv("AMR_S3_BUCKET", "amr-flow-system-data-485988342847-us-east-1-an")
    if tsv_path and os.path.exists(tsv_path):
        df = pd.read_csv(tsv_path, sep='\t').fillna('none')
        st.write("### 🔍 Sample Sheet Preview (S3 Paths)")
        st.dataframe(df, width='stretch')
        
        missing_files = []
        if st.button("🚀 Verify Files on S3"):
            with st.spinner("Scanning S3 Buckets..."):
                for col in ['fastq_1', 'fastq_2', 'long']:
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
                for f in missing_files:
                    st.write(f"- {f}")
                st.warning("Did the upload in Tab 1 finish completely?")
            else:
                st.success("✅ All S3 paths verified! AWS Batch can now access your data.")
                st.session_state['tsv_ready'] = True
                st.session_state['validated_file'] = tsv_path
                st.info("➡️ Move to Tab 3 to launch the pipeline.")
    else:
        st.info("Please complete the upload in Tab 1 first.")