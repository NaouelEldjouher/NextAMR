import streamlit as st
import pandas as pd
import boto3
import os
import glob
import json
import io
# Initialize S3 Client
BUCKET_NAME = os.getenv("AMR_S3_BUCKET")
s3 = boto3.client('s3')
def render_reporter():
    st.header("📊 AMR-Flow Analysis Dashboard")
    if not BUCKET_NAME:
        st.error("🚨 **Configuration Missing:** `AMR_S3_BUCKET` is not set.")
        st.info("Please set your bucket name in the .env file to view results.")
        return
    res_prefix = "results/"
    def list_s3_files(prefix):
        """Helper to list objects in S3 with a specific prefix"""
        try:
            response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=prefix)
            return [obj['Key'] for obj in response.get('Contents', [])]
        except Exception:
            return []

    def get_s3_file_content(key):
        """Helper to read S3 object content into string"""
        obj = s3.get_object(Bucket=BUCKET_NAME, Key=key)
        return obj['Body'].read().decode('utf-8')

    # --- SECTION 1: RAW READ QUALITY (FASTP) ---
    st.subheader("🧬 1. Raw Read Metrics")
    fastp_keys= [k for k in list_s3_files(f"{res_prefix}fastp/") if k.endswith(".json")]
    
    if fastp_keys:
        qc_stats = []
        for f in fastp_keys:
            sample = os.path.basename(f).replace(".json", "")
            try:
                with open(f, 'r') as j:
                    data = json.loads(get_s3_file_content(key)).get('summary', {}).get('after_filtering', {})
                    total_bases = data.get('total_bases', data.get('total_bp', 0))
                    qc_stats.append({
                        "Sample": sample,
                        "Avg Read Len": f"{int(data.get('read1_mean_length', 0))} bp",
                        "Raw GC %": round(data.get('gc_content', 0) * 100, 2),
                        "Yield (Mb)": round(total_bases / 1e6, 2),
                        "Q30 %": round(data.get('q30_rate', 0) * 100, 2)
                    })
            except Exception: continue
        st.dataframe(pd.DataFrame(qc_stats), width='stretch')
    else:
        st.info("Waiting for Fastp results...")

    # --- SECTION 2: ASSEMBLY QUALITY (DIRECT FASTA SCAN) ---
    st.divider()
    st.subheader("🏗️ 2. Assembly Quality (N50 & GC)")
    
    # Scans all fasta/fna files found in the results tree
    all_files = list_s3_files(res_prefix)
    fasta_keys = [k for k in all_files if k.endswith((".fna", ".fasta"))]

    if fasta_keys:
        fasta_stats = []
        with st.spinner("Calculating assembly metrics from S3..."):
            for key in fasta_keys:
                fname = os.path.basename(key)
                
                # 1. Filter for main assembly files (moved inside the loop)
                if any(x in fname.lower() for x in ["polished", "assembly", "flye", "unicycler", "polypolish"]):
                    try:
                        # 2. Fetch from S3 (Replaced local 'open' with your S3 helper)
                        content = get_s3_file_content(key)
                        
                        sections = content.split('>')
                        lengths = []
                        total_seq_list = [] # Using a list for better memory management
                        
                        for s in sections[1:]:
                            lines = s.split('\n')
                            seq = "".join(lines[1:]).replace('\n','').replace('\r','')
                            lengths.append(len(seq))
                            total_seq_list.append(seq)
                        
                        full_txt = "".join(total_seq_list)
                        
                        # 3. GC % Calculation
                        if full_txt:
                            gc_count = full_txt.count('G') + full_txt.count('C') + \
                                       full_txt.count('g') + full_txt.count('c')
                            gc_pct = (gc_count / len(full_txt) * 100)
                            
                            # 4. N50 Calculation
                            lengths.sort(reverse=True)
                            total_sum = sum(lengths)
                            run_sum, n50 = 0, 0
                            for l in lengths:
                                run_sum += l
                                if run_sum >= total_sum / 2:
                                    n50 = l
                                    break
                            
                            fasta_stats.append({
                                "Assembly File": fname,
                                "N50": f"{n50:,}",
                                "GC %": round(gc_pct, 2),
                                "Total Length": f"{total_sum:,}",
                                "Contigs": len(lengths)
                            })
                    except Exception as e:
                        st.error(f"Error parsing {fname}: {e}")
                        continue
        
        if fasta_stats:
            st.dataframe(pd.DataFrame(fasta_stats), use_container_width=True)
        if fasta_stats:
            st.dataframe(pd.DataFrame(fasta_stats), use_container_width=True)
    else:
        st.warning("No assembly files (.fasta/.fna) detected yet.")

    # --- SECTION 3: CLINICAL AMR REPORT ---
    st.divider()
    st.subheader("💊 3. Clinical AMR Findings")
    amr_keys = [k for k in list_s3_files(f"{res_prefix}amrfinderplus/") if k.endswith(".tsv")]
    if amr_keys:
        all_amr = []
        for key in amr_keys:
            sample = os.path.basename(key).replace("_amr.tsv", "").replace(".tsv", "")
            try:
                content = get_s3_file_content(key)
                df = pd.read_csv(io.StringIO(content), sep='\t')
                if not df.empty:
                    df.insert(0, "Sample", sample)
                    df.insert(1, "Status", "🧬 RESISTANT")
                    all_amr.append(df)
                else:
                    all_amr.append(pd.DataFrame({
                        "Sample": [sample], 
                        "Status": ["🟢 CLEAN"], 
                        "Gene symbol": ["-"], 
                        "Class": ["No resistance genes detected"]
                    }))
            except Exception as e:
                st.error(f"Error reading AMR results for {sample}: {e}")
                continue       
              
        
        if all_amr:
            master_amr = pd.concat(all_amr, ignore_index=True, sort=False)
            
            # Map for professional headers
            cols = {"Sample":"Sample", "Status":"Status", "Gene symbol":"Gene", 
                    "Class":"Antibiotic Class", "% Identity":"Identity %"}
            
            avail = [c for c in cols.keys() if c in master_amr.columns]
            final_df = master_amr[avail].rename(columns=cols)

           
            try:
                def color_status(val):
                    return 'color: red; font-weight: bold' if val == "Resistant" else 'color: green'
                st.dataframe(final_df.style.map(color_status, subset=['Status']), use_container_width=True)
            except Exception:
            
                st.dataframe(final_df, use_container_width=True)
            
            # Download and Search
            st.download_button("📥 Download Full Report", master_amr.to_csv(index=False), "AMR_Report.csv")
            search = st.text_input("🔍 Search Genes (e.g. bla, tet, gyr)")
            if search:
                query = master_amr[master_amr.apply(lambda r: r.astype(str).str.contains(search, case=False).any(), axis=1)]
                st.dataframe(query, width='stretch')
        else:
            st.info("All samples processed. No resistance genes found.")
    else:
        st.info("Waiting for AMRFinderPlus output...")

    if st.button("🔄 Refresh Data"):
        st.rerun()