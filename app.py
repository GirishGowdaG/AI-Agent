"""Resume Screening Agent - Streamlit Application."""

import streamlit as st
import time
from datetime import datetime

from src.runner import ResumeScreeningRunner
from src.utils.validation import validate_pdf_files, validate_job_description
from src.utils.export import ExportService
from src.models.status import ProcessingStatus
from src.config import MAX_PDF_FILES, MAX_JOB_DESCRIPTION_LENGTH

# Page configuration
st.set_page_config(
    page_title="Resume Screening Agent",
    page_icon="📄",
    layout="wide"
)

# Initialize session state
if 'results' not in st.session_state:
    st.session_state.results = None
if 'job_description' not in st.session_state:
    st.session_state.job_description = ""
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'status' not in st.session_state:
    st.session_state.status = None
if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = []
if 'resume_text' not in st.session_state:
    st.session_state.resume_text = None
if 'job_file' not in st.session_state:
    st.session_state.job_file = None


def main():
    """Main application entry point."""
    st.title("📄 Resume Screening Agent")
    st.markdown("*AI-powered resume screening using Google ADK & Gemini API*")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        st.info(f"Max files: {MAX_PDF_FILES}")
        st.info(f"Max job description: {MAX_JOB_DESCRIPTION_LENGTH} chars")
        
        if st.button("🔄 Reset"):
            st.session_state.results = None
            st.session_state.job_description = ""
            st.session_state.processing = False
            st.session_state.status = None
            st.session_state.uploaded_files = []
            st.session_state.resume_text = None
            st.session_state.job_file = None
            st.rerun()
    
    # Main content
    col1, col2 = st.columns([1, 1])
    
    with col1:
        render_upload_section()
    
    with col2:
        render_job_description_section()
    
    # Screen button
    st.markdown("---")
    render_screen_button()
    
    # Progress and results
    if st.session_state.processing:
        render_progress_section()
    
    if st.session_state.results:
        render_results_section()


def render_upload_section():
    """Render the file upload section."""
    st.header("📁 Upload Resumes")
    
    # Tab for file upload or text input
    tab1, tab2 = st.tabs(["📄 Upload PDF Files", "✍️ Paste Resume Text"])
    
    with tab1:
        uploaded_files = st.file_uploader(
            "Upload PDF resumes",
            type=['pdf'],
            accept_multiple_files=True,
            help=f"Upload up to {MAX_PDF_FILES} PDF files",
            key="resume_files"
        )
        
        if uploaded_files:
            st.success(f"✅ {len(uploaded_files)} file(s) uploaded")
            st.session_state.uploaded_files = uploaded_files
            st.session_state.resume_text = None
        else:
            if 'resume_text' not in st.session_state or not st.session_state.resume_text:
                st.session_state.uploaded_files = []
    
    with tab2:
        resume_text = st.text_area(
            "Paste resume text here",
            height=300,
            help="Enter the full resume text",
            key="resume_text_input"
        )
        
        if resume_text:
            st.success(f"✅ Resume text entered ({len(resume_text)} characters)")
            st.session_state.resume_text = resume_text
            st.session_state.uploaded_files = []
        else:
            if 'uploaded_files' not in st.session_state or not st.session_state.uploaded_files:
                st.session_state.resume_text = None


def render_job_description_section():
    """Render the job description input section."""
    st.header("📝 Job Description")
    
    # Tab for file upload or text input (Upload File is default/first)
    tab1, tab2 = st.tabs(["📄 Upload File", "✍️ Paste Text"])
    
    with tab1:
        job_file = st.file_uploader(
            "Upload job description file",
            type=['pdf', 'txt', 'docx'],
            help="Upload job description as PDF, TXT, or DOCX file",
            key="job_desc_file"
        )
        
        if job_file:
            # Read file content based on type
            try:
                if job_file.type == "application/pdf":
                    from src.utils.pdf_extractor import PDFExtractor
                    extractor = PDFExtractor()
                    job_text, error = extractor.extract_text(job_file.read())
                    if error:
                        st.error(f"❌ {error}")
                        job_text = ""
                elif job_file.type == "text/plain":
                    job_text = job_file.read().decode('utf-8')
                elif job_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                    # Handle DOCX files
                    try:
                        import docx
                        doc = docx.Document(job_file)
                        job_text = "\n".join([para.text for para in doc.paragraphs])
                    except ImportError:
                        st.warning("⚠️ python-docx not installed. Install it to read DOCX files.")
                        job_text = ""
                else:
                    job_text = job_file.read().decode('utf-8')
                
                if job_text:
                    st.session_state.job_description = job_text[:MAX_JOB_DESCRIPTION_LENGTH]
                    st.session_state.job_file = job_file
                    st.success(f"✅ Job description loaded ({len(st.session_state.job_description)} characters)")
                    if len(job_text) > MAX_JOB_DESCRIPTION_LENGTH:
                        st.warning(f"⚠️ Content truncated to {MAX_JOB_DESCRIPTION_LENGTH} characters")
            except Exception as e:
                st.error(f"❌ Error reading file: {str(e)}")
        else:
            if 'job_description' not in st.session_state or not st.session_state.job_description:
                st.session_state.job_file = None
    
    with tab2:
        job_description = st.text_area(
            "Enter the job description",
            value=st.session_state.get('job_description', ''),
            height=300,
            max_chars=MAX_JOB_DESCRIPTION_LENGTH,
            help="Paste the full job description here",
            key="job_desc_text"
        )
        
        if job_description:
            st.session_state.job_description = job_description
            st.session_state.job_file = None
            st.caption(f"📊 {len(job_description)} / {MAX_JOB_DESCRIPTION_LENGTH} characters")
        else:
            if 'job_file' not in st.session_state or not st.session_state.job_file:
                st.session_state.job_description = ""


def process_resumes():
    """Process uploaded resumes against job description."""
    uploaded_files = st.session_state.get('uploaded_files', [])
    resume_text = st.session_state.get('resume_text', None)
    job_description = st.session_state.job_description
    
    # Validate inputs - must have either uploaded files or resume text
    if not uploaded_files and not resume_text:
        st.error("❌ Please upload PDF resumes or paste resume text.")
        return
    
    # Prepare resume data
    if resume_text:
        # Create a temporary PDF-like structure from text
        # For text input, we'll process it directly
        pdf_bytes_list = []
        st.session_state.resume_text_mode = True
    else:
        # Read file bytes
        pdf_bytes_list = [f.read() for f in uploaded_files]
        st.session_state.resume_text_mode = False
    
    # Validate PDFs (only if we have files)
    if pdf_bytes_list:
        pdf_validation = validate_pdf_files(pdf_bytes_list)
        if not pdf_validation.is_valid:
            st.error(f"❌ {pdf_validation.error_message}")
            return
    elif resume_text:
        # For text mode, create a simple validation
        if len(resume_text.strip()) < 50:
            st.error("❌ Resume text is too short. Please provide a complete resume.")
            return
        # Convert text to bytes for processing (wrap in a simple structure)
        pdf_bytes_list = [resume_text.encode('utf-8')]


def render_screen_button():
    """Render the screen resumes button."""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("🔍 Screen Resumes", type="primary", use_container_width=True):
            process_resumes()


def process_resumes():
    """Process uploaded resumes against job description."""
    uploaded_files = st.session_state.get('uploaded_files', [])
    job_description = st.session_state.job_description
    
    # Validate inputs
    if not uploaded_files:
        st.error("❌ Please upload at least one PDF resume.")
        return
    
    # Read file bytes
    pdf_bytes_list = [f.read() for f in uploaded_files]
    
    # Validate PDFs
    pdf_validation = validate_pdf_files(pdf_bytes_list)
    if not pdf_validation.is_valid:
        st.error(f"❌ {pdf_validation.error_message}")
        return
    
    # Validate job description
    jd_validation = validate_job_description(job_description)
    if not jd_validation.is_valid:
        st.error(f"❌ {jd_validation.error_message}")
        return
    
    # Start processing
    st.session_state.processing = True
    st.session_state.results = None
    
    # Create progress placeholders
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    start_time = datetime.now()
    
    def on_status_update(status: ProcessingStatus):
        """Handle status updates from runner."""
        st.session_state.status = status
        if status.total_count > 0:
            progress = status.processed_count / status.total_count
            progress_bar.progress(min(progress, 1.0))
        status_text.text(f"🔄 {status.current_agent}: {status.processed_count}/{status.total_count}")
    
    try:
        runner = ResumeScreeningRunner()
        results, error = runner.process(
            pdf_bytes_list,
            job_description,
            on_status_update=on_status_update,
            generate_explanations=False  # Disable AI explanations for speed
        )
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        if results:
            st.session_state.results = results
            progress_bar.progress(1.0)
            status_text.text(f"✅ Complete! Processed {len(results)} candidates in {elapsed:.1f}s")
            st.success(f"🎉 Successfully screened {len(results)} candidates!")
        else:
            st.error(f"❌ Processing failed: {error}")
            
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
    finally:
        st.session_state.processing = False


def render_progress_section():
    """Render the progress tracking section."""
    status = st.session_state.status
    if status:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Current Agent", status.current_agent)
        with col2:
            st.metric("Progress", f"{status.processed_count}/{status.total_count}")
        with col3:
            st.metric("Elapsed", f"{status.elapsed_seconds:.1f}s")


def render_results_section():
    """Render the results display section."""
    results = st.session_state.results
    if not results:
        return
    
    st.markdown("---")
    st.header("📊 Screening Results")
    
    # Results table
    render_results_table(results)
    
    # Visualizations
    st.subheader("📈 Score Distribution")
    render_score_chart(results)
    
    # Skill overlap
    st.subheader("🎯 Skill Analysis")
    render_skill_summary(results)
    
    # Export buttons
    st.subheader("📥 Export Results")
    render_export_buttons(results)


def render_results_table(results):
    """Render the ranked results table."""
    import pandas as pd
    
    data = []
    for r in results:
        data.append({
            'Rank': r.rank,
            'Name': r.name,
            'Score': f"{r.overall_score:.1f}%",
            'Skills': f"{r.skills_score:.0f}%",
            'Experience': f"{r.experience_score:.0f}%",
            'Education': f"{r.education_score:.0f}%",
            'Top Skills': ', '.join(r.matched_skills[:3]) if r.matched_skills else '-',
            'Gaps': ', '.join(r.skill_gaps[:3]) if r.skill_gaps else '-'
        })
    
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Expandable details
    st.subheader("📋 Detailed Analysis")
    for r in results:
        with st.expander(f"#{r.rank} - {r.name} ({r.overall_score:.1f}%)"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Scores:**")
                st.write(f"- Skills: {r.skills_score:.1f}%")
                st.write(f"- Experience: {r.experience_score:.1f}%")
                st.write(f"- Education: {r.education_score:.1f}%")
            with col2:
                st.markdown("**Matched Skills:**")
                st.write(', '.join(r.matched_skills) if r.matched_skills else 'None')
                st.markdown("**Skill Gaps:**")
                st.write(', '.join(r.skill_gaps) if r.skill_gaps else 'None')
            
            if r.strengths:
                st.markdown("**Strengths:**")
                for s in r.strengths:
                    st.write(f"- {s}")
            
            st.markdown("**Explanation:**")
            st.write(r.explanation)


def render_score_chart(results):
    """Render match score bar chart."""
    import pandas as pd
    
    chart_data = pd.DataFrame({
        'Candidate': [r.name for r in results],
        'Overall Score': [r.overall_score for r in results]
    })
    
    st.bar_chart(chart_data.set_index('Candidate'))


def render_skill_summary(results):
    """Render skill overlap summary."""
    # Aggregate skills
    all_matched = []
    all_gaps = []
    for r in results:
        all_matched.extend(r.matched_skills)
        all_gaps.extend(r.skill_gaps)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Most Common Matched Skills:**")
        if all_matched:
            from collections import Counter
            matched_counts = Counter(all_matched).most_common(5)
            for skill, count in matched_counts:
                st.write(f"- {skill}: {count} candidates")
        else:
            st.write("No matched skills")
    
    with col2:
        st.markdown("**Most Common Skill Gaps:**")
        if all_gaps:
            from collections import Counter
            gap_counts = Counter(all_gaps).most_common(5)
            for skill, count in gap_counts:
                st.write(f"- {skill}: {count} candidates")
        else:
            st.write("No skill gaps")


def render_export_buttons(results):
    """Render CSV and PDF export buttons."""
    export_service = ExportService()
    job_summary = st.session_state.job_description[:200]
    
    col1, col2 = st.columns(2)
    
    with col1:
        csv_data = export_service.to_csv(results, job_summary)
        st.download_button(
            label="📄 Download CSV",
            data=csv_data,
            file_name=f"screening_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    with col2:
        pdf_data = export_service.to_pdf(results, job_summary)
        st.download_button(
            label="📑 Download PDF",
            data=pdf_data,
            file_name=f"screening_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mime="application/pdf"
        )


if __name__ == "__main__":
    main()
