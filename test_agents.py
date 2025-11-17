"""
Тесты для агентов чатбота
"""
import pytest
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src.agents.finance_agent import finance_agent
from src.agents.legal_agent import legal_agent
from src.agents.project_agent import project_agent
from tests.test_cases import (
    FINANCE_TEST_CASES,
    LEGAL_TEST_CASES,
    PROJECT_TEST_CASES,
    ALL_TEST_CASES,
    calculate_accuracy,
    print_test_report
)


class TestAgents:
    """Тесты для агентов"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Настройка перед каждым тестом"""
        self.agents = {
            'finance': finance_agent,
            'legal': legal_agent,
            'project': project_agent
        }
        self.test_user_id = 12345
    
    def check_keywords_in_answer(self, answer: str, keywords: list) -> bool:
        """
        Проверить наличие ключевых слов в ответе
        
        Args:
            answer: Ответ агента
            keywords: Список ключевых слов
        
        Returns:
            True если найдено хотя бы 70% ключевых слов
        """
        answer_lower = answer.lower()
        found_keywords = sum(
            1 for keyword in keywords 
            if keyword.lower() in answer_lower
        )
        
        threshold = len(keywords) * 0.7  # 70% ключевых слов
        return found_keywords >= threshold
    
    @pytest.mark.asyncio
    async def test_finance_agent(self):
        """Тест финансового агента"""
        agent = self.agents['finance']
        results = []
        
        print("\n\nТестирование Финансового агента...")
        
        for i, test_case in enumerate(FINANCE_TEST_CASES, 1):
            query = test_case['query']
            expected_keywords = test_case['expected_keywords']
            
            print(f"  [{i}/{len(FINANCE_TEST_CASES)}] {query[:50]}...")
            
            result = await agent.process_query(
                query=query,
                user_id=self.test_user_id
            )
            
            if result['success']:
                answer = result['answer']
                passed = self.check_keywords_in_answer(answer, expected_keywords)
                
                results.append({
                    'query': query,
                    'passed': passed,
                    'agent': 'finance',
                    'answer_length': len(answer)
                })
                
                status = "✅" if passed else "❌"
                print(f"    {status} {'PASSED' if passed else 'FAILED'}")
            else:
                results.append({
                    'query': query,
                    'passed': False,
                    'agent': 'finance',
                    'error': result.get('error')
                })
                print(f"    ❌ ERROR: {result.get('error')}")
        
        accuracy = calculate_accuracy(results)
        assert accuracy >= 85, f"Finance agent accuracy {accuracy:.1f}% < 85%"
    
    @pytest.mark.asyncio
    async def test_legal_agent(self):
        """Тест юридического агента"""
        agent = self.agents['legal']
        results = []
        
        print("\n\nТестирование Юридического агента...")
        
        for i, test_case in enumerate(LEGAL_TEST_CASES, 1):
            query = test_case['query']
            expected_keywords = test_case['expected_keywords']
            
            print(f"  [{i}/{len(LEGAL_TEST_CASES)}] {query[:50]}...")
            
            result = await agent.process_query(
                query=query,
                user_id=self.test_user_id
            )
            
            if result['success']:
                answer = result['answer']
                passed = self.check_keywords_in_answer(answer, expected_keywords)
                
                results.append({
                    'query': query,
                    'passed': passed,
                    'agent': 'legal',
                    'answer_length': len(answer)
                })
                
                status = "✅" if passed else "❌"
                print(f"    {status} {'PASSED' if passed else 'FAILED'}")
            else:
                results.append({
                    'query': query,
                    'passed': False,
                    'agent': 'legal',
                    'error': result.get('error')
                })
                print(f"    ❌ ERROR: {result.get('error')}")
        
        accuracy = calculate_accuracy(results)
        assert accuracy >= 85, f"Legal agent accuracy {accuracy:.1f}% < 85%"
    
    @pytest.mark.asyncio
    async def test_project_agent(self):
        """Тест проектного агента"""
        agent = self.agents['project']
        results = []
        
        print("\n\nТестирование Проектного агента...")
        
        for i, test_case in enumerate(PROJECT_TEST_CASES, 1):
            query = test_case['query']
            expected_keywords = test_case['expected_keywords']
            
            print(f"  [{i}/{len(PROJECT_TEST_CASES)}] {query[:50]}...")
            
            result = await agent.process_query(
                query=query,
                user_id=self.test_user_id
            )
            
            if result['success']:
                answer = result['answer']
                passed = self.check_keywords_in_answer(answer, expected_keywords)
                
                results.append({
                    'query': query,
                    'passed': passed,
                    'agent': 'project',
                    'answer_length': len(answer)
                })
                
                status = "✅" if passed else "❌"
                print(f"    {status} {'PASSED' if passed else 'FAILED'}")
            else:
                results.append({
                    'query': query,
                    'passed': False,
                    'agent': 'project',
                    'error': result.get('error')
                })
                print(f"    ❌ ERROR: {result.get('error')}")
        
        accuracy = calculate_accuracy(results)
        assert accuracy >= 85, f"Project agent accuracy {accuracy:.1f}% < 85%"
    
    @pytest.mark.asyncio
    async def test_all_agents_combined(self):
        """Тест всех агентов вместе"""
        results = []
        
        print("\n\nТестирование всех агентов...")
        
        for test_case in ALL_TEST_CASES:
            agent_type = test_case['agent']
            query = test_case['query']
            expected_keywords = test_case['expected_keywords']
            
            agent = self.agents[agent_type]
            
            result = await agent.process_query(
                query=query,
                user_id=self.test_user_id
            )
            
            if result['success']:
                answer = result['answer']
                passed = self.check_keywords_in_answer(answer, expected_keywords)
                
                results.append({
                    'query': query,
                    'passed': passed,
                    'agent': agent_type,
                    'answer_length': len(answer)
                })
            else:
                results.append({
                    'query': query,
                    'passed': False,
                    'agent': agent_type,
                    'error': result.get('error')
                })
        
        # Вывести отчет
        print_test_report(results)
        
        # Проверить общую точность
        accuracy = calculate_accuracy(results)
        assert accuracy >= 85, f"Overall accuracy {accuracy:.1f}% < 85%"
    
    @pytest.mark.asyncio
    async def test_response_time(self):
        """Тест времени ответа"""
        import time
        
        agent = finance_agent
        query = "Какой бюджет на маркетинг?"
        
        start_time = time.time()
        result = await agent.process_query(
            query=query,
            user_id=self.test_user_id
        )
        duration = time.time() - start_time
        
        assert result['success'], "Query processing failed"
        assert duration <= 3.0, f"Response time {duration:.2f}s exceeds 3s limit"
        
        print(f"\n✅ Response time: {duration:.2f}s (limit: 3s)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
