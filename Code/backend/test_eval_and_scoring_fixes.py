"""
Verification test for:
1. Intelligent rubric matching in offline/fallback answer evaluation (testing Docker CI/CD question).
2. Elimination of 'quota exceeded' dummy message from missed_points.
3. Accurate coding challenge resolution and 100/100 score calculation.
4. Text mode communication scoring (preventing acoustic penalty drag / 53 score).
5. Technical score normalization in recruiter report.
"""

import unittest
from datetime import datetime, timedelta
from app.interview.domain.interview_models import (
    AnswerEvaluation,
    EmotionLabel,
    FrameAnalysisResult,
    ObservableCVMetrics,
    ObservableVocalMetrics,
    QuestionRubric,
    QuestionType,
)
from app.interview.services.llm_service import _fallback_answer_evaluation
from app.interview.services.code_execution import calculate_coding_score, evaluate_coding_challenge
from app.interview.domain.coding_challenges import CodingTestCase
from app.interview.services.recruiter_report import (
    calculate_five_dimension_scores,
    RecruiterReportGenerator,
)


class TestEvaluationAndScoringFixes(unittest.TestCase):
    def test_docker_cicd_rubric_matching(self):
        """Test candidate's Docker CI/CD answer against rubric in fallback/offline mode."""
        question_text = (
            "How do you containerize a full MERN application with Docker (multi-stage builds for React and Node), "
            "manage environment variables securely, and structure automated CI/CD testing pipelines?"
        )
        candidate_answer = (
            "I would containerize the React frontend and Node.js backend separately using multi-stage Docker builds, "
            "keeping the final images small and production-focused. Environment variables and secrets such as database URLs "
            "and JWT keys would be injected through the deployment environment or CI/CD secret manager, never committed to Git. "
            "The CI/CD pipeline would run linting, unit and integration tests, build the Docker images, scan them for "
            "vulnerabilities, push them to a registry, and deploy to the target environment only if all checks pass."
        )
        rubric = QuestionRubric(
            reference_answer=(
                "Use multi-stage Dockerfiles with separate builder and production runner stages. "
                "Store secrets in environment variables or cloud secret managers without checking into version control. "
                "Set up CI/CD with linting, unit tests, integration tests, image scanning, and automated deployment."
            ),
            key_concepts_expected=[
                "Multi-stage Docker builds for separate React and Node containers",
                "Secure environment variable & secret management without Git commits",
                "Automated CI/CD pipeline with linting, unit/integration testing, vulnerability scanning, and deployment",
            ],
        )

        evaluation = _fallback_answer_evaluation(
            question_text=question_text,
            question_type=QuestionType.TECHNICAL,
            candidate_transcript=candidate_answer,
            rubric=rubric,
            job_role="MERN Stack Developer",
            input_mode="text",
        )

        print("\n--- Docker CI/CD Evaluation Result ---")
        print(f"Accuracy Score: {evaluation.accuracy_score}/100")
        print(f"Relevance Score: {evaluation.relevance_score}/10")
        print(f"Depth Score: {evaluation.depth_score}/10")
        print(f"Communication Score: {evaluation.communication_score}/10")
        print(f"Key Points Covered ({len(evaluation.key_points_covered)}): {evaluation.key_points_covered}")
        print(f"Missed Points ({len(evaluation.missed_points)}): {evaluation.missed_points}")
        print(f"Evaluator Notes: {evaluation.evaluator_notes}")

        # Invariant checks
        self.assertTrue(evaluation.is_correct, "Answer should be evaluated as correct")
        self.assertGreaterEqual(evaluation.accuracy_score, 85.0, "Accuracy should be >= 85 for this comprehensive answer")
        self.assertGreaterEqual(evaluation.communication_score, 8.5, "Communication score should be >= 8.5 for well-written text")
        self.assertGreater(len(evaluation.key_points_covered), 0, "Key concepts should be covered")
        self.assertNotIn("Full rubric unavailable while LLM quota is exceeded.", evaluation.missed_points)
        for mp in evaluation.missed_points:
            self.assertNotIn("LLM quota", mp)

    def test_text_mode_communication_scoring(self):
        """Test that candidate using text mode receives accurate communication score without 53/100 audio drag."""
        evaluations = [
            AnswerEvaluation(
                question_index=0,
                question_text="Describe your background and expertise.",
                question_type=QuestionType.ICEBREAKER,
                candidate_transcript="I am a full stack engineer with 4 years of experience building scalable MERN web applications.",
                relevance_score=9.0,
                depth_score=8.5,
                communication_score=9.2,
                accuracy_score=90.0,
                is_correct=True,
            ),
            AnswerEvaluation(
                question_index=1,
                question_text="How do you optimize React rendering performance?",
                question_type=QuestionType.TECHNICAL,
                candidate_transcript="I utilize React.memo, useMemo, useCallback, code splitting via React.lazy, and virtualization for long lists to prevent unnecessary re-renders.",
                relevance_score=9.5,
                depth_score=9.0,
                communication_score=9.0,
                accuracy_score=95.0,
                is_correct=True,
            ),
        ]
        # Text mode produces empty vocal metrics (0 WPM, 0 clarity)
        empty_vocal_metrics = [
            ObservableVocalMetrics(
                speaking_rate_wpm=0.0,
                pause_duration_ratio=0.0,
                speech_clarity_score=0.0,
                acoustic_flags=["No audio stream provided"],
            ),
            ObservableVocalMetrics(
                speaking_rate_wpm=0.0,
                pause_duration_ratio=0.0,
                speech_clarity_score=0.0,
                acoustic_flags=["No audio stream provided"],
            ),
        ]

        scores = calculate_five_dimension_scores(
            evaluations=evaluations,
            coding_results=[{"overall_coding_score": 95.0, "all_passed": True}],
            role_fit_data={"overall_fit_score": 88.0, "role": "mern_stack_developer"},
            vocal_metrics=empty_vocal_metrics,
            cv_metrics=[],
        )

        print("\n--- 5-Dimension Scores (Text Mode) ---")
        print(f"Technical Score: {scores.technical_knowledge_score}")
        print(f"Coding Score: {scores.coding_ability_score}")
        print(f"Role Fit Score: {scores.role_fit_score}")
        print(f"Communication Score: {scores.communication_score}")
        print(f"Overall Composite: {scores.overall_composite_score}")
        print(f"Fit Status: {scores.fit_status.value}")

        # Communication score must be >= 85.0 (from written communication) and NOT degraded to 53!
        self.assertGreaterEqual(scores.communication_score, 85.0, "Text mode communication score should reflect written quality (>= 85)")
        self.assertNotAlmostEqual(scores.communication_score, 53.0, delta=5.0)

    def test_coding_challenge_evaluation_with_custom_test_cases(self):
        """Test evaluate_coding_challenge with custom test cases from dynamically generated questions."""
        custom_test_cases = [
            CodingTestCase(
                test_id=1,
                is_hidden=False,
                stdin="3\n1 2 3\n",
                expected_stdout="6",
                description="Sample 1",
            ),
            CodingTestCase(
                test_id=2,
                is_hidden=False,
                stdin="4\n10 20 30 40\n",
                expected_stdout="100",
                description="Sample 2",
            ),
        ]
        source_code = (
            "import sys\n"
            "def main():\n"
            "    lines = sys.stdin.read().split()\n"
            "    if not lines: return\n"
            "    n = int(lines[0])\n"
            "    nums = [int(x) for x in lines[1:n+1]]\n"
            "    print(sum(nums))\n"
            "if __name__ == '__main__':\n"
            "    main()\n"
        )

        eval_res = evaluate_coding_challenge(
            challenge_id="CHAL-CUSTOM-TEST",
            language="python",
            source_code=source_code,
            custom_test_cases=custom_test_cases,
        )

        print("\n--- Coding Challenge Evaluation ---")
        print(f"Compile Success: {eval_res.compile_success}")
        print(f"Public Tests Passed: {eval_res.public_tests_passed}/{eval_res.public_tests_total}")
        print(f"Overall Coding Score: {eval_res.overall_coding_score}/100")

        self.assertTrue(eval_res.compile_success)
        self.assertEqual(eval_res.public_tests_passed, 2)
        self.assertGreaterEqual(eval_res.overall_coding_score, 90.0, "Coding score should be >= 90 when all tests pass")

    def test_recruiter_report_technical_narrative_and_red_flags(self):
        """Test recruiter report generator to ensure no false red flags and correct technical score."""
        generator = RecruiterReportGenerator()

        evals = [
            AnswerEvaluation(
                question_index=0,
                question_text="Explain MongoDB indexing strategies.",
                question_type=QuestionType.TECHNICAL,
                candidate_transcript="I use compound indexes, covered queries with projected fields, and explain() plans to avoid full collection scans.",
                relevance_score=9.5,
                depth_score=9.0,
                communication_score=9.0,
                accuracy_score=95.0,
                is_correct=True,
            )
        ]
        now = datetime.utcnow()
        report = generator.generate_report(
            candidate_name="Test Candidate",
            job_role="MERN Stack Developer",
            session_start=now - timedelta(minutes=20),
            session_end=now,
            evaluations=evals,
            behavioral_metrics=[],
            vocal_metrics=[],
            coding_results=[{"overall_coding_score": 100.0, "all_passed": True}],
            role_fit_data={"overall_fit_score": 90.0},
        )

        print("\n--- Recruiter Report Summary ---")
        print(f"Technical Score: {report.technical_score}")
        print(f"Coding Score: {report.coding_score}")
        print(f"Communication Score: {report.communication_score}")
        print(f"Overall Score: {report.overall_score}")
        print(f"Recommendation: {report.hiring_recommendation}")
        print(f"Red Flags: {report.red_flags}")
        print(f"Strengths: {report.strengths}")

        self.assertGreaterEqual(report.technical_score, 85.0)
        self.assertEqual(report.coding_score, 100.0)
        self.assertNotIn("No audio stream provided", report.red_flags)
        self.assertIn("Relevant and focused answers", report.technical_analysis)
        self.assertNotIn("Answers often lacked relevance", report.technical_analysis)


if __name__ == "__main__":
    unittest.main()
