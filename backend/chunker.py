import ast
import re
from typing import List, Dict, Any
from models.chunk import ChunkCreate
from utils.file_utils import read_file_content


class CodeChunker:
    def __init__(self):
        self.supported_languages = ['python']
    
    async def chunk_file(self, file_path: str, file_content: str, language: str, project_id: str) -> List[ChunkCreate]:
        """Parse a file into code chunks based on language."""
        if language == 'python':
            return await self._chunk_python_file(file_path, file_content, project_id)
        else:
            # For other languages, create a single chunk for the entire file
            return [ChunkCreate(
                project_id=project_id,
                function_name=None,
                file_path=file_path,
                language=language,
                chunk_type='file',
                code=file_content
            )]
    
    async def _chunk_python_file(self, file_path: str, file_content: str, project_id: str) -> List[ChunkCreate]:
        """Parse Python file into functions and classes."""
        chunks = []
        
        try:
            tree = ast.parse(file_content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    chunk = self._create_function_chunk(node, file_path, file_content, project_id)
                    chunks.append(chunk)
                
                elif isinstance(node, ast.ClassDef):
                    chunk = self._create_class_chunk(node, file_path, file_content, project_id)
                    chunks.append(chunk)
            
            # If no functions or classes found, create a module chunk
            if not chunks:
                chunks.append(ChunkCreate(
                    project_id=project_id,
                    function_name=None,
                    file_path=file_path,
                    language='python',
                    chunk_type='module',
                    code=file_content
                ))
            
            return chunks
            
        except SyntaxError:
            # If AST parsing fails, create a single chunk for the entire file
            return [ChunkCreate(
                project_id=project_id,
                function_name=None,
                file_path=file_path,
                language='python',
                chunk_type='file',
                code=file_content
            )]
    
    def _create_function_chunk(self, node: ast.FunctionDef, file_path: str, file_content: str, project_id: str) -> ChunkCreate:
        """Create a chunk for a Python function."""
        # Get the function code
        start_line = node.lineno - 1  # AST lines are 1-indexed
        end_line = self._get_end_line(node)
        
        # Extract function code
        lines = file_content.split('\n')
        function_lines = lines[start_line:end_line]
        function_code = '\n'.join(function_lines)
        
        # Get docstring if available
        docstring = ast.get_docstring(node)
        if docstring:
            # Include docstring in the code
            pass  # Already included in the extracted code
        
        return ChunkCreate(
            project_id=project_id,
            function_name=node.name,
            file_path=file_path,
            language='python',
            chunk_type='function',
            code=function_code
        )
    
    def _create_class_chunk(self, node: ast.ClassDef, file_path: str, file_content: str, project_id: str) -> ChunkCreate:
        """Create a chunk for a Python class."""
        # Get the class code
        start_line = node.lineno - 1  # AST lines are 1-indexed
        end_line = self._get_end_line(node)
        
        # Extract class code
        lines = file_content.split('\n')
        class_lines = lines[start_line:end_line]
        class_code = '\n'.join(class_lines)
        
        # Get docstring if available
        docstring = ast.get_docstring(node)
        if docstring:
            # Include docstring in the code
            pass  # Already included in the extracted code
        
        return ChunkCreate(
            project_id=project_id,
            function_name=node.name,
            file_path=file_path,
            language='python',
            chunk_type='class',
            code=class_code
        )
    
    def _get_end_line(self, node: ast.AST) -> int:
        """Get the end line number of an AST node."""
        if hasattr(node, 'end_lineno'):
            return node.end_lineno
        else:
            # Fallback: find the last line with content
            return node.lineno + 1  # Simple fallback
    
    def _extract_code_section(self, file_content: str, start_line: int, end_line: int) -> str:
        """Extract a section of code from file content."""
        lines = file_content.split('\n')
        return '\n'.join(lines[start_line:end_line])


# Global chunker instance
chunker = CodeChunker()
