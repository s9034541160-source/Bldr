# namespace:documents
from typing import Any, Dict, List
import time
from core.tools.base_tool import ToolManifest, ToolInterface, ToolParam, ToolParamType

# Создаем Pydantic модели для универсального представления
coordinator_interface = ToolInterface(
    purpose='AI-генерация профессиональных официальных писем с настройкой стиля, тона и формата',
    input_requirements={
        'description': ToolParam(
            name='description',
            type=ToolParamType.STRING,
            required=True,
            description='Описание содержания письма'
        ),
        'letter_type': ToolParam(
            name='letter_type',
            type=ToolParamType.ENUM,
            required=False,
            default='business',
            description='Тип письма'
        )
    },
    execution_flow=[
        'Валидация входных параметров',
        'Генерация контента письма',
        'Форматирование и стилизация',
        'Сохранение результата'
    ],
    output_format={
        'status': 'success|error',
        'data': {
            'letter': 'str',
            'file_path': 'str',
            'metadata': 'dict'
        }
    },
    usage_guidelines={
        'for_coordinator': [
            'Используй для создания официальных документов',
            'Учитывай тип письма и получателя'
        ],
        'for_models': [
            'Будьте конкретны в описании содержания',
            'Укажите получателя для персонализации'
        ]
    }
)

manifest = ToolManifest(
    name='generate_letter',
    version='1.0.0',
    title='📝 Генератор официальных писем',
    description='AI-генерация профессиональных официальных писем с настройкой стиля, тона и формата. Поддерживает различные типы документов и автоматическое форматирование.',
    category='document_generation',
    ui_placement='dashboard',
    enabled=True,
    system=False,
    entrypoint='tools.custom.generate_letter:execute',
    params=[
        ToolParam(
            name='description',
            type=ToolParamType.STRING,
            required=True,
            description='Описание содержания письма',
            ui={
                'placeholder': 'Опишите, о чем должно быть письмо...',
                'rows': 4,
                'maxLength': 1000
            }
        ),
        { 
            'name': 'letter_type', 
            'type': 'enum', 
            'required': False, 
            'default': 'business',
            'description': 'Тип письма',
            'enum': [
                {'value': 'business', 'label': 'Деловое письмо'},
                {'value': 'complaint', 'label': 'Претензия'},
                {'value': 'request', 'label': 'Запрос'},
                {'value': 'response', 'label': 'Ответ'},
                {'value': 'notification', 'label': 'Уведомление'},
                {'value': 'agreement', 'label': 'Соглашение'},
                {'value': 'contract', 'label': 'Договорное письмо'}
            ]
        },
        { 
            'name': 'recipient', 
            'type': 'string', 
            'required': False, 
            'description': 'Получатель письма',
            'ui': {
                'placeholder': 'ООО "Компания", Иван Иванов и т.д.'
            }
        },
        { 
            'name': 'sender', 
            'type': 'string', 
            'required': False, 
            'description': 'Отправитель',
            'ui': {
                'placeholder': 'Ваше имя/компания'
            }
        },
        { 
            'name': 'tone', 
            'type': 'number', 
            'required': False, 
            'default': 0.0, 
            'description': 'Тон письма (-1.0 = очень мягкий, +1.0 = очень строгий)',
            'ui': {
                'min': -1.0,
                'max': 1.0,
                'step': 0.1,
                'slider': True
            }
        },
        { 
            'name': 'formality', 
            'type': 'enum', 
            'required': False, 
            'default': 'formal',
            'description': 'Уровень формальности',
            'enum': [
                {'value': 'very_formal', 'label': 'Очень формально'},
                {'value': 'formal', 'label': 'Формально'},
                {'value': 'semi_formal', 'label': 'Полуформально'},
                {'value': 'casual', 'label': 'Неформально'}
            ]
        },
        { 
            'name': 'length', 
            'type': 'enum', 
            'required': False, 
            'default': 'medium',
            'description': 'Длина письма',
            'enum': [
                {'value': 'short', 'label': 'Краткое (до 200 слов)'},
                {'value': 'medium', 'label': 'Среднее (200-500 слов)'},
                {'value': 'long', 'label': 'Подробное (500+ слов)'}
            ]
        },
        { 
            'name': 'include_signature', 
            'type': 'boolean', 
            'required': False, 
            'default': True, 
            'description': 'Включить подпись',
            'ui': {
                'switch': True
            }
        },
        { 
            'name': 'include_date', 
            'type': 'boolean', 
            'required': False, 
            'default': True, 
            'description': 'Включить дату',
            'ui': {
                'switch': True
            }
        },
        { 
            'name': 'language', 
            'type': 'enum', 
            'required': False, 
            'default': 'ru',
            'description': 'Язык письма',
            'enum': [
                {'value': 'ru', 'label': 'Русский'},
                {'value': 'en', 'label': 'English'},
                {'value': 'auto', 'label': 'Автоопределение'}
            ]
        }
    ],
    outputs=['file_path', 'letter', 'metadata'],
    result_display={
        'type': 'document',
        'title': 'Сгенерированное письмо',
        'description': 'Профессионально оформленное письмо готово к использованию',
        'features': {
            'editable': True,
            'exportable': True,
            'printable': True,
            'formatted': True
        }
    },
    permissions=['filesystem:write', 'network:out'],
    tags=['document', 'ai', 'generation', 'business', 'professional'],
    documentation={
        'examples': [
            {
                'title': 'Деловое письмо',
                'description': 'Запрос о поставке материалов',
                'letter_type': 'business',
                'formality': 'formal'
            },
            {
                'title': 'Претензия',
                'description': 'Жалоба на качество выполненных работ',
                'letter_type': 'complaint',
                'tone': 0.5
            }
        ],
        'tips': [
            'Будьте конкретны в описании содержания',
            'Укажите получателя для персонализации',
            'Настройте тон в зависимости от ситуации'
        ]
    },
    coordinator_interface=coordinator_interface
)

def execute(**kwargs) -> Dict[str, Any]:
    """Execute enterprise-level letter generation with advanced features."""
    start_time = time.time()
    
    try:
        # Validate and parse parameters
        description = kwargs.get('description', '').strip()
        if not description:
            return {
                'status': 'error',
                'error': 'Описание письма не может быть пустым',
                'execution_time': time.time() - start_time
            }
        
        # Parse parameters with defaults
        letter_type = kwargs.get('letter_type', 'business')
        recipient = kwargs.get('recipient', '')
        sender = kwargs.get('sender', '')
        tone = max(-1.0, min(1.0, kwargs.get('tone', 0.0)))
        formality = kwargs.get('formality', 'formal')
        length = kwargs.get('length', 'medium')
        include_signature = kwargs.get('include_signature', True)
        include_date = kwargs.get('include_date', True)
        language = kwargs.get('language', 'ru')
        
        # Generate letter using AI
        try:
            from core.unified_tools_system import execute_tool as unified_exec
            res = unified_exec('generate_letter', **kwargs)
            
            if getattr(res, 'status', None) == 'success':
                letter_content = res.data.get('letter', '')
                file_path = res.data.get('file_path', '')
                
                # Enhance letter with formatting
                formatted_letter = _format_letter(
                    letter_content, 
                    recipient, 
                    sender, 
                    include_date, 
                    include_signature,
                    formality
                )
                
                # Generate metadata
                metadata = {
                    'letter_type': letter_type,
                    'tone': tone,
                    'formality': formality,
                    'length': length,
                    'language': language,
                    'word_count': len(formatted_letter.split()),
                    'character_count': len(formatted_letter),
                    'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'file_path': file_path
                }
                
                execution_time = time.time() - start_time
                
                return {
                    'status': 'success',
                    'data': {
                        'letter': formatted_letter,
                        'file_path': file_path,
                        'metadata': metadata
                    },
                    'execution_time': execution_time,
                    'result_type': 'document',
                    'result_title': f'📝 {_get_letter_type_title(letter_type)}',
                    'result_content': formatted_letter,
                    'files': [file_path] if file_path else [],
                    'metadata': metadata
                }
            
            return { 
                'status': 'error', 
                'error': getattr(res, 'error', 'Ошибка генерации письма'),
                'execution_time': time.time() - start_time
            }
            
        except Exception as ai_error:
            print(f"⚠️ AI генерация недоступна: {ai_error}")
            
            # Fallback: template-based generation
            return _generate_letter_fallback(
                description, letter_type, recipient, sender, 
                tone, formality, length, include_date, include_signature
            )
        
    except Exception as e:
        return { 
            'status': 'error', 
            'error': str(e),
            'execution_time': time.time() - start_time
        }


def _format_letter(content: str, recipient: str, sender: str, 
                  include_date: bool, include_signature: bool, formality: str) -> str:
    """Format letter with proper structure and styling."""
    formatted = []
    
    # Add date if requested
    if include_date:
        formatted.append(f"Дата: {time.strftime('%d.%m.%Y')}")
        formatted.append("")
    
    # Add recipient if provided
    if recipient:
        formatted.append(f"Получатель: {recipient}")
        formatted.append("")
    
    # Add greeting based on formality
    greeting = _get_greeting(formality, recipient)
    formatted.append(greeting)
    formatted.append("")
    
    # Add main content
    formatted.append(content)
    formatted.append("")
    
    # Add closing based on formality
    closing = _get_closing(formality)
    formatted.append(closing)
    formatted.append("")
    
    # Add signature if requested
    if include_signature and sender:
        formatted.append(f"С уважением,")
        formatted.append(f"{sender}")
        formatted.append("")
    
    return "\n".join(formatted)


def _get_greeting(formality: str, recipient: str) -> str:
    """Get appropriate greeting based on formality level."""
    if formality == 'very_formal':
        return f"Уважаемый{_get_recipient_suffix(recipient)}!"
    elif formality == 'formal':
        return f"Уважаемый{_get_recipient_suffix(recipient)}!"
    elif formality == 'semi_formal':
        return f"Здравствуйте{_get_recipient_suffix(recipient)}!"
    else:  # casual
        return f"Привет{_get_recipient_suffix(recipient)}!"


def _get_recipient_suffix(recipient: str) -> str:
    """Get appropriate suffix for recipient name."""
    if not recipient:
        return ""
    
    # Simple gender detection based on name endings
    if recipient.endswith(('а', 'я', 'ь')):
        return "ая"
    else:
        return "ый"


def _get_closing(formality: str) -> str:
    """Get appropriate closing based on formality level."""
    if formality == 'very_formal':
        return "С глубоким уважением,"
    elif formality == 'formal':
        return "С уважением,"
    elif formality == 'semi_formal':
        return "С наилучшими пожеланиями,"
    else:  # casual
        return "До свидания,"


def _get_letter_type_title(letter_type: str) -> str:
    """Get human-readable title for letter type."""
    titles = {
        'business': 'Деловое письмо',
        'complaint': 'Претензия',
        'request': 'Запрос',
        'response': 'Ответ',
        'notification': 'Уведомление',
        'agreement': 'Соглашение',
        'contract': 'Договорное письмо'
    }
    return titles.get(letter_type, 'Письмо')


def _generate_letter_fallback(description: str, letter_type: str, recipient: str, 
                             sender: str, tone: float, formality: str, length: str,
                             include_date: bool, include_signature: bool) -> Dict[str, Any]:
    """Generate letter using template-based fallback."""
    start_time = time.time()
    
    try:
        # Create template-based letter
        templates = {
            'business': f"Уважаемый{_get_recipient_suffix(recipient)}!\n\n{description}\n\nС уважением,",
            'complaint': f"Уважаемый{_get_recipient_suffix(recipient)}!\n\n{description}\n\nС требованием разобраться,",
            'request': f"Уважаемый{_get_recipient_suffix(recipient)}!\n\n{description}\n\nС просьбой рассмотреть,",
            'response': f"Уважаемый{_get_recipient_suffix(recipient)}!\n\n{description}\n\nС уважением,",
            'notification': f"Уважаемый{_get_recipient_suffix(recipient)}!\n\n{description}\n\nС уведомлением,",
            'agreement': f"Уважаемый{_get_recipient_suffix(recipient)}!\n\n{description}\n\nС согласием,",
            'contract': f"Уважаемый{_get_recipient_suffix(recipient)}!\n\n{description}\n\nС предложением сотрудничества,"
        }
        
        base_letter = templates.get(letter_type, templates['business'])
        
        # Add sender if provided
        if sender:
            base_letter += f"\n{sender}"
        
        # Format with proper structure
        formatted_letter = _format_letter(
            base_letter, recipient, sender, include_date, include_signature, formality
        )
        
        # Generate file path
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        filename = f"letter_{letter_type}_{timestamp}.txt"
        file_path = f"exports/{filename}"
        
        # Save to file
        try:
            import os
            os.makedirs("exports", exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(formatted_letter)
        except Exception as e:
            print(f"⚠️ Не удалось сохранить файл: {e}")
            file_path = ""
        
        execution_time = time.time() - start_time
        
        return {
            'status': 'success',
            'data': {
                'letter': formatted_letter,
                'file_path': file_path,
                'metadata': {
                    'letter_type': letter_type,
                    'tone': tone,
                    'formality': formality,
                    'length': length,
                    'word_count': len(formatted_letter.split()),
                    'character_count': len(formatted_letter),
                    'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'method': 'template_fallback'
                }
            },
            'execution_time': execution_time,
            'result_type': 'document',
            'result_title': f'📝 {_get_letter_type_title(letter_type)} (шаблон)',
            'result_content': formatted_letter,
            'files': [file_path] if file_path else []
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'error': f'Ошибка генерации письма: {str(e)}',
            'execution_time': time.time() - start_time
        }


