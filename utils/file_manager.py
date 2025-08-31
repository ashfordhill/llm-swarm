"""
File management utilities for the LLM Swarm system.
"""

import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Union
import logging
import json
import yaml


class FileManager:
    """
    Manages file operations for the generated project.
    """
    
    def __init__(self, output_dir: Union[str, Path]):
        """
        Initialize the file manager.
        
        Args:
            output_dir: Directory where generated files will be written
        """
        self.output_dir = Path(output_dir).resolve()
        self.logger = logging.getLogger(__name__)
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"Output directory: {self.output_dir}")
    
    def write_file(self, relative_path: str, content: str, overwrite: bool = True) -> Path:
        """
        Write content to a file in the output directory.
        
        Args:
            relative_path: Path relative to output directory
            content: File content to write
            overwrite: Whether to overwrite existing files
            
        Returns:
            Path to the written file
            
        Raises:
            FileExistsError: If file exists and overwrite is False
        """
        file_path = self.output_dir / relative_path
        
        # Create parent directories
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if file exists
        if file_path.exists() and not overwrite:
            raise FileExistsError(f"File already exists: {file_path}")
        
        # Write content
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.debug(f"Written file: {relative_path}")
            return file_path
            
        except Exception as e:
            self.logger.error(f"Failed to write file {relative_path}: {e}")
            raise
    
    def write_files(self, files: Dict[str, str], overwrite: bool = True) -> List[Path]:
        """
        Write multiple files at once.
        
        Args:
            files: Dictionary mapping relative paths to content
            overwrite: Whether to overwrite existing files
            
        Returns:
            List of paths to written files
        """
        written_files = []
        
        for relative_path, content in files.items():
            try:
                file_path = self.write_file(relative_path, content, overwrite)
                written_files.append(file_path)
            except Exception as e:
                self.logger.error(f"Failed to write {relative_path}: {e}")
                # Continue with other files
        
        self.logger.info(f"Written {len(written_files)} files")
        return written_files
    
    def read_file(self, relative_path: str) -> str:
        """
        Read content from a file in the output directory.
        
        Args:
            relative_path: Path relative to output directory
            
        Returns:
            File content
        """
        file_path = self.output_dir / relative_path
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"Failed to read file {relative_path}: {e}")
            raise
    
    def file_exists(self, relative_path: str) -> bool:
        """Check if a file exists in the output directory."""
        return (self.output_dir / relative_path).exists()
    
    def list_files(self, pattern: str = "*") -> List[Path]:
        """
        List files in the output directory matching a pattern.
        
        Args:
            pattern: Glob pattern to match files
            
        Returns:
            List of matching file paths
        """
        return list(self.output_dir.glob(pattern))
    
    def create_directory(self, relative_path: str) -> Path:
        """
        Create a directory in the output directory.
        
        Args:
            relative_path: Path relative to output directory
            
        Returns:
            Path to created directory
        """
        dir_path = self.output_dir / relative_path
        dir_path.mkdir(parents=True, exist_ok=True)
        self.logger.debug(f"Created directory: {relative_path}")
        return dir_path
    
    def copy_file(self, source: Union[str, Path], relative_dest: str) -> Path:
        """
        Copy a file to the output directory.
        
        Args:
            source: Source file path
            relative_dest: Destination path relative to output directory
            
        Returns:
            Path to copied file
        """
        source_path = Path(source)
        dest_path = self.output_dir / relative_dest
        
        # Create parent directories
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        shutil.copy2(source_path, dest_path)
        self.logger.debug(f"Copied file: {source_path} -> {relative_dest}")
        return dest_path
    
    def copy_directory(self, source: Union[str, Path], relative_dest: str) -> Path:
        """
        Copy a directory to the output directory.
        
        Args:
            source: Source directory path
            relative_dest: Destination path relative to output directory
            
        Returns:
            Path to copied directory
        """
        source_path = Path(source)
        dest_path = self.output_dir / relative_dest
        
        if dest_path.exists():
            shutil.rmtree(dest_path)
        
        shutil.copytree(source_path, dest_path)
        self.logger.debug(f"Copied directory: {source_path} -> {relative_dest}")
        return dest_path
    
    def write_json(self, relative_path: str, data: dict, indent: int = 2) -> Path:
        """
        Write data as JSON to a file.
        
        Args:
            relative_path: Path relative to output directory
            data: Data to write as JSON
            indent: JSON indentation
            
        Returns:
            Path to written file
        """
        content = json.dumps(data, indent=indent, ensure_ascii=False)
        return self.write_file(relative_path, content)
    
    def write_yaml(self, relative_path: str, data: dict) -> Path:
        """
        Write data as YAML to a file.
        
        Args:
            relative_path: Path relative to output directory
            data: Data to write as YAML
            
        Returns:
            Path to written file
        """
        content = yaml.dump(data, default_flow_style=False, allow_unicode=True)
        return self.write_file(relative_path, content)
    
    def get_project_structure(self) -> Dict[str, List[str]]:
        """
        Get the current project structure.
        
        Returns:
            Dictionary mapping directories to their files
        """
        structure = {}
        
        for root, dirs, files in os.walk(self.output_dir):
            rel_root = os.path.relpath(root, self.output_dir)
            if rel_root == ".":
                rel_root = ""
            
            structure[rel_root] = files
        
        return structure
    
    def cleanup(self, keep_files: Optional[List[str]] = None) -> None:
        """
        Clean up the output directory.
        
        Args:
            keep_files: List of files to keep (relative paths)
        """
        if not self.output_dir.exists():
            return
        
        keep_files = keep_files or []
        keep_paths = {self.output_dir / path for path in keep_files}
        
        for item in self.output_dir.iterdir():
            if item not in keep_paths:
                if item.is_file():
                    item.unlink()
                else:
                    shutil.rmtree(item)
        
        self.logger.info("Cleaned up output directory")
    
    def get_size_info(self) -> Dict[str, int]:
        """
        Get size information about the generated project.
        
        Returns:
            Dictionary with size statistics
        """
        total_size = 0
        file_count = 0
        dir_count = 0
        
        for root, dirs, files in os.walk(self.output_dir):
            dir_count += len(dirs)
            for file in files:
                file_path = Path(root) / file
                total_size += file_path.stat().st_size
                file_count += 1
        
        return {
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "file_count": file_count,
            "directory_count": dir_count
        }