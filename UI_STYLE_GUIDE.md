# UI Component Quick Reference Guide

## 🎨 Visual Style Guide

### Color Palette Quick Reference

```
DARK MODE                    LIGHT MODE
─────────────────────────  ─────────────────────────
Background:  #000000       Background:  #FFFFFF
Surface:     #0A0A0A       Surface:     #FAFAFA
Accent 1:    #00D9FF       Accent 1:    #0066FF
Accent 2:    #FFE500       Accent 2:    #FF0040
Accent 3:    #00FF88       Accent 3:    #00FF88
Text:        #FFFFFF       Text:        #000000
```

---

## 📐 Typography Scale

### Font Families
- **Headers/Buttons**: Plus Jakarta Sans
- **Body/Text**: Poppins

### Font Sizes
```
Hero Logo:          4.5rem
Hero Title:         3.5rem
Section Title:      2.5rem
Card Title:         1.5rem
Button Text:        1.3rem
Body Text:          1rem
Small Text:         0.85rem
```

### Font Weights
```
Extra Bold:  800  (Titles)
Bold:        700  (Buttons, Headers)
Semibold:    600  (Labels)
Medium:      500  (Navigation)
Regular:     400  (Body)
Light:       300  (Captions)
```

---

## 🔘 Button Styles

### Primary Button
```css
Background:     Gradient (Cyan → Green / Blue → Red)
Font Size:      1.3rem
Font Weight:    700
Border Radius:  1.5rem
Padding:        0.85rem 2rem
Shadow:         0 8px 30px accent-color

Hover:
  Transform:    translateY(-4px) scale(1.05)
  Shadow:       0 12px 45px accent-color
```

### Secondary Button
```css
Background:     Transparent
Border:         2px solid accent
Font Size:      1.1rem
Border Radius:  1.5rem

Hover:
  Background:   Gradient fill
  Color:        #FFFFFF
```

---

## 📦 Card Components

### Standard Card (.vcard)
```css
Border:         2px solid
Border Radius:  1.5rem
Padding:        2rem
Shadow:         Multi-layer depth
Top Border:     4px gradient (on hover)

Hover:
  Transform:    translateY(-4px)
  Border Color: Accent
```

### Accent Card
```css
Background:     Full gradient
Border:         3px solid accent
Color:          #FFFFFF
Shadow:         Enhanced glow
Animation:      Rotating radial overlay
```

---

## 🎭 Animation Timing

### Transitions
```css
Standard:   0.3s cubic-bezier(0.4, 0, 0.2, 1)
Fast:       0.2s ease
Slow:       0.5s ease-in-out
```

### Keyframe Durations
```css
Logo Pulse:         4s infinite
Gradient Shift:     5s infinite
Title Glow:         3s infinite
Float Animation:    3s infinite
Background Rotate:  15-20s infinite
```

---

## 📱 Input Fields

### Text Input / Textarea
```css
Background:     Surface color
Border:         2px solid
Border Radius:  1rem
Padding:        0.85rem 1.2rem
Font Size:      1rem

Focus State:
  Border Color: Accent
  Shadow:       0 0 0 4px accent-glow
  Transform:    scale(1.02)
```

---

## 💬 Chat Messages

### User Message
```css
Background:     Light accent tint
Border Left:    4px solid cyan/blue
Border Radius:  1.5rem 1.5rem 0.5rem 1.5rem
Padding:        1.25rem 1.5rem
Align:          Right (margin-left: auto)
Shadow:         Cyan/Blue glow
```

### Bot Message
```css
Background:     Light accent tint
Border Left:    4px solid green/red
Border Radius:  1.5rem 1.5rem 1.5rem 0.5rem
Padding:        1.25rem 1.5rem
Align:          Left (margin-right: auto)
Shadow:         Green/Red glow
```

---

## 🎯 Mode Cards

### Inactive State
```css
Border:         3px solid gray
Background:     Surface
Border Radius:  1.5rem
Padding:        2rem

Hover:
  Border Color:   Accent
  Transform:      translateY(-6px) scale(1.04)
  Overlay:        Gradient 10% opacity
```

### Active State
```css
Background:     Full gradient
Border:         3px solid accent
Color:          #FFFFFF
Shadow:         0 0 0 4px accent + depth shadow
```

---

## 📤 Upload Zone

### Style
```css
Border:         3px dashed gray
Border Radius:  1.5rem
Padding:        3.5rem 2.5rem
Icon Size:      4.5rem
Shadow:         Depth shadow

Icon Animation: Float (3s infinite)

Hover:
  Border Color:   Accent
  Transform:      translateY(-5px) scale(1.02)
  Overlay:        Gradient 8% opacity
```

---

## 🔄 Loading Animations

### Gear Animation
- Dual rotating gears
- Glow effects with drop-shadow
- 80px & 50px sizes
- Opposite rotation directions

### Circle Progress
- SVG circular progress (0-100%)
- 140px diameter
- Animated stroke-dashoffset
- Glowing accent color

### Spinner
- 4-ring rotating loader
- Staggered animation delays
- 64px diameter
- Accent colored borders

### Backdrop
```css
Background:     95% opacity solid + blur(12px)
Animation:      Fade in (0.3s)
Text:           1.3rem gradient with pulse
```

---

## 🎨 Gradient Patterns

### Title Gradient
```css
linear-gradient(135deg, 
  #FFE500,   /* Yellow */
  #00D9FF,   /* Cyan */
  #FF0080    /* Pink */
)
Background Size: 200% auto
Animation: Horizontal shift
```

### Accent Gradient (Dark)
```css
linear-gradient(135deg,
  #00D9FF,   /* Cyan */
  #00FF88    /* Light Green */
)
```

### Accent Gradient (Light)
```css
linear-gradient(135deg,
  #0066FF,   /* Blue */
  #FF0040    /* Red */
)
```

---

## 📏 Spacing Scale

```
Tight:    0.25rem - 0.5rem
Normal:   0.75rem - 1rem
Relaxed:  1.5rem - 2rem
Loose:    2.5rem - 3rem
```

---

## 🎪 Icon Sizes

```
Small:    1rem - 1.5rem
Medium:   2rem - 3rem
Large:    4rem - 4.5rem
```

---

## 🌈 Shadow Depths

### Standard Shadow
```css
0 10px 40px rgba(0,0,0,0.15)
```

### Large Shadow
```css
0 20px 60px rgba(0,0,0,0.25)
```

### Glow Shadow
```css
0 8px 30px {accent-color}
```

### Enhanced Glow
```css
0 12px 45px {accent-color}
```

---

## 🎯 Border Radius Guide

```
Small:       0.5rem
Standard:    1rem
Large:       1.5rem
Pill:        2rem
```

---

## ✨ Hover Transform Patterns

### Cards
```css
translateY(-4px)
```

### Buttons
```css
translateY(-4px) scale(1.05)
```

### Mode Cards
```css
translateY(-6px) scale(1.04)
```

### Sidebar Items
```css
translateX(6px) scale(1.03)
```

---

## 🎨 Quick Copy-Paste Snippets

### Gradient Title
```html
<div style="
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-size: 2.5rem;
  font-weight: 800;
  background: linear-gradient(135deg, #FFE500, #00D9FF, #FF0080);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
">
  Your Title Here
</div>
```

### Gradient Button
```css
background: linear-gradient(135deg, #00D9FF, #00FF88);
color: #FFFFFF;
border: none;
border-radius: 1.5rem;
font-family: 'Plus Jakarta Sans', sans-serif;
font-weight: 700;
font-size: 1.3rem;
padding: 0.85rem 2rem;
box-shadow: 0 8px 30px #00D9FF;
transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
```

### Modern Card
```css
background: var(--surface);
border: 2px solid var(--border);
border-radius: 1.5rem;
padding: 2rem;
box-shadow: 0 10px 40px rgba(0,0,0,0.15);
transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
```

---

## 🎉 Usage Tips

1. **Always use gradients** for titles and primary actions
2. **Maintain 1.3rem+** font size for buttons
3. **Use Plus Jakarta Sans** for bold, important text
4. **Use Poppins** for body content
5. **Apply 1.5rem border-radius** for modern feel
6. **Add glow shadows** to accent elements
7. **Animate on hover** with scale and translateY
8. **Use 0.3s transitions** for smooth interactions

---

This guide ensures **consistent, bold, and modern** styling throughout Vishleshak AI! 🚀
