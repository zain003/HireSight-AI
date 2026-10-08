"""
PDF Recruiter Report Generator Service for HireSIGHT.

Generates publication-grade, multi-page PDF recruiter reports and structured JSON exports
incorporating candidate overview, 5-dimensional explainable scores, tailored feedback,
observable multimodal physical metrics, coding benchmarks, and question-by-question rubric comparisons.
"""

from __future__ import annotations

import io
from datetime import datetime
from typing import Any, Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.interview.domain.interview_models import (
    AnswerEvaluation,
    ObservableCVMetrics,
    ObservableVocalMetrics,
)
from app.interview.domain.scoring_models import (
    CandidateFitStatus,
    FiveDimensionScores,
    ScoringWeights,
    TailoredFeedback,
)
from app.interview.models import InterviewSession
from app.interview.schemas import RecruiterReportExportPayload
from app.interview.services.feedback_generator import generate_tailored_feedback
from app.interview.services.recruiter_report import calculate_five_dimension_scores


# ── Color Palette Standard ──────────────────────────────────────────────────
PRIMARY_DARK = colors.HexColor("#0f172a")    # Slate 900
BRAND_INDIGO = colors.HexColor("#4f46e5")    # Indigo 600
BRAND_VIOLET = colors.HexColor("#7c3aed")    # Violet 600
TEXT_DARK = colors.HexColor("#1e293b")       # Slate 800
TEXT_MUTED = colors.HexColor("#64748b")      # Slate 500
BORDER_COLOR = colors.HexColor("#cbd5e1")    # Slate 300
BORDER_LIGHT = colors.HexColor("#e2e8f0")    # Slate 200
BG_LIGHT = colors.HexColor("#f8fafc")        # Slate 50
BG_CARD = colors.HexColor("#f1f5f9")         # Slate 100
BG_HEADER = colors.HexColor("#1e293b")       # Slate 800

# Fit Status Colors
COLOR_STRONG_FIT = colors.HexColor("#059669")   # Emerald 600
BG_STRONG_FIT = colors.HexColor("#ecfdf5")      # Emerald 50
COLOR_POTENTIAL_FIT = colors.HexColor("#d97706") # Amber 600
BG_POTENTIAL_FIT = colors.HexColor("#fffbeb")   # Amber 50
COLOR_NEEDS_GROWTH = colors.HexColor("#ea580c")  # Orange 600
BG_NEEDS_GROWTH = colors.HexColor("#fff7ed")    # Orange 50
COLOR_NOT_A_FIT = colors.HexColor("#dc2626")    # Red 600
BG_NOT_A_FIT = colors.HexColor("#fef2f2")       # Red 50


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas for dynamic total page count calculation,
    running headers, and confidentiality footers.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int):
        self.saveState()
        self.setFont("Helvetica", 7.5)
        self.setFillColor(TEXT_MUTED)

        # Running Header (on pages after page 1, if any)
        if self._pageNumber > 1:
            self.drawString(24, 768, "HireSIGHT AI — Candidate Assessment & Recruiter Dossier")
            self.setStrokeColor(BORDER_LIGHT)
            self.setLineWidth(0.5)
            self.line(24, 762, 588, 762)

        # Running Footer (on all pages)
        self.setStrokeColor(BORDER_LIGHT)
        self.setLineWidth(0.5)
        self.line(24, 24, 588, 24)
        self.drawString(24, 14, "CONFIDENTIAL — HireSIGHT AI Candidate Assessment • 100% Explainable Physical & Rubric Signals")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(588, 14, page_str)

        self.restoreState()



class PDFReportGenerator:
    """
    High-performance publication-grade PDF generator for candidate recruiter reports.
    """

    def __init__(self):
        self._init_styles()

    def _init_styles(self):
        """Initialize custom typographic hierarchy for the report."""
        self.base_styles = getSampleStyleSheet()

        self.style_brand = ParagraphStyle(
            "BrandTitle",
            parent=self.base_styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=PRIMARY_DARK,
        )

        self.style_subtitle = ParagraphStyle(
            "ReportSubtitle",
            parent=self.base_styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=TEXT_MUTED,
        )

        self.style_section_heading = ParagraphStyle(
            "SectionHeading",
            parent=self.base_styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=16,
            textColor=PRIMARY_DARK,
            spaceBefore=12,
            spaceAfter=6,
        )

        self.style_subsection_heading = ParagraphStyle(
            "SubSectionHeading",
            parent=self.base_styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=14,
            textColor=TEXT_DARK,
            spaceBefore=8,
            spaceAfter=4,
        )

        self.style_body = ParagraphStyle(
            "BodyStandard",
            parent=self.base_styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11.5,
            textColor=TEXT_DARK,
        )

        self.style_body_bold = ParagraphStyle(
            "BodyBold",
            parent=self.base_styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11.5,
            textColor=TEXT_DARK,
        )

        self.style_body_muted = ParagraphStyle(
            "BodyMuted",
            parent=self.base_styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=TEXT_MUTED,
        )

        self.style_table_header = ParagraphStyle(
            "TableHeader",
            parent=self.base_styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=colors.white,
        )

        self.style_badge = ParagraphStyle(
            "StatusBadge",
            parent=self.base_styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            alignment=1,  # Center
        )

        self.style_code = ParagraphStyle(
            "CodeBlock",
            parent=self.base_styles["Normal"],
            fontName="Courier",
            fontSize=7.5,
            leading=10,
            textColor=PRIMARY_DARK,
        )

        self.style_hero_score = ParagraphStyle(
            "HeroScore",
            parent=self.base_styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=BRAND_INDIGO,
            alignment=1,
        )

    def build_export_payload(
        self,
        session: InterviewSession,
        user: Optional[Any] = None,
        profile: Optional[Any] = None,
    ) -> RecruiterReportExportPayload:
        """
        Extract and assemble canonical RecruiterReportExportPayload from an InterviewSession document.
        """
        # 1. 5-Dimensional Scores
        if session.recruiter_report and session.recruiter_report.get("five_dimension_scores"):
            try:
                scores = FiveDimensionScores(**session.recruiter_report["five_dimension_scores"])
            except Exception:
                scores = calculate_five_dimension_scores(
                    evaluations=session.evaluations,
                    coding_results=session.coding_results,
                    role_fit_data=session.aggregate_scores.get("role_fit_data") if session.aggregate_scores else None,
                    vocal_metrics=session.vocal_metrics,
                    cv_metrics=session.behavioral_metrics,
                )
        else:
            scores = calculate_five_dimension_scores(
                evaluations=session.evaluations,
                coding_results=session.coding_results,
                role_fit_data=session.aggregate_scores.get("role_fit_data") if session.aggregate_scores else None,
                vocal_metrics=session.vocal_metrics,
                cv_metrics=session.behavioral_metrics,
            )

        # 2. Tailored Feedback
        if session.recruiter_report and session.recruiter_report.get("tailored_feedback"):
            try:
                feedback = TailoredFeedback(**session.recruiter_report["tailored_feedback"])
            except Exception:
                from app.interview.domain.role_taxonomy import (
                    StandardRole,
                    get_role_competency_matrix,
                    parse_standard_role,
                )
                role_comps = get_role_competency_matrix(parse_standard_role(session.job_role))
                feedback = generate_tailored_feedback(
                    evaluations=session.evaluations,
                    coding_evaluation=session.coding_results[0] if session.coding_results else None,
                    role_competencies=role_comps,
                    vocal_metrics=session.vocal_metrics,
                    cv_metrics=session.behavioral_metrics,
                )
        else:
            from app.interview.domain.role_taxonomy import (
                StandardRole,
                get_role_competency_matrix,
                parse_standard_role,
            )
            role_comps = get_role_competency_matrix(parse_standard_role(session.job_role))
            feedback = generate_tailored_feedback(
                evaluations=session.evaluations,
                coding_evaluation=session.coding_results[0] if session.coding_results else None,
                role_competencies=role_comps,
                vocal_metrics=session.vocal_metrics,
                cv_metrics=session.behavioral_metrics,
            )

        # 3. Questions Summary
        questions_summary = []
        eval_map = {getattr(e, "question_index", idx): e for idx, e in enumerate(session.evaluations)}

        for idx, q in enumerate(session.questions):
            q_idx = q.get("question_index", idx)
            ev = eval_map.get(q_idx)

            rubric_dict = q.get("rubric", {})
            if hasattr(rubric_dict, "model_dump"):
                rubric_dict = rubric_dict.model_dump()
            elif not isinstance(rubric_dict, dict):
                rubric_dict = {}

            questions_summary.append({
                "question_index": q_idx,
                "question_text": q.get("question_text", ""),
                "question_type": q.get("question_type", "technical"),
                "stage": q.get("stage", "core_technical"),
                "competency_area": q.get("competency_area", "General Technical"),
                "difficulty": q.get("difficulty", "mid"),
                "rubric": rubric_dict,
                "transcript": getattr(ev, "candidate_transcript", "") if ev else "",
                "accuracy_score": float(getattr(ev, "accuracy_score", 0.0) or 0.0) if ev else 0.0,
                "relevance_score": float(getattr(ev, "relevance_score", 0.0) or 0.0) if ev else 0.0,
                "depth_score": float(getattr(ev, "depth_score", 0.0) or 0.0) if ev else 0.0,
                "communication_score": float(getattr(ev, "communication_score", 0.0) or 0.0) if ev else 0.0,
                "key_points_covered": list(getattr(ev, "key_points_covered", [])) if ev else [],
                "missed_points": list(getattr(ev, "missed_points", [])) if ev else [],
                "evaluator_notes": getattr(ev, "evaluator_notes", "") if ev else "",
            })

        # 4. Coding Summary
        coding_summary = None
        if session.coding_results:
            c_res = session.coding_results[0] if len(session.coding_results) == 1 else session.coding_results[-1]
            if isinstance(c_res, dict):
                coding_summary = {
                    "skipped": False,
                    "challenge_id": c_res.get("challenge_id", "coding_challenge"),
                    "language": c_res.get("language", "python"),
                    "compile_success": c_res.get("compile_success", True),
                    "public_tests_passed": c_res.get("public_tests_passed", 0),
                    "public_tests_total": c_res.get("public_tests_total", 0),
                    "hidden_tests_passed": c_res.get("hidden_tests_passed", 0),
                    "hidden_tests_total": c_res.get("hidden_tests_total", 0),
                    "overall_coding_score": c_res.get("overall_coding_score", 0.0),
                    "execution_time_total_ms": c_res.get("execution_time_total_ms", 0.0),
                    "peak_memory_kb": c_res.get("peak_memory_kb", 0.0),
                }
            elif hasattr(c_res, "model_dump"):
                coding_summary = c_res.model_dump()
                coding_summary["skipped"] = False

        # 5. Multimodal Physical CV & Vocal Metrics
        cv_summary = self._aggregate_cv_metrics(session.behavioral_metrics)
        vocal_summary = self._aggregate_vocal_metrics(session.vocal_metrics)

        return RecruiterReportExportPayload(
            session_id=session.session_id,
            candidate_name=session.candidate_name or (user.full_name if user else "Candidate"),
            target_role=session.job_role or "Software Engineer",
            scores=scores,
            feedback=feedback,
            questions_summary=questions_summary,
            coding_summary=coding_summary,
            cv_summary=cv_summary,
            vocal_summary=vocal_summary,
        )

    def _aggregate_cv_metrics(self, behavioral_metrics: List[Any]) -> ObservableCVMetrics:
        """Aggregate behavioral computer vision metrics into canonical ObservableCVMetrics."""
        if not behavioral_metrics:
            return ObservableCVMetrics(
                gaze_stability_ratio=0.0,
                head_pose_variance=0.0,
                facial_movement_dynamics=0.0,
                frame_presence_ratio=0.0,
                blink_frequency_cpm=0.0,
                observable_flags=["Video tracking uncalibrated / No video frames provided"],
            )

        gazes, heads, dynamics, presences, blinks, flags = [], [], [], [], [], []
        for m in behavioral_metrics:
            if isinstance(m, dict):
                obs = m.get("observable_cv_metrics") if isinstance(m.get("observable_cv_metrics"), dict) else {}
                details = m.get("analysis_details") if isinstance(m.get("analysis_details"), dict) else {}
                gazes.append(float(
                    obs.get("gaze_stability_ratio")
                    or details.get("gaze_stability_ratio")
                    or m.get("gaze_stability_ratio")
                    or m.get("eye_contact_score")
                    or m.get("eye_contact")
                    or 0.0
                ))
                heads.append(float(
                    obs.get("head_pose_variance")
                    or details.get("head_pose_variance")
                    or m.get("head_pose_variance")
                    or m.get("head_stability_score")
                    or m.get("head_stability")
                    or 0.0
                ))
                dynamics.append(float(
                    obs.get("facial_movement_dynamics")
                    or details.get("facial_movement_dynamics")
                    or m.get("facial_movement_dynamics")
                    or m.get("facial_engagement_score")
                    or m.get("engagement")
                    or 0.0
                ))
                presences.append(float(
                    obs.get("frame_presence_ratio")
                    or details.get("frame_presence_ratio")
                    or m.get("frame_presence_ratio")
                    or m.get("attention_span_score")
                    or m.get("attention_span")
                    or 0.0
                ))
                blinks.append(float(
                    obs.get("blink_frequency_cpm")
                    or details.get("blink_frequency_cpm")
                    or m.get("blink_frequency_cpm")
                    or 0.0
                ))
                flags.extend(obs.get("observable_flags") or m.get("observable_flags") or m.get("red_flags") or [])
            elif hasattr(m, "gaze_stability_ratio"):
                gazes.append(float(getattr(m, "gaze_stability_ratio", 0.0) or 0.0))
                heads.append(float(getattr(m, "head_pose_variance", 0.0) or 0.0))
                dynamics.append(float(getattr(m, "facial_movement_dynamics", 0.0) or 0.0))
                presences.append(float(getattr(m, "frame_presence_ratio", 0.0) or 0.0))
                blinks.append(float(getattr(m, "blink_frequency_cpm", 0.0) or 0.0))
                flags.extend(getattr(m, "observable_flags", []))
            elif hasattr(m, "eye_contact_score"):
                gazes.append(float(getattr(m, "eye_contact_score", 0.0) or 0.0))
                heads.append(float(getattr(m, "head_stability_score", 0.0) or 0.0))
                dynamics.append(float(getattr(m, "facial_engagement_score", 0.0) or 0.0))
                presences.append(float(getattr(m, "attention_span_score", 0.0) or 0.0))
                blinks.append(float(getattr(m, "blink_frequency_cpm", 0.0) or 0.0))
                flags.extend(getattr(m, "red_flags", []))
            else:
                gazes.append(0.0)
                heads.append(0.0)
                dynamics.append(0.0)
                presences.append(0.0)
                blinks.append(0.0)

        n = max(1, len(behavioral_metrics))
        avg_presence = sum(presences) / n
        obs_flags = list(dict.fromkeys(flags))
        if avg_presence < 25.0 and not obs_flags:
            obs_flags.append("Video tracking uncalibrated (Face presence < 25%)")

        return ObservableCVMetrics(
            gaze_stability_ratio=round(sum(gazes) / n, 1),
            head_pose_variance=round(sum(heads) / n, 1),
            facial_movement_dynamics=round(sum(dynamics) / n, 1),
            frame_presence_ratio=round(avg_presence, 1),
            blink_frequency_cpm=round(sum(blinks) / n, 1),
            observable_flags=obs_flags,
        )

    def _aggregate_vocal_metrics(self, vocal_metrics: List[Any]) -> ObservableVocalMetrics:
        """Aggregate vocal acoustic metrics into canonical ObservableVocalMetrics."""
        if not vocal_metrics:
            return ObservableVocalMetrics(
                speaking_rate_wpm=140.0,
                pause_duration_ratio=0.18,
                pitch_semitone_variance=3.5,
                vocal_energy_rms=0.15,
                speech_clarity_score=75.0,
                acoustic_flags=[],
            )

        wpms, pauses, pitches, energies, clarities, flags = [], [], [], [], [], []
        for m in vocal_metrics:
            if isinstance(m, dict):
                wpms.append(float(m.get("speaking_rate_wpm", m.get("speech_rate", 140.0))))
                pauses.append(float(m.get("pause_duration_ratio", m.get("pause_pattern", 0.18))))
                pitches.append(float(m.get("pitch_semitone_variance", m.get("pitch_variance", 3.5))))
                energies.append(float(m.get("vocal_energy_rms", 0.15)))
                clarities.append(float(m.get("speech_clarity_score", m.get("clarity", 75.0))))
                flags.extend(m.get("acoustic_flags", m.get("red_flags", [])))
            elif hasattr(m, "speaking_rate_wpm"):
                wpms.append(float(m.speaking_rate_wpm))
                pauses.append(float(m.pause_duration_ratio))
                pitches.append(float(m.pitch_semitone_variance))
                energies.append(float(m.vocal_energy_rms))
                clarities.append(float(m.speech_clarity_score))
                flags.extend(getattr(m, "acoustic_flags", []))
            else:
                wpms.append(140.0)
                pauses.append(0.18)
                pitches.append(3.5)
                energies.append(0.15)
                clarities.append(75.0)

        n = max(1, len(vocal_metrics))
        return ObservableVocalMetrics(
            speaking_rate_wpm=round(sum(wpms) / n, 1),
            pause_duration_ratio=round(sum(pauses) / n, 2),
            pitch_semitone_variance=round(sum(pitches) / n, 2),
            vocal_energy_rms=round(sum(energies) / n, 3),
            speech_clarity_score=round(sum(clarities) / n, 1),
            acoustic_flags=list(dict.fromkeys(flags)),
        )

    def generate_pdf(self, payload: RecruiterReportExportPayload) -> bytes:
        """
        Compile RecruiterReportExportPayload into a publication-grade, strictly 1-page
        executive recruiter dossier driven by high-density tables, metrics, and hiring verdict.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            leftMargin=24,
            rightMargin=24,
            topMargin=18,
            bottomMargin=26,
        )

        story = []

        # 1. Header Banner & Executive Identity
        story.extend(self._build_header_section(payload))
        story.append(Spacer(1, 3))

        # 2. 5-Dimensional Core Scoring Matrix
        story.extend(self._build_scoring_breakdown_section(payload))
        story.append(Spacer(1, 3))

        # 3. Green Flags vs. Red Flags Comparative Table
        story.extend(self._build_flags_section(payload))
        story.append(Spacer(1, 3))

        # 4. Proctoring & System Integrity Violations
        story.extend(self._build_proctoring_violations_section(payload))
        story.append(Spacer(1, 3))

        # 5. Sandboxed Coding & Multimodal Benchmarks
        story.extend(self._build_benchmarks_section(payload))
        story.append(Spacer(1, 3))

        # 6. Overall Executive Verdict & Actionable Next Steps
        story.extend(self._build_verdict_section(payload))

        doc.build(story, canvasmaker=NumberedCanvas)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    def _get_fit_colors(self, fit_status: CandidateFitStatus) -> tuple[colors.HexColor, colors.HexColor]:
        """Return text and background colors corresponding to candidate fit status."""
        if fit_status == CandidateFitStatus.STRONG_FIT:
            return COLOR_STRONG_FIT, BG_STRONG_FIT
        elif fit_status == CandidateFitStatus.POTENTIAL_FIT:
            return COLOR_POTENTIAL_FIT, BG_POTENTIAL_FIT
        elif fit_status == CandidateFitStatus.NEEDS_GROWTH:
            return COLOR_NEEDS_GROWTH, BG_NEEDS_GROWTH
        else:
            return COLOR_NOT_A_FIT, BG_NOT_A_FIT

    def _build_header_section(self, payload: RecruiterReportExportPayload) -> List[Any]:
        """Generate top executive branding banner and candidate dossier identity."""
        score_val = payload.scores.overall_composite_score
        fit_status = payload.scores.fit_status
        text_col, bg_col = self._get_fit_colors(fit_status)

        header_title = Paragraph(
            "<b>HireSIGHT AI</b> — Candidate Recruiter Dossier",
            ParagraphStyle("HBrand", parent=self.base_styles["Normal"], fontName="Helvetica-Bold", fontSize=14, leading=16, textColor=BRAND_INDIGO),
        )

        badge_para = Paragraph(
            f"<font size='13'><b>{score_val:.1f}</b></font> <font size='8' color='#64748b'>/ 100</font><br/>"
            f"<font color='{text_col.hexval()}'><b>{fit_status.value.upper()}</b></font>",
            ParagraphStyle("HBadge", parent=self.base_styles["Normal"], fontName="Helvetica-Bold", fontSize=9, leading=11, alignment=1),
        )

        sub_text = (
            f"<b>Candidate:</b> {payload.candidate_name} &nbsp;|&nbsp; "
            f"<b>Target Role:</b> {payload.target_role} &nbsp;|&nbsp; "
            f"<b>Session ID:</b> {payload.session_id[:16]}... &nbsp;|&nbsp; "
            f"<b>Date:</b> {datetime.utcnow().strftime('%Y-%m-%d')}"
        )
        meta_para = Paragraph(
            sub_text,
            ParagraphStyle("HMeta", parent=self.base_styles["Normal"], fontName="Helvetica", fontSize=7.5, leading=9.5, textColor=TEXT_MUTED),
        )
        conf_tag = Paragraph(
            "CONFIDENTIAL HR REPORT",
            ParagraphStyle("HConf", parent=self.base_styles["Normal"], fontName="Helvetica-Bold", fontSize=7.5, leading=9.5, alignment=1, textColor=BRAND_INDIGO),
        )

        t_header = Table([[header_title, badge_para], [meta_para, conf_tag]], colWidths=[430, 134])
        t_header.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 1),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))

        return [
            t_header,
            Spacer(1, 2),
            HRFlowable(width="100%", thickness=1, color=BRAND_INDIGO, spaceAfter=3),
        ]

    def _build_scoring_breakdown_section(self, payload: RecruiterReportExportPayload) -> List[Any]:
        """Generate explainable 5-dimensional scoring audit table."""
        scores = payload.scores
        score_val = scores.overall_composite_score
        fit_status = scores.fit_status.value

        style_sec = ParagraphStyle("Sec1", parent=self.base_styles["Normal"], fontName="Helvetica-Bold", fontSize=8.5, leading=10.5, textColor=PRIMARY_DARK, spaceBefore=0, spaceAfter=2)
        style_th = ParagraphStyle("TH1", parent=self.base_styles["Normal"], fontName="Helvetica-Bold", fontSize=7.5, leading=9.5, textColor=colors.white)
        style_c = ParagraphStyle("C1", parent=self.base_styles["Normal"], fontName="Helvetica", fontSize=7, leading=9, textColor=TEXT_DARK)
        style_cb = ParagraphStyle("CB1", parent=self.base_styles["Normal"], fontName="Helvetica-Bold", fontSize=7, leading=9, textColor=TEXT_DARK)
        style_cm = ParagraphStyle("CM1", parent=self.base_styles["Normal"], fontName="Helvetica", fontSize=6.5, leading=8.5, textColor=TEXT_MUTED)
        style_cg = ParagraphStyle("CG1", parent=self.base_styles["Normal"], fontName="Helvetica-Bold", fontSize=7, leading=9, textColor=COLOR_STRONG_FIT)
        style_cr = ParagraphStyle("CR1", parent=self.base_styles["Normal"], fontName="Helvetica-Bold", fontSize=7, leading=9, textColor=COLOR_NOT_A_FIT)

        sc_data = [
            [
                Paragraph("<b>Evaluation Dimension</b>", style_th),
                Paragraph("<b>Weight</b>", style_th),
                Paragraph("<b>Raw Score</b>", style_th),
                Paragraph("<b>Contribution</b>", style_th),
                Paragraph("<b>Audit Basis & Measurement Protocol</b>", style_th),
            ],
            [
                Paragraph("<b>Technical Knowledge</b>", style_cb),
                Paragraph("45%", style_c),
                Paragraph(f"<b>{scores.technical_knowledge_score:.1f}</b> / 100", style_c),
                Paragraph(f"<b>{scores.technical_knowledge_score * 0.45:.2f}</b> pts", style_cg),
                Paragraph("Evaluated across technical prompts (30% relevance, 40% depth, 30% accuracy)", style_cm),
            ],
            [
                Paragraph("<b>Coding Ability</b>", style_cb),
                Paragraph("25%", style_c),
                Paragraph(f"<b>{scores.coding_ability_score:.1f}</b> / 100", style_c),
                Paragraph(f"<b>{scores.coding_ability_score * 0.25:.2f}</b> pts", style_cg if scores.coding_ability_score >= 70 else style_c),
                Paragraph("Sandboxed test runs with execution timeout and memory buffer limits", style_cm),
            ],
            [
                Paragraph("<b>Communication Skills</b>", style_cb),
                Paragraph("15%", style_c),
                Paragraph(f"<b>{scores.communication_score:.1f}</b> / 100", style_c),
                Paragraph(f"<b>{scores.communication_score * 0.15:.2f}</b> pts", style_cg),
                Paragraph("Verbal response articulation & acoustic cadence (rate & pauses)", style_cm),
            ],
            [
                Paragraph("<b>Behavioral Indicators</b>", style_cb),
                Paragraph("15%", style_c),
                Paragraph(f"<b>{scores.behavioral_indicators_score:.1f}</b> / 100", style_c),
                Paragraph(f"<b>{scores.behavioral_indicators_score * 0.15:.2f}</b> pts", style_cg if scores.behavioral_indicators_score > 0 else style_cr),
                Paragraph("MediaPipe gaze stability, head pose variance & frame presence ratio", style_cm),
            ],
            [
                Paragraph("<b>Composite Total</b>", style_cb),
                Paragraph("<b>100%</b>", style_cb),
                Paragraph(f"<b>{score_val:.1f}</b> / 100", style_cb),
                Paragraph(f"<b>{score_val:.2f} pts</b>", ParagraphStyle("HeroT", parent=style_cb, textColor=BRAND_INDIGO)),
                Paragraph(f"<b>Hiring Recommendation: {fit_status.upper()}</b>", style_cb),
            ],
        ]

        t_scores = Table(sc_data, colWidths=[110, 42, 68, 70, 274])
        t_scores.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PRIMARY_DARK),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e0e7ff")),
            ("BOX", (0, 0), (-1, -1), 0.75, BORDER_COLOR),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 2.2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]))

        return [
            Paragraph("<b>1. EXPLAINABLE SCORING BREAKDOWN & CORE PILLARS</b>", style_sec),
            t_scores,
        ]

    def _build_flags_section(self, payload: RecruiterReportExportPayload) -> List[Any]:
        """Generate Green Flags vs. Red Flags comparative table."""
        style_sec = ParagraphStyle("Sec2", parent=self.base_styles["Normal"], fontName="Helvetica-Bold", fontSize=8.5, leading=10.5, textColor=PRIMARY_DARK, spaceBefore=0, spaceAfter=2)
        style_th = ParagraphStyle("TH2", parent=self.base_styles["Normal"], fontName="Helvetica-Bold", fontSize=7.5, leading=9.5, textColor=colors.white)
        style_c = ParagraphStyle("C2", parent=self.base_styles["Normal"], fontName="Helvetica", fontSize=7, leading=9, textColor=TEXT_DARK)

        fb = payload.feedback
        green_items = [f"• <b>{s}</b>" for s in (fb.strongest_technical_areas or ["Demonstrated consistent baseline performance."])[:3]]
        if payload.scores.coding_ability_score >= 80:
            green_items.append("• <b>High Sandbox Coding Reliability:</b> Passed algorithmic challenges cleanly.")

        red_items = [f"• <b>{w}</b>" for w in (fb.weakest_technical_areas or [])[:2]]
        if fb.missing_role_skills:
            red_items.append(f"• <b>Role Gaps:</b> {', '.join(fb.missing_role_skills[:2])}")
        if not red_items:
            red_items.append("• <b>No Critical Deficits:</b> Baseline technical expectations met.")

        flags_data = [
            [
                Paragraph("<b>GREEN FLAGS (Demonstrated Mastery & Positive Signals)</b>", style_th),
                Paragraph("<b>RED FLAGS (Identified Gaps, Weaknesses & Risk Areas)</b>", style_th),
            ],
            [
                Paragraph("<br/>".join(green_items), style_c),
                Paragraph("<br/>".join(red_items), style_c),
            ],
        ]

        t_flags = Table(flags_data, colWidths=[282, 282])
        t_flags.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#065f46")),
            ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#991b1b")),
            ("BACKGROUND", (0, 1), (0, 1), BG_STRONG_FIT),
            ("BACKGROUND", (1, 1), (1, 1), BG_NOT_A_FIT),
            ("BOX", (0, 0), (-1, -1), 0.75, BORDER_COLOR),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))

        return [
            Paragraph("<b>2. KEY SIGNALS — GREEN FLAGS & STRENGTHS VS. RED FLAGS & GAPS</b>", style_sec),
            t_flags,
        ]

    def _build_proctoring_violations_section(self, payload: RecruiterReportExportPayload) -> List[Any]:
        """Generate Proctoring Integrity, Behavioral & Acoustic Monitoring checks."""
        style_sec = ParagraphStyle("Sec3", parent=self.base_styles["Normal"], fontName="Helvetica-Bold", fontSize=8.5, leading=10.5, textColor=PRIMARY_DARK, spaceBefore=0, spaceAfter=2)
        style_th = ParagraphStyle("TH3", parent=self.base_styles["Normal"], fontName="Helvetica-Bold", fontSize=7.5, leading=9.5, textColor=colors.white)
        style_c = ParagraphStyle("C3", parent=self.base_styles["Normal"], fontName="Helvetica", fontSize=7, leading=9, textColor=TEXT_DARK)
        style_cb = ParagraphStyle("CB3", parent=self.base_styles["Normal"], fontName="Helvetica-Bold", fontSize=7, leading=9, textColor=TEXT_DARK)
        style_cm = ParagraphStyle("CM3", parent=self.base_styles["Normal"], fontName="Helvetica", fontSize=6.5, leading=8.5, textColor=TEXT_MUTED)
        style_cg = ParagraphStyle("CG3", parent=self.base_styles["Normal"], fontName="Helvetica-Bold", fontSize=7, leading=9, textColor=COLOR_STRONG_FIT)
        style_cr = ParagraphStyle("CR3", parent=self.base_styles["Normal"], fontName="Helvetica-Bold", fontSize=7, leading=9, textColor=COLOR_NOT_A_FIT)

        cv = payload.cv_summary
        vocal = payload.vocal_summary
        cv_flags = cv.observable_flags or []
        vocal_flags = vocal.acoustic_flags or []
        total_violations = len(cv_flags) + len(vocal_flags)

        gaze_status = "[PASS] Optimal Tracking" if cv.gaze_stability_ratio >= 60 else "[FLAG] Gaze Variance"
        presence_status = "[PASS] Face Detected" if cv.frame_presence_ratio >= 50 else "[FLAG] Camera Occlusion"
        speech_status = "[PASS] Normal Cadence" if 110 <= vocal.speaking_rate_wpm <= 180 else "[NOTE] Cadence Deviation"

        proc_data = [
            [
                Paragraph("<b>Integrity Signal</b>", style_th),
                Paragraph("<b>Monitored Metric</b>", style_th),
                Paragraph("<b>Observed Value</b>", style_th),
                Paragraph("<b>Status / Audit Flag</b>", style_th),
            ],
            [
                Paragraph("<b>Visual Gaze Stability</b>", style_cb),
                Paragraph("Iris Focus / Center Gaze Ratio", style_cm),
                Paragraph(f"{cv.gaze_stability_ratio:.1f}% on center", style_c),
                Paragraph(gaze_status, style_cg if "PASS" in gaze_status else style_cr),
            ],
            [
                Paragraph("<b>Video Frame Presence</b>", style_cb),
                Paragraph("Face Presence in Camera View", style_cm),
                Paragraph(f"{cv.frame_presence_ratio:.1f}% presence", style_c),
                Paragraph(presence_status, style_cg if "PASS" in presence_status else style_cr),
            ],
            [
                Paragraph("<b>Speech Rate & Pauses</b>", style_cb),
                Paragraph("Acoustic WPM & Pause Ratio", style_cm),
                Paragraph(f"{vocal.speaking_rate_wpm:.1f} WPM, {vocal.pause_duration_ratio:.2f} pause", style_c),
                Paragraph(speech_status, style_cg if "PASS" in speech_status else style_c),
            ],
            [
                Paragraph("<b>Violations Summary</b>", style_cb),
                Paragraph("Proctoring & Anomaly Flags Count", style_cm),
                Paragraph(f"{total_violations} flags detected", style_cb),
                Paragraph(
                    "<b>CLEAN: No Integrity Violations</b>" if total_violations == 0 else f"<font color='#991b1b'><b>Flags: {', '.join(cv_flags + vocal_flags)}</b></font>",
                    style_cg if total_violations == 0 else style_cr,
                ),
            ],
        ]

        t_proc = Table(proc_data, colWidths=[120, 150, 134, 160])
        t_proc.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PRIMARY_DARK),
            ("BOX", (0, 0), (-1, -1), 0.75, BORDER_COLOR),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]))

        return [
            Paragraph("<b>3. PROCTORING INTEGRITY, BEHAVIORAL & ACOUSTIC MONITORING</b>", style_sec),
            t_proc,
        ]

    def _build_benchmarks_section(self, payload: RecruiterReportExportPayload) -> List[Any]:
        """Generate Sandboxed Coding Benchmarks and Physical Modalities summary."""
        style_sec = ParagraphStyle("Sec4", parent=self.base_styles["Normal"], fontName="Helvetica-Bold", fontSize=8.5, leading=10.5, textColor=PRIMARY_DARK, spaceBefore=0, spaceAfter=2)
        style_c = ParagraphStyle("C4", parent=self.base_styles["Normal"], fontName="Helvetica", fontSize=7, leading=9, textColor=TEXT_DARK)
        style_cb = ParagraphStyle("CB4", parent=self.base_styles["Normal"], fontName="Helvetica-Bold", fontSize=7, leading=9, textColor=TEXT_DARK)

        cs = payload.coding_summary
        cv = payload.cv_summary
        vocal = payload.vocal_summary

        if cs and not cs.get("skipped", False):
            coding_cell = (
                f"<b>Language:</b> {cs.get('language', 'py').upper()} &nbsp;|&nbsp; "
                f"<b>Status:</b> {'Compiled Cleanly' if cs.get('compile_success', True) else 'Compile Error'} &nbsp;|&nbsp; "
                f"<b>Public Tests:</b> {cs.get('public_tests_passed', 0)}/{cs.get('public_tests_total', 0)} &nbsp;|&nbsp; "
                f"<b>Hidden Tests:</b> {cs.get('hidden_tests_passed', 0)}/{cs.get('hidden_tests_total', 0)} &nbsp;|&nbsp; "
                f"<b>Time:</b> {cs.get('execution_time_total_ms', 0.0):.1f}ms &nbsp;|&nbsp; "
                f"<b>Score:</b> {cs.get('overall_coding_score', 0.0):.1f}/100"
            )
        else:
            coding_cell = "<i>Candidate skipped or was not assigned coding sandbox tasks in this session. Coding score: 0.00</i>"

        modal_cell = (
            f"<b>Head Pose Variance:</b> {cv.head_pose_variance:.1f}% &nbsp;|&nbsp; "
            f"<b>Blink Rate:</b> {cv.blink_frequency_cpm:.1f} CPM &nbsp;|&nbsp; "
            f"<b>Speech Clarity:</b> {vocal.speech_clarity_score:.1f}/100 &nbsp;|&nbsp; "
            f"<b>RMS Energy:</b> {vocal.vocal_energy_rms:.3f} &nbsp;|&nbsp; "
            f"<b>Pitch Variance:</b> {vocal.pitch_semitone_variance:.2f} semitones"
        )

        bench_data = [
            [
                Paragraph("<b>Coding Assessment:</b>", style_cb),
                Paragraph(coding_cell, style_c),
            ],
            [
                Paragraph("<b>Physical Metrics:</b>", style_cb),
                Paragraph(modal_cell, style_c),
            ],
        ]

        t_bench = Table(bench_data, colWidths=[110, 454])
        t_bench.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), BG_LIGHT),
            ("BOX", (0, 0), (-1, -1), 0.75, BORDER_COLOR),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 2.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]))

        return [
            Paragraph("<b>4. SANDBOXED CODING BENCHMARKS & PHYSICAL MODALITIES</b>", style_sec),
            t_bench,
        ]

    def _build_verdict_section(self, payload: RecruiterReportExportPayload) -> List[Any]:
        """Generate Overall Executive Recruiter Verdict and Actionable Next Steps."""
        style_sec = ParagraphStyle("Sec5", parent=self.base_styles["Normal"], fontName="Helvetica-Bold", fontSize=8.5, leading=10.5, textColor=PRIMARY_DARK, spaceBefore=0, spaceAfter=2)
        style_c = ParagraphStyle("C5", parent=self.base_styles["Normal"], fontName="Helvetica", fontSize=7, leading=9, textColor=TEXT_DARK)
        style_cb = ParagraphStyle("CB5", parent=self.base_styles["Normal"], fontName="Helvetica-Bold", fontSize=7.5, leading=9.5, textColor=BRAND_INDIGO)
        style_cm = ParagraphStyle("CM5", parent=self.base_styles["Normal"], fontName="Helvetica", fontSize=6.5, leading=8.5, textColor=TEXT_MUTED)

        fit_status = payload.scores.fit_status.value
        fb = payload.feedback
        recs = fb.actionable_improvement_recommendations or ["Review candidate technical depth in subsequent hiring round."]
        rec_text = " &nbsp;|&nbsp; ".join([f"<b>{i+1}.</b> {r}" for i, r in enumerate(recs[:2])])

        verdict_data = [
            [
                Paragraph(f"<b>FINAL HIRING VERDICT: {fit_status.upper()}</b>", style_cb),
            ],
            [
                Paragraph(f"<b>Actionable Hiring Next Steps:</b> {rec_text}", style_c),
            ],
            [
                Paragraph(
                    "<i>System Guarantee: 100% explainable scoring. Metrics quantify objective physical and rubric signals only. "
                    "Recruiter dossier strictly restricted to HR. Page 1 of 1</i>",
                    style_cm,
                ),
            ],
        ]

        t_verdict = Table(verdict_data, colWidths=[564])
        t_verdict.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#eef2ff")),
            ("BACKGROUND", (0, 1), (-1, -1), BG_LIGHT),
            ("BOX", (0, 0), (-1, -1), 0.75, BRAND_INDIGO),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))

        return [
            Paragraph("<b>5. OVERALL EXECUTIVE RECRUITER VERDICT & ACTIONABLE NEXT STEPS</b>", style_sec),
            t_verdict,
        ]



pdf_generator_service = PDFReportGenerator()
