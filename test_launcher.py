#!/usr/bin/env python3
"""
Test script for system launcher
"""

import time
from system_launcher.component_manager import SystemComponentManager

def main():
    print("Starting system launcher test...")
    cm = SystemComponentManager()
    
    # Проверяем статус компонентов
    print("\nInitial component status:")
    for comp_id, component in cm.get_all_components().items():
        print(f"- {component.name}: {component.status.value}")
    
    # Запускаем Redis
    print("\nStarting Redis...")
    result = cm.start_component('redis')
    print(f"Redis started: {result}")
    print(f"Redis status: {cm.components['redis'].status.value}")
    time.sleep(5)  # Ждем запуска Redis
    
    # Запускаем Celery Worker
    print("\nStarting Celery Worker...")
    result = cm.start_component('celery_worker')
    print(f"Celery Worker started: {result}")
    print(f"Celery Worker status: {cm.components['celery_worker'].status.value}")
    time.sleep(5)  # Ждем запуска Celery
    
    # Запускаем Backend
    print("\nStarting Backend...")
    result = cm.start_component('backend')
    print(f"Backend started: {result}")
    print(f"Backend status: {cm.components['backend'].status.value}")
    
    # Ждем немного, чтобы увидеть результат
    time.sleep(30)
    
    print("\nFinal component status:")
    for comp_id, component in cm.get_all_components().items():
        print(f"- {component.name}: {component.status.value}")

if __name__ == "__main__":
    main()