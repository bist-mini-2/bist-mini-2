import os
import re
import base64
import urllib.request
import json

def render_mermaid_to_png(mermaid_code, output_path):
    """Encodes mermaid code to base64 and fetches PNG from mermaid.ink"""
    # Fix any syntax properties for web rendering
    clean_code = mermaid_code.strip()
    
    # We serialize the code into JSON specification for mermaid.ink
    data = {
        "code": clean_code,
        "mermaid": {"theme": "default"}
    }
    json_str = json.dumps(data)
    # base64url encoding
    b64_bytes = base64.urlsafe_b64encode(json_str.encode('utf-8'))
    b64_str = b64_bytes.decode('utf-8').replace('=', '')
    
    url = f"https://mermaid.ink/img/pako:{b64_str}"
    
    # Fallback to simple base64 if pako compression fails or isn't required
    simple_b64 = base64.b64encode(clean_code.encode('utf-8')).decode('utf-8')
    fallback_url = f"https://mermaid.ink/img/{simple_b64}"
    
    print(f"Rendering: {output_path}")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as response:
            with open(output_path, 'wb') as f:
                f.write(response.read())
        print(f"Successfully generated using Pako: {output_path}")
    except Exception as e:
        print(f"Pako rendering failed: {e}. Trying fallback simple base64...")
        try:
            req = urllib.request.Request(fallback_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as response:
                with open(output_path, 'wb') as f:
                    f.write(response.read())
            print(f"Successfully generated using simple fallback: {output_path}")
        except Exception as err:
            print(f"Fallback also failed for {output_path}: {err}")

def process_markdown_file(file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
        
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        
    # Find all mermaid blocks
    pattern = re.compile(r'```mermaid\s*(.*?)\s*```', re.DOTALL)
    matches = pattern.findall(content)
    
    if not matches:
        print(f"No mermaid blocks found in {file_path}")
        return
        
    file_name = os.path.basename(file_path).replace('.md', '')
    dir_name = os.path.dirname(file_path)
    
    # We will replace the blocks by prepending the generated images
    new_content = content
    
    for i, mermaid_code in enumerate(matches):
        if file_name.endswith("_detail"):
            if i == 0:
                suffix = "ingestion"
            elif i == 1:
                suffix = "rag"
            elif i == 2:
                suffix = "analysis"
            else:
                suffix = "gem"
        elif file_name.endswith("_roadmap"):
            if i == 0:
                suffix = "gantt"
            else:
                suffix = "debate"
        else:
            suffix = "architecture" if i == 0 else "sequence"
        png_name = f"{file_name}_{suffix}.png"
        png_path = os.path.join(dir_name, png_name)
        
        # Render the image
        render_mermaid_to_png(mermaid_code, png_path)
        
        # We find the specific block and insert the image callout above it
        mermaid_block = f"```mermaid\n{mermaid_code}\n```"
        
        callout = (
            f"> 📢 **[구글 독스 이미지 삽입 안내 - {suffix.upper()}]**\n"
            f"> *   구글 독스 메뉴의 `삽입 ➡️ 이미지 ➡️ 컴퓨터에서 업로드`를 통해 아래 이미지 파일을 본문에 넣어주세요.\n"
            f"> *   **삽입 파일**: `docs/deliverables/4th/{png_name}`\n\n"
            f"![{file_name}_{suffix}]({png_name})\n\n"
        )
        
        # Only replace if the image link is not already there
        if f"![{file_name}_{suffix}]" not in new_content:
            new_content = new_content.replace(mermaid_block, callout + mermaid_block)
            
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"Updated markdown file: {file_path}")

if __name__ == "__main__":
    files = [
        "./docs/deliverables/4th/chat-hub-system.md",
        "./docs/deliverables/4th/research-gap-analyzer.md",
        "./docs/deliverables/4th/research-gem-factory.md",
        "./docs/deliverables/4th/05_evaluation_and_qa.md",
        "./docs/deliverables/4th/07_system_sequence_diagrams.md",
        "./docs/deliverables/4th/07_system_sequence_diagrams_detail.md",
        "./docs/deliverables/4th/11_limitations_and_roadmap.md",
        "./docs/deliverables/4th/15_database_erd.md"
    ]
    for file in files:
        process_markdown_file(file)


