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
        self.setFont("Helvetica", 8)
        self.setFillColor(TEXT_MUTED)

        # Running Header (on pages after page 1)
        if self._pageNumber > 1:
            self.drawString(36, 762, "HireSIGHT AI — Candidate Assessment & Recruiter Dossier")
            self.setStrokeColor(BORDER_LIGHT)
            self.setLineWidth(0.5)
            self.line(36, 755, 576, 755)

        # Running Footer (on all pages)
        self.setStrokeColor(BORDER_LIGHT)
        self.setLineWidth(0.5)
        self.line(36, 40, 576, 40)
        self.drawString(36, 28, "CONFIDENTIAL — For Recruiter & Hiring Committee Use Only")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(576, 28, page_str)

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
                from app.interview.domain.role_taxonomy import StandardRole, get_role_competency_matrix
                try:
                    role_comps = get_role_competency_matrix(StandardRole(session.job_role))
                except Exception:
                    role_comps = []
                feedback = generate_tailored_feedback(
                    evaluations=session.evaluations,
                    coding_evaluation=session.coding_results[0] if session.coding_results else None,
                    role_competencies=role_comps,
                    vocal_metrics=session.vocal_metrics,
                    cv_metrics=session.behavioral_metrics,
                )
        else:
            from app.interview.domain.role_taxonomy import StandardRole, get_role_competency_matrix
            try:
                role_comps = get_role_competency_matrix(StandardRole(session.job_role))
            except Exception:
                role_comps = []
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
                gaze_stability_ratio=75.0,
                head_pose_variance=75.0,
                facial_movement_dynamics=70.0,
                frame_presence_ratio=85.0,
                blink_frequency_cpm=18.0,
                observable_flags=[],
            )

        gazes, heads, dynamics, presences, blinks, flags = [], [], [], [], [], []
        for m in behavioral_metrics:
            if isinstance(m, dict):
                gazes.append(float(m.get("gaze_stability_ratio", m.get("eye_contact", 75.0))))
                heads.append(float(m.get("head_pose_variance", m.get("head_stability", 75.0))))
                dynamics.append(float(m.get("facial_movement_dynamics", m.get("engagement", 70.0))))
                presences.append(float(m.get("frame_presence_ratio", m.get("attention_span", 85.0))))
                blinks.append(float(m.get("blink_frequency_cpm", 18.0)))
                flags.extend(m.get("observable_flags", m.get("red_flags", [])))
            elif hasattr(m, "gaze_stability_ratio"):
                gazes.append(float(m.gaze_stability_ratio))
                heads.append(float(m.head_pose_variance))
                dynamics.append(float(m.facial_movement_dynamics))
                presences.append(float(m.frame_presence_ratio))
                blinks.append(float(m.blink_frequency_cpm))
                flags.extend(getattr(m, "observable_flags", []))
            else:
                gazes.append(75.0)
                heads.append(75.0)
                dynamics.append(70.0)
                presences.append(85.0)
                blinks.append(18.0)

        n = max(1, len(behavioral_metrics))
        return ObservableCVMetrics(
            gaze_stability_ratio=round(sum(gazes) / n, 1),
            head_pose_variance=round(sum(heads) / n, 1),
            facial_movement_dynamics=round(sum(dynamics) / n, 1),
            frame_presence_ratio=round(sum(presences) / n, 1),
            blink_frequency_cpm=round(sum(blinks) / n, 1),
            observable_flags=list(dict.fromkeys(flags)),
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
        Compile RecruiterReportExportPayload into a publication-grade PDF file in-memory.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            leftMargin=36,
            rightMargin=36,
            topMargin=48,
            bottomMargin=48,
        )

        story = []

        # 1. Header & Executive Dossier Summary
        story.extend(self._build_header_section(payload))
        story.append(Spacer(1, 10))

        # 2. 5-Dimensional Explainable Scoring Breakdown
        story.extend(self._build_scoring_breakdown_section(payload))
        story.append(Spacer(1, 10))

        # 3. Tailored Feedback & Remediation Roadmap
        story.extend(self._build_feedback_section(payload))
        story.append(Spacer(1, 10))

        # 4. Multimodal Physical & Acoustic Analysis
        story.extend(self._build_multimodal_section(payload))
        story.append(Spacer(1, 10))

        # 5. Sandboxed Coding Assessment Summary
        story.extend(self._build_coding_section(payload))
        story.append(Spacer(1, 10))

        # 6. Question-by-Question Rubric & Transcript Comparison
        story.extend(self._build_questions_section(payload))

        # Build document with multi-pass NumberedCanvas
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
        """Generate top executive branding and candidate dossier summary card."""
        elements = []

        # Top Title & Date Row
        title_para = Paragraph("HireSIGHT AI", self.style_brand)
        sub_para = Paragraph(
            f"<b>Recruiter Assessment Report</b> | Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
            self.style_subtitle,
        )
        header_table = Table([[title_para, sub_para]], colWidths=[200, 340])
        header_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (1, 0), (1, 0), "RIGHT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(header_table)
        elements.append(HRFlowable(width="100%", thickness=1.5, color=BRAND_INDIGO, spaceAfter=8))

        # Candidate Executive Overview Card
        fit_status = payload.scores.fit_status
        text_col, bg_col = self._get_fit_colors(fit_status)

        overview_data = [
            [
                Paragraph(f"<b>Candidate:</b> {payload.candidate_name}", self.style_body),
                Paragraph(f"<b>Target Role:</b> {payload.target_role}", self.style_body),
                Paragraph("<b>Overall Score:</b>", self.style_body),
            ],
            [
                Paragraph(f"<b>Session ID:</b> <font color='#64748b'>{payload.session_id[:16]}...</font>", self.style_body),
                Paragraph(f"<b>Questions Evaluated:</b> {len(payload.questions_summary)}", self.style_body),
                Paragraph(f"<font size='16' color='{BRAND_INDIGO.hexval()}'><b>{payload.scores.overall_composite_score:.1f}</b></font> <font size='9' color='#64748b'>/ 100</font>", self.style_body),
            ],
            [
                Paragraph(f"<b>Fit Assessment:</b> <font color='{text_col.hexval()}'><b>{fit_status.value}</b></font>", self.style_body),
                Paragraph(f"<b>Coding Round:</b> {'Completed' if payload.coding_summary and not payload.coding_summary.get('skipped') else 'Skipped / None'}", self.style_body),
                Paragraph(f"<font color='{text_col.hexval()}'><b>{fit_status.value.upper()}</b></font>", self.style_body),
            ]
        ]

        overview_table = Table(overview_data, colWidths=[200, 200, 140])
        overview_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), BG_LIGHT),
            ("BOX", (0, 0), (-1, -1), 1, BORDER_COLOR),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(overview_table)

        return elements

    def _build_scoring_breakdown_section(self, payload: RecruiterReportExportPayload) -> List[Any]:
        """Generate 5-dimensional explainable scoring table and mathematical audit box."""
        elements = []
        elements.append(Paragraph("1. 5-Dimensional Explainable Scoring Breakdown", self.style_section_heading))

        scores = payload.scores

        dim_rows = [
            [
                Paragraph("<b>Evaluation Dimension</b>", self.style_table_header),
                Paragraph("<b>Weight</b>", self.style_table_header),
                Paragraph("<b>Score (0-100)</b>", self.style_table_header),
                Paragraph("<b>Weighted Contribution</b>", self.style_table_header),
                Paragraph("<b>Status / Audit Note</b>", self.style_table_header),
            ],
            [
                Paragraph("<b>Technical Knowledge</b>", self.style_body),
                Paragraph("35%", self.style_body),
                Paragraph(f"<b>{scores.technical_knowledge_score:.1f}</b>", self.style_body),
                Paragraph(f"{scores.technical_knowledge_score * 0.35:.2f} pts", self.style_body),
                Paragraph("Rubric relevance (30%), depth (40%), accuracy (30%)", self.style_body_muted),
            ],
            [
                Paragraph("<b>Coding Ability</b>", self.style_body),
                Paragraph("20%", self.style_body),
                Paragraph(f"<b>{scores.coding_ability_score:.1f}</b>", self.style_body),
                Paragraph(f"{scores.coding_ability_score * 0.20:.2f} pts", self.style_body),
                Paragraph("Sandboxed public & hidden test execution", self.style_body_muted),
            ],
            [
                Paragraph("<b>Role Fit Alignment</b>", self.style_body),
                Paragraph("15%", self.style_body),
                Paragraph(f"<b>{scores.role_fit_score:.1f}</b>", self.style_body),
                Paragraph(f"{scores.role_fit_score * 0.15:.2f} pts", self.style_body),
                Paragraph("Competency taxonomy & skill coverage matrix", self.style_body_muted),
            ],
            [
                Paragraph("<b>Communication</b>", self.style_body),
                Paragraph("15%", self.style_body),
                Paragraph(f"<b>{scores.communication_score:.1f}</b>", self.style_body),
                Paragraph(f"{scores.communication_score * 0.15:.2f} pts", self.style_body),
                Paragraph("Verbal clarity (60%) + acoustic speech rate/pauses (40%)", self.style_body_muted),
            ],
            [
                Paragraph("<b>Behavioral Indicators</b>", self.style_body),
                Paragraph("15%", self.style_body),
                Paragraph(f"<b>{scores.behavioral_indicators_score:.1f}</b>", self.style_body),
                Paragraph(f"{scores.behavioral_indicators_score * 0.15:.2f} pts", self.style_body),
                Paragraph("Objective physical CV signals (gaze, pose, dynamics)", self.style_body_muted),
            ],
            [
                Paragraph("<b>Overall Composite Score</b>", self.style_body_bold),
                Paragraph("<b>100%</b>", self.style_body_bold),
                Paragraph(f"<font color='{BRAND_INDIGO.hexval()}'><b>{scores.overall_composite_score:.1f}</b></font>", self.style_body_bold),
                Paragraph(f"<b>{scores.overall_composite_score:.2f} pts</b>", self.style_body_bold),
                Paragraph(f"<b>Fit Status: {scores.fit_status.value}</b>", self.style_body_bold),
            ],
        ]

        table = Table(dim_rows, colWidths=[130, 50, 75, 95, 190])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BG_HEADER),
            ("BOX", (0, 0), (-1, -1), 1, BORDER_COLOR),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
            ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, BG_LIGHT]),
            ("BACKGROUND", (0, -1), (-1, -1), BG_CARD),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(table)

        # Audit Formula Explanation
        audit_note = (
            "<b>Mathematical Audit Formula:</b> "
            "Composite = 0.35 × Tech + 0.20 × Coding + 0.15 × RoleFit + 0.15 × Comm + 0.15 × Behavioral. "
            "All weights strictly sum to 1.00 with zero opaque or arbitrary adjustments."
        )
        audit_table = Table([[Paragraph(audit_note, self.style_body_muted)]], colWidths=[540])
        audit_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), BG_LIGHT),
            ("BOX", (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(Spacer(1, 4))
        elements.append(audit_table)

        return elements

    def _build_feedback_section(self, payload: RecruiterReportExportPayload) -> List[Any]:
        """Generate tailored feedback, skill gaps, and concrete remediation roadmaps."""
        elements = []
        elements.append(Paragraph("2. Tailored Feedback & Skill Gap Analysis", self.style_section_heading))

        fb = payload.feedback

        # Strengths & Weaknesses 2-Column Table
        strong_items = [f"• {s}" for s in fb.strongest_technical_areas] if fb.strongest_technical_areas else ["• Demonstrated consistent baseline performance."]
        weak_items = [f"• {w}" for w in fb.weakest_technical_areas] if fb.weakest_technical_areas else ["• No critical technical deficits flagged."]

        strong_text = "<br/>".join(strong_items[:5])
        weak_text = "<br/>".join(weak_items[:5])

        sw_data = [
            [
                Paragraph("<b>Demonstrated Technical Mastery</b>", self.style_table_header),
                Paragraph("<b>Identified Technical & Role Gaps</b>", self.style_table_header),
            ],
            [
                Paragraph(strong_text, self.style_body),
                Paragraph(weak_text, self.style_body),
            ],
        ]

        sw_table = Table(sw_data, colWidths=[270, 270])
        sw_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#065f46")), # Emerald Dark
            ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#991b1b")), # Red Dark
            ("BOX", (0, 0), (-1, -1), 1, BORDER_COLOR),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
            ("BACKGROUND", (0, 1), (-1, 1), BG_LIGHT),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(sw_table)

        # Actionable Remediation Roadmap
        if fb.actionable_improvement_recommendations:
            elements.append(Spacer(1, 4))
            elements.append(Paragraph("<b>Actionable Technology Remediation Roadmap:</b>", self.style_subsection_heading))
            rec_items = []
            for idx, r in enumerate(fb.actionable_improvement_recommendations[:4], start=1):
                rec_items.append([
                    Paragraph(f"<b>{idx}.</b>", self.style_body_bold),
                    Paragraph(r, self.style_body),
                ])
            rec_table = Table(rec_items, colWidths=[20, 520])
            rec_table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ]))
            elements.append(rec_table)

        return elements

    def _build_multimodal_section(self, payload: RecruiterReportExportPayload) -> List[Any]:
        """Generate Computer Vision and Acoustic Physical Analysis tables."""
        elements = []
        elements.append(Paragraph("3. Multimodal Physical & Acoustic Analysis (Observable Signals Only)", self.style_section_heading))

        cv = payload.cv_summary
        vocal = payload.vocal_summary

        cv_flags_str = ", ".join(cv.observable_flags) if cv.observable_flags else "None (Optimal stability)"
        vocal_flags_str = ", ".join(vocal.acoustic_flags) if vocal.acoustic_flags else "None (Optimal acoustic cadence)"

        multi_data = [
            [
                Paragraph("<b>Computer Vision Physical Signals</b>", self.style_table_header),
                Paragraph("<b>Acoustic Speech & Vocal Signals</b>", self.style_table_header),
            ],
            [
                Paragraph(
                    f"• <b>Gaze Stability Ratio:</b> {cv.gaze_stability_ratio:.1f}%<br/>"
                    f"• <b>Head Pose Variance:</b> {cv.head_pose_variance:.1f}%<br/>"
                    f"• <b>Facial Movement Dynamics:</b> {cv.facial_movement_dynamics:.1f}%<br/>"
                    f"• <b>Frame Presence Ratio:</b> {cv.frame_presence_ratio:.1f}%<br/>"
                    f"• <b>Blink Frequency:</b> {cv.blink_frequency_cpm:.1f} CPM<br/>"
                    f"• <b>Physical Flags:</b> {cv_flags_str}",
                    self.style_body,
                ),
                Paragraph(
                    f"• <b>Speaking Rate:</b> {vocal.speaking_rate_wpm:.1f} WPM (Norm: 120-160)<br/>"
                    f"• <b>Pause Duration Ratio:</b> {vocal.pause_duration_ratio:.2f} (Norm: 0.10-0.25)<br/>"
                    f"• <b>Pitch Semitone Variance:</b> {vocal.pitch_semitone_variance:.2f} semitones<br/>"
                    f"• <b>RMS Energy Stability:</b> {vocal.vocal_energy_rms:.3f}<br/>"
                    f"• <b>Speech Clarity Score:</b> {vocal.speech_clarity_score:.1f} / 100<br/>"
                    f"• <b>Acoustic Flags:</b> {vocal_flags_str}",
                    self.style_body,
                ),
            ],
        ]

        multi_table = Table(multi_data, colWidths=[270, 270])
        multi_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PRIMARY_DARK),
            ("BOX", (0, 0), (-1, -1), 1, BORDER_COLOR),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
            ("BACKGROUND", (0, 1), (-1, 1), BG_LIGHT),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(multi_table)

        # Invariant Note
        disclaimer = (
            "<i>System Invariant: All CV and vocal metrics quantify objective physical signals only. "
            "HireSIGHT does not perform psychological mind-reading or emotion classification.</i>"
        )
        elements.append(Spacer(1, 3))
        elements.append(Paragraph(disclaimer, self.style_body_muted))

        return elements

    def _build_coding_section(self, payload: RecruiterReportExportPayload) -> List[Any]:
        """Generate Sandboxed Coding Assessment summary or clean skip card."""
        elements = []
        elements.append(Paragraph("4. Sandboxed Coding Assessment", self.style_section_heading))

        cs = payload.coding_summary
        if not cs or cs.get("skipped", False):
            skip_data = [[
                Paragraph("<b>Coding Round Skipped / No Submissions:</b> Candidate did not execute coding challenge tasks in this session. Coding ability weighted score defaults to 0.00 points.", self.style_body_muted)
            ]]
            skip_table = Table(skip_data, colWidths=[540])
            skip_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), BG_LIGHT),
                ("BOX", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]))
            elements.append(skip_table)
            return elements

        # Completed coding round
        c_score = cs.get("overall_coding_score", 0.0)
        c_lang = cs.get("language", "python").upper()
        c_compile = "Success" if cs.get("compile_success", True) else "Failed"
        c_pub = f"{cs.get('public_tests_passed', 0)} / {cs.get('public_tests_total', 0)}"
        c_hid = f"{cs.get('hidden_tests_passed', 0)} / {cs.get('hidden_tests_total', 0)}"
        c_time = f"{cs.get('execution_time_total_ms', 0.0):.1f} ms"
        c_mem = f"{cs.get('peak_memory_kb', 0.0):.1f} KB"

        code_data = [
            [
                Paragraph("<b>Language</b>", self.style_table_header),
                Paragraph("<b>Compilation</b>", self.style_table_header),
                Paragraph("<b>Public Tests</b>", self.style_table_header),
                Paragraph("<b>Hidden Tests</b>", self.style_table_header),
                Paragraph("<b>Runtime / Mem</b>", self.style_table_header),
                Paragraph("<b>Coding Score</b>", self.style_table_header),
            ],
            [
                Paragraph(f"<b>{c_lang}</b>", self.style_body),
                Paragraph(f"<b>{c_compile}</b>", self.style_body),
                Paragraph(c_pub, self.style_body),
                Paragraph(c_hid, self.style_body),
                Paragraph(f"{c_time} | {c_mem}", self.style_body),
                Paragraph(f"<font color='{BRAND_INDIGO.hexval()}'><b>{c_score:.1f} / 100</b></font>", self.style_body_bold),
            ]
        ]

        code_table = Table(code_data, colWidths=[80, 80, 85, 85, 110, 100])
        code_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PRIMARY_DARK),
            ("BOX", (0, 0), (-1, -1), 1, BORDER_COLOR),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
            ("BACKGROUND", (0, 1), (-1, 1), BG_LIGHT),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(code_table)

        return elements

    def _build_questions_section(self, payload: RecruiterReportExportPayload) -> List[Any]:
        """Generate question-by-question transcripts with rubric comparison and robust pagination."""
        elements = []
        elements.append(Paragraph("5. Question-by-Question Rubric & Transcript Evaluations", self.style_section_heading))

        if not payload.questions_summary:
            elements.append(Paragraph("<i>No question evaluation records available for this session.</i>", self.style_body_muted))
            return elements

        for q in payload.questions_summary:
            q_idx = q.get("question_index", 0) + 1
            stage = q.get("stage", "core_technical").replace("_", " ").title()
            competency = q.get("competency_area", "General")
            difficulty = q.get("difficulty", "mid").title()

            q_text = q.get("question_text", "No question prompt available.")
            rubric = q.get("rubric", {})
            ref_ans = rubric.get("reference_answer", "No reference answer key provided.") if isinstance(rubric, dict) else ""
            key_concepts = rubric.get("key_concepts_expected", []) if isinstance(rubric, dict) else []
            concepts_str = ", ".join(key_concepts) if key_concepts else "None specified"

            transcript = q.get("transcript", "") or "(No candidate verbal or text answer submitted)"
            acc = q.get("accuracy_score", 0.0)
            rel = q.get("relevance_score", 0.0)
            depth = q.get("depth_score", 0.0)
            comm = q.get("communication_score", 0.0)

            covered = ", ".join(q.get("key_points_covered", [])) or "None identified"
            missed = ", ".join(q.get("missed_points", [])) or "None identified"

            header_table = Table([
                [
                    Paragraph(
                        f"<b>Question {q_idx}: {competency}</b> ({stage} | {difficulty})",
                        self.style_table_header,
                    ),
                    Paragraph(
                        f"Acc: {acc:.0f} | Rel: {rel:.0f} | Depth: {depth:.0f} | Comm: {comm:.0f}",
                        ParagraphStyle("QHeaderScore", parent=self.style_table_header, alignment=2),
                    ),
                ]
            ], colWidths=[380, 160])
            header_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), PRIMARY_DARK),
                ("BOX", (0, 0), (-1, -1), 1, BORDER_COLOR),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]))

            q_elements = [
                header_table,
                Spacer(1, 3),
                Paragraph(f"<b>Prompt:</b> {q_text}", self.style_body),
                Paragraph(f"<b>Key Concepts Expected:</b> {concepts_str}", self.style_body_muted),
                Paragraph(f"<b>Reference Answer Key:</b> <font color='#475569'>{ref_ans}</font>", self.style_body_muted),
                Paragraph(f"<b>Candidate Transcript:</b> <font color='#1e293b'>\"{transcript}\"</font>", self.style_body),
                Paragraph(f"<b>Points Covered:</b> <font color='#059669'>{covered}</font> | <b>Points Missed:</b> <font color='#dc2626'>{missed}</font>", self.style_body),
                Spacer(1, 4),
                HRFlowable(width="100%", thickness=0.5, color=BORDER_LIGHT, spaceAfter=4),
            ]

            # If transcript is normal length, try to keep question together; otherwise let it flow
            if len(transcript) < 400:
                elements.append(KeepTogether(q_elements))
            else:
                elements.extend(q_elements)

        return elements


pdf_generator_service = PDFReportGenerator()
