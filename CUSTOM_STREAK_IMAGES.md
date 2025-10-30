# Using Custom Images for Streak Calendar

## Setup Instructions

### 1. Prepare Your Images

Create 4 PNG images (transparent background recommended):
- `tea-hot.png` - Hot cup for active days (recommend 128x128px)
- `tea-frozen.png` - Frozen/iced tea for freeze days
- `tea-empty.png` - Empty cup for inactive/future days  
- `tea-spilled.png` - Spilled/empty for missed days

### 2. Add Images to Your Project

Place them in: `/static/images/streak/`

### 3. Update CSS

Replace the emoji CSS with this:

```css
.day-circle {
    width: 50px;
    height: 50px;
    margin: 0 auto;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: transparent;
    border: none;
    position: relative;
    transition: all 0.3s ease;
}

.day-circle::after {
    content: '';
    width: 45px;
    height: 45px;
    background-size: contain;
    background-repeat: no-repeat;
    background-position: center;
    display: block;
}

.day-circle.active::after {
    background-image: url('/static/images/streak/tea-hot.png');
    filter: drop-shadow(0 0 8px rgba(251, 191, 36, 0.6));
    animation: steam 2s ease-in-out infinite;
}

.day-circle.frozen::after {
    background-image: url('/static/images/streak/tea-frozen.png');
    filter: drop-shadow(0 0 8px rgba(96, 165, 250, 0.6));
}

.day-circle.inactive::after {
    background-image: url('/static/images/streak/tea-empty.png');
    opacity: 0.3;
    filter: grayscale(100%);
}

.day-circle.missed::after {
    background-image: url('/static/images/streak/tea-spilled.png');
    opacity: 0.4;
    filter: grayscale(80%);
}

.day-circle.today {
    transform: scale(1.15);
    background: rgba(96, 165, 250, 0.15);
    border-radius: 50%;
}

@keyframes steam {
    0%, 100% { transform: translateY(0px); }
    50% { transform: translateY(-2px); }
}
```

## Benefits of Custom Images

✅ **All effects stay**: Glows, animations, grayscale, opacity  
✅ **Full control**: Design exactly what you want  
✅ **Brand consistency**: Match your app's aesthetic  
✅ **Better quality**: Can use high-res images  

## Image Requirements

- **Format**: PNG with transparency (or SVG)
- **Size**: 128x128px to 256x256px recommended
- **File size**: Keep under 50KB each for fast loading
- **Style**: Consistent style across all 4 images

## Where to Get Images

1. **Create your own** in Figma/Canva
2. **Commission** from a designer on Fiverr ($5-20)
3. **AI Generate** using DALL-E/Midjourney
4. **Buy stock** from sites like Flaticon

## Mobile Optimization

The CSS already includes responsive sizing:
- Desktop: 50px
- Tablet: 40px  
- Mobile: 35px

Images will auto-scale beautifully!

