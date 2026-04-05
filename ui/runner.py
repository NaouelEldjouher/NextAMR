import streamlit as st
import subprocess
import os

def render_runner():
    st.header("🚀 3. Cloud Pipeline Launcher")
    
    # 1. State Verification
    if 'validated_file' not in st.session_state or not st.session_state['validated_file']:
        st.warning("⚠️ No validated sample sheet detected. Please go to the 'Validate' tab first.")
        return

    input_tsv = st.session_state['validated_file']
    st.success(f"📂 Sample Sheet Ready: `{input_tsv}`")

    # 2. Cloud-Specific User Inputs
    st.markdown("### AWS Configuration")
    col1, col2 = st.columns(2)
    
    with col1:
        # The 'Work' bucket is where Nextflow stores intermediate 'trash' files
        s3_bucket = st.text_input("AWS S3 Work Bucket", "s3://my-amr-flow-data/work")
    with col2:
        # The 'Results' path is where the final tables and fastas go
        s3_out = st.text_input("AWS S3 Output Path", "s3://my-amr-flow-data/results")

    # RESUME FEATURE
    use_cache = st.checkbox("Use Nextflow Cache (-resume)", value=True, 
                            help="Turn this off if you want a completely fresh run.")

    # 3. The Launch Button
    if st.button("🔥 Launch AWS Batch Pipeline"):
        
        # Automatic Path Detection
        current_dir = os.path.basename(os.getcwd())
        nf_script = "../nextflow/main.nf" if current_dir == "ui" else "nextflow/main.nf"
        
        # 4. Build Command for Cloud Execution
        # We use -profile aws to trigger the AWS Batch executor defined in nextflow.config
        cmd = [
            "nextflow", "run", nf_script,
            "-profile", "aws", 
            "-bucket-dir", s3_bucket,
            "--input", input_tsv,
            "--outdir", s3_out
        ]

        if use_cache:
            cmd.append("-resume")

        st.info(f"⚡ Dispatching tasks to AWS Batch...")
        
        # 5. Execution and Real-time Log Streaming
        log_placeholder = st.empty()
        try:
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            full_log = ""
            for line in process.stdout:
                full_log += line
                # Keep only the last 15 lines in the UI to prevent lag
                log_placeholder.code("\n".join(full_log.splitlines()[-15:]))
            
            process.wait()
            
            if process.returncode == 0:
                st.balloons()
                st.success("✅ Pipeline Finished! Results are safe in your S3 bucket.")
                st.session_state['tsv_ready'] = False 
            else:
                st.error(f"❌ Cloud Execution Failed (Code: {process.returncode})")
                
        except Exception as e:
            st.error(f"Critical Cloud Error: {e}")