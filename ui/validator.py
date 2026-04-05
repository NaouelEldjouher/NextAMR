import streamlit as st
import pandas as pd
import boto3
from botocore.exceptions import ClientError

def check_s3_file(s3_client, bucket, key):
    try:
        s3_client.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError:
        return False

def render_validator():
    st.header("☁️ S3 Data Validator")
    s3 = boto3.client('s3')
    
    uploaded_file = st.file_uploader("Upload samples.tsv", type=["tsv"])
    
    if uploaded_file:
        df = pd.read_csv(uploaded_file, sep='\t').fillna('none')
        st.dataframe(df, width='stretch')
        
        # Validation Logic for S3
        missing_files = []
        if st.button("Verify Files on S3"):
            with st.spinner("Searching S3 Buckets..."):
                for col in ['fastq_1', 'fastq_2', 'longreads']:
                    if col in df.columns:
                        for path in df[col]:
                            if path != 'none' and path.startswith('s3://'):
                                # Parse s3://bucket/key
                                parts = path.replace("s3://", "").split("/", 1)
                                bucket, key = parts[0], parts[1]
                                if not check_s3_file(s3, bucket, key):
                                    missing_files.append(path)
            
            if missing_files:
                st.error(f"❌ Files not found in S3: {missing_files}")
            else:
                st.success("✅ All S3 paths verified!")
                st.session_state['tsv_ready'] = True
                # Save locally so Nextflow can read the sample sheet itself
                df.to_csv("samples_cloud.tsv", sep='\t', index=False)
                st.session_state['validated_file'] = "samples_cloud.tsv"