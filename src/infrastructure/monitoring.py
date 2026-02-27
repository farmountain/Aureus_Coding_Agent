"""
Monitoring and Telemetry

Provides:
- Execution time tracking
- Memory usage monitoring
- Performance metrics
- Operation counters
- Health checks
"""

import time
import psutil
import os
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from contextlib import contextmanager


@dataclass
class PerformanceMetrics:
    """Performance metrics for an operation"""
    operation: str
    duration_ms: float
    memory_mb: float
    cpu_percent: float
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HealthStatus:
    """System health status"""
    healthy: bool
    memory_available_mb: float
    cpu_percent: float
    disk_available_gb: float
    active_sessions: int
    last_check: datetime = field(default_factory=datetime.now)
    issues: list[str] = field(default_factory=list)


class PerformanceMonitor:
    """
    Monitors performance metrics
    
    Tracks:
    - Execution time
    - Memory usage
    - CPU usage
    - Operation counts
    """
    
    def __init__(self):
        self._metrics: list[PerformanceMetrics] = []
        self._operation_counts: Dict[str, int] = {}
        self._process = psutil.Process(os.getpid())
    
    @contextmanager
    def track_operation(self, operation: str, metadata: Optional[Dict] = None):
        """
        Track performance of an operation
        
        Example:
            with monitor.track_operation("build_feature"):
                # ... do work ...
                pass
        """
        start_time = time.time()
        start_memory = self._process.memory_info().rss / (1024 * 1024)  # MB
        
        try:
            yield
            
        finally:
            end_time = time.time()
            end_memory = self._process.memory_info().rss / (1024 * 1024)  # MB
            
            duration_ms = (end_time - start_time) * 1000
            memory_used = end_memory - start_memory
            cpu_percent = self._process.cpu_percent()
            
            metrics = PerformanceMetrics(
                operation=operation,
                duration_ms=duration_ms,
                memory_mb=memory_used,
                cpu_percent=cpu_percent,
                metadata=metadata or {}
            )
            
            self._metrics.append(metrics)
            self._operation_counts[operation] = self._operation_counts.get(operation, 0) + 1
    
    def get_metrics(
        self,
        operation: Optional[str] = None,
        limit: Optional[int] = None
    ) -> list[PerformanceMetrics]:
        """
        Get performance metrics
        
        Args:
            operation: Filter by operation name
            limit: Maximum number of metrics to return
            
        Returns:
            List of performance metrics
        """
        metrics = self._metrics
        
        if operation:
            metrics = [m for m in metrics if m.operation == operation]
        
        if limit:
            metrics = metrics[-limit:]
        
        return metrics
    
    def get_operation_stats(self, operation: str) -> Dict[str, Any]:
        """
        Get statistics for an operation
        
        Args:
            operation: Operation name
            
        Returns:
            Statistics dictionary
        """
        op_metrics = [m for m in self._metrics if m.operation == operation]
        
        if not op_metrics:
            return {
                'count': 0,
                'avg_duration_ms': 0.0,
                'avg_memory_mb': 0.0,
                'total_duration_ms': 0.0
            }
        
        total_duration = sum(m.duration_ms for m in op_metrics)
        total_memory = sum(m.memory_mb for m in op_metrics)
        
        return {
            'count': len(op_metrics),
            'avg_duration_ms': total_duration / len(op_metrics),
            'avg_memory_mb': total_memory / len(op_metrics),
            'total_duration_ms': total_duration,
            'min_duration_ms': min(m.duration_ms for m in op_metrics),
            'max_duration_ms': max(m.duration_ms for m in op_metrics)
        }
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all operations"""
        return {
            operation: self.get_operation_stats(operation)
            for operation in self._operation_counts.keys()
        }
    
    def clear_metrics(self):
        """Clear all metrics"""
        self._metrics.clear()
        self._operation_counts.clear()


class HealthChecker:
    """
    System health checker
    
    Monitors:
    - Memory availability
    - CPU usage
    - Disk space
    - Active sessions
    """
    
    def __init__(
        self,
        memory_threshold_mb: float = 100.0,
        cpu_threshold_percent: float = 90.0,
        disk_threshold_gb: float = 1.0
    ):
        self.memory_threshold_mb = memory_threshold_mb
        self.cpu_threshold_percent = cpu_threshold_percent
        self.disk_threshold_gb = disk_threshold_gb
        self._active_sessions = 0
    
    def check_health(self) -> HealthStatus:
        """
        Check system health
        
        Returns:
            HealthStatus with current health state
        """
        issues = []
        
        # Check memory
        memory = psutil.virtual_memory()
        memory_available_mb = memory.available / (1024 * 1024)
        
        if memory_available_mb < self.memory_threshold_mb:
            issues.append(f"Low memory: {memory_available_mb:.1f}MB available")
        
        # Check CPU
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        if cpu_percent > self.cpu_threshold_percent:
            issues.append(f"High CPU usage: {cpu_percent:.1f}%")
        
        # Check disk space
        disk = psutil.disk_usage('/')
        disk_available_gb = disk.free / (1024 * 1024 * 1024)
        
        if disk_available_gb < self.disk_threshold_gb:
            issues.append(f"Low disk space: {disk_available_gb:.1f}GB available")
        
        healthy = len(issues) == 0
        
        return HealthStatus(
            healthy=healthy,
            memory_available_mb=memory_available_mb,
            cpu_percent=cpu_percent,
            disk_available_gb=disk_available_gb,
            active_sessions=self._active_sessions,
            issues=issues
        )
    
    def register_session(self):
        """Register active session"""
        self._active_sessions += 1
    
    def unregister_session(self):
        """Unregister session"""
        self._active_sessions = max(0, self._active_sessions - 1)
    
    @contextmanager
    def session_tracking(self):
        """
        Track session lifecycle
        
        Example:
            with health_checker.session_tracking():
                # ... process session ...
                pass
        """
        self.register_session()
        try:
            yield
        finally:
            self.unregister_session()


# Global instances
_global_monitor: Optional[PerformanceMonitor] = None
_global_health_checker: Optional[HealthChecker] = None


def get_monitor() -> PerformanceMonitor:
    """Get global performance monitor"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = PerformanceMonitor()
    return _global_monitor


def get_health_checker() -> HealthChecker:
    """Get global health checker"""
    global _global_health_checker
    if _global_health_checker is None:
        _global_health_checker = HealthChecker()
    return _global_health_checker
