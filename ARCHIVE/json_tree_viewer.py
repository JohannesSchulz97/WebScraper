import json

def build_article_structure(article, indent=0):
    lines = []
    name = article.get("name", "Unnamed Article")
    lines.append("  " * indent + f"📘 {name}")
    
    content = article.get("content", {})
    lines.extend(build_section_tree(content, indent + 1))
    
    return lines

def build_section_tree(section_dict, indent):
    lines = []
    for key, value in section_dict.items():
        if key in ["title", "content"]:
            continue
        lines.append("  " * indent + f"📂 {key}")
        if isinstance(value, dict):
            lines.extend(build_section_tree(value, indent + 1))
    return lines

def save_structure_to_file(json_file, output_file="article_structure.txt"):
    with open(json_file, "r", encoding="utf-8") as f:
        articles = json.load(f)

    all_lines = []
    for article in articles:
        all_lines.extend(build_article_structure(article))
        all_lines.append("")  # Add a blank line between articles

    with open(output_file, "w", encoding="utf-8") as out:
        out.write("\n".join(all_lines))

    print(f"Structure saved to: {output_file}")

if __name__ == "__main__":
    # Replace with your actual file name
    save_structure_to_file("merck_articles.json")