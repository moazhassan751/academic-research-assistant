"""
CSS Optimization Script
Analyzes and optimizes inline styles in the dashboard
"""

import re
from pathlib import Path
from collections import Counter

def analyze_inline_styles():
    """Analyze inline style patterns and suggest optimizations"""
    print("🔧 CSS OPTIMIZATION ANALYSIS")
    print("=" * 60)
    
    dashboard_file = Path("integrated_dashboard.py")
    
    if not dashboard_file.exists():
        print("❌ Dashboard file not found")
        return
    
    content = dashboard_file.read_text(encoding='utf-8')
    
    # Extract all inline styles
    style_pattern = r'style="([^"]+)"'
    inline_styles = re.findall(style_pattern, content)
    
    print(f"📊 Found {len(inline_styles)} inline styles")
    
    # Analyze common patterns
    patterns = {}
    
    # Flex patterns
    flex_patterns = []
    for style in inline_styles:
        if 'display: flex' in style:
            flex_patterns.append(style)
    
    # Color patterns
    color_patterns = []
    for style in inline_styles:
        if 'color:' in style:
            color_patterns.append(style)
    
    # Spacing patterns
    spacing_patterns = []
    for style in inline_styles:
        if any(prop in style for prop in ['margin', 'padding']):
            spacing_patterns.append(style)
    
    print(f"\n📋 PATTERN ANALYSIS:")
    print(f"  🔲 Flex layouts: {len(flex_patterns)}")
    print(f"  🎨 Color declarations: {len(color_patterns)}")
    print(f"  📏 Spacing declarations: {len(spacing_patterns)}")
    
    # Most common styles
    style_counter = Counter(inline_styles)
    most_common = style_counter.most_common(10)
    
    print(f"\n🔝 MOST COMMON INLINE STYLES:")
    for i, (style, count) in enumerate(most_common, 1):
        print(f"  {i}. [{count}x] {style[:80]}{'...' if len(style) > 80 else ''}")
    
    # Generate optimization suggestions
    print(f"\n💡 OPTIMIZATION SUGGESTIONS:")
    
    # Suggest utility classes for common patterns
    if len(flex_patterns) > 5:
        print(f"  1. Create flex utility classes to replace {len(flex_patterns)} flex patterns")
        common_flex = Counter(flex_patterns).most_common(3)
        for style, count in common_flex:
            class_name = suggest_class_name(style)
            print(f"     .{class_name} {{ {style} }} /* Used {count} times */")
    
    if len(color_patterns) > 10:
        print(f"  2. Create color utility classes to replace {len(color_patterns)} color patterns")
        common_colors = Counter([extract_color(style) for style in color_patterns]).most_common(5)
        for color, count in common_colors:
            if color:
                class_name = suggest_color_class_name(color)
                print(f"     .{class_name} {{ color: {color}; }} /* Used {count} times */")
    
    if len(spacing_patterns) > 10:
        print(f"  3. Create spacing utility classes to replace {len(spacing_patterns)} spacing patterns")
    
    # Generate automated replacements
    print(f"\n🤖 AUTOMATED OPTIMIZATION OPPORTUNITIES:")
    
    # Find exact duplicates that can be easily replaced
    duplicates = [(style, count) for style, count in style_counter.items() if count > 2]
    
    for style, count in duplicates[:5]:
        class_name = suggest_class_name(style)
        print(f"  Replace '{style}' with '.{class_name}' ({count} occurrences)")
    
    return {
        'total_styles': len(inline_styles),
        'flex_patterns': len(flex_patterns),
        'color_patterns': len(color_patterns),
        'spacing_patterns': len(spacing_patterns),
        'duplicates': len(duplicates)
    }

def suggest_class_name(style):
    """Suggest a CSS class name based on inline style"""
    # Simple heuristics for class naming
    if 'display: flex' in style:
        if 'justify-content: space-between' in style:
            return 'flex-between'
        elif 'justify-content: center' in style:
            return 'flex-center'
        elif 'flex-direction: column' in style:
            return 'flex-column'
        else:
            return 'flex-layout'
    elif 'margin-bottom' in style:
        if 'var(--spacing-md)' in style:
            return 'mb-md'
        elif 'var(--spacing-lg)' in style:
            return 'mb-lg'
        else:
            return 'mb-custom'
    elif 'padding' in style:
        return 'p-custom'
    elif 'font-size' in style:
        return 'text-size'
    elif 'font-weight' in style:
        return 'text-weight'
    else:
        return 'custom-style'

def extract_color(style):
    """Extract color value from style"""
    color_match = re.search(r'color:\s*([^;]+)', style)
    return color_match.group(1).strip() if color_match else None

def suggest_color_class_name(color):
    """Suggest color class name based on color value"""
    if 'primary' in color:
        return 'text-primary'
    elif 'gray-600' in color:
        return 'text-secondary'
    elif 'gray-500' in color:
        return 'text-muted'
    elif 'gray-700' in color:
        return 'text-dark'
    elif 'success' in color:
        return 'text-success'
    elif 'warning' in color:
        return 'text-warning'
    elif 'error' in color:
        return 'text-error'
    else:
        return 'text-custom'

def generate_optimization_plan():
    """Generate a comprehensive optimization plan"""
    print("\n🚀 COMPREHENSIVE OPTIMIZATION PLAN")
    print("=" * 60)
    
    stats = analyze_inline_styles()
    
    # Calculate potential reduction
    potential_reduction = stats['duplicates'] * 0.7  # Assume 70% of duplicates can be optimized
    current_total = stats['total_styles']
    projected_total = current_total - potential_reduction
    
    print(f"\n📈 OPTIMIZATION IMPACT:")
    print(f"  Current inline styles: {current_total}")
    print(f"  Projected after optimization: {projected_total:.0f}")
    print(f"  Potential reduction: {potential_reduction:.0f} ({(potential_reduction/current_total)*100:.1f}%)")
    
    print(f"\n✅ IMPLEMENTATION ROADMAP:")
    print(f"  1. Add {stats['flex_patterns']} flex utility classes")
    print(f"  2. Add {min(stats['color_patterns'], 10)} color utility classes")
    print(f"  3. Add {min(stats['spacing_patterns'], 15)} spacing utility classes")
    print(f"  4. Convert {stats['duplicates']} duplicate patterns to classes")
    print(f"  5. Implement CSS containment and performance optimizations")
    
    print(f"\n🎯 EXPECTED PERFORMANCE BENEFITS:")
    print(f"  ✅ Reduced CSS payload by ~{(potential_reduction * 50):.0f} bytes")
    print(f"  ✅ Improved caching efficiency")
    print(f"  ✅ Better maintainability")
    print(f"  ✅ Faster style computation")
    print(f"  ✅ Enhanced animation performance")

if __name__ == "__main__":
    stats = generate_optimization_plan()
    print(f"\n{'✅ ANALYSIS COMPLETE' if stats else '❌ ANALYSIS FAILED'}")
