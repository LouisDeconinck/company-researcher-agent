from pydantic import BaseModel, Field
from typing import List

class NewsItem(BaseModel):
    headline: str = Field(description="The headline of the news article")
    date: str = Field(description="The date of the news article")
    link: str = Field(description="URL link to the news article")

class KeyPerson(BaseModel):
    name: str = Field(description="Name of the executive")
    role: str = Field(description="Role/title of the executive")

class JobOpening(BaseModel):
    title: str = Field(description="Job title")
    description: str = Field(description="Job description")
    link: str = Field(description="Link to the job posting")

class ReportSection(BaseModel):
    title: str = Field(description="Section title")
    content: str = Field(description="Section content", default="")
    level: int = Field(description="Heading level (1-6)", default=1)
    
class ReportMetrics(BaseModel):
    total_length: int = Field(description="Total character length of the report")
    sections_count: int = Field(description="Number of sections in the report")
    shallow_sections: list[str] = Field(description="Sections with limited content", default_factory=list)
    missing_sections: list[str] = Field(description="Required sections missing from the report", default_factory=list)
    data_point_count: int = Field(description="Number of numeric data points found", default=0)
    sources_count: int = Field(description="Number of sources cited", default=0) 