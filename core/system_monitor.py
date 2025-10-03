#!/usr/bin/env python3
"""
System resource monitoring for Namaskah.App
Monitors memory, CPU, disk usage and system health
"""
import os
import logging
import psutil
from typing import Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)


def get_system_resources() -> Dict[str, any]:
    """Get current system resource usage"""
    try:
        # Memory information
        memory = psutil.virtual_memory()
        
        # CPU information
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # Disk information
        disk_usage = psutil.disk_usage('/')
        
        # Process information
        process = psutil.Process()
        process_memory = process.memory_info()
        
        return {
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used,
                "free": memory.free
            },
            "cpu": {
                "percent": cpu_percent,
                "count": cpu_count,
                "load_avg": os.getloadavg() if hasattr(os, 'getloadavg') else None
            },
            "disk": {
                "total": disk_usage.total,
                "used": disk_usage.used,
                "free": disk_usage.free,
                "percent": (disk_usage.used / disk_usage.total) * 100
            },
            "process": {
                "memory_rss": process_memory.rss,
                "memory_vms": process_memory.vms,
                "pid": process.pid,
                "cpu_percent": process.cpu_percent()
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get system resources: {e}")
        return {"error": str(e), "timestamp": datetime.utcnow().isoformat()}


def check_resource_limits() -> Dict[str, any]:
    """Check if system resources are within safe limits"""
    
    limits = {
        "memory_percent_warning": 80,
        "memory_percent_critical": 90,
        "cpu_percent_warning": 80,
        "cpu_percent_critical": 95,
        "disk_percent_warning": 85,
        "disk_percent_critical": 95
    }
    
    resources = get_system_resources()
    alerts = []
    status = "healthy"
    
    if "error" in resources:
        return {"status": "error", "error": resources["error"]}
    
    # Check memory
    memory_percent = resources["memory"]["percent"]
    if memory_percent >= limits["memory_percent_critical"]:
        alerts.append(f"CRITICAL: Memory usage at {memory_percent:.1f}%")
        status = "critical"
    elif memory_percent >= limits["memory_percent_warning"]:
        alerts.append(f"WARNING: Memory usage at {memory_percent:.1f}%")
        if status == "healthy":
            status = "warning"
    
    # Check CPU
    cpu_percent = resources["cpu"]["percent"]
    if cpu_percent >= limits["cpu_percent_critical"]:
        alerts.append(f"CRITICAL: CPU usage at {cpu_percent:.1f}%")
        status = "critical"
    elif cpu_percent >= limits["cpu_percent_warning"]:
        alerts.append(f"WARNING: CPU usage at {cpu_percent:.1f}%")
        if status == "healthy":
            status = "warning"
    
    # Check disk
    disk_percent = resources["disk"]["percent"]
    if disk_percent >= limits["disk_percent_critical"]:
        alerts.append(f"CRITICAL: Disk usage at {disk_percent:.1f}%")
        status = "critical"
    elif disk_percent >= limits["disk_percent_warning"]:
        alerts.append(f"WARNING: Disk usage at {disk_percent:.1f}%")
        if status == "healthy":
            status = "warning"
    
    return {
        "status": status,
        "alerts": alerts,
        "resources": resources,
        "limits": limits,
        "timestamp": datetime.utcnow().isoformat()
    }


def get_platform_info() -> Dict[str, any]:
    """Detect deployment platform and get platform-specific info"""
    
    platform_info = {
        "platform": "unknown",
        "detected_from": None,
        "environment_vars": {},
        "constraints": {}
    }
    
    # Railway detection
    if os.getenv("RAILWAY_ENVIRONMENT"):
        platform_info.update({
            "platform": "railway",
            "detected_from": "RAILWAY_ENVIRONMENT",
            "environment_vars": {
                "RAILWAY_ENVIRONMENT": os.getenv("RAILWAY_ENVIRONMENT"),
                "RAILWAY_PROJECT_ID": os.getenv("RAILWAY_PROJECT_ID"),
                "RAILWAY_SERVICE_ID": os.getenv("RAILWAY_SERVICE_ID")
            },
            "constraints": {
                "memory_limit": "8GB",
                "cpu_limit": "8 vCPU",
                "build_timeout": "30 minutes"
            }
        })
    
    # Render detection
    elif os.getenv("RENDER"):
        platform_info.update({
            "platform": "render",
            "detected_from": "RENDER",
            "environment_vars": {
                "RENDER": os.getenv("RENDER"),
                "RENDER_SERVICE_ID": os.getenv("RENDER_SERVICE_ID"),
                "RENDER_SERVICE_NAME": os.getenv("RENDER_SERVICE_NAME")
            },
            "constraints": {
                "memory_limit": "512MB-4GB",
                "cpu_limit": "0.5-2 vCPU",
                "build_timeout": "15 minutes"
            }
        })
    
    # Heroku detection
    elif os.getenv("DYNO"):
        platform_info.update({
            "platform": "heroku",
            "detected_from": "DYNO",
            "environment_vars": {
                "DYNO": os.getenv("DYNO"),
                "HEROKU_APP_NAME": os.getenv("HEROKU_APP_NAME"),
                "HEROKU_SLUG_COMMIT": os.getenv("HEROKU_SLUG_COMMIT")
            },
            "constraints": {
                "memory_limit": "512MB-14GB",
                "cpu_limit": "1x-Performance-L",
                "build_timeout": "15 minutes",
                "dyno_sleep": "30 minutes inactivity"
            }
        })
    
    # Docker detection
    elif os.path.exists("/.dockerenv"):
        platform_info.update({
            "platform": "docker",
            "detected_from": "/.dockerenv file",
            "environment_vars": {
                "HOSTNAME": os.getenv("HOSTNAME"),
                "CONTAINER_ID": os.getenv("HOSTNAME", "unknown")[:12]
            },
            "constraints": {
                "memory_limit": "depends on container config",
                "cpu_limit": "depends on container config"
            }
        })
    
    # Local development
    else:
        platform_info.update({
            "platform": "local",
            "detected_from": "no platform indicators found",
            "environment_vars": {
                "USER": os.getenv("USER"),
                "HOME": os.getenv("HOME"),
                "PWD": os.getenv("PWD")
            },
            "constraints": {
                "memory_limit": "system dependent",
                "cpu_limit": "system dependent"
            }
        })
    
    return platform_info


def validate_system_dependencies() -> Dict[str, any]:
    """Validate that required system dependencies are available"""
    
    dependencies = {
        "python": {
            "command": "python --version",
            "required": True,
            "status": "unknown"
        },
        "postgresql_client": {
            "command": "pg_config --version",
            "required": False,
            "status": "unknown"
        }
    }
    
    results = {
        "all_critical_available": True,
        "dependencies": {},
        "warnings": [],
        "errors": []
    }
    
    for dep_name, dep_info in dependencies.items():
        try:
            import subprocess
            result = subprocess.run(
                dep_info["command"].split(),
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                results["dependencies"][dep_name] = {
                    "available": True,
                    "version": result.stdout.strip(),
                    "required": dep_info["required"]
                }
            else:
                results["dependencies"][dep_name] = {
                    "available": False,
                    "error": result.stderr.strip(),
                    "required": dep_info["required"]
                }
                
                if dep_info["required"]:
                    results["all_critical_available"] = False
                    results["errors"].append(f"Required dependency {dep_name} not available")
                else:
                    results["warnings"].append(f"Optional dependency {dep_name} not available")
                    
        except subprocess.TimeoutExpired:
            results["dependencies"][dep_name] = {
                "available": False,
                "error": "Command timeout",
                "required": dep_info["required"]
            }
            
            if dep_info["required"]:
                results["all_critical_available"] = False
                results["errors"].append(f"Required dependency {dep_name} check timed out")
                
        except Exception as e:
            results["dependencies"][dep_name] = {
                "available": False,
                "error": str(e),
                "required": dep_info["required"]
            }
    
    return results