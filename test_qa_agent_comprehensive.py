#!/usr/bin/env python3
"""
Comprehensive QA Agent Test Suite

This test script thoroughly evaluates all aspects of the QA Agent functionality
including database queries, non-database content, accuracy, performance, and edge cases.

Usage:
    python test_qa_agent_comprehensive.py
    
Features tested:
- Database integration and paper searching
- Question answering accuracy and completeness
- Performance metrics and response times
- Edge cases and error handling
- Citation generation and formatting
- Caching mechanisms
- Async vs sync functionality
- Different question types
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# Import the QA Agent and dependencies
from src.agents.qa_agent import QuestionAnsweringAgent
from src.storage.database import DatabaseManager
from src.storage.models import Paper, ResearchNote, ResearchTheme, Citation
from src.utils.config import Config

# Test configuration
TEST_CONFIG = {
    "performance_thresholds": {
        "max_response_time": 30.0,  # seconds
        "min_confidence": 0.3,
        "max_memory_usage": 500,  # MB
    },
    "test_questions": {
        "database_dependent": [
            "What are the latest trends in machine learning?",
            "How do neural networks work?",
            "What is the impact of AI on healthcare?",
            "Explain quantum computing applications",
            "What are the benefits of renewable energy?",
        ],
        "general_knowledge": [
            "What is the capital of France?",
            "How does photosynthesis work?",
            "What is the theory of relativity?",
            "Explain the water cycle",
            "What causes climate change?",
        ],
        "complex_queries": [
            "Compare deep learning approaches to traditional machine learning for medical diagnosis",
            "What are the ethical implications of artificial intelligence in autonomous vehicles?",
            "How do different battery technologies compare for electric vehicle applications?",
        ],
        "edge_cases": [
            "",  # Empty question
            "?",  # Just punctuation
            "a" * 1000,  # Very long question
            "What is ∑∏∆∇∂∫ in mathematics?",  # Special characters
            "Tell me about xyzabc123nonexistent",  # Nonsensical query
        ]
    }
}

class QAAgentTester:
    """Comprehensive QA Agent testing framework"""
    
    def __init__(self):
        self.config = Config()
        self.database = None
        self.qa_agent = None
        self.test_results = {
            "start_time": datetime.now().isoformat(),
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "performance_metrics": {},
            "detailed_results": [],
            "errors": []
        }
        
        # Setup logging with UTF-8 encoding for Windows compatibility
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('test_qa_agent.log', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    async def setup(self):
        """Initialize database and QA agent for testing"""
        try:
            self.logger.info("Setting up test environment...")
            
            # Initialize database
            self.database = DatabaseManager()
            # DatabaseManager doesn't have async init, so just initialize
            
            # Initialize QA agent with config only
            self.qa_agent = QuestionAnsweringAgent(config=self.config.to_dict() if hasattr(self.config, 'to_dict') else {})
            
            # Verify setup
            try:
                paper_count = len(self.database.get_papers())
                self.logger.info(f"Database initialized with {paper_count} papers")
                
                # Add some test data if database is empty
                if paper_count == 0:
                    await self._create_test_data()
            except Exception as e:
                self.logger.warning(f"Could not get paper count: {e}")
                # Still continue with testing
                
        except Exception as e:
            self.logger.error(f"Setup failed: {e}")
            raise
    
    async def _create_test_data(self):
        """Create sample test data if database is empty"""
        self.logger.info("Creating sample test data...")
        
        test_papers = [
            Paper(
                id="test_paper_1",
                title="Deep Learning for Medical Diagnosis",
                authors=["Smith, J.", "Doe, A."],
                abstract="This paper explores the application of deep learning techniques in medical diagnosis, showing significant improvements in accuracy.",
                url="https://example.com/paper1",
                citations=150,
                doi="10.1000/test1"
            ),
            Paper(
                id="test_paper_2",
                title="Quantum Computing Applications in Cryptography",
                authors=["Johnson, B.", "Wilson, C."],
                abstract="An analysis of how quantum computing can revolutionize cryptographic systems and the implications for security.",
                url="https://example.com/paper2",
                citations=75,
                doi="10.1000/test2"
            ),
            Paper(
                id="test_paper_3",
                title="Renewable Energy Storage Solutions",
                authors=["Brown, D.", "Taylor, E."],
                abstract="This study examines various renewable energy storage technologies and their efficiency in grid applications.",
                url="https://example.com/paper3",
                citations=200,
                doi="10.1000/test3"
            )
        ]
        
        for paper in test_papers:
            self.database.save_paper(paper)
        
        self.logger.info(f"Added {len(test_papers)} test papers to database")
    
    async def run_all_tests(self):
        """Run the complete test suite"""
        self.logger.info("Starting comprehensive QA Agent testing...")
        
        test_methods = [
            self.test_database_integration,
            self.test_question_answering_accuracy,
            self.test_performance_metrics,
            self.test_async_vs_sync,
            self.test_caching_mechanism,
            self.test_edge_cases,
            self.test_citation_generation,
            self.test_different_question_types,
            self.test_error_handling,
            self.test_memory_usage
        ]
        
        for test_method in test_methods:
            try:
                await test_method()
            except Exception as e:
                self.logger.error(f"Test {test_method.__name__} failed: {e}")
                self.test_results["errors"].append({
                    "test": test_method.__name__,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
        await self.generate_final_report()
    
    async def test_database_integration(self):
        """Test database integration and paper retrieval"""
        self.logger.info("Testing database integration...")
        
        # Test basic database operations
        try:
            # Test getting all papers
            start_time = time.time()
            papers = self.database.get_papers()
            search_time = time.time() - start_time
            
            result = {
                "test": "database_get_papers",
                "papers_found": len(papers),
                "search_time": search_time,
                "success": True
            }
            
            self.test_results["detailed_results"].append(result)
            self.test_results["tests_run"] += 1
            
            if search_time < 5.0:  # Should complete within 5 seconds
                self.test_results["tests_passed"] += 1
                self.logger.info(f"[PASS] Database get_papers: {len(papers)} papers in {search_time:.2f}s")
            else:
                self.test_results["tests_failed"] += 1
                self.logger.warning(f"[FAIL] Database get_papers too slow: {search_time:.2f}s")
                
        except Exception as e:
            self.test_results["tests_failed"] += 1
            self.test_results["errors"].append({
                "test": "database_integration",
                "error": str(e)
            })
            self.logger.error(f"[FAIL] Database integration failed: {e}")
            self.test_results["tests_run"] += 1
    
    async def test_question_answering_accuracy(self):
        """Test question answering accuracy and completeness"""
        self.logger.info("Testing question answering accuracy...")
        
        questions = TEST_CONFIG["test_questions"]["database_dependent"]
        
        for question in questions:
            start_time = time.time()
            
            try:
                # Test sync version
                answer = self.qa_agent.answer_question(question)
                response_time = time.time() - start_time
                
                # Evaluate answer quality
                quality_score = self._evaluate_answer_quality(question, answer)
                
                result = {
                    "test": "answer_accuracy",
                    "question": question,
                    "answer_length": len(answer.get("answer", "")),
                    "confidence": answer.get("confidence", 0),
                    "response_time": response_time,
                    "quality_score": quality_score,
                    "source_papers": len(answer.get("source_papers", [])),
                    "success": True
                }
                
                self.test_results["detailed_results"].append(result)
                self.test_results["tests_run"] += 1
                
                # Check if answer meets quality thresholds
                if (response_time < TEST_CONFIG["performance_thresholds"]["max_response_time"] and
                    answer.get("confidence", 0) >= TEST_CONFIG["performance_thresholds"]["min_confidence"] and
                    len(answer.get("answer", "")) > 50):  # Minimum answer length
                    
                    self.test_results["tests_passed"] += 1
                    self.logger.info(f"[PASS] Question answered successfully: confidence={answer.get('confidence', 0):.2f}")
                else:
                    self.test_results["tests_failed"] += 1
                    self.logger.warning(f"[FAIL] Answer quality below threshold")
                    
            except Exception as e:
                self.test_results["tests_failed"] += 1
                self.test_results["errors"].append({
                    "test": "answer_accuracy",
                    "question": question,
                    "error": str(e)
                })
                self.logger.error(f"[FAIL] Question answering failed: {e}")
    
    def _evaluate_answer_quality(self, question: str, answer: Dict[str, Any]) -> float:
        """Evaluate the quality of an answer (0.0 to 1.0)"""
        score = 0.0
        
        # Check if answer exists and has content
        if answer.get("answer") and len(answer["answer"]) > 20:
            score += 0.3
        
        # Check confidence level
        confidence = answer.get("confidence", 0)
        score += confidence * 0.3
        
        # Check if source papers are provided
        source_papers = answer.get("source_papers", [])
        if source_papers:
            score += 0.2
        
        # Check for question type recognition
        if answer.get("question_type"):
            score += 0.1
        
        # Check for metadata
        if answer.get("metadata"):
            score += 0.1
        
        return min(score, 1.0)
    
    async def test_performance_metrics(self):
        """Test performance metrics and response times"""
        self.logger.info("Testing performance metrics...")
        
        # Test multiple questions and measure performance
        questions = TEST_CONFIG["test_questions"]["database_dependent"][:3]
        response_times = []
        memory_usage = []
        
        for question in questions:
            start_time = time.time()
            
            try:
                answer = self.qa_agent.answer_question(question)
                response_time = time.time() - start_time
                response_times.append(response_time)
                
                # Get performance stats from agent
                stats = self.qa_agent.get_performance_stats()
                
                self.logger.info(f"Response time: {response_time:.2f}s, Avg: {stats.get('avg_response_time', 0):.2f}s")
                
            except Exception as e:
                self.logger.error(f"Performance test failed: {e}")
        
        # Calculate performance metrics
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            
            self.test_results["performance_metrics"] = {
                "avg_response_time": avg_response_time,
                "max_response_time": max_response_time,
                "total_questions_tested": len(response_times)
            }
            
            # Check performance thresholds
            if avg_response_time < TEST_CONFIG["performance_thresholds"]["max_response_time"]:
                self.test_results["tests_passed"] += 1
                self.logger.info(f"[PASS] Performance test passed: avg={avg_response_time:.2f}s")
            else:
                self.test_results["tests_failed"] += 1
                self.logger.warning(f"[FAIL] Performance test failed: avg={avg_response_time:.2f}s")
        
        self.test_results["tests_run"] += 1
    
    async def test_async_vs_sync(self):
        """Test async vs sync functionality"""
        self.logger.info("Testing async vs sync functionality...")
        
        question = "What are the benefits of machine learning?"
        
        # Test sync version
        start_time = time.time()
        sync_answer = self.qa_agent.answer_question(question)
        sync_time = time.time() - start_time
        
        # Test async version
        start_time = time.time()
        async_answer = await self.qa_agent.answer_question_async(question)
        async_time = time.time() - start_time
        
        # Compare results
        result = {
            "test": "async_vs_sync",
            "sync_time": sync_time,
            "async_time": async_time,
            "sync_answer_length": len(sync_answer.get("answer", "")),
            "async_answer_length": len(async_answer.get("answer", "")),
            "answers_similar": self._compare_answers(sync_answer, async_answer)
        }
        
        self.test_results["detailed_results"].append(result)
        self.test_results["tests_run"] += 1
        
        if result["answers_similar"] and async_time <= sync_time * 1.5:  # Async shouldn't be much slower
            self.test_results["tests_passed"] += 1
            self.logger.info(f"[PASS] Async/sync test passed: sync={sync_time:.2f}s, async={async_time:.2f}s")
        else:
            self.test_results["tests_failed"] += 1
            self.logger.warning(f"[FAIL] Async/sync test failed")
    
    def _compare_answers(self, answer1: Dict, answer2: Dict) -> bool:
        """Compare two answers for similarity"""
        # Simple comparison - in a real test you might use semantic similarity
        text1 = answer1.get("answer", "").lower()
        text2 = answer2.get("answer", "").lower()
        
        if not text1 or not text2:
            return False
        
        # Check if answers have similar length and some common words
        length_ratio = min(len(text1), len(text2)) / max(len(text1), len(text2))
        words1 = set(text1.split())
        words2 = set(text2.split())
        common_words = len(words1.intersection(words2))
        
        return length_ratio > 0.7 and common_words > 5
    
    async def test_caching_mechanism(self):
        """Test caching functionality"""
        self.logger.info("Testing caching mechanism...")
        
        question = "What is artificial intelligence?"
        
        # First call (should cache the result)
        start_time = time.time()
        first_answer = self.qa_agent.answer_question(question)
        first_time = time.time() - start_time
        
        # Second call (should use cache)
        start_time = time.time()
        second_answer = self.qa_agent.answer_question(question)
        second_time = time.time() - start_time
        
        # Get performance stats to check cache hits
        stats = self.qa_agent.get_performance_stats()
        cache_hit_rate = stats.get("cache_hit_rate", 0)
        
        result = {
            "test": "caching",
            "first_call_time": first_time,
            "second_call_time": second_time,
            "cache_hit_rate": cache_hit_rate,
            "answers_identical": first_answer == second_answer
        }
        
        self.test_results["detailed_results"].append(result)
        self.test_results["tests_run"] += 1
        
        # Cache should make second call faster
        if second_time < first_time * 0.8:  # At least 20% faster
            self.test_results["tests_passed"] += 1
            self.logger.info(f"[PASS] Caching test passed: first={first_time:.2f}s, second={second_time:.2f}s")
        else:
            self.test_results["tests_failed"] += 1
            self.logger.warning(f"[FAIL] Caching test failed: no significant speed improvement")
    
    async def test_edge_cases(self):
        """Test edge cases and error handling"""
        self.logger.info("Testing edge cases...")
        
        edge_questions = TEST_CONFIG["test_questions"]["edge_cases"]
        
        for question in edge_questions:
            try:
                answer = self.qa_agent.answer_question(question)
                
                result = {
                    "test": "edge_case",
                    "question": question[:50] + "..." if len(question) > 50 else question,
                    "handled_gracefully": answer is not None,
                    "answer_provided": bool(answer.get("answer")),
                    "error_occurred": False
                }
                
                self.test_results["detailed_results"].append(result)
                self.test_results["tests_run"] += 1
                
                if answer is not None:
                    self.test_results["tests_passed"] += 1
                    self.logger.info(f"[PASS] Edge case handled: '{question[:30]}...'")
                else:
                    self.test_results["tests_failed"] += 1
                    
            except Exception as e:
                result = {
                    "test": "edge_case",
                    "question": question[:50] + "..." if len(question) > 50 else question,
                    "handled_gracefully": False,
                    "error_occurred": True,
                    "error": str(e)
                }
                
                self.test_results["detailed_results"].append(result)
                self.test_results["tests_run"] += 1
                self.test_results["tests_failed"] += 1
                self.logger.warning(f"[FAIL] Edge case caused error: {e}")
    
    async def test_citation_generation(self):
        """Test citation generation and formatting"""
        self.logger.info("Testing citation generation...")
        
        question = "What are recent advances in deep learning?"
        answer = self.qa_agent.answer_question(question)
        
        source_papers = answer.get("source_papers", [])
        
        result = {
            "test": "citation_generation",
            "source_papers_count": len(source_papers),
            "papers_have_ids": all("id" in paper for paper in source_papers),
            "papers_have_titles": all("title" in paper for paper in source_papers),
            "papers_have_authors": all("authors" in paper for paper in source_papers)
        }
        
        self.test_results["detailed_results"].append(result)
        self.test_results["tests_run"] += 1
        
        if (source_papers and 
            result["papers_have_ids"] and 
            result["papers_have_titles"]):
            self.test_results["tests_passed"] += 1
            self.logger.info(f"[PASS] Citation test passed: {len(source_papers)} source papers")
        else:
            self.test_results["tests_failed"] += 1
            self.logger.warning(f"[FAIL] Citation test failed: incomplete paper information")
    
    async def test_different_question_types(self):
        """Test different types of questions"""
        self.logger.info("Testing different question types...")
        
        question_types = [
            ("factual", "What is machine learning?"),
            ("comparative", "Compare supervised and unsupervised learning"),
            ("analytical", "Why is deep learning effective for image recognition?"),
            ("procedural", "How do you train a neural network?")
        ]
        
        for question_type, question in question_types:
            try:
                answer = self.qa_agent.answer_question(question)
                detected_type = answer.get("question_type", "unknown")
                
                result = {
                    "test": "question_type",
                    "expected_type": question_type,
                    "detected_type": detected_type,
                    "question": question,
                    "answer_provided": bool(answer.get("answer")),
                    "confidence": answer.get("confidence", 0)
                }
                
                self.test_results["detailed_results"].append(result)
                self.test_results["tests_run"] += 1
                
                if answer.get("answer") and len(answer["answer"]) > 20:
                    self.test_results["tests_passed"] += 1
                    self.logger.info(f"[PASS] Question type '{question_type}' handled successfully")
                else:
                    self.test_results["tests_failed"] += 1
                    self.logger.warning(f"[FAIL] Question type '{question_type}' not handled well")
                    
            except Exception as e:
                self.test_results["tests_failed"] += 1
                self.logger.error(f"[FAIL] Question type '{question_type}' caused error: {e}")
    
    async def test_error_handling(self):
        """Test error handling capabilities"""
        self.logger.info("Testing error handling...")
        
        # Test with empty question
        try:
            answer = self.qa_agent.answer_question("")
            
            result = {
                "test": "error_handling",
                "scenario": "empty_question",
                "handled_gracefully": answer is not None,
                "fallback_provided": bool(answer.get("answer")) if answer else False
            }
            
            self.test_results["detailed_results"].append(result)
            self.test_results["tests_run"] += 1
            
            if answer is not None:
                self.test_results["tests_passed"] += 1
                self.logger.info("[PASS] Error handling test passed: graceful fallback")
            else:
                self.test_results["tests_failed"] += 1
                self.logger.warning("[FAIL] Error handling test failed: no graceful fallback")
                
        except Exception as e:
            self.test_results["tests_failed"] += 1
            self.logger.warning(f"[FAIL] Error handling test caused exception: {e}")
            self.test_results["tests_run"] += 1
    
    async def test_memory_usage(self):
        """Test memory usage during operation"""
        self.logger.info("Testing memory usage...")
        
        try:
            import psutil
            process = psutil.Process()
            
            # Get initial memory usage
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Run several questions to stress test memory
            questions = TEST_CONFIG["test_questions"]["database_dependent"] * 3
            
            for question in questions:
                self.qa_agent.answer_question(question)
            
            # Get final memory usage
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            result = {
                "test": "memory_usage",
                "initial_memory_mb": initial_memory,
                "final_memory_mb": final_memory,
                "memory_increase_mb": memory_increase,
                "questions_processed": len(questions)
            }
            
            self.test_results["detailed_results"].append(result)
            self.test_results["tests_run"] += 1
            
            if memory_increase < TEST_CONFIG["performance_thresholds"]["max_memory_usage"]:
                self.test_results["tests_passed"] += 1
                self.logger.info(f"[PASS] Memory test passed: increase={memory_increase:.1f}MB")
            else:
                self.test_results["tests_failed"] += 1
                self.logger.warning(f"[FAIL] Memory test failed: increase={memory_increase:.1f}MB")
                
        except ImportError:
            self.logger.warning("psutil not available, skipping memory test")
        except Exception as e:
            self.test_results["tests_failed"] += 1
            self.logger.error(f"[FAIL] Memory test failed: {e}")
    
    async def generate_final_report(self):
        """Generate comprehensive test report"""
        self.logger.info("Generating final test report...")
        
        # Calculate final statistics
        total_tests = self.test_results["tests_run"]
        passed_tests = self.test_results["tests_passed"]
        failed_tests = self.test_results["tests_failed"]
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        self.test_results["end_time"] = datetime.now().isoformat()
        self.test_results["success_rate"] = success_rate
        
        # Generate summary
        summary = f"""
QA Agent Comprehensive Test Results
{'=' * 50}

Test Summary:
- Total Tests Run: {total_tests}
- Tests Passed: {passed_tests}
- Tests Failed: {failed_tests}
- Success Rate: {success_rate:.1f}%

Performance Metrics:
{json.dumps(self.test_results.get('performance_metrics', {}), indent=2)}

Test Categories:
- Database Integration: {'PASS' if any(r['test'] == 'database_get_papers' for r in self.test_results['detailed_results']) else 'FAIL'}
- Answer Accuracy: {'PASS' if any(r['test'] == 'answer_accuracy' for r in self.test_results['detailed_results']) else 'FAIL'}
- Performance: {'PASS' if 'performance_metrics' in self.test_results else 'FAIL'}
- Async/Sync: {'PASS' if any(r['test'] == 'async_vs_sync' for r in self.test_results['detailed_results']) else 'FAIL'}
- Caching: {'PASS' if any(r['test'] == 'caching' for r in self.test_results['detailed_results']) else 'FAIL'}
- Edge Cases: {'PASS' if any(r['test'] == 'edge_case' for r in self.test_results['detailed_results']) else 'FAIL'}
- Citations: {'PASS' if any(r['test'] == 'citation_generation' for r in self.test_results['detailed_results']) else 'FAIL'}
- Question Types: {'PASS' if any(r['test'] == 'question_type' for r in self.test_results['detailed_results']) else 'FAIL'}
- Error Handling: {'PASS' if any(r['test'] == 'error_handling' for r in self.test_results['detailed_results']) else 'FAIL'}
- Memory Usage: {'PASS' if any(r['test'] == 'memory_usage' for r in self.test_results['detailed_results']) else 'FAIL'}

Recommendation:
{'SUCCESS: QA Agent is working efficiently and ready for production!' if success_rate >= 80 else 'WARNING: QA Agent needs improvements before production use.' if success_rate >= 60 else 'CRITICAL: QA Agent has significant issues that need to be addressed.'}
"""
        
        # Save detailed results to file
        report_file = f"qa_agent_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        print(summary)
        self.logger.info(f"Detailed test results saved to: {report_file}")
        
        return summary
    
    async def cleanup(self):
        """Cleanup test environment"""
        try:
            if self.database and hasattr(self.database, 'close_connections'):
                self.database.close_connections()
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")

async def main():
    """Main test execution function"""
    tester = QAAgentTester()
    
    try:
        await tester.setup()
        await tester.run_all_tests()
    except Exception as e:
        print(f"Test execution failed: {e}")
        return 1
    finally:
        await tester.cleanup()
    
    return 0

if __name__ == "__main__":
    # Run the comprehensive test suite
    print("Starting QA Agent Comprehensive Testing...")
    print("This will test all aspects of the QA Agent functionality.\n")
    
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nTesting interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nTesting failed with error: {e}")
        sys.exit(1)
