"""
🧪 Простой тест российского LLM без квантизации
"""

import logging
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_simple_llm():
    """Простой тест российского LLM"""
    
    try:
        logger.info("🔄 Загрузка простого российского LLM...")
        
        model_name = "ai-forever/rugpt3large_based_on_gpt2"
        
        # Загружаем токенизатор
        logger.info("📝 Загрузка токенизатора...")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        logger.info("✅ Токенизатор загружен")
        
        # Загружаем модель БЕЗ квантизации
        logger.info("🧠 Загрузка модели...")
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else None,
            trust_remote_code=True
        )
        
        logger.info("✅ Модель загружена")
        logger.info(f"📊 Устройство: {model.device}")
        
        # Тестовый промпт
        test_prompt = """Определи тип документа:

СНиП 2.01.07-85* "Нагрузки и воздействия"

Тип документа:"""
        
        # Токенизация
        inputs = tokenizer(test_prompt, return_tensors="pt")
        if torch.cuda.is_available():
            inputs = {k: v.to(model.device) for k, v in inputs.items()}
        
        logger.info(f"📊 Токенов в промпте: {inputs['input_ids'].shape[1]}")
        
        # Генерация
        logger.info("🔄 Генерация ответа...")
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_length=inputs['input_ids'].shape[1] + 50,
                temperature=0.1,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
        
        # Декодирование
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        generated_text = response[len(test_prompt):].strip()
        
        logger.info(f"✅ Ответ модели: {generated_text}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Запуск простого теста российского LLM")
    
    success = test_simple_llm()
    
    if success:
        logger.info("🎉 Тест прошел успешно!")
    else:
        logger.info("❌ Тест не прошел")
    
    logger.info("🏁 Тестирование завершено")
