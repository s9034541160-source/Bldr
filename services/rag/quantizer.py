"""
Int8 quantization для оптимизации эмбеддингов
"""
import numpy as np
import logging
from typing import Optional, Union, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class QuantizationConfig:
    """Конфигурация quantization"""
    quantile: float = 0.99
    always_ram: bool = True
    use_optimum: bool = True

class Int8Quantizer:
    """Int8 quantization для эмбеддингов"""
    
    def __init__(self, config: Optional[QuantizationConfig] = None):
        """
        Инициализация quantizer
        
        Args:
            config: Конфигурация quantization
        """
        self.config = config or QuantizationConfig()
        self.optimum_available = False
        self.quantizer = None
        
        # Проверяем доступность optimum
        self._check_optimum_availability()
    
    def _check_optimum_availability(self):
        """Проверка доступности optimum-intel"""
        try:
            if self.config.use_optimum:
                from optimum.intel import OptimumQuantizer
                self.optimum_available = True
                logger.info("✅ Optimum-intel доступен для quantization")
            else:
                logger.info("ℹ️ Optimum-intel отключен")
        except ImportError:
            logger.warning("⚠️ Optimum-intel не установлен, используем fallback quantization")
            self.optimum_available = False
    
    def quantize(self, embeddings: np.ndarray) -> np.ndarray:
        """
        Quantization эмбеддингов в int8
        
        Args:
            embeddings: Эмбеддинги в float32
            
        Returns:
            Quantized эмбеддинги в int8
        """
        try:
            if self.optimum_available and self.config.use_optimum:
                return self._quantize_with_optimum(embeddings)
            else:
                return self._quantize_fallback(embeddings)
        except Exception as e:
            logger.error(f"❌ Ошибка quantization: {e}")
            # Возвращаем оригинальные эмбеддинги в случае ошибки
            return embeddings.astype(np.float32)
    
    def _quantize_with_optimum(self, embeddings: np.ndarray) -> np.ndarray:
        """Quantization с использованием optimum-intel"""
        try:
            from optimum.intel import OptimumQuantizer
            
            # Создаем quantizer если еще не создан
            if self.quantizer is None:
                self.quantizer = OptimumQuantizer()
            
            # Применяем quantization
            quantized = self.quantizer.quantize(embeddings)
            
            logger.info(f"✅ Optimum quantization применен: {embeddings.shape} -> {quantized.shape}")
            return quantized
            
        except Exception as e:
            logger.error(f"❌ Ошибка optimum quantization: {e}")
            # Fallback к простой quantization
            return self._quantize_fallback(embeddings)
    
    def _quantize_fallback(self, embeddings: np.ndarray) -> np.ndarray:
        """Fallback quantization без optimum"""
        try:
            # Улучшенная scalar quantization
            # Используем глобальные min/max для лучшего качества
            global_min = np.min(embeddings)
            global_max = np.max(embeddings)
            
            # Нормализуем к [0, 1] с глобальными границами
            normalized = (embeddings - global_min) / (global_max - global_min + 1e-8)
            
            # Конвертируем в int8 с лучшим распределением
            # Используем [-127, 127] для лучшего качества
            int8_embeddings = (normalized * 254 - 127).astype(np.int8)
            
            logger.info(f"✅ Fallback quantization применен: {embeddings.shape} -> {int8_embeddings.shape}")
            return int8_embeddings
            
        except Exception as e:
            logger.error(f"❌ Ошибка fallback quantization: {e}")
            return embeddings.astype(np.float32)
    
    def dequantize(self, quantized_embeddings: np.ndarray, 
                   min_vals: Optional[np.ndarray] = None,
                   max_vals: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Dequantization из int8 обратно в float32
        
        Args:
            quantized_embeddings: Quantized эмбеддинги
            min_vals: Минимальные значения (если известны)
            max_vals: Максимальные значения (если известны)
            
        Returns:
            Dequantized эмбеддинги в float32
        """
        try:
            # Конвертируем из int8 [-127, 127] в [0, 1]
            normalized = (quantized_embeddings.astype(np.float32) + 127) / 254.0
            
            # Если min/max известны, восстанавливаем оригинальный диапазон
            if min_vals is not None and max_vals is not None:
                embeddings = normalized * (max_vals - min_vals) + min_vals
            else:
                # Используем статистику из данных
                embeddings = normalized
            
            logger.info(f"✅ Dequantization применен: {quantized_embeddings.shape} -> {embeddings.shape}")
            return embeddings
            
        except Exception as e:
            logger.error(f"❌ Ошибка dequantization: {e}")
            return quantized_embeddings.astype(np.float32)
    
    def get_compression_ratio(self, original_embeddings: np.ndarray, 
                             quantized_embeddings: np.ndarray) -> float:
        """
        Вычисление коэффициента сжатия
        
        Args:
            original_embeddings: Оригинальные эмбеддинги
            quantized_embeddings: Quantized эмбеддинги
            
        Returns:
            Коэффициент сжатия
        """
        try:
            original_size = original_embeddings.nbytes
            quantized_size = quantized_embeddings.nbytes
            compression_ratio = original_size / quantized_size if quantized_size > 0 else 1.0
            
            logger.info(f"📊 Коэффициент сжатия: {compression_ratio:.2f}x")
            return compression_ratio
            
        except Exception as e:
            logger.error(f"❌ Ошибка вычисления сжатия: {e}")
            return 1.0
    
    def get_quality_metrics(self, original_embeddings: np.ndarray, 
                           quantized_embeddings: np.ndarray) -> dict:
        """
        Вычисление метрик качества quantization
        
        Args:
            original_embeddings: Оригинальные эмбеддинги
            quantized_embeddings: Quantized эмбеддинги
            
        Returns:
            Метрики качества
        """
        try:
            # Dequantize для сравнения
            dequantized = self.dequantize(quantized_embeddings)
            
            # Вычисляем метрики
            mse = np.mean((original_embeddings - dequantized) ** 2)
            mae = np.mean(np.abs(original_embeddings - dequantized))
            
            # Cosine similarity
            original_norm = np.linalg.norm(original_embeddings, axis=1, keepdims=True)
            dequantized_norm = np.linalg.norm(dequantized, axis=1, keepdims=True)
            
            cosine_sim = np.mean(
                np.sum(original_embeddings * dequantized, axis=1) / 
                (original_norm.flatten() * dequantized_norm.flatten() + 1e-8)
            )
            
            metrics = {
                "mse": float(mse),
                "mae": float(mae),
                "cosine_similarity": float(cosine_sim),
                "compression_ratio": self.get_compression_ratio(original_embeddings, quantized_embeddings)
            }
            
            logger.info(f"📊 Метрики качества: MSE={metrics['mse']:.6f}, MAE={metrics['mae']:.6f}, "
                       f"Cosine={metrics['cosine_similarity']:.4f}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"❌ Ошибка вычисления метрик: {e}")
            return {
                "mse": float('inf'),
                "mae": float('inf'),
                "cosine_similarity": 0.0,
                "compression_ratio": 1.0
            }
    
    def is_quantized(self, embeddings: np.ndarray) -> bool:
        """
        Проверка являются ли эмбеддинги quantized
        
        Args:
            embeddings: Эмбеддинги для проверки
            
        Returns:
            True если quantized
        """
        try:
            # Проверяем тип данных
            if embeddings.dtype == np.int8:
                return True
            
            # Проверяем диапазон значений
            if embeddings.dtype in [np.uint8, np.int8]:
                return True
            
            return False
            
        except Exception:
            return False


# Функция для демонстрации quantization
def demonstrate_quantization():
    """Демонстрация работы quantization"""
    print("=== ДЕМОНСТРАЦИЯ INT8 QUANTIZATION ===")
    
    # Создаем тестовые эмбеддинги
    print("📊 Создаем тестовые эмбеддинги...")
    original_embeddings = np.random.randn(100, 384).astype(np.float32)
    print(f"  • Размер: {original_embeddings.shape}")
    print(f"  • Тип: {original_embeddings.dtype}")
    print(f"  • Память: {original_embeddings.nbytes / 1024:.1f} KB")
    
    # Создаем quantizer
    quantizer = Int8Quantizer()
    
    # Применяем quantization
    print("\n🔧 Применяем quantization...")
    quantized_embeddings = quantizer.quantize(original_embeddings)
    print(f"  • Размер: {quantized_embeddings.shape}")
    print(f"  • Тип: {quantized_embeddings.dtype}")
    print(f"  • Память: {quantized_embeddings.nbytes / 1024:.1f} KB")
    
    # Вычисляем метрики
    print("\n📈 Вычисляем метрики качества...")
    metrics = quantizer.get_quality_metrics(original_embeddings, quantized_embeddings)
    
    print(f"  • MSE: {metrics['mse']:.6f}")
    print(f"  • MAE: {metrics['mae']:.6f}")
    print(f"  • Cosine Similarity: {metrics['cosine_similarity']:.4f}")
    print(f"  • Compression Ratio: {metrics['compression_ratio']:.2f}x")
    
    # Тестируем dequantization
    print("\n🔄 Тестируем dequantization...")
    dequantized = quantizer.dequantize(quantized_embeddings)
    print(f"  • Размер: {dequantized.shape}")
    print(f"  • Тип: {dequantized.dtype}")
    
    # Проверяем качество восстановления
    reconstruction_error = np.mean((original_embeddings - dequantized) ** 2)
    print(f"  • Reconstruction Error: {reconstruction_error:.6f}")
    
    print("\n✅ Демонстрация quantization завершена!")


if __name__ == "__main__":
    demonstrate_quantization()
