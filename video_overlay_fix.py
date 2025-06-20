def create_stable_video_overlay(self, video_file, goal_events):
    """Create stable video overlay system without app resets"""
    
    # Display the video using Streamlit's native player
    st.video(video_file)
    
    # Create goal-based advertisement system
    if goal_events:
        st.markdown("### Goal-Triggered Jersey Advertisements")
        st.info(f"Found {len(goal_events)} goal moments with automatic jersey targeting")
        
        # Initialize session state for overlay
        if 'show_test_overlay' not in st.session_state:
            st.session_state.show_test_overlay = False
        
        # Show goal timeline with interactive advertisements
        st.markdown("#### Goal Timeline & Advertisement System")
        
        for i, event in enumerate(goal_events):
            timestamp_str = event.get('timestamp', f'{i*60}:00')
            description = event.get('description', '')
            
            # Get player merchandise
            player_key = self.extract_player_from_event(description)
            if player_key and player_key in self.merchandise_db:
                merchandise = self.merchandise_db[player_key]
            else:
                merchandise = self.merchandise_db['messi']
            
            # Create collapsible goal advertisement
            with st.expander(f"⚽ {timestamp_str} - {merchandise['name']} Goal Advertisement"):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(45deg, #ff6b6b, #ee5a52);
                        color: white;
                        padding: 20px;
                        border-radius: 15px;
                        text-align: center;
                        box-shadow: 0 8px 16px rgba(0,0,0,0.3);
                    ">
                        <h3 style="margin: 0 0 10px 0; color: #90EE90;">⚽ GOAL SCORER</h3>
                        <h2 style="margin: 0 0 8px 0; font-size: 28px;">{merchandise['name']}</h2>
                        <p style="margin: 0 0 15px 0; font-size: 16px; opacity: 0.9;">{merchandise['team']}</p>
                        <div style="background: rgba(255,255,255,0.2); padding: 15px; border-radius: 10px;">
                            <p style="margin: 0 0 8px 0; font-size: 14px;">Official Jersey</p>
                            <h1 style="margin: 0; color: #90EE90; font-size: 36px;">${merchandise['jersey_price']:.2f}</h1>
                            <p style="margin: 8px 0 0 0; font-size: 12px; opacity: 0.8;">{merchandise['description']}</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    if st.button(f"🛒 Buy Jersey", key=f"buy_stable_{i}", type="primary"):
                        st.success(f"Added {merchandise['name']} jersey to cart!")
                        st.balloons()
                    
                    if st.button(f"❤️ Save", key=f"save_stable_{i}"):
                        st.info(f"Saved {merchandise['name']} jersey to wishlist!")
                
                with col3:
                    st.metric("Goal Time", timestamp_str)
                    st.metric("Price", f"${merchandise['jersey_price']:.2f}")
                    st.write(f"**Player:** {merchandise['name']}")
                    st.write(f"**Team:** {merchandise['team']}")
        
        # Add stable overlay test system
        st.markdown("---")
        st.markdown("#### Overlay Advertisement Test")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🎬 Show Overlay Ad", type="secondary"):
                st.session_state.show_test_overlay = True
        
        with col2:
            if st.button("❌ Hide Overlay", type="secondary"):
                st.session_state.show_test_overlay = False
        
        # Display overlay if active
        if st.session_state.show_test_overlay and goal_events:
            event = goal_events[0]
            player_key = self.extract_player_from_event(event.get('description', ''))
            if player_key and player_key in self.merchandise_db:
                merchandise = self.merchandise_db[player_key]
            else:
                merchandise = self.merchandise_db['messi']
            
            # Display overlay advertisement
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
                color: white;
                padding: 25px;
                border-radius: 20px;
                margin: 20px 0;
                box-shadow: 0 15px 35px rgba(255,107,107,0.4);
                border: 3px solid #fff;
                text-align: center;
                animation: slideInRight 0.8s ease-out;
            ">
                <h1 style="margin: 0 0 15px 0; font-size: 32px; color: #90EE90;">⚽ GOAL!</h1>
                <h2 style="margin: 0 0 10px 0; font-size: 28px;">{merchandise['name']}</h2>
                <p style="margin: 0 0 20px 0; font-size: 18px; opacity: 0.9;">{merchandise['team']}</p>
                <div style="background: rgba(255,255,255,0.2); padding: 20px; border-radius: 15px; margin-bottom: 20px;">
                    <p style="margin: 0 0 10px 0; font-size: 16px;">Get the Official Jersey!</p>
                    <h1 style="margin: 0; color: #90EE90; font-size: 40px;">${merchandise['jersey_price']:.2f}</h1>
                    <p style="margin: 10px 0 0 0; font-size: 14px; opacity: 0.8;">Limited Time Offer</p>
                </div>
                <p style="margin: 0; font-size: 14px; opacity: 0.7;">This overlay appears during goal moments</p>
            </div>
            <style>
            @keyframes slideInRight {{
                from {{ transform: translateX(100%); opacity: 0; }}
                to {{ transform: translateX(0); opacity: 1; }}
            }}
            </style>
            """, unsafe_allow_html=True)
            
            # Add purchase buttons for the overlay
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"🛒 Buy {merchandise['name']} Jersey", key="overlay_buy", type="primary"):
                    st.success(f"Added {merchandise['name']} jersey to cart for ${merchandise['jersey_price']:.2f}!")
                    st.balloons()
                    st.session_state.show_test_overlay = False
            
            with col2:
                if st.button(f"❤️ Save Jersey", key="overlay_save"):
                    st.info(f"Saved {merchandise['name']} jersey to wishlist!")
                    st.session_state.show_test_overlay = False