"""
Weather Card Generator
Creates cute, minimalistic, downloadable weather cards
"""

from PIL import Image, ImageDraw, ImageFont
import io
from datetime import datetime
import random

class WeatherCardGenerator:
    """Generate beautiful, shareable weather cards"""
    
    # Color schemes for different weather conditions with variations
    WEATHER_COLORS = {
        'sunny': [
            {'bg_start': '#FFE082', 'bg_end': '#FF6F00', 'text_primary': '#E65100', 'text_secondary': '#BF360C', 'accent': '#FFF9C4'},
            {'bg_start': '#FFECB3', 'bg_end': '#FFB300', 'text_primary': '#F57F00', 'text_secondary': '#E65100', 'accent': '#FFF8E1'},
            {'bg_start': '#FFF3E0', 'bg_end': '#FB8C00', 'text_primary': '#E65100', 'text_secondary': '#BF360C', 'accent': '#FFE0B2'},
        ],
        'partly_cloudy': [
            {'bg_start': '#FFF9C4', 'bg_end': '#FFB74D', 'text_primary': '#F57C00', 'text_secondary': '#E65100', 'accent': '#FFECB3'},
            {'bg_start': '#E1F5FE', 'bg_end': '#4FC3F7', 'text_primary': '#0277BD', 'text_secondary': '#01579B', 'accent': '#B3E5FC'},
            {'bg_start': '#F1F8E9', 'bg_end': '#9CCC65', 'text_primary': '#558B2F', 'text_secondary': '#33691E', 'accent': '#DCEDC8'},
        ],
        'cloudy': [
            {'bg_start': '#ECEFF1', 'bg_end': '#90A4AE', 'text_primary': '#455A64', 'text_secondary': '#263238', 'accent': '#CFD8DC'},
            {'bg_start': '#F5F5F5', 'bg_end': '#BDBDBD', 'text_primary': '#616161', 'text_secondary': '#424242', 'accent': '#E0E0E0'},
            {'bg_start': '#E8EAF6', 'bg_end': '#9FA8DA', 'text_primary': '#3F51B5', 'text_secondary': '#283593', 'accent': '#C5CAE9'},
        ],
        'rainy': [
            {'bg_start': '#B3E5FC', 'bg_end': '#0277BD', 'text_primary': '#01579B', 'text_secondary': '#004D85', 'accent': '#E1F5FE'},
            {'bg_start': '#E0F2F1', 'bg_end': '#00897B', 'text_primary': '#00695C', 'text_secondary': '#004D40', 'accent': '#B2DFDB'},
            {'bg_start': '#E1F5FE', 'bg_end': '#0288D1', 'text_primary': '#01579B', 'text_secondary': '#004368', 'accent': '#B3E5FC'},
        ],
        'stormy': [
            {'bg_start': '#B0BEC5', 'bg_end': '#37474F', 'text_primary': '#263238', 'text_secondary': '#000000', 'accent': '#CFD8DC'},
            {'bg_start': '#90A4AE', 'bg_end': '#455A64', 'text_primary': '#263238', 'text_secondary': '#000000', 'accent': '#B0BEC5'},
            {'bg_start': '#9FA8DA', 'bg_end': '#3949AB', 'text_primary': '#1A237E', 'text_secondary': '#000051', 'accent': '#C5CAE9'},
        ],
        'snowy': [
            {'bg_start': '#E0F7FA', 'bg_end': '#80DEEA', 'text_primary': '#00838F', 'text_secondary': '#006064', 'accent': '#B2EBF2'},
            {'bg_start': '#F1F8E9', 'bg_end': '#AED581', 'text_primary': '#558B2F', 'text_secondary': '#33691E', 'accent': '#DCEDC8'},
            {'bg_start': '#E8EAF6', 'bg_end': '#7986CB', 'text_primary': '#3F51B5', 'text_secondary': '#283593', 'accent': '#C5CAE9'},
        ],
        'foggy': [
            {'bg_start': '#ECEFF1', 'bg_end': '#78909C', 'text_primary': '#455A64', 'text_secondary': '#263238', 'accent': '#CFD8DC'},
            {'bg_start': '#F5F5F5', 'bg_end': '#9E9E9E', 'text_primary': '#616161', 'text_secondary': '#424242', 'accent': '#EEEEEE'},
            {'bg_start': '#E0F2F1', 'bg_end': '#4DB6AC', 'text_primary': '#00897B', 'text_secondary': '#00695C', 'accent': '#B2DFDB'},
        ],
        'windy': [
            {'bg_start': '#E0F2F1', 'bg_end': '#26A69A', 'text_primary': '#00897B', 'text_secondary': '#00695C', 'accent': '#B2DFDB'},
            {'bg_start': '#E8F5E9', 'bg_end': '#66BB6A', 'text_primary': '#388E3C', 'text_secondary': '#2E7D32', 'accent': '#C8E6C9'},
            {'bg_start': '#F3E5F5', 'bg_end': '#AB47BC', 'text_primary': '#7B1FA2', 'text_secondary': '#4A148C', 'accent': '#E1BEE7'},
        ]
    }
    
    WEATHER_ICONS = {
        'sunny': '☀',            # BLACK SUN WITH RAYS (U+2600)
        'partly_cloudy': '⛅',    # SUN BEHIND CLOUD (U+26C5)
        'cloudy': '☁',           # CLOUD (U+2601)
        'rainy': '🌧',            # CLOUD WITH RAIN (U+1F327)
        'stormy': '⛈',           # CLOUD WITH LIGHTNING AND RAIN (U+26C8)
        'snowy': '❄',            # SNOWFLAKE (U+2744)
        'foggy': '🌫',            # FOG (U+1F32B)
        'windy': '🌬',            # WIND BLOWING FACE (U+1F32C)
    }

    # Inspirational quotes based on weather
    WEATHER_QUOTES = {
        'sunny': [
            "Keep your face to the sunshine!",
            "Sunshine is the best medicine",
            "Every day is a sunny day!",
            "Let the sunshine in your soul"
        ],
        'partly_cloudy': [
            "Perfect balance in the sky",
            "Sun and clouds make magic",
            "Nature's perfect mix",
            "Beautiful skies ahead"
        ],
        'rainy': [
            "Dancing in the rain",
            "Life isn't about waiting for the storm to pass",
            "Some people feel the rain, others just get wet",
            "Let it rain, let it pour!"
        ],
        'cloudy': [
            "Every cloud has a silver lining",
            "Behind every cloud is another cloud",
            "Clouds come floating into my life",
            "Keep calm and enjoy the clouds"
        ],
        'snowy': [
            "Winter wonderland vibes",
            "Snowflakes are kisses from heaven",
            "Let it snow, let it snow!",
            "Cold hands, warm heart"
        ],
        'stormy': [
            "Embrace the storm",
            "After the storm comes the calm",
            "Thunder is good, thunder is impressive",
            "Storm chasers unite"
        ],
        'foggy': [
            "Mysterious and beautiful",
            "Lost in the mist",
            "Fog is just clouds on the ground",
            "Embrace the mystery"
        ],
        'windy': [
            "Gone with the wind",
            "Let the wind carry you",
            "Feel the breeze",
            "Wind in my hair, freedom in my heart"
        ]
    }
    
    def __init__(self, width=800, height=1000):
        """Initialize the card generator with dimensions"""
        self.width = width
        self.height = height
    
    def create_gradient_background(self, color_start, color_end):
        """Create a smooth gradient background"""
        base = Image.new('RGB', (self.width, self.height), color_start)
        draw = ImageDraw.Draw(base)
        
        # Convert hex to RGB
        r1, g1, b1 = self._hex_to_rgb(color_start)
        r2, g2, b2 = self._hex_to_rgb(color_end)
        
        # Create gradient
        for i in range(self.height):
            ratio = i / self.height
            r = int(r1 + (r2 - r1) * ratio)
            g = int(g1 + (g2 - g1) * ratio)
            b = int(b1 + (b2 - b1) * ratio)
            draw.rectangle([(0, i), (self.width, i + 1)], fill=(r, g, b))
        
        return base
    
    def _hex_to_rgb(self, hex_color):
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def generate_card(self, weather_data, persona='balanced', include_quote=True):
        """
        Generate a weather card
        
        Args:
            weather_data: Dictionary with weather information
            persona: User's weather persona (now ignored, using weather-based colors)
            include_quote: Whether to include inspirational quote
        
        Returns:
            PIL Image object
        """
        # Get weather condition and select random color scheme
        condition = weather_data.get('condition', 'cloudy')
        
        # Get color schemes for this weather condition, fallback to cloudy if not found
        color_options = self.WEATHER_COLORS.get(condition, self.WEATHER_COLORS['cloudy'])
        colors = random.choice(color_options)
        
        # Create gradient background
        card = self.create_gradient_background(colors['bg_start'], colors['bg_end'])
        draw = ImageDraw.Draw(card)
        
        # Add rounded corners effect with accent color overlay
        self._add_rounded_overlay(card, colors['accent'])
        
        # Positions
        y_pos = 60
        center_x = self.width // 2
        
        # Main Title
        self._draw_text(
            draw, "Weather Card", 
            (center_x, y_pos), 
            colors['text_primary'],
            font_size=52,
            bold=True,
            center=True
        )
        
        y_pos += 70
        
        # Subtitle
        self._draw_text(
            draw, "Weather Or Not", 
            (center_x, y_pos), 
            colors['text_secondary'],
            font_size=28,
            center=True
        )
        
        y_pos += 80
        
        # Weather icon (large) - using Unicode symbols
        icon = self.WEATHER_ICONS.get(condition, '☁')
        self._draw_text(
            draw, icon,
            (center_x, y_pos),
            colors['text_primary'],
            font_size=140,
            center=True
        )
        
        y_pos += 140
        
        # Temperature (main feature) - limited to 1 decimal
        temp = weather_data.get('temperature', 0)
        temp_text = f"{temp:.1f}°C"
        self._draw_text(
            draw, temp_text,
            (center_x, y_pos),
            colors['text_primary'],
            font_size=96,
            bold=True,
            center=True
        )
        
        y_pos += 80
        
        # Condition text
        condition_text = weather_data.get('condition_text', condition.replace('_', ' ').title())
        self._draw_text(
            draw, condition_text,
            (center_x, y_pos),
            colors['text_secondary'],
            font_size=36,
            center=True
        )
        
        y_pos += 100
        
        # Date and time
        date_val = weather_data.get('date', datetime.now())
        if isinstance(date_val, str):
            date_str = date_val
        else:
            date_str = date_val.strftime('%B %d, %Y')
        
        time_val = weather_data.get('time', datetime.now().time())
        if isinstance(time_val, str):
            time_str = time_val
        else:
            time_str = time_val.strftime('%I:%M %p')
        
        self._draw_text(
            draw, f"Date: {date_str}",
            (center_x, y_pos),
            colors['text_secondary'],
            font_size=24,
            center=True
        )
        
        y_pos += 45
        
        self._draw_text(
            draw, f"Time: {time_str}",
            (center_x, y_pos),
            colors['text_secondary'],
            font_size=24,
            center=True
        )
        
        y_pos += 75
        
        # Key weather parameters in a cute grid
        humidity = weather_data.get('humidity', 0)
        wind_speed = weather_data.get('wind_speed', 0)
        precipitation = weather_data.get('precipitation', 0)
        
        params = [
            ('H', f"{humidity:.1f}%", 'Humidity'),
            ('W', f"{wind_speed:.1f} km/h", 'Wind'),
            ('R', f"{precipitation:.1f}%", 'Rain')
        ]
        
        # Draw parameter boxes
        box_width = 200
        box_spacing = 30
        start_x = center_x - (len(params) * box_width + (len(params) - 1) * box_spacing) // 2
        
        for i, (symbol, value, label) in enumerate(params):
            x = start_x + i * (box_width + box_spacing)
            self._draw_param_box(draw, x, y_pos, box_width, symbol, value, label, colors)
        
        y_pos += 180
        
        # Inspirational quote (optional)
        if include_quote:
            quotes = self.WEATHER_QUOTES.get(condition, self.WEATHER_QUOTES['cloudy'])
            quote = random.choice(quotes)
            
            # Quote box with accent background
            quote_box_height = 100
            padding = 40
            draw.rounded_rectangle(
                [(padding, y_pos - 20), (self.width - padding, y_pos + quote_box_height)],
                radius=15,
                fill=self._hex_to_rgb(colors['accent']),
                outline=self._hex_to_rgb(colors['text_secondary']),
                width=2
            )
            
            self._draw_text(
                draw, f'"{quote}"',
                (center_x, y_pos + quote_box_height // 2),
                colors['text_secondary'],
                font_size=22,
                center=True,
                italic=True
            )
            
            y_pos += 140
        
        # Footer - branding
        footer_text = "Generated with love by Weather Sage"
        self._draw_text(
            draw, footer_text,
            (center_x, self.height - 50),
            colors['text_secondary'],
            font_size=18,
            center=True
        )
        
        return card
    
    def _draw_param_box(self, draw, x, y, width, symbol, value, label, colors):
        """Draw a parameter box with symbol, value, and label"""
        height = 130
        
        # Box background with rounded corners
        rgb_accent = self._hex_to_rgb(colors['accent'])
        draw.rounded_rectangle(
            [(x, y), (x + width, y + height)],
            radius=15,
            fill=rgb_accent,
            outline=self._hex_to_rgb(colors['text_secondary']),
            width=2
        )
        
        # Draw symbol (letter instead of emoji for better compatibility)
        self._draw_text(
            draw, symbol,
            (x + width // 2, y + 25),
            colors['text_primary'],
            font_size=36,
            bold=True,
            center=True
        )
        
        # Draw value (ensure text fits in box)
        self._draw_text(
            draw, value,
            (x + width // 2, y + 65),
            colors['text_primary'],
            font_size=22,
            bold=True,
            center=True
        )
        
        # Draw label
        self._draw_text(
            draw, label,
            (x + width // 2, y + 100),
            colors['text_secondary'],
            font_size=18,
            center=True
        )
    
    def _add_rounded_overlay(self, image, accent_color, opacity=30):
        """Add a subtle rounded overlay for depth"""
        overlay = Image.new('RGBA', (self.width, self.height), (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)
        
        margin = 30
        rgb = self._hex_to_rgb(accent_color)
        draw.rounded_rectangle(
            [(margin, margin), (self.width - margin, self.height - margin)],
            radius=40,
            fill=rgb + (opacity,)
        )
        
        image.paste(overlay, (0, 0), overlay)
    
    def _draw_text(self, draw, text, position, color, font_size=24, 
                   bold=False, italic=False, center=False):
        """
        Draw text with fallback to default font
        
        Args:
            draw: ImageDraw object
            text: Text to draw
            position: (x, y) tuple
            color: Text color (hex or RGB)
            font_size: Font size
            bold: Whether to use bold
            italic: Whether to use italic
            center: Whether to center the text
        """
        try:
            # Try to load a nice font (you may need to adjust path based on OS)
            font_paths = [
                # Linux
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else 
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf" if italic else
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                # Windows
                "C:\\Windows\\Fonts\\arialbd.ttf" if bold else
                "C:\\Windows\\Fonts\\ariali.ttf" if italic else
                "C:\\Windows\\Fonts\\arial.ttf",
                # macOS
                "/System/Library/Fonts/Helvetica.ttc",
                "/Library/Fonts/Arial.ttf"
            ]
            
            font = None
            for font_path in font_paths:
                try:
                    font = ImageFont.truetype(font_path, font_size)
                    break
                except:
                    continue
            
            if font is None:
                raise Exception("No suitable font found")
                
        except:
            # Fallback to default font
            font = ImageFont.load_default()
        
        # Convert hex to RGB if needed
        if isinstance(color, str):
            color = self._hex_to_rgb(color)
        
        # Center the text if requested
        if center:
            try:
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                position = (position[0] - text_width // 2, position[1] - text_height // 2)
            except:
                # Fallback for older PIL versions
                try:
                    text_width, text_height = draw.textsize(text, font=font)
                    position = (position[0] - text_width // 2, position[1] - text_height // 2)
                except:
                    pass
        
        draw.text(position, text, fill=color, font=font)
    
    def save_card(self, card, filepath):
        """Save the card to a file"""
        card.save(filepath, 'PNG', quality=95)
        return filepath
    
    def card_to_bytes(self, card):
        """Convert card to bytes for download"""
        buf = io.BytesIO()
        card.save(buf, format='PNG')
        return buf.getvalue()