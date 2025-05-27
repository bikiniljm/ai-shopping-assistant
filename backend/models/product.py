from typing import Optional
from pydantic import BaseModel, Field
import re


class Product(BaseModel):
    """Product model for search results"""

    id: str = Field(..., description="Product ID or position")
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., description="Product price")
    price_str: str = Field(..., description="Formatted price string")
    link: str = Field(..., description="Product URL")
    imageUrl: str = Field(..., description="Product image URL")
    rating: Optional[float] = Field(None, description="Product rating")
    ratingCount: int = Field(0, description="Number of ratings")
    delivery: Optional[str] = Field(None, description="Delivery information")
    source: str = Field(..., description="Store/seller name")

    @classmethod
    def from_serper_result(cls, result: dict) -> "Product":
        """Create a Product instance from Serper API result"""
        # Extract price from the price string
        price_str = result.get("price")
        price = 0.0

        if price_str:
            try:
                # Remove $ and , from price string and convert to float
                price = float(price_str.replace("$", "").replace(",", ""))
                # Keep the original formatted price string if valid
                price_str = result["price"]
            except (ValueError, TypeError):
                # If price conversion fails, try to extract numbers from the string
                numbers = re.findall(r"\d+\.?\d*", price_str)
                if numbers:
                    try:
                        price = float(numbers[0])
                        price_str = f"${price:,.2f}"
                    except (ValueError, TypeError):
                        price = 0.0
                        price_str = "Contact for price"
                else:
                    price_str = "Contact for price"
        else:
            price_str = "Contact for price"

        return cls(
            id=str(result.get("position", "")),
            title=result.get("title", "No title"),
            description=result.get("description", ""),
            price=price,
            price_str=price_str,
            link=result.get("link", "#"),
            imageUrl=result.get("imageUrl", ""),
            rating=result.get("rating"),
            ratingCount=result.get("ratingCount", 0),
            delivery=result.get("delivery"),
            source=result.get("source", "Unknown store"),
        )
