import os
import zipfile
import aiofiles
from pathlib import Path
from typing import List, Optional
import git
from config import settings


async def ensure_workspace_dir(project_id: str) -> str:
    """Ensure workspace directory exists for project."""
    project_dir = os.path.join(settings.workspace_dir, project_id)
    os.makedirs(project_dir, exist_ok=True)
    return project_dir


async def clone_repository(repo_url: str, project_id: str) -> str:
    """Clone git repository to workspace."""
    project_dir = await ensure_workspace_dir(project_id)
    
    try:
        git.Repo.clone_from(repo_url, project_dir)
        return project_dir
    except Exception as e:
        raise Exception(f"Failed to clone repository: {str(e)}")


async def extract_zip(zip_path: str, project_id: str) -> str:
    """Extract zip file to workspace."""
    project_dir = await ensure_workspace_dir(project_id)
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(project_dir)
        return project_dir
    except Exception as e:
        raise Exception(f"Failed to extract zip file: {str(e)}")


def get_file_extension(file_path: str) -> str:
    """Get file extension and determine language."""
    ext = Path(file_path).suffix.lower()
    language_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.java': 'java',
        '.cpp': 'cpp',
        '.c': 'c',
        '.go': 'go',
        '.rs': 'rust',
        '.php': 'php',
        '.rb': 'ruby',
        '.cs': 'csharp',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.scala': 'scala',
        '.r': 'r',
        '.m': 'matlab',
        '.sh': 'bash',
        '.sql': 'sql',
        '.html': 'html',
        '.css': 'css',
        '.vue': 'vue',
        '.jsx': 'jsx',
        '.tsx': 'tsx'
    }
    return language_map.get(ext, 'unknown')


def is_code_file(file_path: str) -> bool:
    """Check if file is a code file."""
    code_extensions = {
        '.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs',
        '.php', '.rb', '.cs', '.swift', '.kt', '.scala', '.r',
        '.m', '.sh', '.sql', '.html', '.css', '.vue', '.jsx', '.tsx'
    }
    return Path(file_path).suffix.lower() in code_extensions


async def find_code_files(project_dir: str) -> List[str]:
    """Find all code files in project directory."""
    code_files = []
    
    for root, dirs, files in os.walk(project_dir):
        # Skip common directories that shouldn't be processed
        dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', 'node_modules', '.venv', 'venv', 'env', '.env'}]
        
        for file in files:
            file_path = os.path.join(root, file)
            if is_code_file(file_path):
                # Make path relative to project directory
                rel_path = os.path.relpath(file_path, project_dir)
                code_files.append(rel_path)
    
    return code_files


async def read_file_content(file_path: str) -> str:
    """Read file content asynchronously."""
    try:
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            return await f.read()
    except UnicodeDecodeError:
        # Try with different encoding if UTF-8 fails
        async with aiofiles.open(file_path, 'r', encoding='latin-1') as f:
            return await f.read()
