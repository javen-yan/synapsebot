import os
import yaml
import shutil
from pathlib import Path
from typing import List, Optional
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

def upload_skill_zip(skill_path: str, zip_file_path: str) -> List[str]:
    """
    Extracts a ZIP file containing one or more skills to the specified path.
    Scans for directories containing SKILL.md and installs them.
    Returns a list of installed skill names.
    """
    import zipfile
    import tempfile
    
    base_path = Path(skill_path)
    if not base_path.exists():
        base_path.mkdir(parents=True)
    
    installed_skills = []
    
    with tempfile.TemporaryDirectory() as temp_dir:
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
            
        # Walk through the temp dir to find SKILL.md files
        for root, dirs, files in os.walk(temp_dir):
            if "SKILL.md" in files:
                # This directory is a skill
                source_dir = Path(root)
                # Use the directory name as the skill name, or parent if it's top level?
                # Usually skill name = directory name
                skill_name = source_dir.name
                
                # Validation: Does SKILL.md have valid yaml?
                # We could parse it here to get the 'real' name, but directory name is safer for filesystem
                
                target_dir = base_path / skill_name
                
                # If it already exists, overwrite? or merge?
                # For now, remove existing and move new
                if target_dir.exists():
                    shutil.rmtree(target_dir)
                
                shutil.move(str(source_dir), str(target_dir))
                installed_skills.append(skill_name)
                
    if not installed_skills:
        raise ValueError("No valid skills (directories containing SKILL.md) found in ZIP")
        
    return installed_skills
