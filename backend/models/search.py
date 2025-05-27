import os
import json
import aiohttp
import ssl
import certifi
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, conint, confloat
from .product import Product
from .product_store import SortOption


class PriceRange(BaseModel):
    """Price range filter parameters"""

    min: Optional[float] = Field(None, description="Minimum price")
    max: Optional[float] = Field(None, description="Maximum price")


class SearchFilters(BaseModel):
    """Search filter parameters"""

    price_range: Optional[PriceRange] = Field(
        None, description="Price range constraints"
    )
    min_rating: Optional[confloat(ge=0, le=5)] = Field(
        None, description="Minimum rating requirement (1-5)"
    )
    free_shipping: Optional[bool] = Field(
        None, description="Whether free shipping is required"
    )
    free_returns: Optional[bool] = Field(
        None, description="Whether free returns are required"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "price_range": {"min": 50.0, "max": 150.0},
                "min_rating": 4.0,
                "free_shipping": True,
                "free_returns": False,
            }
        }


class SearchParameters(BaseModel):
    """Main search parameters model"""

    # Basic search information
    base_query: str = Field(
        ..., description="The base item or category being searched for"
    )
    # Additional filters
    filters: Optional[SearchFilters] = Field(
        None, description="Additional search filters"
    )
    # Sorting option
    sort_by: Optional[SortOption] = Field(
        None,
        description="How to sort the products (relevance, rating, rating_count, rating_weighted, price_low, price_high)",
    )

    def build_search_query(self) -> str:
        """Build the final search query string from all parameters"""
        return self.base_query

    class Config:
        json_schema_extra = {
            "example": {
                "base_query": "running shoes",
                "filters": {
                    "price_range": {"min": 50.0, "max": 150.0},
                    "min_rating": 3.0,
                    "free_shipping": True,
                    "free_returns": False,
                },
                "sort_by": "rating_weighted",
            }
        }


class ProductSearcher:
    """Handles product search operations using external APIs"""

    def __init__(self):
        self.api_key = os.getenv("SERPER_API_KEY")
        if not self.api_key:
            raise ValueError("SERPER_API_KEY environment variable is not set")

    async def search_products(self, search_params: SearchParameters) -> List[Product]:
        """
        Search for products using Serper API with the provided search parameters
        """
        # Build the search query
        search_query = search_params.build_search_query()

        # Build the filters
        filters = search_params.filters or SearchFilters()

        url = "https://google.serper.dev/shopping"
        headers = {"X-API-KEY": self.api_key, "Content-Type": "application/json"}

        # Build tbs parameter for filters
        tbs_parts = ["mr:1"]  # Always include mr:1

        # Add price range filter
        if filters.price_range:
            if filters.price_range.min and filters.price_range.max:
                tbs_parts.append(
                    f"price:1,ppr_min:{filters.price_range.min},ppr_max:{filters.price_range.max}"
                )
            elif filters.price_range.max:
                tbs_parts.append(f"price:1,ppr_max:{filters.price_range.max}")
            elif filters.price_range.min:
                tbs_parts.append(f"price:1,ppr_min:{filters.price_range.min}")

        # Add rating filter
        if filters.min_rating:
            rating_value = int(float(filters.min_rating) * 100)
            tbs_parts.append(f"avg_rating:{rating_value}")

        # Add shipping and returns filters
        if filters.free_shipping:
            tbs_parts.append("ship:1")
        if filters.free_returns:
            tbs_parts.append("free_return:1")

        # Construct payload
        payload = {
            "q": search_query,
            "location": "United States",
            "num": 60,  # Request more results
        }

        if len(tbs_parts) > 1:  # More than just mr:1
            payload["tbs"] = ",".join(tbs_parts)

        # Create SSL context
        ssl_context = ssl.create_default_context(cafile=certifi.where())

        try:
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=ssl_context)
            ) as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        print(
                            f"Serper API error: Status {response.status}, Response: {error_text}"
                        )
                        return []

                    data = await response.json()
                    products = []

                    for result in data.get("shopping", []):
                        try:
                            product = Product.from_serper_result(result)
                            products.append(product)
                        except Exception as e:
                            print(f"Error processing product result: {e}")
                            continue

                    return products

        except Exception as e:
            print(f"Error searching products: {e}")
            return []
