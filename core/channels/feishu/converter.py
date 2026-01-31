
def markdown_to_feishu_post(text: str) -> dict:
    """
    Converts a full markdown string into Feishu Post content structure.
    """
    lines = text.split('\n')
    content = []
    for line in lines:
        if not line:
            content.append([{"tag": "text", "text": ""}])
            continue
        line_elements = [{
            "tag": "md",
            "text": line
        }]
        content.append(line_elements)
        
    return content
