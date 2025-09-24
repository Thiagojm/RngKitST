#!/usr/bin/env python3
"""
Simple Streamlit test to isolate browser performance issues
"""

import streamlit as st
import time
import plotly.graph_objects as go
import random

st.set_page_config(
    page_title="Browser Performance Test",
    page_icon="🧪",
    layout="wide"
)

def test_simple_updates():
    """Test simple text updates without complex UI"""
    st.header("🧪 Simple Update Test")
    
    if 'counter' not in st.session_state:
        st.session_state.counter = 0
    
    if st.button("Start Simple Counter"):
        st.session_state.simple_running = True
    
    if st.button("Stop Simple Counter"):
        st.session_state.simple_running = False
    
    if st.session_state.get('simple_running', False):
        @st.fragment(run_every=1)
        def update_counter():
            st.session_state.counter += 1
            st.write(f"Counter: {st.session_state.counter}")
            st.write(f"Time: {time.time()}")
        
        update_counter()

def test_plotly_simple():
    """Test simple Plotly chart updates"""
    st.header("📊 Simple Plot Test")
    
    if 'plot_data' not in st.session_state:
        st.session_state.plot_data = []
    
    if st.button("Start Simple Plot"):
        st.session_state.plot_running = True
    
    if st.button("Stop Simple Plot"):
        st.session_state.plot_running = False
    
    if st.session_state.get('plot_running', False):
        @st.fragment(run_every=1)
        def update_plot():
            # Add random data point
            st.session_state.plot_data.append(random.random())
            
            # Keep only last 50 points
            if len(st.session_state.plot_data) > 50:
                st.session_state.plot_data = st.session_state.plot_data[-50:]
            
            # Create simple plot
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                y=st.session_state.plot_data,
                mode='lines',
                name='Random Data'
            ))
            
            fig.update_layout(
                title="Simple Random Data Plot",
                height=300,
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
            st.write(f"Data points: {len(st.session_state.plot_data)}")
        
        update_plot()

def test_complex_plotly():
    """Test complex Plotly chart similar to your app"""
    st.header("📈 Complex Plot Test (Like Your App)")
    
    if 'complex_data' not in st.session_state:
        st.session_state.complex_data = []
        st.session_state.complex_index = []
    
    if st.button("Start Complex Plot"):
        st.session_state.complex_running = True
    
    if st.button("Stop Complex Plot"):
        st.session_state.complex_running = False
    
    if st.session_state.get('complex_running', False):
        @st.fragment(run_every=1)
        def update_complex_plot():
            # Simulate Z-score calculation
            new_value = random.gauss(0, 1)  # Normal distribution
            st.session_state.complex_data.append(new_value)
            st.session_state.complex_index.append(len(st.session_state.complex_data))
            
            # Keep only last 100 points
            if len(st.session_state.complex_data) > 100:
                st.session_state.complex_data = st.session_state.complex_data[-100:]
                st.session_state.complex_index = st.session_state.complex_index[-100:]
            
            # Create complex plot like your app
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=st.session_state.complex_index,
                y=st.session_state.complex_data,
                mode='lines',
                name='Z-Score',
                line=dict(color='orange', width=2)
            ))
            
            fig.update_layout(
                title="Complex Z-Score Plot (Simulated)",
                xaxis_title="Number of samples",
                yaxis_title="Z-Score",
                height=400,
                showlegend=False,
                uirevision=True,
                transition_duration=0
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Show metrics like your app
            if st.session_state.complex_data:
                current_value = st.session_state.complex_data[-1]
                current_samples = st.session_state.complex_index[-1]
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Current Z-Score", f"{current_value:.3f}")
                with col2:
                    st.metric("Samples Collected", current_samples)
                with col3:
                    if current_value > 2:
                        st.metric("Status", "🔴 High", delta="Above +2σ")
                    elif current_value < -2:
                        st.metric("Status", "🔴 Low", delta="Below -2σ")
                    else:
                        st.metric("Status", "🟢 Normal", delta="Within ±2σ")
        
        update_complex_plot()

def main():
    st.title("🧪 Browser Performance Test")
    st.markdown("This test helps isolate browser performance issues from your main app.")
    
    tab1, tab2, tab3 = st.tabs(["Simple Updates", "Simple Plot", "Complex Plot"])
    
    with tab1:
        test_simple_updates()
    
    with tab2:
        test_plotly_simple()
    
    with tab3:
        test_complex_plotly()
    
    st.markdown("---")
    st.markdown("**Instructions:**")
    st.markdown("1. Test each tab to see which one causes freezing")
    st.markdown("2. Use browser developer tools (F12) to monitor performance")
    st.markdown("3. Check if the issue is specific to Plotly charts or general UI updates")

if __name__ == "__main__":
    main()
