import os
import yaml
import shutil
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

def delete_skill(skill_path: str, name: str) -> bool:
    """
    Deletes a skill directory.
    """
    base_path = Path(skill_path)
    skill_dir = base_path / name
    
    if skill_dir.exists() and skill_dir.is_dir():
        shutil.rmtree(skill_dir)
        return True
    return False

def upload_skill_zip(skill_path: str, zip_file_path: str) -> str:
    """
    Extracts a ZIP file containing a skill to the specified path.
    The ZIP should contain a single directory with SKILL.md inside.
    Returns the skill name.
    """
    import zipfile
    
    base_path = Path(skill_path)
    if not base_path.exists():
        base_path.mkdir(parents=True)
    
    # Extract to temporary location first
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        # Get the root directory name from the ZIP
        namelist = zip_ref.namelist()
        if not namelist:
            raise ValueError("ZIP file is empty")
        
        # Find the root directory
        root_dirs = set()
        for name in namelist:
            parts = Path(name).parts
            if parts:
                root_dirs.add(parts[0])
        
        if len(root_dirs) != 1:
            raise ValueError("ZIP must contain exactly one root directory")
        
        skill_name = list(root_dirs)[0]
        
        # Check if SKILL.md exists in the ZIP
        skill_md_path = f"{skill_name}/SKILL.md"
        if skill_md_path not in namelist:
            raise ValueError(f"ZIP must contain {skill_name}/SKILL.md")
        
        # Extract all files
        zip_ref.extractall(base_path)
    
    return skill_name
