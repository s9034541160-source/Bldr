"""
ENTERPRISE RAG 3.0: VLM GPU Configuration
Оптимизированные настройки для RTX 4060
"""

import torch
import os
from typing import Dict, Any

class VLMGPUConfig:
    """Конфигурация GPU для VLM"""
    
    def __init__(self):
        self.device = self._get_optimal_device()
        self.memory_config = self._get_memory_config()
        self.model_config = self._get_model_config()
    
    def _get_optimal_device(self) -> str:
        """Определяет оптимальное устройство"""
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
            
            print(f"GPU: {gpu_name}")
            print(f"Memory: {gpu_memory:.1f} GB")
            
            if gpu_memory >= 8:  # RTX 4060 и выше
                return "cuda"
            elif gpu_memory >= 4:  # Средние GPU
                return "cuda"
            else:
                return "cpu"
        else:
            return "cpu"
    
    def _get_memory_config(self) -> Dict[str, Any]:
        """Конфигурация памяти для RTX 4060"""
        return {
            "max_memory": "7GB",  # Оставляем 1GB для системы
            "low_cpu_mem_usage": True,
            "device_map": "auto",
            "torch_dtype": torch.float16,  # Используем половинную точность
            "offload_folder": "./offload",  # Папка для оффлоада
        }
    
    def _get_model_config(self) -> Dict[str, Any]:
        """Конфигурация моделей"""
        return {
            "blip": {
                "model_name": "Salesforce/blip-image-captioning-base",
                "max_length": 50,
                "num_beams": 4,
                "do_sample": False,
            },
            "layoutlmv3": {
                "model_name": "microsoft/layoutlmv3-base",
                "max_length": 512,
                "batch_size": 4,  # Оптимально для RTX 4060
            }
        }
    
    def get_optimized_settings(self) -> Dict[str, Any]:
        """Возвращает оптимизированные настройки"""
        return {
            "device": self.device,
            "memory": self.memory_config,
            "models": self.model_config,
            "performance": {
                "use_cache": True,
                "use_gradient_checkpointing": True,
                "use_flash_attention": False,  # Не поддерживается на RTX 4060
            }
        }

def optimize_gpu_memory():
    """Оптимизирует GPU память"""
    
    if torch.cuda.is_available():
        # Очищаем кэш
        torch.cuda.empty_cache()
        
        # Настраиваем память
        torch.cuda.set_per_process_memory_fraction(0.9)  # 90% от GPU памяти
        
        # Включаем оптимизации
        torch.backends.cudnn.benchmark = True
        torch.backends.cudnn.deterministic = False
        
        print("GPU memory optimized")

def test_gpu_performance():
    """Тестирует производительность GPU"""
    
    if not torch.cuda.is_available():
        print("CUDA not available")
        return False
    
    try:
        # Тест производительности
        device = torch.device("cuda")
        
        # Создаем тестовые тензоры
        x = torch.randn(1000, 1000, device=device)
        y = torch.randn(1000, 1000, device=device)
        
        # Тест матричного умножения
        import time
        start_time = time.time()
        
        for _ in range(100):
            z = torch.matmul(x, y)
        
        torch.cuda.synchronize()
        end_time = time.time()
        
        gpu_time = end_time - start_time
        print(f"GPU performance test: {gpu_time:.3f}s for 100 matrix multiplications")
        
        # Очищаем память
        del x, y, z
        torch.cuda.empty_cache()
        
        return True
        
    except Exception as e:
        print(f"GPU performance test failed: {e}")
        return False

if __name__ == "__main__":
    # Тестируем конфигурацию
    config = VLMGPUConfig()
    settings = config.get_optimized_settings()
    
    print("VLM GPU Configuration:")
    print(f"   Device: {settings['device']}")
    print(f"   Memory: {settings['memory']['max_memory']}")
    print(f"   Dtype: {settings['memory']['torch_dtype']}")
    
    # Оптимизируем память
    optimize_gpu_memory()
    
    # Тестируем производительность
    test_gpu_performance()
    
    print("VLM GPU configuration ready!")
