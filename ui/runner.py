import streamlit as st
import subprocess
import os

def render_runner():
    st.header("🚀 3. Pipeline Launcher")
    
    # 1. State Verification
    if 'validated_file' not in st.session_state or not st.session_state['validated_file']:
        st.warning("⚠️ No validated sample sheet detected. Please go to the 'Validate' tab first.")
        return

    input_tsv = st.session_state['validated_file']
    st.success(f"📂 Sample Sheet Ready: `{input_tsv}`")

    # 2. Local Configuration
    st.markdown("### Execution Configuration")
    
    # Let the user choose a folder name for the results
    out_dir = st.text_input("Output Directory Name", "results")

    # RESUME FEATURE
    use_cache = st.checkbox("Use Nextflow Cache (-resume)", value=True, 
                            help="Turn this off if you want a completely fresh run.")

    # 3. The Launch Button
    if st.button("🔥 Launch Pipeline"):
        
        # We assume main.nf is in your root AMR-Flow folder
        nf_script = "main.nf" 
        
        # 4. Build Command for Local EC2 Execution
        # We use -profile docker to run it right there on your AWS server
        cmd = [
            "nextflow", "run", nf_script,
            "-profile", "docker", 
            "--input", input_tsv,
            "--outdir", out_dir
        ]

        if use_cache:
            cmd.append("-resume")

        st.info(f"⚡ Dispatching tasks to the local Docker engine...")
        
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
                st.success(f"✅ Pipeline Finished! Your reports are saved in the `{out_dir}` folder on the server.")
                st.session_state['tsv_ready'] = False 
            else:
                st.error(f"❌ Execution Failed (Code: {process.returncode})")
                
        except Exception as e:
            st.error(f"Critical Pipeline Error: {e}")