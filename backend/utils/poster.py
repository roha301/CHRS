from PIL import Image, ImageDraw, ImageFont
import base64
import io

def generate_poster(booking, hall, user):
    # Professional & Neat Poster Layout
    width, height = 800, 1000
    
    # Solid clean background color (Soft cream/off-white)
    color = (248, 250, 252) # Slate 50
    img = Image.new('RGB', (width, height), color=color)
    d = ImageDraw.Draw(img)
    
    # Modern elegant header bar (Deep blue/slate)
    header_color = (15, 23, 42) # Slate 900
    d.rectangle([0, 0, width, 180], fill=header_color)
    
    # A vibrant accent line under the header for pop
    accent_color = (14, 165, 233) # Sky 500
    d.rectangle([0, 180, width, 195], fill=accent_color)
    
    # Add a subtle frame to the rest of the canvas
    d.rectangle([30, 225, width-30, height-30], outline=(203, 213, 225), width=2)
    
    try:
        font_main_title = ImageFont.truetype("arial.ttf", 65)
        font_sub_title = ImageFont.truetype("arial.ttf", 36)
        font_heading = ImageFont.truetype("arial.ttf", 26)
        font_body = ImageFont.truetype("arial.ttf", 28)
        font_bold = ImageFont.truetype("arialbd.ttf", 28)
        font_footer = ImageFont.truetype("arial.ttf", 20)
    except Exception:
        font_main_title = font_sub_title = font_heading = font_body = font_bold = font_footer = ImageFont.load_default()

    event_name = booking.get('eventName', 'UPCOMING EVENT').upper()
    
    # --- HEADER SECTION ---
    # Title centered in the header
    d.text((width//2, 70), "YOU'RE INVITED TO", fill=(148, 163, 184), font=font_heading, anchor="mm")
    d.text((width//2, 120), event_name, fill=(255, 255, 255), font=font_main_title, anchor="mm")
    
    # --- CONTENT BOXES ---
    y_cursor = 280
    
    # The Host Info
    club_str = booking.get('club', 'Independent')
    organizer_name = user.get('name') or booking.get('name') or 'Organizer'
    
    d.text((width//2, y_cursor), "HOSTED BY", fill=(100, 116, 139), font=font_heading, anchor="mm")
    y_cursor += 40
    
    if club_str != "None":
        d.text((width//2, y_cursor), f"{club_str} & {organizer_name}", fill=header_color, font=font_sub_title, anchor="mm")
    else:
        d.text((width//2, y_cursor), organizer_name, fill=header_color, font=font_sub_title, anchor="mm")
    
    y_cursor += 90
    
    # Elegant Separator
    d.line([(width//2 - 150, y_cursor), (width//2 + 150, y_cursor)], fill=accent_color, width=3)
    y_cursor += 70
    
    # Date & Time Block
    d.text((width//2, y_cursor), "DATE & TIME", fill=(100, 116, 139), font=font_heading, anchor="mm")
    y_cursor += 40
    d.text((width//2, y_cursor), f"{booking['date']}", fill=header_color, font=font_bold, anchor="mm")
    y_cursor += 40
    d.text((width//2, y_cursor), f"{booking['startTime']} - {booking['endTime']}", fill=header_color, font=font_body, anchor="mm")
    
    y_cursor += 80
    
    # Location Block
    d.text((width//2, y_cursor), "LOCATION", fill=(100, 116, 139), font=font_heading, anchor="mm")
    y_cursor += 40
    d.text((width//2, y_cursor), hall['name'].upper(), fill=header_color, font=font_bold, anchor="mm")
    
    y_cursor += 80
    
    # Purpose/Description
    d.text((width//2, y_cursor), "ABOUT THIS EVENT", fill=(100, 116, 139), font=font_heading, anchor="mm")
    y_cursor += 40
    # Wrap text if purpose is too long
    purpose_text = booking['purpose']
    if len(purpose_text) > 45:
        purpose_text = purpose_text[:42] + "..."
    d.text((width//2, y_cursor), purpose_text, fill=header_color, font=font_body, anchor="mm")
    
    # --- FOOTER SECTION ---
    # Bottom accent element
    y_footer = height - 120
    d.rectangle([30, y_footer, width-30, y_footer+80], fill=(241, 245, 249))
    d.text((width//2, y_footer + 40), "OFFICIALLY APPROVED BY CHRS ADMINISTRATION", fill=(71, 85, 105), font=font_footer, anchor="mm")

    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()
