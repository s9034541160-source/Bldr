"""
FastAPI router для tender_analyzer с интеграцией сметного калькулятора
"""
from fastapi import APIRouter, HTTPException, File, UploadFile
from fastapi.responses import FileResponse
import os
import tempfile
from typing import Optional

from .pipeline import TenderAnalyzerPipeline

# Создаем router
router = APIRouter(prefix="/analyze", tags=["tender_analyzer"])

# Инициализация пайплайна
pipeline = TenderAnalyzerPipeline()


@router.post("/tender")
async def analyze_tender(
    pdf_file: UploadFile = File(...),
    region: str = "Москва",
    shift_pattern: str = "30/15",
    north_coeff: float = 1.2
):
    """
    Полный анализ тендера с генерацией сметы и упаковкой в ZIP
    
    Args:
        pdf_file: PDF файл тендера
        region: Регион пользователя
        shift_pattern: График вахты (дни работы/дни отдыха)
        north_coeff: Северный коэффициент
        
    Returns:
        FileResponse: ZIP файл с результатами анализа
    """
    try:
        # Сохраняем загруженный PDF во временный файл
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf:
            content = await pdf_file.read()
            temp_pdf.write(content)
            temp_pdf_path = temp_pdf.name
        
        try:
            # Запускаем анализ тендера
            zip_path = pipeline.analyze_tender(
                pdf_path=temp_pdf_path,
                user_region=region,
                shift_pattern=shift_pattern,
                north_coeff=north_coeff
            )
            
            # Проверяем что ZIP файл создан
            if not os.path.exists(zip_path):
                raise HTTPException(status_code=500, detail="ZIP файл не был создан")
            
            # Возвращаем ZIP файл
            return FileResponse(
                path=zip_path,
                filename=f"tender_analysis_{region}.zip",
                media_type="application/zip"
            )
            
        finally:
            # Удаляем временный PDF файл
            if os.path.exists(temp_pdf_path):
                os.unlink(temp_pdf_path)
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка анализа тендера: {str(e)}")


@router.get("/regions")
async def get_available_regions():
    """
    Получение списка доступных регионов
    
    Returns:
        Dict: Список регионов с коэффициентами
    """
    try:
        # Получаем регионы из estimate_calculator
        regions = {}
        for region, coeff in pipeline.estimate_calculator.region_coeffs.items():
            regions[region] = {
                "coeff": coeff.coeff,
                "description": coeff.description
            }
        
        return {"regions": regions}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения регионов: {str(e)}")


@router.get("/health")
async def health_check():
    """
    Проверка состояния сервиса
    
    Returns:
        Dict: Статус сервиса
    """
    return {
        "status": "healthy",
        "service": "tender_analyzer",
        "estimate_calculator": "integrated",
        "pipeline_steps": 9,
        "output_files": ["tender_report.docx", "estimate.xlsx", "gantt.xlsx", "finance.json"]
    }


@router.post("/test")
async def test_analysis():
    """
    Тестовый анализ с демонстрационными данными
    
    Returns:
        FileResponse: ZIP файл с тестовыми результатами
    """
    try:
        # Создаем тестовый PDF файл
        test_pdf_path = "/tmp/test_tender.pdf"
        with open(test_pdf_path, 'w') as f:
            f.write("Тестовый PDF файл тендера")
        
        # Запускаем анализ
        zip_path = pipeline.analyze_tender(
            pdf_path=test_pdf_path,
            user_region="Москва",
            shift_pattern="30/15",
            north_coeff=1.2
        )
        
        return FileResponse(
            path=zip_path,
            filename="test_tender_analysis.zip",
            media_type="application/zip"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка тестового анализа: {str(e)}")
