# Style Dictionary build system integration

import asyncio
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from core.config import settings

class StyleDictionaryBuilder:
    """Manages Style Dictionary builds and platform output"""
    
    def __init__(self):
        self.config_file = Path("style-dictionary.config.js")
        self.build_cache: Dict[str, Any] = {}
        self.last_build_time: Optional[str] = None
        
    async def setup_style_dictionary(self) -> None:
        """Initialize Style Dictionary configuration"""
        # Ensure build directory exists
        settings.BUILD_DIR.mkdir(exist_ok=True)
        
        # Check if Style Dictionary is available
        try:
            result = await self._run_command(["npm", "list", "style-dictionary"])
            if result.returncode != 0:
                print("⚠️  Style Dictionary not found in node_modules")
                print("   Run: npm install")
        except Exception as e:
            print(f"⚠️  Could not check Style Dictionary installation: {e}")
        
        print("✅ Style Dictionary setup complete")
    
    async def build_platforms(self, platforms: Optional[List[str]] = None) -> Dict[str, Dict[str, Any]]:
        """Build tokens for specified platforms"""
        if platforms is None:
            platforms = settings.PLATFORMS + ['scss', 'json']
        
        results = {}
        build_start = time.time()
        
        for platform in platforms:
            build_result = await self._build_single_platform(platform)
            results[platform] = build_result
        
        # Update build cache and time
        self.last_build_time = datetime.now().isoformat()
        self.build_cache.update(results)
        
        total_time = int((time.time() - build_start) * 1000)
        print(f"🏗️  Build completed in {total_time}ms for platforms: {', '.join(platforms)}")
        
        return results
    
    async def _build_single_platform(self, platform: str) -> Dict[str, Any]:
        """Build tokens for a single platform"""
        build_start = time.time()
        
        try:
            # Run Style Dictionary build
            result = await self._run_command([
                "npx", "style-dictionary", "build", "--config", "style-dictionary.config.js", "--platform", platform
            ])
            
            build_duration = int((time.time() - build_start) * 1000)
            
            if result.returncode == 0:
                # Collect output files
                platform_dir = settings.BUILD_DIR / platform
                output_files = []
                file_sizes = {}
                
                if platform_dir.exists():
                    for file_path in platform_dir.rglob('*'):
                        if file_path.is_file():
                            relative_path = str(file_path.relative_to(platform_dir))
                            output_files.append(relative_path)
                            file_sizes[relative_path] = file_path.stat().st_size
                
                return {
                    "success": True,
                    "platform": platform,
                    "build_time": datetime.now().isoformat(),
                    "output_files": output_files,
                    "file_sizes": file_sizes,
                    "build_duration_ms": build_duration,
                    "error": None
                }
            else:
                return {
                    "success": False,
                    "platform": platform,
                    "build_time": datetime.now().isoformat(),
                    "output_files": [],
                    "file_sizes": {},
                    "build_duration_ms": build_duration,
                    "error": result.stderr.decode() if result.stderr else "Build failed"
                }
                
        except Exception as e:
            build_duration = int((time.time() - build_start) * 1000)
            return {
                "success": False,
                "platform": platform,
                "build_time": datetime.now().isoformat(),
                "output_files": [],
                "file_sizes": {},
                "build_duration_ms": build_duration,
                "error": str(e)
            }
    
    def get_build_status(self) -> Dict[str, Any]:
        """Get current build status"""
        available_platforms = settings.PLATFORMS + ['scss', 'json']
        
        return {
            "available_platforms": available_platforms,
            "last_build_time": self.last_build_time,
            "build_cache": self.build_cache,
            "config_file_exists": self.config_file.exists(),
            "build_dir_exists": settings.BUILD_DIR.exists()
        }
    
    def get_platform_files(self, platform: str) -> List[Dict[str, Any]]:
        """Get list of files for a specific platform"""
        platform_dir = settings.BUILD_DIR / platform
        files = []
        
        if not platform_dir.exists():
            return files
        
        for file_path in platform_dir.rglob('*'):
            if file_path.is_file():
                relative_path = str(file_path.relative_to(platform_dir))
                stat = file_path.stat()
                
                files.append({
                    "name": file_path.name,
                    "path": relative_path,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "extension": file_path.suffix
                })
        
        # Sort by modification time (newest first)
        files.sort(key=lambda x: x["modified"], reverse=True)
        return files
    
    def get_file_content(self, platform: str, filename: str) -> str:
        """Get the content of a specific build file"""
        file_path = settings.BUILD_DIR / platform / filename
        
        if not file_path.exists():
            raise FileNotFoundError(f"File '{filename}' not found for platform '{platform}'")
        
        # Security check - ensure file is within platform directory
        try:
            file_path.resolve().relative_to(settings.BUILD_DIR / platform)
        except ValueError:
            raise ValueError("Access denied - file outside platform directory")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            raise ValueError("File is not text-readable")
    
    def clear_build_cache(self) -> None:
        """Clear all build files and cache"""
        import shutil
        
        if settings.BUILD_DIR.exists():
            shutil.rmtree(settings.BUILD_DIR)
            settings.BUILD_DIR.mkdir(exist_ok=True)
        
        self.build_cache.clear()
        self.last_build_time = None
        
        print("🧹 Build cache cleared")
    
    async def _run_command(self, command: List[str]) -> subprocess.CompletedProcess:
        """Run a command asynchronously"""
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=Path.cwd()
        )
        
        stdout, stderr = await process.communicate()
        
        return subprocess.CompletedProcess(
            args=command,
            returncode=process.returncode or 0,
            stdout=stdout,
            stderr=stderr
        )

# Global style builder instance
style_builder = StyleDictionaryBuilder()