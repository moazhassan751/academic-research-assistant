"""
CSS Animation and Visual Blocker Diagnostic
Identifies potential issues blocking animations, transitions, and visual effects
"""

import re
from pathlib import Path

def analyze_css_blockers():
    """Analyze potential CSS blockers in the dashboard"""
    print("🔍 ANALYZING CSS AND VISUAL BLOCKERS")
    print("=" * 60)
    
    dashboard_file = Path("integrated_dashboard.py")
    
    if not dashboard_file.exists():
        print("❌ Dashboard file not found")
        return
    
    content = dashboard_file.read_text(encoding='utf-8')
    
    # Check for potential blockers
    blockers_found = []
    warnings = []
    optimizations = []
    performance_issues = []
    
    # 1. Check unsafe_allow_html usage
    if 'unsafe_allow_html=False' in content:
        blockers_found.append("❌ CRITICAL: unsafe_allow_html=False detected - This blocks all HTML/CSS!")
    elif 'unsafe_allow_html=True' in content:
        print("✅ HTML/CSS allowed: unsafe_allow_html=True found")
    else:
        warnings.append("⚠️  No explicit unsafe_allow_html found")
    
    # 2. Check for CSS animation properties
    animation_properties = [
        'transition:', 'transform:', 'animation:', '@keyframes', 
        'will-change:', 'backface-visibility:', 'translate3d', 'translateZ'
    ]
    
    found_animations = []
    for prop in animation_properties:
        if prop in content:
            found_animations.append(prop)
    
    if found_animations:
        print(f"✅ Animation properties found: {', '.join(found_animations)}")
    else:
        blockers_found.append("❌ No CSS animations/transitions detected")
    
    # 3. Check for performance optimizations
    performance_optimizations = [
        'hardware acceleration', 'GPU acceleration', 'transform: translate3d',
        'will-change:', 'backface-visibility: hidden'
    ]
    
    found_optimizations = [opt for opt in performance_optimizations if opt in content]
    if found_optimizations:
        print(f"✅ Performance optimizations: {len(found_optimizations)} found")
    else:
        warnings.append("⚠️  Few performance optimizations detected")
    
    # 4. Check for CSS utility classes vs inline styles
    utility_classes = ['.flex-center', '.text-center', '.mb-lg', '.rounded']
    found_utilities = [cls for cls in utility_classes if cls in content]
    
    if found_utilities:
        print(f"✅ CSS utility classes: {len(found_utilities)} found")
        optimizations.append("💡 Good use of utility classes reduces inline styles")
    else:
        warnings.append("⚠️  No utility classes found - heavy inline style usage likely")
    
    # 5. Check for browser compatibility
    browser_compat = ['-webkit-', '-moz-', 'transform3d', 'perspective:']
    found_compat = [comp for comp in browser_compat if comp in content]
    
    if found_compat:
        print(f"✅ Browser compatibility features: {len(found_compat)} found")
    else:
        warnings.append("⚠️  Limited browser compatibility optimizations")
    
    # Enhanced checks continue with original code...
    
    # Check for excessive !important usage
    important_count = len(re.findall(r'!important', content))
    if important_count > 70:
        performance_issues.append(f"⚠️  Excessive !important usage ({important_count} instances)")
    elif important_count > 0:
        print(f"✅ Reasonable !important usage: {important_count} instances")
    
    # Check for inline styles vs CSS classes
    inline_style_count = len(re.findall(r'style=', content))
    if inline_style_count > 120:
        performance_issues.append(f"⚠️  Many inline styles ({inline_style_count}) - consider CSS classes")
        # Analyze common inline style patterns
        flex_patterns = len(re.findall(r'display:\s*flex', content))
        color_patterns = len(re.findall(r'color:\s*var\(--[^)]+\)', content))
        spacing_patterns = len(re.findall(r'margin|padding', content))
        
        if flex_patterns > 10:
            optimizations.append(f"💡 Create .flex-* utility classes ({flex_patterns} flex patterns found)")
        if color_patterns > 15:
            optimizations.append(f"💡 Create .text-* color classes ({color_patterns} color patterns found)")
        if spacing_patterns > 20:
            optimizations.append(f"💡 Create .m-* .p-* spacing classes ({spacing_patterns} spacing patterns found)")
            
    elif inline_style_count > 50:
        warnings.append(f"⚠️  Moderate inline styles ({inline_style_count}) - optimization possible")
    else:
        print(f"✅ Optimized inline styles: {inline_style_count} instances")
    
    # 4. Check for Streamlit-specific blockers
    streamlit_blockers = []
    
    if '.stDeployButton' in content and 'visibility: hidden' in content:
        print("✅ Streamlit UI elements properly hidden")
    
    if 'initial_sidebar_state="collapsed"' in content:
        print("✅ Sidebar optimization: collapsed by default")
    
    # 5. Check CSS variable usage
    css_variables = re.findall(r'var\(--[\w-]+\)', content)
    if len(css_variables) > 50:
        print(f"✅ Good CSS variable usage: {len(css_variables)} variables")
    else:
        optimizations.append("💡 Consider using more CSS variables for consistency")
    
    # 6. Check for responsive design
    responsive_queries = content.count('@media')
    if responsive_queries >= 3:
        print(f"✅ Responsive design: {responsive_queries} media queries")
    else:
        optimizations.append("💡 Consider adding more responsive breakpoints")
    
    # 7. Check for modern CSS features
    modern_features = [
        'grid-template-columns', 'flex:', 'backdrop-filter:', 
        'box-shadow:', 'border-radius:'
    ]
    
    found_modern = [f for f in modern_features if f in content]
    if len(found_modern) >= 3:
        print(f"✅ Modern CSS features: {', '.join(found_modern[:3])}...")
    else:
        optimizations.append("💡 Consider using more modern CSS features")
    
    # 8. Browser compatibility checks
    compatibility_issues = []
    
    if '-webkit-' in content:
        print("✅ Webkit prefixes found for browser compatibility")
    
    if 'backface-visibility: hidden' in content:
        print("✅ 3D acceleration optimization found")
    
    # Report findings
    print("\n" + "=" * 60)
    print("📊 DIAGNOSTIC RESULTS")
    print("=" * 60)
    
    if not blockers_found and not performance_issues:
        print("🎉 EXCELLENT! No critical blockers found.")
        print("✨ Your CSS animations and visuals should work perfectly!")
    else:
        if blockers_found:
            print("🚨 CRITICAL BLOCKERS FOUND:")
            for blocker in blockers_found:
                print(f"  {blocker}")
        
        if performance_issues:
            print("\n⚠️  PERFORMANCE CONCERNS:")
            for issue in performance_issues:
                print(f"  {issue}")
    
    if warnings:
        print("\n🔔 WARNINGS:")
        for warning in warnings:
            print(f"  {warning}")
    
    if optimizations:
        print("\n💡 OPTIMIZATION SUGGESTIONS:")
        for opt in optimizations:
            print(f"  {opt}")
    
    # Browser-specific recommendations
    print("\n🌐 BROWSER COMPATIBILITY RECOMMENDATIONS:")
    print("  ✅ Use modern browsers (Chrome 90+, Firefox 88+, Safari 14+)")
    print("  ✅ Enable hardware acceleration in browser settings")
    print("  ✅ Ensure JavaScript is enabled")
    print("  ✅ Clear browser cache if animations don't appear")
    
    # Comprehensive optimization guide
    if blockers_found or performance_issues or len(optimizations) > 2:
        print("\n🚀 PERFORMANCE OPTIMIZATION GUIDE:")
        print("=" * 60)
        
        if inline_style_count > 120:
            print("📋 CSS CLASS OPTIMIZATION RECOMMENDATIONS:")
            print("  1. Create utility classes for common flex layouts:")
            print("     .flex-between { display: flex; justify-content: space-between; align-items: center; }")
            print("     .flex-center { display: flex; align-items: center; justify-content: center; }")
            print("     .flex-column { display: flex; flex-direction: column; }")
            print()
            print("  2. Create semantic color classes:")
            print("     .text-primary { color: var(--primary-600); }")
            print("     .text-secondary { color: var(--gray-600); }")
            print("     .text-muted { color: var(--gray-400); }")
            print()
            print("  3. Create spacing utility classes:")
            print("     .mt-sm { margin-top: var(--spacing-sm); }")
            print("     .mb-md { margin-bottom: var(--spacing-md); }")
            print("     .p-lg { padding: var(--spacing-lg); }")
            print()
            print("  4. Create component-specific classes:")
            print("     .paper-header { display: flex; justify-content: space-between; margin-bottom: var(--spacing-md); }")
            print("     .metric-value { font-size: var(--font-size-3xl); font-weight: 700; }")
            print("     .status-badge { padding: var(--spacing-xs) var(--spacing-sm); border-radius: var(--radius-md); }")
        
        print("\n⚡ ANIMATION PERFORMANCE TIPS:")
        print("  1. Use transform and opacity for animations (GPU accelerated)")
        print("  2. Add will-change property for elements that will animate")
        print("  3. Use translate3d(0,0,0) to force hardware acceleration")
        print("  4. Avoid animating layout properties (width, height, padding, margin)")
        print("  5. Use CSS containment for isolated animation areas")
        
        print("\n🎨 VISUAL ENHANCEMENT SUGGESTIONS:")
        print("  1. Add micro-interactions for better UX")
        print("  2. Use consistent timing functions (cubic-bezier)")
        print("  3. Add loading states with skeleton screens")
        print("  4. Implement proper focus management for accessibility")
        print("  5. Add reduced motion support with @media (prefers-reduced-motion)")
    
    return len(blockers_found) == 0 and len(performance_issues) == 0

if __name__ == "__main__":
    success = analyze_css_blockers()
    print(f"\n{'✅ VISUAL SYSTEM HEALTHY' if success else '❌ ISSUES DETECTED'}")
