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
s3 = boto3.client('s3')
def render_validator():
    st.header("🛡️ 2. Cloud Data Validation")
    st.write("Verifying that your FastQ files are safely stored in S3 before launching AWS Batch.")

  
    
    # Pull the TSV path from Tab 1
    target_bucket = os.getenv("AMR_S3_BUCKET")
    if not target_bucket:
        st.error("🚨 Configuration Missing: `AMR_S3_BUCKET` is not set.")
        return
    # 2. State Check: Ensure a sample sheet exists from Tab 1
    tsv_path = st.session_state.get('generated_file', None)
    
    if tsv_path and os.path.exists(tsv_path):
        df = pd.read_csv(tsv_path, sep='\t').fillna('none')
        st.write("### 🔍 Sample Sheet Preview (S3 Paths)")
        st.dataframe(df, use_container_width=True)
        
        if st.button("🚀 Verify Files on S3"):
            missing_files = []
            # Dynamically find columns likely to contain S3 paths
            target_cols = [c for c in ['fastq_1', 'fastq_2', 'long_reads', 'longreads'] if c in df.columns]
            
            with st.spinner("Scanning S3 Buckets..."):
                for index, row in df.iterrows():
                    for col in target_cols:
                        path = str(row[col])
                        
                        if path != 'none' and path.startswith('s3://'):
                            try:
                                # Senior Touch: Parse bucket/key dynamically from URI
                                parts = path.replace("s3://", "").split("/", 1)
                                b_name = parts[0]
                                k_name = parts[1]
                                
                                # Ping S3: head_object is free/fast and checks metadata only
                                s3.head_object(Bucket=b_name, Key=k_name)
                                
                            except (ClientError, IndexError) as e:
                                # Catch 404 (Missing), 403 (Permission), or malformed URIs
                                missing_files.append(f"Row {index+1} ({col}): {path}")
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