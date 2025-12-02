"""Export utilities for generating CSV and PDF reports."""

import io
from datetime import datetime
from typing import List

from src.models.candidate import CandidateResult


class ExportService:
    """Handles exporting screening results to CSV and PDF formats."""

    def to_csv(
        self, 
        results: List[CandidateResult],
        job_summary: str
    ) -> bytes:
        """Export results to CSV format.
        
        Args:
            results: List of candidate results
            job_summary: Summary of the job description
            
        Returns:
            CSV file content as bytes
        """
        import pandas as pd
        
        timestamp = datetime.now().isoformat()
        
        # Build data rows
        data = []
        for result in results:
            data.append({
                'Rank': result.rank,
                'Name': result.name,
                'Overall Score': f"{result.overall_score:.1f}%",
                'Skills Score': f"{result.skills_score:.1f}%",
                'Experience Score': f"{result.experience_score:.1f}%",
                'Education Score': f"{result.education_score:.1f}%",
                'Matched Skills': ', '.join(result.matched_skills),
                'Skill Gaps': ', '.join(result.skill_gaps),
                'Strengths': ', '.join(result.strengths),
                'Explanation': result.explanation
            })
        
        df = pd.DataFrame(data)
        
        # Create CSV with metadata header
        output = io.StringIO()
        output.write(f"# Resume Screening Results\n")
        output.write(f"# Generated: {timestamp}\n")
        output.write(f"# Job Summary: {job_summary[:200]}...\n")
        output.write(f"# Total Candidates: {len(results)}\n")
        output.write("#\n")
        
        df.to_csv(output, index=False)
        
        return output.getvalue().encode('utf-8')

    def to_pdf(
        self,
        results: List[CandidateResult],
        job_summary: str
    ) -> bytes:
        """Export results to PDF format.
        
        Args:
            results: List of candidate results
            job_summary: Summary of the job description
            
        Returns:
            PDF file content as bytes
        """
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=12
        )
        story.append(Paragraph("Resume Screening Results", title_style))
        story.append(Spacer(1, 12))
        
        # Metadata
        meta_style = styles['Normal']
        story.append(Paragraph(f"<b>Generated:</b> {timestamp}", meta_style))
        story.append(Paragraph(f"<b>Total Candidates:</b> {len(results)}", meta_style))
        story.append(Spacer(1, 6))
        story.append(Paragraph(f"<b>Job Summary:</b> {job_summary[:300]}...", meta_style))
        story.append(Spacer(1, 20))
        
        # Results table
        if results:
            table_data = [['Rank', 'Name', 'Score', 'Top Skills', 'Gaps']]
            
            for result in results:
                top_skills = ', '.join(result.matched_skills[:3]) if result.matched_skills else 'None'
                gaps = ', '.join(result.skill_gaps[:3]) if result.skill_gaps else 'None'
                
                table_data.append([
                    str(result.rank),
                    result.name[:30],
                    f"{result.overall_score:.1f}%",
                    top_skills[:40],
                    gaps[:40]
                ])
            
            table = Table(table_data, colWidths=[0.5*inch, 1.5*inch, 0.8*inch, 2*inch, 2*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(table)
            story.append(Spacer(1, 20))
            
            # Detailed results
            story.append(Paragraph("Detailed Analysis", styles['Heading2']))
            story.append(Spacer(1, 12))
            
            for result in results:
                story.append(Paragraph(
                    f"<b>#{result.rank} - {result.name}</b> ({result.overall_score:.1f}%)",
                    styles['Heading3']
                ))
                story.append(Paragraph(result.explanation, styles['Normal']))
                if result.strengths:
                    story.append(Paragraph(
                        f"<b>Strengths:</b> {', '.join(result.strengths)}",
                        styles['Normal']
                    ))
                story.append(Spacer(1, 12))
        
        doc.build(story)
        return buffer.getvalue()

    def get_export_metadata(
        self,
        results: List[CandidateResult],
        job_summary: str
    ) -> dict:
        """Get metadata that should be included in exports.
        
        Args:
            results: List of candidate results
            job_summary: Summary of the job description
            
        Returns:
            Dictionary with export metadata
        """
        return {
            'timestamp': datetime.now().isoformat(),
            'job_summary': job_summary,
            'total_candidates': len(results),
            'top_candidate': results[0].name if results else None,
            'top_score': results[0].overall_score if results else None
        }
