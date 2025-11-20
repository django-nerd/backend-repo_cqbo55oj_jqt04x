"""
Database Schemas for Flomote – Slimmer werken met AI

Each Pydantic model corresponds to a MongoDB collection (collection name is the lowercased class name).
Use these schemas for validation of inbound/outbound payloads and for the DB helper functions.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Literal

# Core business entities

class Company(BaseModel):
    name: str = Field(..., description="Bedrijfsnaam")
    sector: str = Field(..., description="Sector of branche")
    employees: int = Field(..., ge=1, le=500, description="Aantal medewerkers")
    contact_name: Optional[str] = Field(None, description="Naam contactpersoon")
    contact_email: Optional[EmailStr] = Field(None, description="E-mailadres contactpersoon")

class QuickScan(BaseModel):
    company_name: str = Field(..., description="Bedrijfsnaam (koppeling)")
    sector: str = Field(..., description="Sector")
    employees: int = Field(..., ge=1, le=500, description="Aantal medewerkers")
    challenges: List[str] = Field(default_factory=list, description="Huidige uitdagingen")
    goals: Optional[List[str]] = Field(default=None, description="Doelen/prioriteiten")

class Workflow(BaseModel):
    company_name: str = Field(..., description="Koppeling naar bedrijf")
    category: Literal["marketing", "analyse", "klantenservice", "hr", "financien", "operations"]
    title: str
    description: str
    status: Literal["gepland", "actief", "gepauzeerd"] = "gepland"

class ContactRequest(BaseModel):
    name: str
    email: EmailStr
    company: Optional[str] = None
    message: Optional[str] = None
    topic: Literal["offerte", "kennismaking", "advies", "overig"] = "kennismaking"

class Pitch(BaseModel):
    name: str
    company: Optional[str] = None
    sector: Optional[str] = None
    pain_points: Optional[List[str]] = None
    tone: Literal["formeel", "vriendelijk", "to-the-point"] = "vriendelijk"

# Response models

class AdviceItem(BaseModel):
    category: str
    title: str
    impact: Literal["laag", "middel", "hoog"]
    effort: Literal["laag", "middel", "hoog"]
    description: str

class AdviceReport(BaseModel):
    summary: str
    recommendations: List[AdviceItem]

