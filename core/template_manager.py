"""
Template manager module for handling letter templates in Neo4j
"""

import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

# Try to import Neo4j with proper error handling
NEO4J_AVAILABLE = False
GraphDatabase = None
try:
    from neo4j import GraphDatabase  # type: ignore
    NEO4J_AVAILABLE = True
except ImportError:
    GraphDatabase = None
    print("Warning: Neo4j not available for template management")

class TemplateManager:
    def __init__(self, neo4j_uri=None, neo4j_user=None, neo4j_password=None):
        self.neo4j_uri = neo4j_uri or "neo4j://localhost:7687"
        self.neo4j_user = neo4j_user or "neo4j"
        self.neo4j_password = neo4j_password or "neopassword"
        self.driver = None
        
        # Initialize Neo4j driver if available
        if NEO4J_AVAILABLE and GraphDatabase:
            try:
                self.driver = GraphDatabase.driver(self.neo4j_uri, auth=(self.neo4j_user, self.neo4j_password))
                # Test connection
                with self.driver.session() as session:
                    session.run("RETURN 1")
                print("[OK] Neo4j connection established for template management")
            except Exception as e:
                print(f"[WARN] Failed to connect to Neo4j for template management: {e}")
                self.driver = None
    
    def create_default_templates(self) -> None:
        """Create 10+ construction-specific templates in Neo4j"""
        if not self.driver:
            print("⚠️ Neo4j not available, skipping template creation")
            return
        
        templates = [
            {
                "id": "compliance_sp31",
                "name": "Соответствие СП31",
                "category": "compliance",
                "preview": "Уважаемый [Получатель], Настоящим подтверждаем соответствие проекта нормам СП 31.13330...",
                "full_text": """Уважаемый [Получатель],

Настоящим письмом подтверждаем соответствие проектной документации требованиям СП 31.13330.2012 "Инженерные изыскания для строительства. Основные положения" в части организации строительного контроля и обеспечения качества выполняемых работ.

Подробности соответствия:
{% for detail in compliance_details %}
- {{ detail }}
{% endfor %}

{% if violations %}
Выявленные нарушения:
{% for violation in violations %}
- {{ violation }}
{% endfor %}
{% else %}
Нарушений не выявлено.
{% endif %}

Общая стоимость проекта: {{ total_cost }}

Дата: [Дата]
От: [Отправитель]
Подпись: ________________
"""
            },
            {
                "id": "violation_gesn",
                "name": "Отчет о нарушениях ГЭСН",
                "category": "violation",
                "preview": "Уведомление о несоответствии нормам ГЭСН в сметной документации...",
                "full_text": """Уважаемый [Получатель],

Настоящим уведомляем о выявленных нарушениях в сметной документации, связанных с несоответствием применяемых нормативов государственным элементным сметным нормам (ГЭСН).

Выявленные нарушения:
{% for violation in violations %}
- {{ violation }}
{% endfor %}

Рекомендуем внести соответствующие корректировки в сметную документацию в соответствии с действующими нормативами.

Дата: [Дата]
От: [Отправитель]
Подпись: ________________
"""
            },
            {
                "id": "tender_response_fz44",
                "name": "Ответ на тендер ФЗ-44",
                "category": "tender",
                "preview": "Предложение по участию в тендере в соответствии с ФЗ-44...",
                "full_text": """Уважаемый [Получатель],

Настоящим письмом подтверждаем готовность участия в тендере в соответствии с Федеральным законом №44-ФЗ от 05.04.2013 "О контрактной системе в сфере закупок товаров, работ, услуг для обеспечения государственных и муниципальных нужд".

Наши преимущества:
- Опыт работы на аналогичных объектах: более 10 лет
- Наличие необходимых лицензий и сертификатов
- Современная материально-техническая база
- Квалифицированный персонал

Гарантируем выполнение работ в установленные сроки с соблюдением всех нормативных требований.

Дата: [Дата]
От: [Отправитель]
Подпись: ________________
"""
            },
            {
                "id": "delay_notice",
                "name": "Уведомление о задержке",
                "category": "notification",
                "preview": "Уведомление о возможной задержке сроков выполнения работ...",
                "full_text": """Уважаемый [Получатель],

Настоящим уведомляем о возможной задержке сроков выполнения работ по проекту "[Название проекта]" в связи с [причина задержки].

Ориентировочные сроки смещения: [период задержки]
Планируемые меры по минимизации влияния: [меры по минимизации]

Приносим свои извинения за доставленные неудобства и заверяем, что предпринимаем все необходимые меры для скорейшего возвращения к графику работ.

Дата: [Дата]
От: [Отправитель]
Подпись: ________________
"""
            },
            {
                "id": "payment_dispute",
                "name": "Спор по оплате",
                "category": "financial",
                "preview": "Письмо по вопросам оплаты выполненных работ...",
                "full_text": """Уважаемый [Получатель],

Настоящим письмом обращаем ваше внимание на вопрос оплаты выполненных работ по проекту "[Название проекта]".

Согласно условиям контракта, оплата должна быть произведена в течение [срок оплаты] дней с момента подписания акта выполненных работ. На текущий момент просрочка составляет [период просрочки] дней.

Сумма задолженности: [сумма задолженности]
Номер акта: [номер акта]
Дата акта: [дата акта]

Просим рассмотреть вопрос о срочной оплате задолженности во избежание приостановки работ.

Дата: [Дата]
От: [Отправитель]
Подпись: ________________
"""
            },
            {
                "id": "safety_incident_sanpin",
                "name": "Инцидент по охране труда",
                "category": "safety",
                "preview": "Сообщение о несчастном случае на производстве в соответствии с СанПиН...",
                "full_text": """Уважаемый [Получатель],

Настоящим сообщаем о несчастном случае на производстве, произошедшем [дата инцидента] на объекте "[Название объекта]".

Краткое описание инцидента:
[описание инцидента]

Пострадавший(ие):
[информация о пострадавших]

Принятые меры:
- Оказана первая медицинская помощь
- Уведомлены соответствующие органы
- Проведено расследование причин инцидента
- Приняты меры по предотвращению подобных случаев

Приносим свои извинения за произошедшее и заверяем, что предпринимаем все необходимые меры для обеспечения безопасности на производстве в дальнейшем.

Дата: [Дата]
От: [Отправитель]
Подпись: ________________
"""
            },
            {
                "id": "ecology_ovos_fz7",
                "name": "ОВОС по ФЗ-7",
                "category": "ecology",
                "preview": "Заключение по оценке воздействия на окружающую среду в соответствии с ФЗ-7...",
                "full_text": """Уважаемый [Получатель],

Настоящим письмом направляем заключение по оценке воздействия на окружающую среду (ОВОС) в соответствии с Федеральным законом №7-ФЗ от 10.01.2002 "Об охране окружающей среды".

Основные положения ОВОС:
{% for point in ovos_points %}
- {{ point }}
{% endfor %}

Мероприятия по минимизации воздействия на окружающую среду:
{% for measure in mitigation_measures %}
- {{ measure }}
{% endfor %}

Предлагаем рассмотреть представленные материалы и при необходимости провести дополнительные консультации.

Дата: [Дата]
От: [Отправитель]
Подпись: ________________
"""
            },
            {
                "id": "bim_clash_report",
                "name": "Отчет о коллизиях BIM",
                "category": "bim",
                "preview": "Отчет о выявленных коллизиях в BIM-модели проекта...",
                "full_text": """Уважаемый [Получатель],

Настоящим письмом направляем отчет о выявленных коллизиях в BIM-модели проекта "[Название проекта]".

Общее количество выявленных коллизий: [общее количество коллизий]

Классификация коллизий:
- Критические: [количество критических]
- Значительные: [количество значительных]
- Незначительные: [количество незначительных]

Рекомендуемые меры по устранению:
{% for recommendation in recommendations %}
- {{ recommendation }}
{% endfor %}

Просим рассмотреть представленные материалы и при необходимости провести совещание для обсуждения мер по устранению выявленных коллизий.

Дата: [Дата]
От: [Отправитель]
Подпись: ________________
"""
            },
            {
                "id": "budget_overrun",
                "name": "Превышение бюджета",
                "category": "financial",
                "preview": "Уведомление о превышении сметной стоимости проекта...",
                "full_text": """Уважаемый [Получатель],

Настоящим уведомляем о превышении сметной стоимости проекта "[Название проекта]" над утвержденным бюджетом.

Причины превышения:
{% for reason in overrun_reasons %}
- {{ reason }}
{% endfor %}

Финансовые показатели:
- Утвержденный бюджет: [утвержденный бюджет]
- Текущая стоимость: [текущая стоимость]
- Превышение: [сумма превышения] ([процент превышения]%)

Предлагаемые меры:
{% for measure in proposed_measures %}
- {{ measure }}
{% endfor %}

Просим рассмотреть возможность корректировки бюджета или принять меры по оптимизации затрат.

Дата: [Дата]
От: [Отправитель]
Подпись: ________________
"""
            },
            {
                "id": "hr_salary_claim",
                "name": "Запрос на повышение ЗП",
                "category": "hr",
                "preview": "Письмо с обоснованием запроса на повышение заработной платы...",
                "full_text": """Уважаемый [Получатель],

Настоящим письмом обращаемся с обоснованным запросом на повышение заработной платы для сотрудников строительной бригады в связи со следующими факторами:

Обоснование запроса:
{% for reason in salary_reasons %}
- {{ reason }}
{% endfor %}

Анализ рынка труда показывает, что текущие выплаты ниже среднерыночных на [процент ниже рынка]%.

Предлагаемый уровень заработной платы:
- Бригадир: [новая ЗП бригадира] (текущая: [текущая ЗП бригадира])
- Рабочие: [новая ЗП рабочих] (текущая: [текущая ЗП рабочих])

Уверены, что повышение заработной платы позволит:
{% for benefit in expected_benefits %}
- {{ benefit }}
{% endfor %}

Дата: [Дата]
От: [Отправитель]
Подпись: ________________
"""
            },
            {
                "id": "progress_report",
                "name": "Отчет о прогрессе",
                "category": "report",
                "preview": "Отчет о текущем прогрессе выполнения работ по проекту...",
                "full_text": """Уважаемый [Получатель],

Настоящим письмом сообщаем о текущем прогрессе выполнения работ по проекту "[Название проекта]".

Общий прогресс проекта: [процент выполнения]%

Выполненные этапы:
{% for stage in completed_stages %}
- {{ stage }}
{% endfor %}

Текущие работы:
{% for work in current_works %}
- {{ work }}
{% endfor %}

Планируемые мероприятия:
{% for plan in upcoming_plans %}
- {{ plan }}
{% endfor %}

Дата: [Дата]
От: [Отправитель]
Подпись: ________________
"""
            }
        ]
        
        try:
            with self.driver.session() as session:
                # Delete existing templates to avoid duplicates
                session.run("MATCH (t:Template) DETACH DELETE t")
                
                # Create new templates
                for template in templates:
                    session.run(
                        """
                        CREATE (t:Template {
                            id: $id,
                            name: $name,
                            category: $category,
                            preview: $preview,
                            full_text: $full_text,
                            created_at: datetime()
                        })
                        """,
                        id=template["id"],
                            name=template["name"],
                            category=template["category"],
                            preview=template["preview"],
                            full_text=template["full_text"]
                    )
                
                print(f"[OK] Created {len(templates)} construction-specific templates in Neo4j")
        except Exception as e:
            print(f"[ERROR] Error creating templates: {e}")
    
    def get_templates(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all templates or templates by category"""
        if not self.driver:
            return []
        
        try:
            with self.driver.session() as session:
                if category and category != "all":
                    result = session.run(
                        """
                        MATCH (t:Template)
                        WHERE t.category = $category
                        RETURN t
                        ORDER BY t.name
                        """,
                        category=category
                    )
                else:
                    result = session.run(
                        """
                        MATCH (t:Template)
                        RETURN t
                        ORDER BY t.name
                        """
                    )
                
                templates = []
                for record in result:
                    template = dict(record["t"])
                    templates.append({
                        "id": template.get("id", ""),
                        "name": template.get("name", ""),
                        "category": template.get("category", ""),
                        "preview": template.get("preview", ""),
                        "full_text": template.get("full_text", "")
                    })
                return templates
        except Exception as e:
            print(f"[ERROR] Error getting templates: {e}")
            return []
    
    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific template by ID"""
        if not self.driver:
            return None
        
        try:
            with self.driver.session() as session:
                result = session.run(
                    """
                    MATCH (t:Template {id: $id})
                    RETURN t
                    """,
                    id=template_id
                )
                record = result.single()
                if record:
                    template = dict(record["t"])
                    return {
                        "id": template.get("id", ""),
                        "name": template.get("name", ""),
                        "category": template.get("category", ""),
                        "preview": template.get("preview", ""),
                        "full_text": template.get("full_text", "")
                    }
                return None
        except Exception as e:
            print(f"❌ Error getting template: {e}")
            return None
    
    def create_template(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new template"""
        if not self.driver:
            raise Exception("Database not available")
        
        template_id = template_data.get("id") or str(uuid.uuid4())
        
        try:
            with self.driver.session() as session:
                result = session.run(
                    """
                    CREATE (t:Template {
                        id: $id,
                        name: $name,
                        category: $category,
                        preview: $preview,
                        full_text: $full_text,
                        created_at: datetime()
                    })
                    RETURN t
                    """,
                    id=template_id,
                    name=template_data.get("name", ""),
                    category=template_data.get("category", ""),
                    preview=template_data.get("preview", ""),
                    full_text=template_data.get("full_text", "")
                )
                record = result.single()
                if record:
                    template = dict(record["t"])
                    return {
                        "id": template.get("id", ""),
                        "name": template.get("name", ""),
                        "category": template.get("category", ""),
                        "preview": template.get("preview", ""),
                        "full_text": template.get("full_text", "")
                    }
                else:
                    raise Exception("Failed to create template")
        except Exception as e:
            raise Exception(f"Database error: {str(e)}")
    
    def update_template(self, template_id: str, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing template"""
        if not self.driver:
            raise Exception("Database not available")
        
        try:
            with self.driver.session() as session:
                # Build dynamic SET clause
                set_parts = []
                params = {"id": template_id}
                
                if "name" in template_data:
                    set_parts.append("t.name = $name")
                    params["name"] = template_data["name"]
                    
                if "category" in template_data:
                    set_parts.append("t.category = $category")
                    params["category"] = template_data["category"]
                    
                if "preview" in template_data:
                    set_parts.append("t.preview = $preview")
                    params["preview"] = template_data["preview"]
                    
                if "full_text" in template_data:
                    set_parts.append("t.full_text = $full_text")
                    params["full_text"] = template_data["full_text"]
                
                query = f"""
                    MATCH (t:Template {{id: $id}})
                    SET {", ".join(set_parts)}
                    RETURN t
                """
                
                result = session.run(query, parameters=params)
                record = result.single()
                if record:
                    template = dict(record["t"])
                    return {
                        "id": template.get("id", ""),
                        "name": template.get("name", ""),
                        "category": template.get("category", ""),
                        "preview": template.get("preview", ""),
                        "full_text": template.get("full_text", "")
                    }
                else:
                    raise Exception("Template not found")
        except Exception as e:
            raise Exception(f"Database error: {str(e)}")
    
    def delete_template(self, template_id: str) -> Dict[str, str]:
        """Delete a template"""
        if not self.driver:
            raise Exception("Database not available")
        
        try:
            with self.driver.session() as session:
                session.run(
                    """
                    MATCH (t:Template {id: $id})
                    DETACH DELETE t
                    """,
                    id=template_id
                )
                return {"message": "Template deleted successfully"}
        except Exception as e:
            raise Exception(f"Database error: {str(e)}")

# Initialize template manager and create default templates
template_manager = TemplateManager()

# Create default templates on initialization
template_manager.create_default_templates()
