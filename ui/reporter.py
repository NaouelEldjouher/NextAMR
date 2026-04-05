import streamlit as st
import pandas as pd
import os
import glob
import json

def render_reporter():
    st.header("📊 AMR-Flow Analysis Dashboard")
    res_dir = "nextflow/results"
    
    if not os.path.exists(res_dir):
        st.error(f"❌ Results folder not found at `{res_dir}`.")
        return

    # --- SECTION 1: RAW READ QUALITY (FASTP) ---
    st.subheader("🧬 1. Raw Read Metrics")
    fastp_files = glob.glob(os.path.join(res_dir, "fastp", "*.json"))
    
    if fastp_files:
        qc_stats = []
        for f in fastp_files:
            sample = os.path.basename(f).replace(".json", "")
            try:
                with open(f, 'r') as j:
                    data = json.load(j).get('summary', {}).get('after_filtering', {})
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
    fasta_files = glob.glob(os.path.join(res_dir, "**", "*.fna"), recursive=True) + \
                  glob.glob(os.path.join(res_dir, "**", "*.fasta"), recursive=True)

    if fasta_files:
        fasta_stats = []
        for f in fasta_files:
            fname = os.path.basename(f)
            # Filter for main assembly files to avoid cluttering with proteins (.faa)
            if any(x in fname.lower() for x in ["polished", "assembly", "flye", "unicycler", "polypolish"]):
                try:
                    with open(f, 'r') as file:
                        # Simple Fasta Parsing
                        content = file.read()
                        sections = content.split('>')
                        lengths = []
                        total_seq = ""
                        for s in sections[1:]:
                            lines = s.split('\n')
                            seq = "".join(lines[1:]).replace('\n','').replace('\r','')
                            lengths.append(len(seq))
                            total_seq += seq
                        
                        # GC %
                        gc_count = total_seq.count('G') + total_seq.count('C')
                        gc_pct = (gc_count / len(total_seq) * 100) if total_seq else 0
                        
                        # N50
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
                except Exception: continue
        
        if fasta_stats:
            st.dataframe(pd.DataFrame(fasta_stats), width='stretch')
    else:
        st.warning("No assembly files (.fasta/.fna) detected yet.")

    # --- SECTION 3: CLINICAL AMR REPORT ---
    st.divider()
    st.subheader("💊 3. Clinical AMR Findings")
    amr_files = glob.glob(os.path.join(res_dir, "amrfinderplus", "*.tsv"))
    
    if amr_files:
        all_amr = []
        for f in amr_files:
            sample = os.path.basename(f).replace("_amr.tsv", "").replace(".tsv", "")
            try:
                # Skip header-only files (usually ~294 bytes)
                if os.path.getsize(f) > 350: 
                    df = pd.read_csv(f, sep='\t')
                    if not df.empty:
                        df.insert(0, "Sample", sample)
                        df["Status"] = "🧬 RESISTANT"
                        all_amr.append(df)
                else:
                    all_amr.append(pd.DataFrame({
                        "Sample": [sample], "Status": ["🟢 CLEAN"], 
                        "Gene symbol": ["-"], "Class": ["No genes detected"]
                    }))
            except Exception: continue
        
        if all_amr:
            master_amr = pd.concat(all_amr, ignore_index=True, sort=False)
            
            # Map for professional headers
            cols = {"Sample":"Sample", "Status":"Status", "Gene symbol":"Gene", 
                    "Class":"Antibiotic Class", "% Identity":"Identity %"}
            
            avail = [c for c in cols.keys() if c in master_amr.columns]
            final_df = master_amr[avail].rename(columns=cols)

            # Styling logic for Modern Pandas (.map instead of .applymap)
            def color_status(val):
                return 'color: red; font-weight: bold' if val == "🧬 RESISTANT" else 'color: green'

            st.dataframe(final_df.style.map(color_status, subset=['Status']), width='stretch')
            
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