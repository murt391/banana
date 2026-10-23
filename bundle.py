import os
import re
import base64
from bs4 import BeautifulSoup

def automated_mega_bundle():
    print("🚀 Starting automated merge of 173 HTML pages and assets...")
    
    if not os.path.exists("index.html"):
        print("❌ Error: Top-level index.html not found!")
        return
        
    with open("index.html", "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    # Add global styles to handle layout switching smoothly
    if not soup.find("style"):
        style_tag = soup.new_tag("style")
        soup.head.append(style_tag)
    soup.find("style").append("\n.auto-page { display: none; }\n.auto-page.active { display: block; }\n")

    # Wrap the homepage body content into the default starting tab
    original_body_children = list(soup.body.children)
    main_section = soup.new_tag("section", id="index.html", attrs={"class": "auto-page active"})
    for child in original_body_children:
        main_section.append(child.extract())
    soup.body.append(main_section)

    # 1. Recursively find EVERY HTML file across all folders (except index.html and dist)
    html_registry = {}
    for root, dirs, files in os.walk("."):
        # Ignore output and configuration folders
        if "dist" in root or ".github" in root or ".git" in root:
            continue
        for file in files:
            if file.endswith(".html") and file != "index.html":
                # Save the relative file path as the unique ID (e.g., 'games/slope.html')
                rel_path = os.path.relpath(os.path.join(root, file), ".").replace("\\", "/")
                html_registry[rel_path] = os.path.join(root, file)

    print(f"📦 Found {len(html_registry)} sub-pages to merge.")

    # 2. Extract and inject the body content of all 173 pages
    for page_id, full_path in html_registry.items():
        try:
            with open(full_path, "r", encoding="utf-8") as sub_f:
                sub_soup = BeautifulSoup(sub_f.read(), "html.parser")
                
            sub_section = soup.new_tag("section", id=page_id, attrs={"class": "auto-page"})
            
            if sub_soup.body:
                for child in list(sub_soup.body.children):
                    sub_section.append(child.extract())
            else:
                for child in list(sub_soup.children):
                    sub_section.append(child.extract())
                    
            soup.body.append(sub_section)
            print(f"   ✅ Merged: {page_id}")
        except Exception as e:
            print(f"   ⚠️ Failed to read {page_id}: {e}")

    # 3. Rewrite all <a> anchor paths to trigger our smooth JS tab switcher
    for a_tag in soup.find_all("a"):
        href = a_tag.get("href", "").lstrip("./")
        if href in html_registry or href == "index.html":
            target_id = href if href == "index.html" else href
            a_tag["onclick"] = f"switchAutoPage('{target_id}'); return false;"
            a_tag["href"] = "#"

    # 4. Inject the fast routing JavaScript engine into the file footer
    js_router = """
    <script>
    function switchAutoPage(pageId) {
        document.querySelectorAll('.auto-page').forEach(sec => {
            sec.classList.remove('active');
        });
        const target = document.getElementById(pageId);
        if (target) {
            target.classList.add('active');
            window.scrollTo(0, 0);
        } else {
            console.error("Page missing from bundle: " + pageId);
        }
    }
    </script>
    """
    soup.body.append(BeautifulSoup(js_router, "html.parser"))

    # 5. Automatically base64 encode EVERY image asset throughout the compiled file
    for img in soup.find_all("img"):
        src = img.get("src", "")
        if src and not src.startswith(("http://", "https://", "data:")):
            # Strip relative formatting to safely track files in deep directories
            clean_src = src.lstrip("./")
            
            # Find where the file actually lives in the project
            matched_path = None
            if os.path.exists(clean_src):
                matched_path = clean_src
            else:
                # Backup deep-search lookup for complex paths
                for root, _, files in os.walk("."):
                    if "dist" in root or ".git" in root: continue
                    basename = os.path.basename(clean_src)
                    if basename in files:
                        matched_path = os.path.join(root, basename)
                        break

            if matched_path and os.path.exists(matched_path):
                ext = os.path.splitext(matched_path).lower().replace(".", "")
                if ext not in ["png", "jpg", "jpeg", "gif", "webp", "svg"]: ext = "png"
                try:
                    with open(matched_path, "rb") as img_f:
                        encoded = base64.b64encode(img_f.read()).decode("utf-8")
                    img["src"] = f"data:image/{ext};base64,{encoded}"
                    print(f"   🖼️  Inlined asset: {matched_path}")
                except Exception as img_err:
                    print(f"   ⚠️ Could not base64 encode image {matched_path}: {img_err}")

    # 6. Save the final mega bundle file
    os.makedirs("dist", exist_ok=True)
    with open("dist/index.html", "w", encoding="utf-8") as out_f:
        out_f.write(str(soup))
    print("🎉 Success! Your entire game directory is packed into dist/index.html")

if __name__ == "__main__":
    automated_mega_bundle()
