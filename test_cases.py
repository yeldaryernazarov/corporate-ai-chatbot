"""
Тестовые кейсы для проверки работы агентов
"""
import pytest
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

# Тестовые кейсы для финансового агента
FINANCE_TEST_CASES = [
    {
        "query": "Какой бюджет на маркетинг в Q4?",
        "expected_keywords": ["500,000", "руб", "квартал", "маркетинг"],
        "agent": "finance"
    },
    {
        "query": "Когда нужно оплатить аренду офиса?",
        "expected_keywords": ["25 числа", "предыдущего месяца", "аренда"],
        "agent": "finance"
    },
    {
        "query": "Какой лимит на обучение сотрудника?",
        "expected_keywords": ["50,000", "год", "обучение"],
        "agent": "finance"
    },
    {
        "query": "Как утвердить командировочные расходы?",
        "expected_keywords": ["2 недели", "поездк", "командировочн"],
        "agent": "finance"
    },
    {
        "query": "Сколько составляют суточные в Европе?",
        "expected_keywords": ["50", "EUR", "день", "Европ"],
        "agent": "finance"
    },
    {
        "query": "Кто главный бухгалтер?",
        "expected_keywords": ["Иванова", "Мария"],
        "agent": "finance"
    },
    {
        "query": "Когда выплачивается зарплата?",
        "expected_keywords": ["5", "20", "числа", "месяц"],
        "agent": "finance"
    },
    {
        "query": "Какой бюджет на IT отдел?",
        "expected_keywords": ["1,200,000", "квартал", "IT"],
        "agent": "finance"
    },
    {
        "query": "Контакты финансового отдела",
        "expected_keywords": ["accounting@company.ru", "финанс"],
        "agent": "finance"
    },
    {
        "query": "Лимит на канцелярию",
        "expected_keywords": ["15,000", "месяц", "отдел", "канцеляр"],
        "agent": "finance"
    }
]

# Тестовые кейсы для юридического агента
LEGAL_TEST_CASES = [
    {
        "query": "Где найти типовой договор NDA?",
        "expected_keywords": ["SharePoint", "NDA", "шаблон", "template"],
        "agent": "legal"
    },
    {
        "query": "Какие документы нужны для регистрации филиала?",
        "expected_keywords": ["решение", "положение", "приказ", "устав", "доверенность"],
        "agent": "legal"
    },
    {
        "query": "Сколько стоит регистрация филиала?",
        "expected_keywords": ["6,000", "госпошлина", "30,000", "юридическ"],
        "agent": "legal"
    },
    {
        "query": "Кто главный юрист компании?",
        "expected_keywords": ["Козлов", "Сергей"],
        "agent": "legal"
    },
    {
        "query": "Процедура согласования контракта на 300 тысяч",
        "expected_keywords": ["стандартн", "руководител", "юридическ", "2-3 дня"],
        "agent": "legal"
    },
    {
        "query": "Что такое ФЗ-152?",
        "expected_keywords": ["персональн", "данн", "защит"],
        "agent": "legal"
    },
    {
        "query": "Типы трудовых договоров",
        "expected_keywords": ["бессрочн", "срочн", "ГПХ"],
        "agent": "legal"
    },
    {
        "query": "Контакт юриста по договорам",
        "expected_keywords": ["Николаева", "Елена", "nikolaeva"],
        "agent": "legal"
    },
    {
        "query": "Где находится кодекс корпоративной этики?",
        "expected_keywords": ["Intranet", "Политик", "Ethics_Code"],
        "agent": "legal"
    },
    {
        "query": "Сроки согласования срочных документов",
        "expected_keywords": ["1 рабочий день", "срочн"],
        "agent": "legal"
    }
]

# Тестовые кейсы для проектного агента
PROJECT_TEST_CASES = [
    {
        "query": "Какой статус проекта Миграция CRM?",
        "expected_keywords": ["процесс", "65%", "CRM"],
        "agent": "project"
    },
    {
        "query": "Кто project manager проекта мобильного приложения?",
        "expected_keywords": ["Соколов", "Дмитрий"],
        "agent": "project"
    },
    {
        "query": "Какие проекты просрочены?",
        "expected_keywords": ["SSL", "email", "просроч"],
        "agent": "project"
    },
    {
        "query": "Когда дедлайн по миграции данных CRM?",
        "expected_keywords": ["01.12.2025", "миграци", "данн"],
        "agent": "project"
    },
    {
        "query": "Есть ли риски в проекте CRM?",
        "expected_keywords": ["ВЫСОКИЙ", "интеграци", "1С", "риск"],
        "agent": "project"
    },
    {
        "query": "Статус проекта реновации офиса",
        "expected_keywords": ["запланирован", "01.12", "реновац"],
        "agent": "project"
    },
    {
        "query": "Какие дедлайны на этой неделе?",
        "expected_keywords": ["18.11", "20.11", "22.11"],
        "agent": "project"
    },
    {
        "query": "Бюджет проекта Миграция CRM",
        "expected_keywords": ["2,500,000", "68%", "бюджет"],
        "agent": "project"
    },
    {
        "query": "Контакты PMO",
        "expected_keywords": ["Смирнов", "Игорь", "pmo@company.ru"],
        "agent": "project"
    },
    {
        "query": "Какие инструменты используются для управления проектами?",
        "expected_keywords": ["Jira", "Confluence", "MS Project"],
        "agent": "project"
    }
]

# Все тестовые кейсы
ALL_TEST_CASES = FINANCE_TEST_CASES + LEGAL_TEST_CASES + PROJECT_TEST_CASES


def calculate_accuracy(results):
    """
    Рассчитать точность ответов
    
    Args:
        results: Список результатов тестов
    
    Returns:
        Процент правильных ответов
    """
    if not results:
        return 0.0
    
    correct = sum(1 for r in results if r['passed'])
    total = len(results)
    
    return (correct / total) * 100


def print_test_report(results):
    """
    Вывести отчет о тестировании
    
    Args:
        results: Список результатов тестов
    """
    print("\n" + "=" * 70)
    print("ОТЧЕТ О ТЕСТИРОВАНИИ")
    print("=" * 70)
    
    # Группировка по агентам
    agents = {}
    for result in results:
        agent = result['agent']
        if agent not in agents:
            agents[agent] = []
        agents[agent].append(result)
    
    # Статистика по агентам
    for agent_name, agent_results in agents.items():
        accuracy = calculate_accuracy(agent_results)
        passed = sum(1 for r in agent_results if r['passed'])
        total = len(agent_results)
        
        status = "✅ PASSED" if accuracy >= 85 else "❌ FAILED"
        
        print(f"\n{agent_name.upper()} Агент: {status}")
        print(f"  Точность: {accuracy:.1f}%")
        print(f"  Успешных: {passed}/{total}")
        
        # Показать проваленные тесты
        failed = [r for r in agent_results if not r['passed']]
        if failed:
            print(f"  Проваленные тесты:")
            for r in failed:
                print(f"    - {r['query'][:50]}...")
    
    # Общая статистика
    total_accuracy = calculate_accuracy(results)
    total_passed = sum(1 for r in results if r['passed'])
    total_tests = len(results)
    
    print("\n" + "-" * 70)
    print(f"ОБЩАЯ ТОЧНОСТЬ: {total_accuracy:.1f}%")
    print(f"Всего тестов: {total_tests}")
    print(f"Успешных: {total_passed}")
    print(f"Проваленных: {total_tests - total_passed}")
    
    if total_accuracy >= 85:
        print("\n✅ ТРЕБОВАНИЕ ВЫПОЛНЕНО: Точность >= 85%")
    else:
        print(f"\n❌ ТРЕБОВАНИЕ НЕ ВЫПОЛНЕНО: Точность {total_accuracy:.1f}% < 85%")
    
    print("=" * 70)
