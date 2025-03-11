from pydantic_ai import RunContext, ModelRetry
from ..models import ResponseModel
import re

async def validate_company_report(ctx: RunContext, result: ResponseModel) -> ResponseModel:
    """Advanced validation of the company report with potential model retries for improvements."""
    if not result.report:
        raise ModelRetry("Please generate a comprehensive business report for the company.")
        
    # Get the report metrics
    metrics = result.report_metrics
    if not metrics:
        # If metrics are missing, manually parse the report to create metrics
        content_length = len(result.report)
        headings = re.findall(r'^#+\s+.+$', result.report, re.MULTILINE)
        data_points = re.findall(r'\d+%|\$\d+|\d+ million|\d+ billion|\d+\.\d+|approx\w* \d+', result.report, re.IGNORECASE)
        sources = re.findall(r'\[.*?\]\(.*?\)', result.report) + re.findall(r'Source:.*?[\.,]', result.report, re.IGNORECASE)
        
        # Create minimal metrics for validation
        metrics = {
            "total_length": content_length,
            "sections_count": len(headings),
            "data_point_count": len(data_points),
            "sources_count": len(sources),
            "missing_sections": [],
            "shallow_sections": []
        }
        
    # Check for critical issues that require a retry
    critical_issues = []
    
    # 1. Check if the report is too short - increased minimum to 15,000 characters
    if metrics['total_length'] < 15000:
        critical_issues.append(f"The report is too brief at only {metrics['total_length']} characters. Please expand it to at least 15,000 characters with detailed information across all required sections.")
        
    # 2. Check if there are too few sections - increased to 15 required sections
    if metrics['sections_count'] < 15:
        critical_issues.append(f"The report has only {metrics['sections_count']} sections. Please structure it with at least 15 major sections as specified in the requirements.")
        
    # 3. Check for missing critical sections - expanded list
    critical_sections = [
        "executive summary", "company overview", "business model", "revenue streams",
        "products", "services", "market analysis", "competitive landscape", 
        "financial", "leadership", "organizational structure", "company culture", 
        "technology", "innovation", "marketing", "sales strategy", 
        "recent news", "developments", "industry trends", "future outlook",
        "risk assessment", "sources", "citations", "job listings"
    ]
    
    # Count how many critical sections are found
    found_sections = 0
    for section in critical_sections:
        if re.search(section, result.report.lower()):
            found_sections += 1
    
    # Require at least 15 of the critical sections (more than 65%)
    if found_sections < 15:
        critical_issues.append(f"The report only covers {found_sections} of the required topic areas. Please ensure your report covers at least 15 of the required sections with detailed content.")
        
    # 4. Check for shallow sections
    shallow_section_count = len(metrics['shallow_sections']) if 'shallow_sections' in metrics else 0
    if shallow_section_count > 1:
        shallow_sections_list = ", ".join(metrics['shallow_sections']) if 'shallow_sections' in metrics else "multiple sections"
        critical_issues.append(f"These sections have insufficient content: {shallow_sections_list}. Please expand each with detailed analysis of at least 800 characters per major section.")
        
    # 5. Check for data points - increased to 30 minimum
    data_point_count = metrics['data_point_count'] if 'data_point_count' in metrics else 0
    if data_point_count < 30:
        critical_issues.append(f"The report contains only {data_point_count} quantitative data points. Please include at least 30 specific figures, percentages, or metrics to support your analysis.")
        
    # 6. Check for sources - increased to 15 minimum
    sources_count = metrics['sources_count'] if 'sources_count' in metrics else 0
    if sources_count < 15:
        critical_issues.append(f"The report cites only {sources_count} sources. Please include at least 15 specific sources with links to support your findings.")
        
    # 7. Check for markdown formatting variety
    heading_levels = re.findall(r'^(#+)\s+', result.report, re.MULTILINE)
    heading_level_variety = len(set([len(h) for h in heading_levels]))
    
    if heading_level_variety < 3:
        critical_issues.append("The report lacks structural depth. Please use at least 3 different heading levels (# for main sections, ## for subsections, ### for sub-subsections).")
    
    list_patterns = re.findall(r'^\s*[\*\-\+]\s+|^\s*\d+\.\s+', result.report, re.MULTILINE)
    if len(list_patterns) < 10:
        critical_issues.append("The report lacks lists for organized information. Please use at least 10 bulleted or numbered lists to present information clearly.")
    
    emphasis_patterns = re.findall(r'\*\*.*?\*\*|\*.*?\*|__.*?__|_.*?_', result.report)
    if len(emphasis_patterns) < 15:
        critical_issues.append("The report lacks emphasis formatting. Please use bold and italic formatting to highlight at least 15 key points or important information.")
    
    # If there are critical issues, request improvements
    if critical_issues:
        improvement_request = "Please improve the company report by addressing these issues:\n\n" + "\n".join([f"- {issue}" for issue in critical_issues])
        raise ModelRetry(improvement_request)
        
    return result 