from pydantic import BaseModel, Field
from typing import Optional, List


class InvoiceLineItemExtraction(BaseModel):
    """
    Extracted line item from invoice.
    All fields are nullable where not explicitly present in the document.
    """
    product_name: Optional[str] = Field(default=None, description="Name or model of the equipment item")
    description: Optional[str] = Field(default=None, description="Detailed item description")
    hsn_code: Optional[str] = Field(default=None, description="HSN/SAC code if visible on invoice")
    quantity: Optional[float] = Field(default=None, description="Quantity billed")
    unit_price: Optional[float] = Field(default=None, description="Unit price before tax in document currency")
    taxable_amount: Optional[float] = Field(default=None, description="Taxable base amount for this line")
    tax_rate: Optional[float] = Field(default=None, description="Tax percentage rate (e.g. 18.0 for 18% GST)")
    tax_amount: Optional[float] = Field(default=None, description="Calculated or listed tax amount for item")
    total_amount: Optional[float] = Field(default=None, description="Line item gross total amount")
    serial_number: Optional[str] = Field(default=None, description="Primary serial number if single unit")
    serial_numbers: Optional[List[str]] = Field(default=None, description="Array of serial numbers if multiple units")


class InvoiceExtraction(BaseModel):
    """
    Structured factual extraction schema for invoice documents.
    Interpreted by Gemini Free Tier; validated deterministically by Pydantic.
    """
    invoice_number: Optional[str] = Field(default=None, description="Tax invoice number or invoice identifier")
    invoice_date: Optional[str] = Field(default=None, description="Date of invoice issuance in YYYY-MM-DD or visible format")
    dealer_name: Optional[str] = Field(default=None, description="Name of the issuing dealer/supplier entity")
    dealer_gstin: Optional[str] = Field(default=None, description="GSTIN / Tax ID of the dealer entity")
    dealer_address: Optional[str] = Field(default=None, description="Registered or billing address of the dealer")
    customer_name: Optional[str] = Field(default=None, description="Billed customer / borrower name")
    customer_address: Optional[str] = Field(default=None, description="Billed customer delivery or installation address")
    customer_phone: Optional[str] = Field(default=None, description="Customer phone number if listed")
    items: List[InvoiceLineItemExtraction] = Field(default_factory=list, description="List of itemized invoice lines")
    subtotal: Optional[float] = Field(default=None, description="Subtotal amount before taxes")
    total_tax: Optional[float] = Field(default=None, description="Total tax (GST/VAT) amount")
    total_amount: Optional[float] = Field(default=None, description="Final gross total amount payable")
    currency: Optional[str] = Field(default="INR", description="Document currency code (default: INR)")
    extraction_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Model-reported extraction confidence rating from 0.0 (unconfident) to 1.0 (highly confident)"
    )
    notes: Optional[str] = Field(default=None, description="Extraction notes or non-visible document remarks")
