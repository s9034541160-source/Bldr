#!/usr/bin/env python3
"""
Отладка парсинга - посмотрим что именно находит парсер
"""
import asyncio
import httpx
from bs4 import BeautifulSoup
import sys

async def debug_stroyinf_parsing():
    """Отладка парсинга stroyinf.ru"""
    print("DEBUGGING STROYINF.RU PARSING")
    print("=" * 50)
    
    url = "https://files.stroyinf.ru/Index2/1/4293880/4293880.htm"
    selector = "a[href$='.pdf'], a[href$='.htm']"
    
    try:
        async with httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            verify=False
        ) as client:
            
            # Загружаем страницу
            response = await client.get(url)
            response.raise_for_status()
            
            print(f"Status: {response.status_code}")
            print(f"Content length: {len(response.text)}")
            
            # Парсим HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Ищем ссылки
            links = soup.select(selector)
            print(f"Found {len(links)} links")
            
            # Показываем первые 5 ссылок
            for i, link in enumerate(links[:5]):
                href = link.get('href', '')
                text = link.get_text(strip=True)
                print(f"\nLink {i+1}:")
                print(f"  URL: {href}")
                print(f"  Text: '{text}'")
                print(f"  Text length: {len(text)}")
                
                # Проверяем паттерны НТД
                import re
                patterns = [
                    r'(СП\s+\d+\.\d+\.\d+\.\d+)',
                    r'(СНиП\s+\d+\.\d+\.\d+)',
                    r'(ГОСТ\s+\d+\.\d+)',
                    r'(СН\s+\d+\.\d+)',
                    r'(РД\s+\d+\.\d+)',
                    r'(МДС\s+\d+\.\d+)',
                ]
                
                found_patterns = []
                for pattern in patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    if matches:
                        found_patterns.extend(matches)
                
                if found_patterns:
                    print(f"  NTD patterns found: {found_patterns}")
                else:
                    print(f"  No NTD patterns found")
            
            # Показываем сырой HTML для первых ссылок
            print(f"\nRaw HTML for first link:")
            if links:
                print(f"HTML: {str(links[0])[:200]}...")
                
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_stroyinf_parsing())
