#!/usr/bin/env python3
"""
Cost Agent 性能优化模块
"""

import os
import sys
import time
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
from functools import lru_cache, wraps
from datetime import datetime, timedelta

# 添加路径
sys.path.insert(0, str(Path(__file__).parent.parent))


class CacheManager:
    """缓存管理器"""

    def __init__(self, cache_dir: Path = None):
        if cache_dir is None:
            cache_dir = Path(__file__).parent.parent / 'cache'
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True)

    def _get_cache_key(self, *args) -> str:
        """生成缓存键"""
        key_str = json.dumps(args, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(key_str.encode()).hexdigest()

    def _get_cache_path(self, key: str) -> Path:
        """获取缓存文件路径"""
        return self.cache_dir / f"{key}.json"

    def get(self, *args) -> Optional[Any]:
        """获取缓存"""
        key = self._get_cache_key(*args)
        cache_path = self._get_cache_path(key)

        if cache_path.exists():
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # 检查过期时间
                if data.get('expires_at'):
                    expires_at = datetime.fromisoformat(data['expires_at'])
                    if datetime.now() > expires_at:
                        cache_path.unlink()  # 删除过期缓存
                        return None

                return data.get('data')
            except Exception:
                return None

        return None

    def set(self, data: Any, *args, ttl: int = 3600) -> None:
        """设置缓存"""
        key = self._get_cache_key(*args)
        cache_path = self._get_cache_path(key)

        cache_data = {
            'data': data,
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(seconds=ttl)).isoformat()
        }

        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)

    def clear(self) -> None:
        """清除所有缓存"""
        for cache_file in self.cache_dir.glob('*.json'):
            cache_file.unlink()


def cache(ttl: int = 3600):
    """缓存装饰器"""
    cache_manager = CacheManager()

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            key = (func.__name__, args, tuple(sorted(kwargs.items())))
            cached = cache_manager.get(*key)

            if cached is not None:
                return cached

            # 执行函数
            result = func(*args, **kwargs)

            # 缓存结果
            cache_manager.set(result, *key, ttl=ttl)

            return result
        return wrapper
    return decorator


class PerformanceOptimizer:
    """性能优化器"""

    def __init__(self):
        self.cache = CacheManager()
        self.metrics: Dict[str, List[float]] = {}

    def measure_time(self, func):
        """测量执行时间"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            end = time.time()

            elapsed = end - start
            func_name = func.__name__

            if func_name not in self.metrics:
                self.metrics[func_name] = []
            self.metrics[func_name].append(elapsed)

            return result
        return wrapper

    def get_metrics(self) -> Dict[str, Dict]:
        """获取性能指标"""
        metrics = {}
        for func_name, times in self.metrics.items():
            if times:
                metrics[func_name] = {
                    'count': len(times),
                    'avg_time': sum(times) / len(times),
                    'min_time': min(times),
                    'max_time': max(times),
                    'total_time': sum(times)
                }
        return metrics

    def optimize_batch_processing(self, items: List[Any], batch_size: int = 100) -> List[Any]:
        """批量处理优化"""
        results = []
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_results = self._process_batch(batch)
            results.extend(batch_results)
        return results

    def _process_batch(self, batch: List[Any]) -> List[Any]:
        """处理单个批次"""
        # 模拟批量处理
        return batch


class DataLoader:
    """数据加载优化器"""

    def __init__(self):
        self._cache: Dict[str, Any] = {}

    def load_with_cache(self, key: str, loader_func):
        """带缓存的加载"""
        if key in self._cache:
            return self._cache[key]

        data = loader_func()
        self._cache[key] = data
        return data

    def preload(self, keys: List[str], loader_func):
        """预加载"""
        for key in keys:
            self._cache[key] = loader_func(key)

    def clear_cache(self):
        """清除缓存"""
        self._cache.clear()


# ==================== 便捷函数 ====================

def create_optimizer() -> PerformanceOptimizer:
    """创建性能优化器"""
    return PerformanceOptimizer()


def create_data_loader() -> DataLoader:
    """创建数据加载器"""
    return DataLoader()


if __name__ == '__main__':
    # 测试
    optimizer = PerformanceOptimizer()

    @optimizer.measure_time
    def test_function(n: int):
        """测试函数"""
        time.sleep(0.1)
        return n * 2

    # 执行测试
    for i in range(5):
        result = test_function(i)
        print(f"Result: {result}")

    # 获取指标
    metrics = optimizer.get_metrics()
    print(f"\n性能指标：{json.dumps(metrics, indent=2)}")
