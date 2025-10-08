# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: _verify_password
# Основной источник: C:\Bldr\core\bldr_api.py
# Дубликаты (для справки):
#   - C:\Bldr\main.py
#   - C:\Bldr\backend\main.py
#================================================================================
def _verify_password(password: str, password_hash: str) -> bool:
    try:
        salt = "bldr_static_salt"
        return hashlib.sha256((salt + password).encode("utf-8")).hexdigest() == password_hash
    except Exception:
        return False