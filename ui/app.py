import streamlit as st
import boto3
import generator, validator, runner

st.set_page_config(page_title="AMR-Flow Cloud", layout="wide")
st.title("🧬 AMR-Flow: Cloud Controller")

# Sidebar for AWS Health Check
with st.sidebar:
    st.header("AWS Status")
    try:
        iam = boto3.client('sts').get_caller_identity()
        st.success(f"User: {iam['Arn'].split('/')[-1]}")
    except:
        st.error("Offline: No AWS Credentials Found")

# We updated the tab names to match your new workflow!
tabs = st.tabs([
    "1. Upload Data", 
    "2. Validate Sheet", 
    "3. Launch Pipeline", 
    "4. Monitor Logs"
])

with tabs[0]: generator.render_generator()
with tabs[1]: validator.render_validator()
with tabs[2]: runner.render_runner()
with tabs[3]: st.info("Check AWS Batch/EC2 Console for live node scaling.")