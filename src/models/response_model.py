from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime, timezone
import re
from .base_models import NewsItem, KeyPerson, JobOpening, ReportSection, ReportMetrics

class ResponseModel(BaseModel):
    name: str = Field(title="Company Name", description="The trade name of the company")
    description: str = Field(title="Description", description="A concise summary of the company (one to two sentences)")
    industries: List[str] = Field(title="Industries", description="A list of industries or sectors the company operates in")
    annual_revenue: int = Field(title="Annual Revenue", description="The current yearly revenue, best estimate if not available")
    employees: int = Field(title="Number of Employees", description="The total number of employees currently employed by the company")
    funding: str = Field(title="Funding History", description="Summary of the company's funding rounds, key investors, and total capital raised")
    key_personnel: List[KeyPerson] = Field(title="Key Personnel", description="A list of key executives and their roles")
    founded_year: int = Field(title="Founded Year", description="The year the company was established")
    website: str = Field(title="Website", description="The main website URL of the company")
    phone: Optional[str] = Field(title="Phone Number", description="The phone number of the company", default="")
    email: Optional[str] = Field(title="Email Address", description="The email address of the company", default="")
    address: Optional[str] = Field(title="Address", description="The physical address of the company", default="")
    facebook: Optional[str] = Field(title="Facebook", description="The facebook page URL of the company", default="")
    instagram: Optional[str] = Field(title="Instagram", description="The instagram page URL of the company", default="")
    twitter: Optional[str] = Field(title="Twitter", description="The twitter page URL of the company", default="")
    linkedin: Optional[str] = Field(title="LinkedIn", description="The linkedin page URL of the company", default="")
    youtube: Optional[str] = Field(title="YouTube", description="The youtube channel URL of the company", default="")
    tiktok: Optional[str] = Field(title="TikTok", description="The tiktok page URL of the company", default="")
    pinterest: Optional[str] = Field(title="Pinterest", description="The pinterest page URL of the company", default="")
    reddit: Optional[str] = Field(title="Reddit", description="The reddit page URL of the company", default="")
    github: Optional[str] = Field(title="GitHub", description="The github page URL of the company", default="")
    indeed: Optional[str] = Field(title="Indeed", description="The indeed page URL of the company", default="")
    competitors: List[str] = Field(title="Major Competitors", description="A list of the company's key competitors")
    recent_news: List[NewsItem] = Field(title="Recent News", description="A list of recent news items about the company")
    job_openings: List[JobOpening] = Field(title="Job Openings", description="A list of current job openings at the company")
    report: str = Field(title="Business Report", description="An extensive and detailed business report of the company formatted as markdown")

    @field_validator('recent_news', mode='before')
    @classmethod
    def parse_news(cls, v):
        if isinstance(v, str):
            # If it's a string, try to convert it to a list with one item
            return [{"headline": v, "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"), "link": ""}]
        return v

    @field_validator('key_personnel', mode='before')
    @classmethod
    def parse_personnel(cls, v):
        if isinstance(v, list) and v and isinstance(v[0], dict):
            # If it's already a list of dicts, ensure they have the right keys
            return [{"name": p.get("name", ""), "role": p.get("role", "")} for p in v]
        elif isinstance(v, list) and v and isinstance(v[0], str):
            # If it's a list of strings, try to convert them to job objects
            return [{"name": p.split(" - ")[0], "role": p.split(" - ")[1] if " - " in p else ""} for p in v]
        return v

    @field_validator('job_openings', mode='before')
    @classmethod
    def parse_jobs(cls, v):
        if isinstance(v, list) and v and isinstance(v[0], dict):
            # If it's already a list of dicts, ensure they have the right keys
            return [{"title": j.get("title", ""), "description": j.get("description", ""), "link": j.get("link", "")} for j in v]
        elif isinstance(v, list) and v and isinstance(v[0], str):
            # If it's a list of strings, try to convert them to job objects
            return [{"title": j, "description": "", "link": ""} for j in v]
        return v

    @field_validator('report')
    @classmethod
    def validate_report(cls, v):
        """Ensure the report is extensive and properly formatted."""
        if not v:
            return "No detailed report available."
            
        # Check minimum length of report (15000 characters is about 2500 words)
        if len(v) < 15000:
            v += "\n\n**Note: This report has been automatically flagged as potentially too brief. A comprehensive business report should contain detailed information across multiple business aspects.**"
            
        # Check for appropriate markdown structure (at least 5 headings)
        headings = re.findall(r'^#+\s+.+$', v, re.MULTILINE)
        if len(headings) < 5:
            v += "\n\n**Note: This report appears to lack proper section structure. A comprehensive report should be organized into multiple clearly defined sections.**"
            
        # Check for sufficient sections
        required_sections = [
            "executive summary", "company overview", "product", "service", 
            "market analysis", "competitive", "financial", "leadership", 
            "marketing", "technology", "innovation", "risk", "future", "sources"
        ]
        
        found_sections = 0
        for section in required_sections:
            if re.search(section, v.lower()):
                found_sections += 1
                
        if found_sections < 7:  # At least half of the key sections should be present
            v += "\n\n**Note: This report may be missing important business analysis sections. A comprehensive report should cover multiple aspects of business operations and strategy.**"
        
        # Check for data references and figures
        data_points = re.findall(r'\d+%|\$\d+|\d+ million|\d+ billion|\d+\.\d+|approx\w* \d+', v, re.IGNORECASE)
        if len(data_points) < 10:
            v += "\n\n**Note: This report may lack sufficient quantitative data points such as percentages, financial figures, or market metrics.**"
        
        # Check for sources and citations
        sources = re.findall(r'\[.*?\]\(.*?\)', v) + re.findall(r'Source:.*?[\.,]', v, re.IGNORECASE)
        if len(sources) < 5:
            v += "\n\n**Note: This report contains few citations or sources. A comprehensive report should cite multiple reliable sources to support its findings.**"
        
        # Check for comparative analysis
        if not re.search(r'compared to|versus|competition|competitors|market share|industry average', v, re.IGNORECASE):
            v += "\n\n**Note: This report may lack sufficient comparative analysis against competitors or industry benchmarks.**"

        return v
        
    @field_validator('report', mode='after')
    @classmethod
    def parse_report_structure(cls, v, info):
        """Parse the report structure into sections for better analysis"""
        if not v:
            return v
            
        values = info.data
            
        # Extract report metrics
        metrics = ReportMetrics(
            total_length=len(v),
            sections_count=0,
            data_point_count=0,
            sources_count=0
        )
        
        # Parse sections with improved heading detection
        sections = []
        headings_pattern = re.compile(r'^(#+)\s+(.+)$', re.MULTILINE)
        headings_matches = list(headings_pattern.finditer(v))
        
        # If no headings found, return early with warning
        if not headings_matches:
            metrics.sections_count = 0
            metrics.missing_sections = ["No proper headings found in the report"]
            values['report_metrics'] = metrics
            values['report_sections'] = []
            return v
            
        # Build sections list with improved content analysis
        metrics.sections_count = len(headings_matches)
        
        for i, match in enumerate(headings_matches):
            level = len(match.group(1))
            title = match.group(2)
            start_pos = match.end()
            
            # Find end of this section (next heading of same or higher level, or end of text)
            end_pos = len(v)
            for j in range(i+1, len(headings_matches)):
                next_level = len(headings_matches[j].group(1))
                next_pos = headings_matches[j].start()
                # Only consider it the end if it's a heading of the same or higher level
                if next_level <= level:
                    end_pos = next_pos
                    break
                
            content = v[start_pos:end_pos].strip()
            section = ReportSection(title=title, content=content, level=level)
            sections.append(section)
            
            # Check for shallow sections with stricter requirements based on level
            if level == 1 and len(content) < 800:
                metrics.shallow_sections.append(title)
            elif level == 2 and len(content) < 500:
                metrics.shallow_sections.append(f"{title} (subsection)")
        
        # Count data points with more comprehensive patterns
        data_points = re.findall(r'\d+%|\$\d+|\d+M|\d+B|\d+K|\d+ million|\d+ billion|\d+\.\d+|approx\w* \d+|\d{4}(?:-\d{2}){2}|\b\d{1,3}(?:,\d{3})+\b', v, re.IGNORECASE)
        metrics.data_point_count = len(data_points)
        
        # Count sources with more comprehensive patterns
        sources = re.findall(r'\[.*?\]\(.*?\)', v) + re.findall(r'Source:.*?[\.,]', v, re.IGNORECASE) + re.findall(r'According to .*?[\.,]', v, re.IGNORECASE) + re.findall(r'cited by .*?[\.,]', v, re.IGNORECASE)
        metrics.sources_count = len(sources)
        
        # Check for missing required sections with more comprehensive matching
        required_sections = [
            "executive summary", "company overview", "business model", "revenue streams",
            "products", "services", "market analysis", "competitive landscape", 
            "financial", "leadership", "organizational structure", "company culture", 
            "technology", "innovation", "marketing", "sales strategy", 
            "recent news", "developments", "industry trends", "future outlook",
            "risk assessment", "sources", "citations"
        ]
        
        found_sections = set()
        for section in sections:
            section_title_lower = section.title.lower()
            for required in required_sections:
                if required in section_title_lower or any(req_part in section_title_lower for req_part in required.split()):
                    found_sections.add(required)
                    break
        
        metrics.missing_sections = [s for s in required_sections if s not in found_sections]
        
        # Store metrics and sections in values
        values['report_metrics'] = metrics
        values['report_sections'] = sections
        
        return v
        
    class Config:
        extra = "ignore"  # Ignore extra fields 