import json
import argparse
import os

def generate_slides(json_path, output_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    slides_data = data.get("slides", [])
    markdown_output = []

    for i, slide in enumerate(slides_data):
        slide_type = slide.get("slide_type", "content")
        title = slide.get("title", "").replace('"', '\\"')
        content = slide.get("content", [])
        image_data = slide.get("image")
        
        image = None
        if isinstance(image_data, str):
            image = image_data
        elif isinstance(image_data, dict):
            image = image_data.get("path")
            
        has_image = bool(image)
        content_len = len(content)
        
        layout = "split"
        
        if slide_type == "intro" or i == 0:
            layout = "hero"
        elif has_image and content_len < 2:
            layout = "hero"
        elif has_image:
            layout = "split"
        elif not has_image and content_len == 1 and len(content[0]) < 200:
             layout = "statement"
        else:
            layout = "grid"
             
        md_chunk = f"---\nlayout: {layout}\n"
        
        if title:
            md_chunk += f'title: "{title}"\n'
            
        if image:
            md_chunk += f'image: "{image}"\n'
            
        md_chunk += "---\n\n"
        
        if layout == "statement":
             if content:
                 md_chunk += f"{content[0]}\n"
        elif layout == "hero":
            if content:
                for item in content:
                    md_chunk += f"{item}\n"
        else:
            for item in content:
                md_chunk += f"- {item}\n"
                
        markdown_output.append(md_chunk)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(markdown_output))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json")
    parser.add_argument("output_md")
    args = parser.parse_args()
    generate_slides(args.input_json, args.output_md)
