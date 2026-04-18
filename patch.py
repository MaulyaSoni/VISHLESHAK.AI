with open('patch_data_agent.py', 'r', encoding='utf-8') as f:
    text = f.read()

old_str = '''            # Manual refresh button
            if st.button("?? Refresh Status"):
                st.rerun()'''

new_str = '''            # Refresh and Stop buttons
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("?? Refresh Status", use_container_width=True):
                    st.rerun()
            with col_btn2:
                if st.button("?? Stop Agent", type="secondary", use_container_width=True):
                    try:
                        import data_agent_3 as da3
                        da3.cancel_agent()
                    except:
                        pass
                    st.session_state.agent_status = "canceled"
                    st.rerun()'''

text = text.replace(old_str, new_str)
with open('patch_data_agent.py', 'w', encoding='utf-8') as f:
    f.write(text)
