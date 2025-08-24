import platform
import psutil
import time
import logging
from datetime import datetime, timedelta
from typing import Any, Dict
from ..tools.base import BaseTool, ToolResponse, ToolSchema

logger = logging.getLogger(__name__)

class SystemInfoTool(BaseTool):
    """
    Provides system information including CPU, memory, disk usage, and network stats.
    Useful for monitoring system health and performance diagnostics.
    """

    @property
    def name(self) -> str:
        return "system_info"

    @property
    def description(self) -> str:
        return "Get comprehensive system information including CPU, memory, disk, and network statistics"

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=self.description,
            parameters={
                "type": "object",
                "properties": {
                    "include_processes": {
                        "type": "boolean",
                        "description": "Include top CPU/memory consuming processes",
                        "default": False
                    },
                    "top_processes": {
                        "type": "integer",
                        "description": "Number of top processes to return",
                        "default": 5
                    },
                    "include_network": {
                        "type": "boolean",
                        "description": "Include network interface statistics",
                        "default": True
                    }
                },
                "required": []
            }
        )

    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validate input parameters"""
        include_processes = parameters.get("include_processes", False)
        top_processes = parameters.get("top_processes", 5)
        include_network = parameters.get("include_network", True)
        
        if not isinstance(include_processes, bool):
            return False
        
        if not isinstance(include_network, bool):
            return False
            
        if not isinstance(top_processes, int) or top_processes < 1:
            return False
        
        return True

    def _get_size(self, bytes_value):
        """Convert bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} PB"

    def _get_uptime(self):
        """Get system uptime"""
        try:
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            return str(uptime).split('.')[0]  # Remove microseconds
        except:
            return "Unknown"

    async def _run(self, **kwargs) -> Any:
        """Get comprehensive system information"""
        include_processes = kwargs.get("include_processes", False)
        top_processes = kwargs.get("top_processes", 5)
        include_network = kwargs.get("include_network", True)
        
        start_time = time.time()
        
        try:
            # Basic system info
            system_info = {
                "system": platform.system(),
                "node_name": platform.node(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "python_version": platform.python_version(),
                "uptime": self._get_uptime()
            }
            
            # CPU information
            cpu_info = {
                "physical_cores": psutil.cpu_count(logical=False),
                "total_cores": psutil.cpu_count(logical=True),
                "cpu_frequency": {
                    "current": f"{psutil.cpu_freq().current:.2f} MHz" if psutil.cpu_freq() else "Unknown",
                    "min": f"{psutil.cpu_freq().min:.2f} MHz" if psutil.cpu_freq() else "Unknown",
                    "max": f"{psutil.cpu_freq().max:.2f} MHz" if psutil.cpu_freq() else "Unknown"
                },
                "cpu_usage_percent": psutil.cpu_percent(interval=1),
                "cpu_usage_per_core": psutil.cpu_percent(interval=1, percpu=True)
            }
            
            # Memory information
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            memory_info = {
                "total": self._get_size(memory.total),
                "available": self._get_size(memory.available),
                "used": self._get_size(memory.used),
                "percentage": memory.percent,
                "swap_total": self._get_size(swap.total),
                "swap_used": self._get_size(swap.used),
                "swap_free": self._get_size(swap.free),
                "swap_percentage": swap.percent
            }
            
            # Disk information
            partitions = psutil.disk_partitions()
            disk_info = []
            for partition in partitions:
                try:
                    partition_usage = psutil.disk_usage(partition.mountpoint)
                    disk_info.append({
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "file_system": partition.fstype,
                        "total": self._get_size(partition_usage.total),
                        "used": self._get_size(partition_usage.used),
                        "free": self._get_size(partition_usage.free),
                        "percentage": round((partition_usage.used / partition_usage.total) * 100, 2)
                    })
                except PermissionError:
                    # This can happen on Windows for system partitions
                    continue
            
            result = {
                "timestamp": datetime.now().isoformat(),
                "system": system_info,
                "cpu": cpu_info,
                "memory": memory_info,
                "disks": disk_info
            }
            
            # Network information (optional)
            if include_network:
                try:
                    net_io = psutil.net_io_counters()
                    network_info = {
                        "bytes_sent": self._get_size(net_io.bytes_sent),
                        "bytes_received": self._get_size(net_io.bytes_recv),
                        "packets_sent": net_io.packets_sent,
                        "packets_received": net_io.packets_recv,
                        "errors_in": net_io.errin,
                        "errors_out": net_io.errout,
                        "drops_in": net_io.dropin,
                        "drops_out": net_io.dropout
                    }
                    result["network"] = network_info
                except:
                    result["network"] = {"error": "Network stats unavailable"}
            
            # Top processes (optional)
            if include_processes:
                try:
                    processes = []
                    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                        try:
                            processes.append({
                                "pid": proc.info['pid'],
                                "name": proc.info['name'],
                                "cpu_percent": proc.info['cpu_percent'] or 0,
                                "memory_percent": round(proc.info['memory_percent'] or 0, 2)
                            })
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue
                    
                    # Sort by CPU usage and get top N
                    top_cpu_processes = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)[:top_processes]
                    # Sort by memory usage and get top N
                    top_memory_processes = sorted(processes, key=lambda x: x['memory_percent'], reverse=True)[:top_processes]
                    
                    result["processes"] = {
                        "top_cpu": top_cpu_processes,
                        "top_memory": top_memory_processes,
                        "total_processes": len(processes)
                    }
                except:
                    result["processes"] = {"error": "Process information unavailable"}
            
            # Add processing time
            processing_time = time.time() - start_time
            result["processing_time_seconds"] = round(processing_time, 4)
            
            logger.info(f"System info gathered in {processing_time:.4f}s")
            return result
            
        except Exception as e:
            error_msg = f"Failed to gather system information: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)