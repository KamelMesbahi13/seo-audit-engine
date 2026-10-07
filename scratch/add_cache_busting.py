import shutil
import os

def add_cache_busting():
    with open("web_ui.py", "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Add meta tags to head
    old_meta = """    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>InersiaLab — SEO Audit & Architecture Suite</title>"""

    new_meta = """    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <title>InersiaLab — SEO Audit & Architecture Suite</title>"""

    content = content.replace(old_meta, new_meta)

    # 2. Add HTTP response headers in do_GET
    old_get = """        elif path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))"""

    new_get = """        elif path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))"""

    content = content.replace(old_get, new_get)

    with open("web_ui.py", "w", encoding="utf-8") as f:
        f.write(content)

    print("Updated web_ui.py with cache-busting headers.")

    # 3. Synchronize to .gemini skills directory
    dst = r"C:\Users\EL ASSLI HI TECH\.gemini\config\skills\agy-seo\web_ui.py"
    shutil.copy2("web_ui.py", dst)
    print("Synchronized to .gemini/config/skills/agy-seo/web_ui.py")

if __name__ == "__main__":
    add_cache_busting()
