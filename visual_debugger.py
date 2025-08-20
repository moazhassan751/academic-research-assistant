"""
Visual Animation Debugger
Helps identify and fix animation/visual issues in the dashboard
"""

import streamlit as st
import time

def add_visual_debugger():
    """Add visual debugging tools to the dashboard"""
    
    # Only show debugger in development mode
    if st.secrets.get("ENVIRONMENT", "development") == "development":
        
        with st.expander("🔧 Visual Debugger (Dev Mode)", expanded=False):
            st.markdown("### Animation & Visual Tests")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🎬 Test Animations"):
                    test_animations()
            
            with col2:
                if st.button("🎨 Test Colors"):
                    test_color_scheme()
                    
            with col3:
                if st.button("📱 Test Responsive"):
                    test_responsive_design()

def test_animations():
    """Test various animations"""
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #0ea5e9 0%, #8b5cf6 100%);
        color: white;
        padding: 20px;
        border-radius: 12px;
        margin: 10px 0;
        animation: slideInUp 0.6s ease-out;
        transform: translateY(0);
    ">
        <h3>✨ Animation Test</h3>
        <p>If you see this box smoothly slide in, animations are working!</p>
    </div>
    
    <div style="
        background: white;
        border: 2px solid #e2e8f0;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        transition: all 0.3s ease;
        cursor: pointer;
    " 
    onmouseover="this.style.transform='translateY(-4px)'; this.style.boxShadow='0 10px 25px rgba(0,0,0,0.1)'"
    onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 4px rgba(0,0,0,0.1)'">
        <p>🖱️ <strong>Hover Test:</strong> This should lift up on hover</p>
    </div>
    
    <style>
    @keyframes slideInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.success("✅ Animation test complete! Check the boxes above.")

def test_color_scheme():
    """Test color scheme visibility"""
    st.markdown("""
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0;">
        <div style="background: #ffffff; color: #1e293b; padding: 15px; border-radius: 8px; border: 1px solid #e2e8f0;">
            <h4>Primary Background</h4>
            <p>Black text on white - Should be highly visible</p>
            <input type="text" placeholder="Test typing here" style="width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px; color: #000000; background: #ffffff;">
        </div>
        
        <div style="background: #f8fafc; color: #334155; padding: 15px; border-radius: 8px; border: 1px solid #e2e8f0;">
            <h4>Secondary Background</h4>
            <p>Dark gray text on light gray</p>
            <input type="text" placeholder="Test typing here" style="width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px; color: #000000; background: #ffffff;">
        </div>
        
        <div style="background: linear-gradient(135deg, #0ea5e9 0%, #8b5cf6 100%); color: white; padding: 15px; border-radius: 8px;">
            <h4>Accent Gradient</h4>
            <p>White text on gradient - Should be readable</p>
        </div>
        
        <div style="background: #1e293b; color: white; padding: 15px; border-radius: 8px;">
            <h4>Dark Background</h4>
            <p>White text on dark - High contrast</p>
            <input type="text" placeholder="Test typing here" style="width: 100%; padding: 8px; border: 1px solid #666; border-radius: 4px; color: #000000; background: #ffffff;">
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.info("💡 All input fields should have black text on white background for optimal visibility")

def test_responsive_design():
    """Test responsive design elements"""
    st.markdown("""
    <div style="background: #f1f5f9; padding: 20px; border-radius: 12px; margin: 20px 0;">
        <h3>📱 Responsive Design Test</h3>
        <p>Resize your browser window to test responsive behavior</p>
        
        <div style="
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
            gap: 15px; 
            margin-top: 20px;
        ">
            <div style="background: white; padding: 15px; border-radius: 8px; border: 2px solid #0ea5e9;">
                <h4 style="color: #0ea5e9;">Desktop View</h4>
                <p>Multiple columns side by side</p>
            </div>
            <div style="background: white; padding: 15px; border-radius: 8px; border: 2px solid #8b5cf6;">
                <h4 style="color: #8b5cf6;">Tablet View</h4>
                <p>Responsive grid layout</p>
            </div>
            <div style="background: white; padding: 15px; border-radius: 8px; border: 2px solid #10b981;">
                <h4 style="color: #10b981;">Mobile View</h4>
                <p>Stacked on small screens</p>
            </div>
        </div>
        
        <div style="
            margin-top: 20px; 
            padding: 15px; 
            background: white; 
            border-radius: 8px;
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            align-items: center;
            justify-content: space-between;
        ">
            <span style="font-weight: 600;">Flexible Layout:</span>
            <span style="background: #0ea5e9; color: white; padding: 5px 10px; border-radius: 20px; font-size: 12px;">DESKTOP</span>
            <span style="background: #8b5cf6; color: white; padding: 5px 10px; border-radius: 20px; font-size: 12px;">TABLET</span>
            <span style="background: #10b981; color: white; padding: 5px 10px; border-radius: 20px; font-size: 12px;">MOBILE</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def show_performance_tips():
    """Show performance optimization tips"""
    st.markdown("""
    ### 🚀 Performance Optimization Tips
    
    **For Better Animations:**
    - Use modern browsers (Chrome 90+, Firefox 88+, Safari 14+)
    - Enable hardware acceleration in browser settings
    - Close unnecessary browser tabs
    - Clear browser cache regularly
    
    **If Animations Don't Work:**
    1. Hard refresh the page (Ctrl+Shift+R or Cmd+Shift+R)
    2. Check browser console for errors (F12 → Console)
    3. Disable browser extensions temporarily
    4. Try in incognito/private mode
    
    **Visual Issues:**
    - Zoom level should be 100% for best experience
    - Check if "Reduce motion" is disabled in OS accessibility settings
    - Ensure JavaScript is enabled
    """)

# Export functions for use in main dashboard
__all__ = ['add_visual_debugger', 'test_animations', 'test_color_scheme', 'test_responsive_design', 'show_performance_tips']
