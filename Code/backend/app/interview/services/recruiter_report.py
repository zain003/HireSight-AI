"""
Comprehensive Recruiter Report Generator.
Consolidates all evaluation metrics into actionable hiring decision report.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from app.interview.domain.interview_models import AnswerEvaluation, InterviewReport
from app.interview.services.behavioral_analysis import BehavioralMetrics
from app.interview.services.vocal_analysis import VocalMetrics


@dataclass
class RecruiterReport:
    """Comprehensive recruiter report with hiring recommendation."""
    # Candidate Info
    candidate_name: str
    job_role: str
    interview_date: str
    session_duration_minutes: float
    
    # Overall Scores (0-100)
    overall_score: float
    hiring_recommendation: str  # "Strong Hire", "Hire", "Maybe", "No Hire"
    confidence_level: str  # "High", "Medium", "Low"
    
    # Category Scores
    technical_score: float
    communication_score: float
    behavioral_score: float
    coding_score: float
    
    # Detailed Metrics
    vocal_confidence: float
    eye_contact_score: float
    attention_span: float
    speech_clarity: float
    fidgeting_score: float
    
    # Red Flags & Strengths
    red_flags: List[str]
    strengths: List[str]
    areas_for_improvement: List[str]
    
    # Question Performance
    questions_answered: int
    questions_skipped: int
    follow_ups_triggered: int
    coding_challenges_passed: int
    coding_challenges_total: int
    
    # Detailed Analysis
    technical_analysis: str
    behavioral_analysis: str
    communication_analysis: str
    coding_analysis: str
    
    # Decision Summary
    executive_summary: str
    detailed_recommendation: str
    next_steps: str


class RecruiterReportGenerator:
    """
    Generates comprehensive recruiter reports from interview data.
    Consolidates technical, behavioral, vocal, and coding metrics.
    """
    
    def generate_report(
        self,
        candidate_name: str,
        job_role: str,
        session_start: datetime,
        session_end: datetime,
        evaluations: List[AnswerEvaluation],
        behavioral_metrics: List[BehavioralMetrics],
        vocal_metrics: List[VocalMetrics],
        coding_results: List[Dict],
        aggregate_scores: Dict
    ) -> RecruiterReport:
        """
        Generate comprehensive recruiter report.
        
        Args:
            candidate_name: Candidate's name
            job_role: Target job role
            session_start: Interview start time
            session_end: Interview end time
            evaluations: List of answer evaluations
            behavioral_metrics: List of behavioral analysis results
            vocal_metrics: List of vocal analysis results
            coding_results: List of coding challenge results
            aggregate_scores: Pre-calculated aggregate scores
            
        Returns:
            RecruiterReport with comprehensive analysis
        """
        # Calculate duration
        duration = (session_end - session_start).total_seconds() / 60
        
        # Aggregate behavioral metrics
        avg_behavioral = self._aggregate_behavioral_metrics(behavioral_metrics)
        
        # Aggregate vocal metrics
        avg_vocal = self._aggregate_vocal_metrics(vocal_metrics)
        
        # Analyze technical performance
        technical_analysis = self._analyze_technical_performance(evaluations)
        
        # Analyze coding performance
        coding_analysis = self._analyze_coding_performance(coding_results)
        
        # Calculate category scores
        technical_score = technical_analysis["score"]
        communication_score = self._calculate_communication_score(
            evaluations, avg_vocal
        )
        behavioral_score = self._calculate_behavioral_score(avg_behavioral)
        coding_score = coding_analysis["score"]
        
        # Calculate overall score (weighted average)
        overall_score = (
            technical_score * 0.35 +
            communication_score * 0.25 +
            behavioral_score * 0.20 +
            coding_score * 0.20
        )
        
        # Hiring recommendation
        recommendation, confidence = self._determine_hiring_recommendation(
            overall_score,
            technical_score,
            behavioral_score,
            coding_score,
            len(self._collect_all_red_flags(
                evaluations, behavioral_metrics, vocal_metrics
            ))
        )
        
        # Collect red flags and strengths
        all_red_flags = self._collect_all_red_flags(
            evaluations, behavioral_metrics, vocal_metrics
        )
        strengths = self._identify_strengths(
            technical_score,
            communication_score,
            behavioral_score,
            coding_score,
            avg_behavioral,
            avg_vocal
        )
        improvements = self._identify_improvements(
            technical_score,
            communication_score,
            behavioral_score,
            coding_score,
            all_red_flags
        )
        
        # Question statistics
        questions_answered = len(evaluations)
        questions_skipped = sum(
            1 for e in evaluations 
            if "skip" in e.candidate_transcript.lower()
        )
        follow_ups = sum(1 for e in evaluations if e.follow_up_triggered)
        
        # Generate narrative analyses
        tech_narrative = self._generate_technical_narrative(
            technical_analysis, evaluations
        )
        behavioral_narrative = self._generate_behavioral_narrative(
            avg_behavioral, behavioral_metrics
        )
        communication_narrative = self._generate_communication_narrative(
            avg_vocal, communication_score
        )
        coding_narrative = self._generate_coding_narrative(coding_analysis)
        
        # Executive summary
        executive_summary = self._generate_executive_summary(
            candidate_name,
            job_role,
            overall_score,
            recommendation,
            strengths[:3],
            all_red_flags[:3]
        )
        
        # Detailed recommendation
        detailed_rec = self._generate_detailed_recommendation(
            recommendation,
            overall_score,
            technical_score,
            behavioral_score,
            coding_score,
            all_red_flags
        )
        
        # Next steps
        next_steps = self._generate_next_steps(recommendation, improvements)
        
        return RecruiterReport(
            candidate_name=candidate_name,
            job_role=job_role,
            interview_date=session_start.strftime("%Y-%m-%d %H:%M"),
            session_duration_minutes=round(duration, 1),
            overall_score=round(overall_score, 1),
            hiring_recommendation=recommendation,
            confidence_level=confidence,
            technical_score=round(technical_score, 1),
            communication_score=round(communication_score, 1),
            behavioral_score=round(behavioral_score, 1),
            coding_score=round(coding_score, 1),
            vocal_confidence=round(avg_vocal.get("vocal_confidence", 0), 1),
            eye_contact_score=round(avg_behavioral.get("eye_contact", 0), 1),
            attention_span=round(avg_behavioral.get("attention_span", 0), 1),
            speech_clarity=round(avg_vocal.get("clarity", 0), 1),
            fidgeting_score=round(avg_behavioral.get("fidgeting", 0), 1),
            red_flags=all_red_flags,
            strengths=strengths,
            areas_for_improvement=improvements,
            questions_answered=questions_answered,
            questions_skipped=questions_skipped,
            follow_ups_triggered=follow_ups,
            coding_challenges_passed=coding_analysis["passed"],
            coding_challenges_total=coding_analysis["total"],
            technical_analysis=tech_narrative,
            behavioral_analysis=behavioral_narrative,
            communication_analysis=communication_narrative,
            coding_analysis=coding_narrative,
            executive_summary=executive_summary,
            detailed_recommendation=detailed_rec,
            next_steps=next_steps
        )
    
    def _aggregate_behavioral_metrics(
        self, 
        behavioral_metrics: List[BehavioralMetrics]
    ) -> Dict:
        """Aggregate behavioral metrics across all questions."""
        if not behavioral_metrics:
            return {
                "eye_contact": 0,
                "head_stability": 0,
                "engagement": 0,
                "fidgeting": 0,
                "confidence_posture": 0,
                "attention_span": 0
            }
        
        return {
            "eye_contact": sum(m.eye_contact_score for m in behavioral_metrics) / len(behavioral_metrics),
            "head_stability": sum(m.head_stability_score for m in behavioral_metrics) / len(behavioral_metrics),
            "engagement": sum(m.facial_engagement_score for m in behavioral_metrics) / len(behavioral_metrics),
            "fidgeting": sum(m.fidgeting_score for m in behavioral_metrics) / len(behavioral_metrics),
            "confidence_posture": sum(m.confidence_posture_score for m in behavioral_metrics) / len(behavioral_metrics),
            "attention_span": sum(m.attention_span_score for m in behavioral_metrics) / len(behavioral_metrics)
        }
    
    def _aggregate_vocal_metrics(self, vocal_metrics: List[VocalMetrics]) -> Dict:
        """Aggregate vocal metrics across all questions."""
        if not vocal_metrics:
            return {
                "vocal_confidence": 0,
                "clarity": 0,
                "pitch_variance": 0,
                "speech_rate": 0,
                "pause_pattern": 0,
                "tone_consistency": 0,
                "communication_effectiveness": 0
            }
        
        return {
            "vocal_confidence": sum(m.vocal_confidence_score for m in vocal_metrics) / len(vocal_metrics),
            "clarity": sum(m.speech_clarity_score for m in vocal_metrics) / len(vocal_metrics),
            "pitch_variance": sum(m.pitch_variance_score for m in vocal_metrics) / len(vocal_metrics),
            "speech_rate": sum(m.speech_rate_score for m in vocal_metrics) / len(vocal_metrics),
            "pause_pattern": sum(m.pause_pattern_score for m in vocal_metrics) / len(vocal_metrics),
            "tone_consistency": sum(m.tone_consistency_score for m in vocal_metrics) / len(vocal_metrics),
            "communication_effectiveness": sum(m.communication_effectiveness for m in vocal_metrics) / len(vocal_metrics)
        }
    
    def _analyze_technical_performance(
        self, 
        evaluations: List[AnswerEvaluation]
    ) -> Dict:
        """Analyze technical question performance."""
        if not evaluations:
            return {"score": 0, "strong_areas": [], "weak_areas": []}
        
        # Filter technical questions
        tech_evals = [
            e for e in evaluations 
            if e.question_type.value in ["technical", "cv_based"]
        ]
        
        if not tech_evals:
            return {"score": 0, "strong_areas": [], "weak_areas": []}
        
        # Calculate average scores
        avg_relevance = sum(e.relevance_score for e in tech_evals) / len(tech_evals)
        avg_depth = sum(e.depth_score for e in tech_evals) / len(tech_evals)
        avg_accuracy = sum(e.accuracy_score for e in tech_evals) / len(tech_evals)
        
        # Overall technical score
        technical_score = (avg_relevance + avg_depth + avg_accuracy) / 3
        
        # Identify strong/weak areas
        strong_areas = []
        weak_areas = []
        
        if avg_relevance >= 70:
            strong_areas.append("Relevant and focused answers")
        elif avg_relevance < 50:
            weak_areas.append("Answers often lacked relevance")
        
        if avg_depth >= 70:
            strong_areas.append("Deep technical knowledge")
        elif avg_depth < 50:
            weak_areas.append("Superficial technical understanding")
        
        if avg_accuracy >= 70:
            strong_areas.append("Accurate technical details")
        elif avg_accuracy < 50:
            weak_areas.append("Factual inaccuracies in responses")
        
        return {
            "score": technical_score,
            "strong_areas": strong_areas,
            "weak_areas": weak_areas,
            "avg_relevance": avg_relevance,
            "avg_depth": avg_depth,
            "avg_accuracy": avg_accuracy
        }
    
    def _analyze_coding_performance(self, coding_results: List[Dict]) -> Dict:
        """Analyze coding challenge performance."""
        if not coding_results:
            return {"score": 0, "passed": 0, "total": 0}
        
        total = len(coding_results)
        passed = sum(1 for r in coding_results if r.get("all_passed", False))
        
        # Score based on pass rate
        pass_rate = passed / total if total > 0 else 0
        score = pass_rate * 100
        
        return {
            "score": score,
            "passed": passed,
            "total": total,
            "pass_rate": pass_rate
        }
    
    def _calculate_communication_score(
        self,
        evaluations: List[AnswerEvaluation],
        avg_vocal: Dict
    ) -> float:
        """Calculate overall communication score."""
        if not evaluations:
            return 0
        
        # Communication from evaluations
        avg_comm = sum(e.communication_score for e in evaluations) / len(evaluations)
        
        # Vocal effectiveness
        vocal_effectiveness = avg_vocal.get("communication_effectiveness", 0)
        
        # Weighted average
        communication_score = (avg_comm * 10) * 0.6 + vocal_effectiveness * 0.4
        
        return communication_score
    
    def _calculate_behavioral_score(self, avg_behavioral: Dict) -> float:
        """Calculate overall behavioral score."""
        # Weighted combination of behavioral metrics
        score = (
            avg_behavioral.get("eye_contact", 0) * 0.25 +
            avg_behavioral.get("attention_span", 0) * 0.25 +
            avg_behavioral.get("confidence_posture", 0) * 0.20 +
            avg_behavioral.get("engagement", 0) * 0.15 +
            avg_behavioral.get("fidgeting", 0) * 0.10 +
            avg_behavioral.get("head_stability", 0) * 0.05
        )
        return score
    
    def _determine_hiring_recommendation(
        self,
        overall_score: float,
        technical_score: float,
        behavioral_score: float,
        coding_score: float,
        red_flag_count: int
    ) -> tuple:
        """Determine hiring recommendation and confidence level."""
        # Strong Hire: >85 overall, >80 technical, <3 red flags
        if (overall_score >= 85 and technical_score >= 80 and 
            coding_score >= 75 and red_flag_count < 3):
            return "Strong Hire", "High"
        
        # Hire: >75 overall, >70 technical, <5 red flags
        if (overall_score >= 75 and technical_score >= 70 and 
            coding_score >= 60 and red_flag_count < 5):
            return "Hire", "High" if overall_score >= 80 else "Medium"
        
        # Maybe: 60-75 overall or significant concerns
        if (60 <= overall_score < 75 or red_flag_count >= 5):
            return "Maybe", "Medium" if overall_score >= 65 else "Low"
        
        # No Hire: <60 overall or critical failures
        return "No Hire", "High" if overall_score < 50 else "Medium"
    
    def _collect_all_red_flags(
        self,
        evaluations: List[AnswerEvaluation],
        behavioral_metrics: List[BehavioralMetrics],
        vocal_metrics: List[VocalMetrics]
    ) -> List[str]:
        """Collect all red flags from all sources."""
        red_flags = []
        
        # From behavioral analysis
        for bm in behavioral_metrics:
            red_flags.extend(bm.red_flags)
        
        # From vocal analysis
        for vm in vocal_metrics:
            red_flags.extend(vm.red_flags)
        
        # From answer evaluations
        for e in evaluations:
            if e.coaching_detected:
                red_flags.append("Coaching detected - external assistance suspected")
            if not e.is_correct and e.accuracy_score < 30:
                red_flags.append(f"Very poor answer to: {e.question_text[:60]}...")
        
        # Deduplicate
        return list(dict.fromkeys(red_flags))
    
    def _identify_strengths(
        self,
        technical_score: float,
        communication_score: float,
        behavioral_score: float,
        coding_score: float,
        avg_behavioral: Dict,
        avg_vocal: Dict
    ) -> List[str]:
        """Identify candidate strengths."""
        strengths = []
        
        if technical_score >= 80:
            strengths.append("Strong technical knowledge and problem-solving skills")
        
        if coding_score >= 80:
            strengths.append("Excellent coding ability with clean, efficient solutions")
        
        if communication_score >= 80:
            strengths.append("Clear and effective communication skills")
        
        if behavioral_score >= 80:
            strengths.append("Professional demeanor and strong interview presence")
        
        if avg_behavioral.get("eye_contact", 0) >= 80:
            strengths.append("Maintained excellent eye contact throughout")
        
        if avg_vocal.get("vocal_confidence", 0) >= 80:
            strengths.append("Spoke with confidence and conviction")
        
        if avg_behavioral.get("attention_span", 0) >= 85:
            strengths.append("Highly focused and attentive")
        
        return strengths if strengths else ["Candidate completed the interview"]
    
    def _identify_improvements(
        self,
        technical_score: float,
        communication_score: float,
        behavioral_score: float,
        coding_score: float,
        red_flags: List[str]
    ) -> List[str]:
        """Identify areas for improvement."""
        improvements = []
        
        if technical_score < 60:
            improvements.append("Strengthen technical fundamentals and domain knowledge")
        
        if coding_score < 60:
            improvements.append("Practice coding problems and algorithmic thinking")
        
        if communication_score < 60:
            improvements.append("Improve verbal communication and articulation")
        
        if behavioral_score < 60:
            improvements.append("Work on interview presence and confidence")
        
        if "eye contact" in " ".join(red_flags).lower():
            improvements.append("Maintain better eye contact with interviewer")
        
        if "nervous" in " ".join(red_flags).lower() or "fidget" in " ".join(red_flags).lower():
            improvements.append("Practice interview scenarios to reduce nervousness")
        
        return improvements if improvements else ["Continue professional development"]
    
    def _generate_technical_narrative(
        self, 
        technical_analysis: Dict,
        evaluations: List[AnswerEvaluation]
    ) -> str:
        """Generate technical performance narrative."""
        score = technical_analysis["score"]
        strong = technical_analysis["strong_areas"]
        weak = technical_analysis["weak_areas"]
        
        narrative = f"The candidate demonstrated a technical proficiency score of {score:.1f}/100. "
        
        if score >= 75:
            narrative += "Overall technical performance was strong. "
        elif score >= 60:
            narrative += "Technical performance was adequate but showed room for improvement. "
        else:
            narrative += "Technical performance indicated significant knowledge gaps. "
        
        if strong:
            narrative += "Strengths included: " + ", ".join(strong) + ". "
        
        if weak:
            narrative += "Areas needing improvement: " + ", ".join(weak) + "."
        
        return narrative
    
    def _generate_behavioral_narrative(
        self,
        avg_behavioral: Dict,
        behavioral_metrics: List[BehavioralMetrics]
    ) -> str:
        """Generate behavioral analysis narrative."""
        eye_contact = avg_behavioral.get("eye_contact", 0)
        attention = avg_behavioral.get("attention_span", 0)
        confidence = avg_behavioral.get("confidence_posture", 0)
        
        narrative = f"Behavioral analysis showed "
        
        if eye_contact >= 70:
            narrative += "good eye contact, "
        else:
            narrative += "limited eye contact, "
        
        if attention >= 75:
            narrative += "strong attention and focus, "
        else:
            narrative += "some attention challenges, "
        
        if confidence >= 70:
            narrative += "and confident body language."
        else:
            narrative += "and signs of nervousness or uncertainty."
        
        return narrative
    
    def _generate_communication_narrative(
        self,
        avg_vocal: Dict,
        communication_score: float
    ) -> str:
        """Generate communication analysis narrative."""
        vocal_conf = avg_vocal.get("vocal_confidence", 0)
        clarity = avg_vocal.get("clarity", 0)
        
        narrative = f"Communication effectiveness scored {communication_score:.1f}/100. "
        
        if vocal_conf >= 70:
            narrative += "The candidate spoke with confidence and conviction. "
        else:
            narrative += "Vocal delivery showed signs of hesitation or uncertainty. "
        
        if clarity >= 70:
            narrative += "Speech was clear and easy to understand."
        else:
            narrative += "Speech clarity could be improved."
        
        return narrative
    
    def _generate_coding_narrative(self, coding_analysis: Dict) -> str:
        """Generate coding performance narrative."""
        passed = coding_analysis["passed"]
        total = coding_analysis["total"]
        
        if total == 0:
            return "No coding challenges were completed."
        
        narrative = f"Completed {passed} out of {total} coding challenges successfully. "
        
        if passed == total:
            narrative += "Excellent coding performance with all test cases passed."
        elif passed >= total * 0.67:
            narrative += "Good coding ability demonstrated."
        elif passed >= total * 0.33:
            narrative += "Partial coding success; needs more practice."
        else:
            narrative += "Coding challenges were largely unsuccessful."
        
        return narrative
    
    def _generate_executive_summary(
        self,
        candidate_name: str,
        job_role: str,
        overall_score: float,
        recommendation: str,
        strengths: List[str],
        red_flags: List[str]
    ) -> str:
        """Generate executive summary for quick decision-making."""
        summary = f"{candidate_name} interviewed for {job_role} position. "
        summary += f"Overall score: {overall_score:.1f}/100. "
        summary += f"Recommendation: **{recommendation}**.\n\n"
        
        if strengths:
            summary += "**Key Strengths:** " + strengths[0]
            if len(strengths) > 1:
                summary += "; " + strengths[1]
            summary += ".\n\n"
        
        if red_flags:
            summary += "**Concerns:** " + red_flags[0]
            if len(red_flags) > 1:
                summary += "; " + red_flags[1]
            summary += "."
        
        return summary
    
    def _generate_detailed_recommendation(
        self,
        recommendation: str,
        overall_score: float,
        technical_score: float,
        behavioral_score: float,
        coding_score: float,
        red_flags: List[str]
    ) -> str:
        """Generate detailed hiring recommendation."""
        rec = f"**{recommendation}** - Overall Score: {overall_score:.1f}/100\n\n"
        
        rec += f"- Technical: {technical_score:.1f}/100\n"
        rec += f"- Behavioral: {behavioral_score:.1f}/100\n"
        rec += f"- Coding: {coding_score:.1f}/100\n\n"
        
        if recommendation == "Strong Hire":
            rec += "This candidate exceeded expectations across all dimensions. "
            rec += "Strong technical skills, professional demeanor, and excellent coding ability. "
            rec += "Recommend moving to offer stage immediately."
        
        elif recommendation == "Hire":
            rec += "This candidate meets the requirements for the position. "
            rec += "Solid technical foundation and appropriate skill level. "
            rec += "Recommend proceeding with hiring process."
        
        elif recommendation == "Maybe":
            rec += "This candidate shows potential but has some concerns. "
            if red_flags:
                rec += f"Key concerns include: {', '.join(red_flags[:2])}. "
            rec += "Recommend additional interview or assessment before final decision."
        
        else:  # No Hire
            rec += "This candidate does not meet the requirements for the position. "
            rec += "Significant gaps in technical knowledge, communication, or professionalism. "
            rec += "Recommend not proceeding with this candidate."
        
        return rec
    
    def _generate_next_steps(
        self, 
        recommendation: str,
        improvements: List[str]
    ) -> str:
        """Generate next steps based on recommendation."""
        if recommendation == "Strong Hire":
            return "• Extend offer immediately\n• Schedule onboarding\n• Prepare welcome package"
        
        elif recommendation == "Hire":
            return "• Proceed with reference checks\n• Prepare offer letter\n• Schedule team meet-and-greet"
        
        elif recommendation == "Maybe":
            steps = "• Schedule follow-up technical interview\n"
            steps += "• Consider take-home assignment\n"
            if improvements:
                steps += f"• Assess: {improvements[0]}"
            return steps
        
        else:  # No Hire
            return "• Send rejection email\n• Provide constructive feedback if requested\n• Keep profile for future openings"
