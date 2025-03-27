from flask import Flask, render_template, request
import os
import base64
import tiktoken

app = Flask(__name__)
# You might already have a large max content length or other config here
app.config['MAX_CONTENT_LENGTH'] = 2048 * 1024 * 1024

enc = tiktoken.get_encoding("cl100k_base")

# We'll keep a global structure if needed, or simply parse in each request
# but after we use it, we'll reset to empty.

@app.route('/', methods=['GET', 'POST'])
def index():
    # This function-level dictionary will reset on each request (once done).
    # If you had a global structure, consider clearing it at the end.
    root_tree = {}
    tree_html = ""
    prompt_text = ""
    token_count = 0

    if request.method == 'POST':
        # If user uploaded a folder
        if 'folderUpload' in request.files:
            uploaded_files = request.files.getlist('folderUpload')
            for f in uploaded_files:
                relative_path = f.filename
                raw_text = f.read().decode('utf-8', errors='replace')
                b64_content = base64.b64encode(raw_text.encode('utf-8')).decode('utf-8')
                parts = relative_path.replace('\\', '/').split('/')
                insert_into_tree(root_tree, parts, b64_content)

            top_name = "Uploaded Folder"
            tree_html = f"""
            <div class="folder-header">
              <span class="folder-top-text">{top_name}</span>
              <button type="button" class="folder-remove-btn" title="Remove folder">×</button>
            </div>
            """ + build_folder_tree_html(root_tree)

        if 'generate_prompt' in request.form:
            user_instructions = request.form.get('user_instructions', '')
            meta_prompt_text = request.form.get('meta_prompt_text', '')
            use_meta = 'use_meta_prompt' in request.form
            selected_vals = request.form.getlist('selected_file_value')

            contents = []
            for val in selected_vals:
                try:
                    dec = base64.b64decode(val).decode('utf-8', errors='replace')
                    contents.append(dec.strip())
                except Exception as e:
                    contents.append(f"(Could not decode: {e})")

            parts = []
            if user_instructions.strip():
                parts.append(f"<user instructions>{user_instructions}</user instructions>")
            if use_meta and meta_prompt_text.strip():
                parts.append(f"<meta prompt>{meta_prompt_text}</meta prompt>")
            for c in contents:
                parts.append(f"<content>{c}</content>")

            prompt_text = "\n".join(parts)
            token_count = len(enc.encode(prompt_text))

            # Once the prompt is generated, we can clear 'root_tree' or any leftover references:
            root_tree.clear()  # Freed the dictionary of old file references

    return render_template('layout.html',
                           tree_html=tree_html,
                           prompt_text=prompt_text,
                           token_count=token_count)

def insert_into_tree(tree, parts, b64_content):
    # Insert file content (base64) into nested dict structure
    if not parts:
        return
    head = parts[0]
    if len(parts) == 1:
        tree[head] = b64_content
    else:
        if head not in tree:
            tree[head] = {}
        insert_into_tree(tree[head], parts[1:], b64_content)

def build_folder_tree_html(tree):
    html = ['<ul class="folder-list">']
    for name, val in sorted(tree.items()):
        if isinstance(val, dict):
            # It's a folder
            html.append(f"""
            <li class="folder-item">
              <div class="folder-row">
                <span class="arrow expanded">▼</span>
                <span class="icon folder-icon"></span>
                <span class="folder-name">{name}</span>
              </div>
              <div class="folder-contents">
                {build_folder_tree_html(val)}
              </div>
            </li>
            """)
        else:
            # It's a file
            html.append(f"""
            <li class="file-item">
              <label>
                <input type="checkbox" name="selected_file_value" value="{val}">
                <span class="icon file-icon"></span>
                <span class="file-name">{name}</span>
              </label>
            </li>
            """)
    html.append('</ul>')
    return "".join(html)

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0',port=5000)