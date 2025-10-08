"""
FastAPI router для сметного калькулятора
"""
from fastapi import APIRouter, HTTPException, File, UploadFile
from fastapi.responses import FileResponse
import json
import os
from typing import Dict, Any

from .models import EstimateRequest, EstimateResponse
from .calculator import EstimateCalculator

# Создаем router
router = APIRouter(prefix="/tools/estimate_calculator", tags=["estimate_calculator"])

# Инициализация калькулятора
calculator = EstimateCalculator()


@router.post("/calculate", response_model=EstimateResponse)
async def calculate_estimate(request: EstimateRequest) -> EstimateResponse:
    """
    Расчет сметы с маржой %
    
    Args:
        request: Параметры расчета сметы
        
    Returns:
        EstimateResponse: Результаты расчета с Excel файлом
    """
    try:
        # Валидация входных данных
        if not request.volumes:
            raise HTTPException(status_code=400, detail="Список объемов работ не может быть пустым")
        
        # Расчет сметы
        result = calculator.calculate_estimate(request)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка расчета сметы: {str(e)}")


@router.get("/download/{file_id}")
async def download_estimate(file_id: str):
    """
    Скачивание Excel файла сметы
    
    Args:
        file_id: ID файла сметы
        
    Returns:
        FileResponse: Excel файл
    """
    try:
        file_path = f"/tmp/estimate_{file_id}.xlsx"
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Файл сметы не найден")
        
        return FileResponse(
            path=file_path,
            filename=f"estimate_{file_id}.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка скачивания файла: {str(e)}")


@router.get("/regions")
async def get_regions() -> Dict[str, Any]:
    """
    Получение списка доступных регионов с коэффициентами
    
    Returns:
        Dict: Список регионов и их коэффициентов
    """
    try:
        regions = {}
        for region, coeff in calculator.region_coeffs.items():
            regions[region] = {
                "coeff": coeff.coeff,
                "description": coeff.description
            }
        
        return {"regions": regions}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения регионов: {str(e)}")


@router.get("/gesn/{code}")
async def get_gesn_price(code: str) -> Dict[str, Any]:
    """
    Получение цены по коду ГЭСН
    
    Args:
        code: Код ГЭСН
        
    Returns:
        Dict: Информация о цене
    """
    try:
        if code not in calculator.gesn_prices:
            raise HTTPException(status_code=404, detail=f"Код ГЭСН {code} не найден")
        
        gesn = calculator.gesn_prices[code]
        return {
            "code": gesn.code,
            "name": gesn.name,
            "unit": gesn.unit,
            "price_material": gesn.price_material,
            "price_labour": gesn.price_labour,
            "price_machine": gesn.price_machine,
            "total_price": gesn.total_price
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения цены ГЭСН: {str(e)}")


@router.post("/upload_gesn")
async def upload_gesn_data(file: UploadFile = File(...)):
    """
    Загрузка данных ГЭСН из Excel файла
    
    Args:
        file: Excel файл с данными ГЭСН
        
    Returns:
        Dict: Результат загрузки
    """
    try:
        # Сохраняем файл
        file_path = f"/tmp/gesn_upload_{file.filename}"
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Перезагружаем данные
        calculator._load_gesn_prices()
        
        return {
            "message": "Данные ГЭСН успешно загружены",
            "file_path": file_path,
            "records_count": len(calculator.gesn_prices)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки данных ГЭСН: {str(e)}")


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Проверка состояния сервиса
    
    Returns:
        Dict: Статус сервиса
    """
    return {
        "status": "healthy",
        "service": "estimate_calculator",
        "gesn_records": len(calculator.gesn_prices),
        "regions_count": len(calculator.region_coeffs),
        "siz_professions": len(calculator.siz_norms)
    }
