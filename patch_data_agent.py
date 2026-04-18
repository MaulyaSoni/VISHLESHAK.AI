I don't currently have file editing tools available. However, I've extracted the complete DataAgent block from your app.py. Here's the pure Python code without any leading dashes - you can save this to `patch_data_agent.py`:

```python
if st.session_state.mode == "DataAgent":
    st.markdown("## 🤖 Data Agent")

    # Left panel - Input
    col_left, col_right = st.columns([35, 65])
    
    with col_left:
        st.markdown("### 📝 Input")
        
        agent_instruction = st.text_area(
            "What do you want to analyze?",
            placeholder="analyze Insurance.csv and find trends / train a model to predict Amount / download https://... and summarize",
            height=120,
            label_visibility="collapsed",
        )
        
        agent_mode = st.radio(
            "Mode",
            ["Analysis Only", "Analysis + ML Model", "Analysis + ML + Notebook"],
            index=1,
        )
        
        uploaded_file = st.file_uploader(
            "Upload CSV (optional)",
            type=["csv"],
            label_visibility="collapsed",
            key="data_agent_uploader_2",
        )
        
        uploaded_path = None
        if uploaded_file:
            os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
            uploaded_path = os.path.join(settings.UPLOAD_FOLDER, uploaded_file.name)
            with open(uploaded_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
        
        with st.expander("⚙️ Advanced", expanded=False):
            step_delay = st.slider("Step Delay (seconds)", 1, 5, 2)
            max_loop_steps = st.slider("Max Loop Steps", 10, 25, 15)
        
        run_button = st.button("🚀 Run Agent", type="primary", use_container_width=True, key="data_agent_run_btn")
    
    with col_right:
        st.markdown("### 📊 Output")
        
        # Initialize session state for agent
        if "agent_report" not in st.session_state:
            st.session_state.agent_report = None
        if "agent_steps" not in st.session_state:
            st.session_state.agent_steps = []
        
        # Empty state - show instructions
        if not st.session_state.agent_steps and not st.session_state.agent_report:
            st.markdown("""
            <div style="background:var(--surface);border:1px solid var(--border);border-radius:0.8rem;padding:2rem;text-align:center;">
                <div style="font-size:2rem;margin-bottom:1rem;">🤖</div>
                <div style="color:var(--muted);font-size:0.9rem;">
                    Enter an instruction and click <b>Run Agent</b> to start analysis.<br>
                    Example: "analyze Insurance.csv and find trends"
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Run agent on button click
        if run_button:
            if not agent_instruction:
                st.error("Please enter an instruction")
            else:
                try:
                    from data_agent_3 import run_agent
                    
                    # Prepare instruction with file path
                    final_instruction = agent_instruction
                    if uploaded_path:
                        final_instruction = f"{uploaded_path} - {agent_instruction}"
                    
                    st.session_state.agent_status = "running"
                    st.session_state.agent_steps = []
                    st.session_state.agent_report = None
                    
                    # Run agent in a thread
                    import threading
                    
                    def run_agent_thread():
                        try:
                            from data_agent_3 import run_agent
                            
                            # Monkey-patch log to capture steps
                            import data_agent_3 as da3
                            original_log = da3.log
                            
                            def patched_log(state, msg):
                                original_log(state, msg)
                                # Extract step name
                                step_name = msg.split(" → ")[0] if " → " in msg else msg[:30]
                                # Track step status
                                if "✅" in msg:
                                    st.session_state.agent_steps.append({"step": step_name, "status": "done"})
                                elif "⟳" in msg:
                                    st.session_state.agent_steps.append({"step": step_name, "status": "running"})
                                # Mark previous running as done when new step starts
                                if "⟳" in msg:
                                    for i, s in enumerate(st.session_state.agent_steps):
                                        if s["status"] == "running":
                                            st.session_state.agent_steps[i]["status"] = "done"
                            
                            da3.log = patched_log
                            
                            # Run agent
                            report = run_agent(final_instruction)
                            st.session_state.agent_report = report
                            st.session_state.agent_status = "done"
                        except Exception as e:
                            st.session_state.agent_status = "error"
                            st.session_state.agent_error = str(e)
                    
                    thread = threading.Thread(target=run_agent_thread, daemon=True)
                    thread.start()
                    
                    # Small delay to let thread start
                    import time
                    time.sleep(0.5)
                    
                    # Check if already completed (fast execution)
                    if st.session_state.agent_report is not None:
                        st.session_state.agent_status = "done"
                    elif st.session_state.get("agent_error"):
                        st.session_state.agent_status = "error"
                    
                    st.rerun()
                    
                except ImportError as e:
                    st.error(f"❌ Could not import data_agent_3: {e}")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        
        # Show progress during run
        if st.session_state.get("agent_status") == "running":
            st.markdown("#### 🔄 Agent Running...")
            st.info("Please wait while the agent processes your request...")
            
            # Show any captured steps so far
            for step_info in st.session_state.agent_steps:
                status = step_info["status"]
                step_name = step_info["step"]
                icon = "✅" if status == "done" else "🔄"
                st.markdown(f"{icon} {step_name}")
            
            # Manual refresh button
            if st.button("🔄 Refresh Status"):
                st.rerun()
            
            st.markdown("<hr>", unsafe_allow_html=True)
        
        # Show results after run
        if st.session_state.get("agent_status") == "done" and st.session_state.agent_report:
            report = st.session_state.agent_report
            
            # Result tabs
            sub_tabs = st.tabs(["📋 Summary", "📈 Charts", "🤖 ML Results", "📓 Notebook", "📄 Raw JSON"])
            
            with sub_tabs[0]:
                # Summary tab
                st.markdown("#### 📋 Summary")
                
                # Metric cards
                m_rows = report.get("rows", "N/A")
                m_cols = report.get("columns", "N/A")
                m_charts = len(report.get("charts", []))
                m_model = report.get("ml_results", {}).get("metrics", {}).get("r2_score") or report.get("ml_results", {}).get("metrics", {}).get("accuracy") or "N/A"
                
                mc1, mc2, mc3, mc4 = st.columns(4)
                mc1.markdown(f"""
                <div style="background:#1a1a2e;border:1px solid #2a2a3e;border-radius:8px;padding:16px 20px;text-align:center;">
                    <div style="font-size:11px;color:#7c7c9a;text-transform:uppercase;letter-spacing:1px;">Rows</div>
                    <div style="font-size:28px;color:#4fc3f7;">{m_rows}</div>
                </div>
                """, unsafe_allow_html=True)
                mc2.markdown(f"""
                <div style="background:#1a1a2e;border:1px solid #2a2a3e;border-radius:8px;padding:16px 20px;text-align:center;">
                    <div style="font-size:11px;color:#7c7c9a;text-transform:uppercase;letter-spacing:1px;">Columns</div>
                    <div style="font-size:28px;color:#4fc3f7;">{m_cols}</div>
                </div>
                """, unsafe_allow_html=True)
                mc3.markdown(f"""
                <div style="background:#1a1a2e;border:1px solid #2a2a3e;border-radius:8px;padding:16px 20px;text-align:center;">
                    <div style="font-size:11px;color:#7c7c9a;text-transform:uppercase;letter-spacing:1px;">Charts</div>
                    <div style="font-size:28px;color:#4fc3f7;">{m_charts}</div>
                </div>
                """, unsafe_allow_html=True)
                mc4.markdown(f"""
                <div style="background:#1a1a2e;border:1px solid #2a2a3e;border-radius:8px;padding:16px 20px;text-align:center;">
                    <div style="font-size:11px;color:#7c7c9a;text-transform:uppercase;letter-spacing:1px;">Model Score</div>
                    <div style="font-size:28px;color:#4fc3f7;">{m_model}</div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Executive summary
                exec_summary = report.get("executive_summary", "No summary available")
                st.markdown(f"""
                <div style="background:#0d2137;border-left:3px solid #4fc3f7;padding:16px;border-radius:0 8px 8px 0;">
                    <div style="font-size:0.8rem;color:#7c7c9a;margin-bottom:0.5rem;">EXECUTIVE SUMMARY</div>
                    {exec_summary}
                </div>
                """, unsafe_allow_html=True)
                
                # Key findings
                findings = report.get("key_findings", [])
                if findings:
                    st.markdown("#### ◆ Key Findings")
                    for finding in findings:
                        st.markdown(f"- {finding}")
                
                # Recommendations
                recommendations = report.get("recommendations", [])
                if recommendations:
                    st.markdown("""
                    <div style="background:#0d2137;border-left:3px solid #10b981;padding:16px;border-radius:0 8px 8px 0;margin-top:1rem;">
                        <div style="font-size:0.8rem;color:#7c7c9a;margin-bottom:0.5rem;">RECOMMENDATIONS</div>
                    </div>
                    """, unsafe_allow_html=True)
                    for rec in recommendations:
                        st.markdown(f"- {rec}")
                
                # Preprocessing steps
                with st.expander("🔧 Preprocessing Steps"):
                    steps = report.get("preprocessing", [])
                    if steps:
                        for step in steps:
                            st.markdown(f"- {step}")
                    else:
                        st.info("No preprocessing steps recorded")
            
            with sub_tabs[1]:
                # Charts tab
                st.markdown("#### 📈 Charts")
                charts = report.get("charts", [])
                if charts:
                    for chart in charts:
                        html_path = chart.get("html_path")
                        png_path = chart.get("png_path")
                        title = chart.get("title", "Chart")
                        
                        if html_path and os.path.exists(html_path):
                            try:
                                with open(html_path, "r", encoding="utf-8") as f:
                                    html_content = f.read()
                                st.components.v1.html(html_content, height=480)
                                
                                # Interpretation
                                interp = chart.get("interpretation", "")
                                if interp:
                                    st.markdown(f"*{interp}*")
                                
                                # Download PNG
                                if png_path and os.path.exists(png_path):
                                    with open(png_path, "rb") as f:
                                        png_bytes = f.read()
                                    st.download_button(
                                        label=f"⬇️ Download {title}",
                                        data=png_bytes,
                                        file_name=os.path.basename(png_path),
                                        mime="image/png",
                                    )
                                st.markdown("---")
                            except Exception as e:
                                st.error(f"Error loading chart: {e}")
                else:
                    st.info("No charts generated")
            
            with sub_tabs[2]:
                # ML Results tab
                st.markdown("#### 🤖 ML Results")
                ml_results = report.get("ml_results", {})
                
                if ml_results:
                    metrics = ml_results.get("metrics", {})
                    task_type = ml_results.get("task_type", "N/A")
                    target_col = ml_results.get("target_col", "N/A")
                    feat_cols = ml_results.get("feature_cols", [])
                    
                    st.markdown(f"**Task:** {task_type} | **Target:** {target_col}")
                    
                    # Metrics cards
                    if task_type == "regression":
                        rmse = metrics.get("rmse", "N/A")
                        r2 = metrics.get("r2_score", "N/A")
                        mm1, mm2 = st.columns(2)
                        mm1.metric("RMSE", rmse)
                        mm2.metric("R² Score", r2)
                    else:
                        acc = metrics.get("accuracy", "N/A")
                        st.metric("Accuracy", acc)
                    
                    # SHAP chart
                    shap_importance = ml_results.get("shap_importance", {})
                    if shap_importance:
                        st.markdown("##### SHAP Feature Importance")
                        shap_df = pd.DataFrame(list(shap_importance.items()), columns=["Feature", "Importance"])
                        shap_df = shap_df.sort_values("Importance", ascending=True)
                        st.bar_chart(shap_df.set_index("Feature"))
                    
                    # Feature importance
                    feat_imp = ml_results.get("feature_importance", {})
                    if feat_imp:
                        st.markdown("##### Feature Importance")
                        fi_df = pd.DataFrame(list(feat_imp.items()), columns=["Feature", "Importance"])
                        fi_df = fi_df.sort_values("Importance", ascending=False).head(10)
                        st.dataframe(fi_df, hide_index=True)
                    
                    # Train/test split info
                    n_train = ml_results.get("n_train", "N/A")
                    n_test = ml_results.get("n_test", "N/A")
                    st.markdown(f"**Train size:** {n_train} | **Test size:** {n_test}")
                else:
                    st.info("No ML results - run with Analysis + ML Model mode")
            
            with sub_tabs[3]:
                # Notebook tab
                st.markdown("#### 📓 Notebook")
                nb_path = report.get("notebook_path")
                
                if nb_path and os.path.exists(nb_path):
                    st.success("✅ Notebook generated and executed")
                    
                    # Download button
                    with open(nb_path, "rb") as f:
                        nb_bytes = f.read()
                    st.download_button(
                        label="⬇️ Download Notebook",
                        data=nb_bytes,
                        file_name=os.path.basename(nb_path),
                        mime="application/octet-stream",
                    )
                    
                    # Preview first cells
                    with st.expander("📋 Preview Notebook", expanded=False):
                        try:
                            import nbformat
                            nb = nbformat.read(os.path.abspath(nb_path), as_version=4)
                            for i, cell in enumerate(nb.cells[:5]):
                                if cell.cell_type == "code":
                                    st.markdown(f"```python\n{cell.source}\n```")
                                else:
                                    st.markdown(f"{cell.source}")
                        except Exception as e:
                            st.info(f"Could not preview: {e}")
                else:
                    st.info("No notebook generated - run with Analysis + ML + Notebook mode")
            
            with sub_tabs[4]:
                # Raw JSON tab
                st.markdown("#### 📄 Raw JSON")
                st.json(report)
        
        # Error display
        if st.session_state.get("agent_status") == "error":
            error_msg = st.session_state.get("agent_error", "Unknown error")
            st.error(f"❌ Agent failed: {error_msg}")
            
            # Show traceback in expander
            with st.expander("📋 Full Error Details"):
                st.code(error_msg)
```

To create the file, you'll need to enable file editing tools in VS Code. Alternatively, you can copy this code and manually create the file.

