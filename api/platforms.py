# Platform build and download endpoints

from typing import List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, PlainTextResponse

from core.style_dictionary import style_builder
from core.config import settings

router = APIRouter()

@router.get("/")
async def get_available_platforms():
    """Get list of available platforms and build status"""
    status = style_builder.get_build_status()
    
    return {
        "available_platforms": status["available_platforms"],
        "last_build": status["last_build_time"],
        "supported_formats": {
            "web": ["css", "json", "js"],
            "scss": ["scss"],
            "ios": ["swift", "h"],
            "android": ["xml", "java"],
            "flutter": ["dart"],
            "json": ["json"]
        },
        "build_status": status["build_cache"]
    }

@router.post("/build")
async def build_all_platforms(
    platforms: Optional[List[str]] = None,
    background_tasks: BackgroundTasks = None
):
    """Build tokens for all or specified platforms"""
    if platforms is None:
        platforms = settings.PLATFORMS
    
    # Validate platforms
    available = settings.PLATFORMS + ['scss', 'json']
    invalid = [p for p in platforms if p not in available]
    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid platforms: {invalid}. Available: {available}"
        )
    
    try:
        results = await style_builder.build_platforms(platforms)
        
        # Calculate summary
        successful = [r for r in results.values() if r["success"]]
        failed = [r for r in results.values() if not r["success"]]
        total_files = sum(len(r["output_files"]) for r in successful)
        
        return {
            "success": len(failed) == 0,
            "built_platforms": len(successful),
            "failed_platforms": len(failed),
            "total_output_files": total_files,
            "build_results": results,
            "summary": {
                "successful": [r["platform"] for r in successful],
                "failed": [r["platform"] for r in failed]
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Build failed: {str(e)}"
        )

@router.post("/build/{platform}")
async def build_single_platform(platform: str):
    """Build tokens for a specific platform"""
    available = settings.PLATFORMS + ['scss', 'json']
    if platform not in available:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid platform '{platform}'. Available: {available}"
        )
    
    try:
        results = await style_builder.build_platforms([platform])
        result = results[platform]
        
        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"Build failed: {result.get('error', 'Unknown error')}"
            )
        
        return {
            "success": True,
            "platform": platform,
            "build_time": result["build_time"],
            "output_files": result["output_files"],
            "file_count": len(result["output_files"]),
            "build_duration_ms": result["build_duration_ms"],
            "total_size_bytes": sum(result["file_sizes"].values())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Build failed: {str(e)}"
        )

@router.get("/{platform}")
async def get_platform_info(platform: str):
    """Get information about a specific platform"""
    available = settings.PLATFORMS + ['scss', 'json']
    if platform not in available:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid platform '{platform}'. Available: {available}"
        )
    
    files = style_builder.get_platform_files(platform)
    
    return {
        "platform": platform,
        "files": files,
        "file_count": len(files),
        "total_size_bytes": sum(f["size"] for f in files),
        "last_modified": max((f["modified"] for f in files), default=None)
    }

@router.get("/{platform}/files")
async def list_platform_files(platform: str):
    """List all files for a platform"""
    available = settings.PLATFORMS + ['scss', 'json']
    if platform not in available:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid platform '{platform}'. Available: {available}"
        )
    
    files = style_builder.get_platform_files(platform)
    
    if not files:
        raise HTTPException(
            status_code=404,
            detail=f"No files found for platform '{platform}'. Run build first."
        )
    
    return {
        "platform": platform,
        "files": files
    }

@router.get("/{platform}/download")
async def download_platform_bundle(platform: str):
    """Download main file for a platform"""
    available = settings.PLATFORMS + ['scss', 'json']
    if platform not in available:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid platform '{platform}'. Available: {available}"
        )
    
    # Define main file for each platform
    main_files = {
        "web": "tokens.css",
        "scss": "tokens.scss",
        "ios": "DesignTokens.swift",
        "android": "design_tokens.xml",
        "flutter": "design_tokens.dart",
        "json": "tokens-flat.json"
    }
    
    main_file = main_files.get(platform, "tokens.json")
    file_path = settings.BUILD_DIR / platform / main_file
    
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Main file not found for platform '{platform}'. Run build first."
        )
    
    # Determine media type
    media_types = {
        ".css": "text/css",
        ".scss": "text/scss",
        ".swift": "text/x-swift",
        ".xml": "application/xml",
        ".dart": "text/x-dart",
        ".json": "application/json",
        ".js": "text/javascript"
    }
    
    media_type = media_types.get(file_path.suffix, "text/plain")
    
    return FileResponse(
        path=file_path,
        filename=main_file,
        media_type=media_type
    )

@router.get("/{platform}/files/{filename}")
async def download_platform_file(platform: str, filename: str):
    """Download a specific file from a platform"""
    available = settings.PLATFORMS + ['scss', 'json']
    if platform not in available:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid platform '{platform}'. Available: {available}"
        )
    
    file_path = settings.BUILD_DIR / platform / filename
    
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"File '{filename}' not found for platform '{platform}'"
        )
    
    # Security check - ensure file is within platform directory
    try:
        file_path.resolve().relative_to(settings.BUILD_DIR / platform)
    except ValueError:
        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )
    
    return FileResponse(
        path=file_path,
        filename=filename
    )

@router.get("/{platform}/files/{filename}/content")
async def get_file_content(platform: str, filename: str):
    """Get the text content of a specific file"""
    available = settings.PLATFORMS + ['scss', 'json']
    if platform not in available:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid platform '{platform}'. Available: {available}"
        )
    
    try:
        content = style_builder.get_file_content(platform, filename)
        
        return PlainTextResponse(
            content=content,
            media_type="text/plain"
        )
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")

@router.delete("/{platform}")
async def clear_platform_build(platform: str):
    """Clear build files for a specific platform"""
    available = settings.PLATFORMS + ['scss', 'json']
    if platform not in available:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid platform '{platform}'. Available: {available}"
        )
    
    try:
        platform_dir = settings.BUILD_DIR / platform
        if platform_dir.exists():
            import shutil
            shutil.rmtree(platform_dir)
            platform_dir.mkdir(exist_ok=True)
        
        return {
            "success": True,
            "message": f"Build files cleared for platform '{platform}'"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear platform build: {str(e)}"
        )

@router.delete("/")
async def clear_all_builds():
    """Clear all build files"""
    try:
        style_builder.clear_build_cache()
        
        return {
            "success": True,
            "message": "All build files cleared"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear builds: {str(e)}"
        )

@router.get("/status")
async def get_build_status():
    """Get detailed build status"""
    return style_builder.get_build_status()