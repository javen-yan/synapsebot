import os
import yaml
from pathlib import Path
from typing import List, Dict, Optional
from pydantic import BaseModel

class SkillMetadata(BaseModel):
    name: str
    description: str
    license: Optional[str] = None

class Skill(BaseModel):
    metadata: SkillMetadata
    path: str
    instructions: str

def parse_frontmatter(content: str) -> (dict, str):
    """
    Parses YAML frontmatter from a markdown string.
    Returns (metadata_dict, body_content).
    """
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                metadata = yaml.safe_load(parts[1])
                body = parts[2].strip()
                return metadata, body
            except yaml.YAMLError:
                pass
    return {}, content

def load_skills(skills_paths: List[str]) -> List[Skill]:
    skills = []
    
    for skills_path in skills_paths:
        base_path = Path(skills_path)
        
        if not base_path.exists():
            continue

        # Scan for SKILL.md files in immediate subdirectories
        for skill_dir in base_path.iterdir():
            if skill_dir.is_dir():
                skill_file = skill_dir / "SKILL.md"
                if skill_file.exists():
                    with open(skill_file, "r") as f:
                        content = f.read()
                    
                    metadata_dict, body = parse_frontmatter(content)
                    
                    # Validation based on spec
                    if "name" in metadata_dict and "description" in metadata_dict:
                        # Ensure name matches directory name (best practice, but not strictly enforced by parser yet)
                        skill = Skill(
                            metadata=SkillMetadata(**metadata_dict),
                            path=str(skill_dir),
                            instructions=body
                        )
                        skills.append(skill)
    
    return skills

def format_skills_for_prompt(skills: List[Skill]) -> str:
    """
    Formats the skills into a system prompt section.
    """
    if not skills:
        return "No local skills available."
        
    prompt = "## Available Skills\n"
    for skill in skills:
        prompt += f"- **{skill.metadata.name}**: {skill.metadata.description}\n"
        
    prompt += "\nTo use a skill, you can read its `SKILL.md` file for full instructions or execute its scripts."
    return prompt
